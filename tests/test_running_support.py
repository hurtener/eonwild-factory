"""The support-driven cycle must preserve flight and continuous momentum."""
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.running import resolve_running
from eonwild_motion.planning.running_support import RunningSupportCycle

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(params=[(a,v) for a in ['allo','tarbo'] for v in [2,3]])
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
                assert abs(a['feet'][side][key]-b['feet'][side][key])<.002

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
