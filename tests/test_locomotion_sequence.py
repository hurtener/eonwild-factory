"""Connected walking must preserve root and planted-foot continuity."""
import numpy as np
import pytest
from eonwild_motion.planning.grounded_gait import GroundedGait
from eonwild_motion.planning.locomotion_sequence import WalkSequence

@pytest.fixture(params=[None, {"response_step_fraction":.9,"moving_articulation_floor":.85,"anticipation_seconds":.35}, {"response_step_fraction":.9,"moving_articulation_floor":.85,"anticipation_seconds":.35,"stop_stance_policy":"retain_braking_support"}])
def sequence(request):
    gait = GroundedGait(step_period_s=1.23, step_length_body_heights=.6, duty_factor=.62)
    return WalkSequence(gait, 2., {}, walking_response=request.param)

def test_stage_joins_preserve_body_and_feet(sequence):
    for boundary in sequence.bounds[1:-1]:
        a,b = (sequence.sample(boundary+d) for d in (-1e-7,1e-7))
        for key in ('root_forward_m','pelvis_height_offset_m','root_velocity_mps'):
            assert abs(a[key]-b[key]) < 1e-5
        for side in ('left','right'):
            for key in ('forward_m','height_m','foot_pitch_degrees'):
                assert abs(a['feet'][side][key]-b['feet'][side][key]) < 1e-4

def test_stance_placements_do_not_slide_under_changing_speed(sequence):
    rows = [sequence.sample(float(t)) for t in np.linspace(0,sequence.duration,3000)]
    for a,b in zip(rows,rows[1:]):
        assert b['root_forward_m'] >= a['root_forward_m']-1e-10
        assert b['support_count'] >= 1
        for side in ('left','right'):
            if a['feet'][side]['contact'] and b['feet'][side]['contact']:
                assert a['feet'][side]['forward_m'] == pytest.approx(b['feet'][side]['forward_m'], abs=1e-9)
    assert rows[0]['root_velocity_mps'] == 0
    assert rows[-1]['root_velocity_mps'] == 0
    assert rows[0]['support_count'] == rows[-1]['support_count'] == 2

def test_cadence_changes_integrate_velocity(sequence):
    for time in np.linspace(sequence.bounds[1]+.01,sequence.bounds[5]-.01,100):
        a,b = sequence.sample(time-1e-5), sequence.sample(time+1e-5)
        assert (b['root_forward_m']-a['root_forward_m'])/2e-5 == pytest.approx(sequence.sample(time)['root_velocity_mps'], abs=1e-7)


def test_slow_toe_off_releases_its_actual_roll_amplitude(sequence):
    for choreography in (sequence.start, sequence.stop):
        for side in ('left','right'):
            for touchdown in (-choreography.step, 0., choreography.step):
                lift = choreography.liftoff(touchdown)
                if lift < 0: continue
                foot = choreography.foot(side, lift + 1e-7)
                if foot['contact']: continue
                assert foot['stance_roll_release_scale'] == pytest.approx(choreography.articulation_weight(foot['liftoff_time_s']))


def test_purposeful_start_reaches_speed_before_second_step():
    gait=GroundedGait(step_period_s=1.23, step_length_body_heights=.6, duty_factor=.62)
    s=WalkSequence(gait,2.,{},walking_response={"response_step_fraction":.9,"moving_articulation_floor":.85,"anticipation_seconds":.35})
    assert s.start.sample(s.start.delay+gait.step_period_s)['root_velocity_mps']==pytest.approx(s.speed)
    for c in (s.start,s.stop):
        begin,duration=c.response_window()
        for t in np.linspace(begin+.001,begin+duration-.001,80):
            assert (c.root(t+1e-5)[0]-c.root(t-1e-5)[0])/2e-5==pytest.approx(c.root(t)[1],abs=1e-7)


def test_stop_retains_useful_support_without_a_post_stop_reset():
    gait=GroundedGait(step_period_s=1.23,step_length_body_heights=.6,duty_factor=.62)
    response={"response_step_fraction":.9,"moving_articulation_floor":.85,"anticipation_seconds":.35}
    previous=WalkSequence(gait,2.,{},walking_response=response)
    candidate=WalkSequence(gait,2.,{},walking_response={**response,"stop_stance_policy":"retain_braking_support"})
    # The entire preceding sequence stays identical. At stop entry the existing
    # airborne foot must still own the same landing, rather than jump to idle.
    for t in np.linspace(0,candidate.bounds[-2],200):
        assert candidate.sample(t)==previous.sample(t)
    c=candidate.stop
    end=c.sample(c.duration)
    assert end['feet']['left']['forward_m']!=end['feet']['right']['forward_m']
    for t in np.linspace(c.ramp,c.duration,100):
        row=c.sample(t)
        assert row['root_velocity_mps']==0 and row['support_count']==2
        for s in ('left','right'):
            f=row['feet'][s]
            assert f['forward_m']==end['feet'][s]['forward_m']
            assert f['height_m']==f['foot_pitch_degrees']==f['toe_flex_degrees']==0
    # The earlier braking placement stays planted while the other leg arrives.
    fixed=c.foot('right',c.step)['forward_m']
    for t in np.linspace(c.step,c.duration,100):
        assert c.foot('right',t)['contact']
        assert c.foot('right',t)['forward_m']==fixed


def test_retained_stop_reports_its_actual_exit_stance_and_continuous_landings():
    from eonwild_motion.planning.gait_transition import GaitTransition, _Choreography, build_transition_plan
    gait=GroundedGait(step_period_s=1.23,step_length_body_heights=.6,duty_factor=.62)
    transition=GaitTransition('stop',ramp_cycles=1,response_step_fraction=.9,
        moving_articulation_floor=.85,stop_stance_policy='retain_braking_support')
    plan=build_transition_plan(transition,gait,2.)
    assert plan['transition_contract']['exit_pose']=='retained_braking_stance'
    c=_Choreography(transition,gait,2.)
    for s,t in [('right',c.step),('left',c.ramp)]:
        before,after=(c.foot(s,t+d) for d in (-1e-7,1e-7))
        for key in ('forward_m','height_m','foot_pitch_degrees','toe_flex_degrees'):
            assert abs(before[key]-after[key])<1e-4
