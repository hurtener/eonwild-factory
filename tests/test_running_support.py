"""The support-driven cycle must preserve flight and continuous momentum."""
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.running import resolve_running
from eonwild_motion.planning.running_support import RunningSupportCycle

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(params=[(a,v) for a in ['allo','tarbo'] for v in [2,3,4,5]])
def cycle(request):
    animal, version = request.param
    recipe = json.loads((ROOT/f'catalog/behaviors/running-review.v{version}.json').read_text())
    profile = json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    return RunningSupportCycle(resolve_running(profile,recipe),profile['authoring']['bodyHeightM'],recipe['coordination'])

def test_support_impulse_balances_gravity_and_has_a_real_flight(cycle):
    times = np.linspace(0,cycle.step,2001)
    rows = [cycle.sample(t) for t in times]
    loads = np.array([r['support_load_bodyweights'] for r in rows])
    assert np.trapezoid(loads,times) == pytest.approx(cycle.step,abs=1e-6)
    flight = [r for r in rows if r['flight']]
    assert len(flight)>0
    for r in flight:
        assert r['support_load_bodyweights']==0
        assert all(f['support_load_bodyweights']==0 for f in r['feet'].values())
        assert r['pelvis_vertical_acceleration_mps2']==pytest.approx(-cycle.gravity)
    for r in rows:
        assert sum(f['support_load_bodyweights'] for f in r['feet'].values())==pytest.approx(r['support_load_bodyweights'])

def test_root_and_feet_keep_periodic_positions_and_boundary_velocities(cycle):
    eps=1e-5
    for t in np.linspace(.001,2*cycle.step-.001,101):
        a,b=cycle.sample(t),cycle.sample(t+2*cycle.step)
        assert b['root_forward_m']-a['root_forward_m']==pytest.approx(2*cycle.speed*cycle.step)
        assert a['pelvis_height_offset_m']==pytest.approx(b['pelvis_height_offset_m'])
        for side in a['feet']:
            assert a['feet'][side]['height_m']==pytest.approx(b['feet'][side]['height_m'])
            assert b['feet'][side]['forward_m']-a['feet'][side]['forward_m']==pytest.approx(2*cycle.speed*cycle.step)
            if a['feet'][side]['contact']:
                assert cycle.sample(t+eps)['feet'][side]['forward_m']==pytest.approx(a['feet'][side]['forward_m'],abs=1e-6)
    for t in [0,cycle.contact*cycle.step,cycle.step,2*cycle.step]:
        a,b=cycle.sample(t-eps),cycle.sample(t+eps)
        assert abs(a['pelvis_vertical_velocity_mps']-b['pelvis_vertical_velocity_mps'])<.001
        assert abs(a['pelvis_vertical_acceleration_mps2']-b['pelvis_vertical_acceleration_mps2'])<.001
        assert (b['pelvis_height_offset_m']-a['pelvis_height_offset_m'])/(2*eps)==pytest.approx(cycle.sample(t)['pelvis_vertical_velocity_mps'],abs=1e-5)
        for side in a['feet']:
            for key in ['forward_m','height_m','foot_pitch_degrees','pad_pitch_degrees']:
                center = cycle.sample(t)['feet'][side][key]
                before, after = a['feet'][side][key], b['feet'][side][key]
                # Compare continuity, not a hidden speed limit on the other
                # foot while it is partway through a valid fast recovery.
                assert abs(center-(before+after)*.5)<2e-6
                assert abs((center-before)/eps-(after-center)/eps)<.2

def test_loading_yields_before_propulsion_and_recovery_has_one_peak(cycle):
    landing=cycle.sample(0)
    bottom=cycle.sample(cycle.contact*cycle.step*.5)
    launch=cycle.sample(cycle.contact*cycle.step)
    assert landing['pelvis_vertical_velocity_mps']<0
    assert bottom['pelvis_height_offset_m']<landing['pelvis_height_offset_m']
    assert abs(bottom['pelvis_vertical_velocity_mps'])<1e-9
    assert launch['pelvis_vertical_velocity_mps']>0
    values=[cycle.gather(u) for u in np.linspace(0,1,201)]
    peak=np.argmax(values)
    assert np.min(np.diff(values[:peak+1]))>=-1e-9
    assert np.max(np.diff(values[peak:]))<=1e-9


