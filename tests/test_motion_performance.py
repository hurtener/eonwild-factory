"""Regression witnesses for articulation, recipe reuse, and real cyclic contact."""
from dataclasses import replace
import math
from pathlib import Path
import json

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.grounded_gait import GroundedGait, sample_grounded_gait, build_grounded_plan
from eonwild_motion.solve.performance import Performance, decorate_plan, load_performance
from eonwild_motion.solve.skin_targets import cyclic_authority, _cyclic_fill
from eonwild_motion.dynamics.contact_authority import PatchFrame, AuthorityThresholds


@pytest.mark.parametrize('length', [.6, -.38])
def test_articulated_grounded_stroke_is_not_the_old_shuffle(length):
    gait = GroundedGait(step_length_body_heights=length, toe_flex_degrees=24,
        foot_recovery_pitch_degrees=28, push_off_pitch_degrees=20, rounded_swing_peak_fraction=.42)
    plan = build_grounded_plan(gait, 2.5)
    rows = plan['samples']
    assert rows[-1]['root_forward_m'] == pytest.approx(2 * gait.cycles * length * 2.5)
    assert not any(row['flight'] for row in rows)
    assert {row['support_count'] for row in rows} == {1, 2}
    foot = [row['feet']['left'] for row in rows]
    assert max(f['toe_flex_degrees'] for f in foot) > 23
    assert min(f['foot_pitch_degrees'] for f in foot) < -25
    assert max(f['foot_pitch_degrees'] for f in foot) > 18
    assert max(f['height_m'] for f in foot) > .1


@pytest.mark.parametrize('boundary', ['release', 'touchdown'])
def test_authored_ankle_and_toes_have_continuous_release(boundary):
    gait = GroundedGait(toe_flex_degrees=24,foot_recovery_pitch_degrees=28,push_off_pitch_degrees=20)
    period = 2 * gait.step_period_s
    t = period * gait.duty_factor if boundary == 'release' else period
    eps = 1e-6
    frames = [sample_grounded_gait(gait, t + d, 2.)['feet']['left'] for d in [-eps, 0, eps]]
    for key in ['height_m','forward_m','foot_pitch_degrees','toe_flex_degrees']:
        assert abs(frames[0][key] - frames[2][key]) < 1e-5


@pytest.mark.parametrize('parameters', [{'lane_width_body_heights':0}, {'tail_yaw_degrees':100}, {'center_tail':1}, {'gaze_elevation_degrees':float('nan')}, {'pelvis_sway_body_heights':.1}])
def test_performance_rejects_invalid_or_unbounded_controls(parameters):
    with pytest.raises(ContractError): Performance(**parameters)


def test_performance_has_no_shared_mutable_plan_state():
    plan = build_grounded_plan(GroundedGait(),2.)
    before = json.dumps(plan,sort_keys=True)
    a = decorate_plan(plan,Performance())
    b = decorate_plan(plan,Performance(gaze_elevation_degrees=5))
    a['samples'][0]['feet']['left']['forward_m']=99
    assert json.dumps(plan,sort_keys=True)==before
    assert b['samples'][0]['feet']['left']['forward_m']!=99
    with pytest.raises(ContractError): load_performance({'schema':'eonwild.motion.performance.v1','parameters':{'mystery':3}})


def patch(time,x,y=0):
    points=((x,y,0),(x+.05,y,0),(x,y,.08))
    return PatchFrame(time,points,points)


def test_loop_terminal_contact_gets_real_next_cycle_context():
    # Late support begins exactly at the duplicate end. It must be evaluated
    # with next cycle's contacts, not rejected as one isolated frame.
    frames=[patch(0,0),patch(.1,0),patch(.2,0,.1),patch(.3,1,.1),patch(.4,1)]
    loaded=[True,True,False,False,True]
    verdict=cyclic_authority(frames,loaded,[1,0,0],AuthorityThresholds())
    assert verdict['verdict']=='PASS'
    assert verdict['maximum_skin_seam_error_m']==pytest.approx(0)


@pytest.mark.parametrize('case',['hover','skate','seam','state'])
def test_cyclic_authority_does_not_hide_bad_endpoints_or_contacts(case):
    frames=[patch(0,0),patch(.1,0),patch(.2,0,.1),patch(.3,1,.1),patch(.4,1)]
    loaded=[True,True,False,False,True]
    if case=='hover': frames=[replace(f,sole_m=tuple((x,y+.01,z) for x,y,z in f.sole_m),toe_m=tuple((x,y+.01,z) for x,y,z in f.toe_m)) for f in frames]
    if case=='skate': frames[1]=patch(.1,.1)
    if case=='seam': frames[-1]=patch(.4,1.01)
    if case=='state': loaded[-1]=False
    assert cyclic_authority(frames,loaded,[1,0,0],AuthorityThresholds())['verdict']=='FAIL'


def test_unloaded_correction_is_bounded_between_contact_endpoints():
    times=np.linspace(0,1,11)
    loaded=np.array([True,True,True,False,False,False,False,False,True,True,True])
    values=np.zeros((11,3));values[8:,1]=.02
    filled=_cyclic_fill(times,values,loaded)
    assert np.array_equal(filled[loaded],values[loaded])
    assert np.all(filled[:,1]>=0) and np.all(filled[:,1]<=.02)


def test_new_locomotion_recipes_retain_v9_run_stride_and_explicit_narrow_gauge():
    root=Path(__file__).parents[1]
    for gait in ['run','sprint']:
        old=json.loads((root/f'catalog/programs/heavy-biped.{gait}.v2.json').read_text())['parameters']
        new=json.loads((root/f'catalog/programs/heavy-biped.{gait}.v3.json').read_text())['parameters']
        for key in ['step_length_body_heights','step_period_s','flight_fraction','compression_peak_fraction','push_off_start_fraction']:
            assert new[key]==old[key]
    for name in ['walk.v2','fast-walk.v1','reverse-walk.v3','run.v3','sprint.v3']:
        recipe=json.loads((root/f'recipes/heavy-biped/{name}.json').read_text())
        assert 'performance_profile' in recipe
        params=json.loads((root/recipe['performance_profile']['path']).read_text())['parameters']
        assert params['lane_width_body_heights']<=.3
        assert params['tail_yaw_degrees']>0
