"""Connected walking must preserve root and planted-foot continuity."""
import numpy as np
import pytest
from eonwild_motion.planning.grounded_gait import GroundedGait
from eonwild_motion.planning.locomotion_sequence import WalkSequence

@pytest.fixture
def sequence():
    gait = GroundedGait(step_period_s=1.23, step_length_body_heights=.6, duty_factor=.62)
    return WalkSequence(gait, 2., {})

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
                assert foot['stance_roll_release_scale'] == pytest.approx(choreography.envelope(foot['liftoff_time_s'])[0])