def test_rear_fold_clears_behind_hip_and_opens_for_contact():
    for animal in ('allo','tarbo'):
        recipe=json.loads((ROOT/'catalog/behaviors/running-review.v4.json').read_text())
        profile=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
        c=RunningSupportCycle(resolve_running(profile,recipe),profile['authoring']['bodyHeightM'],recipe['coordination'])
        t=(c.contact+(2-c.contact)*c.policy['recovery_peak_fraction'])*c.step
        row=c.sample(t); foot=row['feet']['left']
        assert not foot['contact']
        assert foot['forward_m']<row['root_forward_m']
        assert foot['height_m']>.2*c.height
        assert foot['running_leg_shape']['metatarsus_min_degrees']<-40
        landing=c.sample(2*c.step)
        assert landing['feet']['left']['height_m']==0
        assert landing['feet']['left']['running_leg_shape']['metatarsus_min_degrees']==-5


def test_damped_tail_has_quieter_base_and_periodic_curvature():
    from eonwild_motion.planning.running_support import support_body_response
    roles={'chest':'chest','head':'head','neck':['neck'],
           'tail':['base','middle','tip']}
    for animal in ('allo','tarbo'):
        profile=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
        results=[]
        for version in (3,4):
            recipe=json.loads((ROOT/f'catalog/behaviors/running-review.v{version}.json').read_text())
            cycle=RunningSupportCycle(resolve_running(profile,recipe),profile['authoring']['bodyHeightM'],recipe['coordination'])
            rows=support_body_response(cycle,cycle.plan(),roles,profile,{'left':-1,'right':1})
            angles=np.array([[r['sagittal_node_degrees'][n] for n in roles['tail']] for r in rows])
            assert np.max(np.abs(angles[0]-angles[-1]))<1e-8
            results.append(angles)
        assert np.ptp(results[1][:,0])<.2*np.ptp(results[0][:,0])
        assert np.ptp(results[1][:,-1])>.1


@pytest.mark.parametrize('animal', ['allo', 'tarbo'])
def test_regional_body_response_preserves_leg_cycle_and_loop_seam(animal):
    from eonwild_motion.planning.running_support import support_body_response
    profile=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    cycles=[]
    for version in (4,5):
        recipe=json.loads((ROOT/f'catalog/behaviors/running-review.v{version}.json').read_text())
        cycles.append(RunningSupportCycle(resolve_running(profile,recipe),profile['authoring']['bodyHeightM'],recipe['coordination']))
    before,after=cycles
    for t in np.linspace(0,4*after.step,501):
        assert before.sample(t)==after.sample(t)
    roles={'spine':['lumbar','thoracic'],'chest':'chest','neck':['neck'],
           'head':'head','tail':['base','middle','tip']}
    # Sample on both sides of the loop seam to catch resets hidden by matching
    # endpoint values alone. A response must retain velocity through the seam.
    eps=1e-4; period=2*after.step
    query=[period-eps,period,period+eps]+list(np.linspace(0,period,241))
    plan={'samples':[after.sample(t) for t in query]}
    rows=support_body_response(after,plan,roles,profile,{'left':-1,'right':1})
    for key in ('sagittal_node_degrees','node_roll_yaw_degrees'):
        for name in rows[0][key]:
            values=np.array([r[key][name] for r in rows])
            assert np.max(np.abs(values[3]-values[-1]))<1e-8
            assert np.max(np.abs((values[2]-values[1])-(values[1]-values[0])))/eps<.1
    for name in roles['spine']+[roles['chest']]+roles['tail']:
        assert np.ptp([r['node_roll_yaw_degrees'][name][1] for r in rows[3:]])>.1


@pytest.mark.parametrize('value', [[float('nan'),0], [True,0], [1], 'yaw'])
def test_regional_axial_sample_rejects_invalid_rotation(value):
    from eonwild_motion.solve.airborne_gait import _require_body_response_sample
    from eonwild_motion.errors import ContractError
    with pytest.raises(ContractError):
        _require_body_response_sample({'sagittal_node_degrees':{},'node_roll_yaw_degrees':{'chest':value}})
