"""Behavior constraints: lateral recovery widens support without crossing."""
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.lateral_recovery import LateralRecoverySteps
from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities
from eonwild_motion.solve.turn_support import contact_loads

ROOT=Path(__file__).resolve().parents[1]

def planner(animal='allo',acceleration_scale=1.):
    profile=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    c=resolve_capabilities(profile);c['lateralAccelerationMps2']*=acceleration_scale
    recipe=json.loads((ROOT/'catalog/behaviors/lateral-recovery-review.v1.json').read_text())
    return LateralRecoverySteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,
        {'left':-.36,'right':.36},{'left':.1,'right':.1},c,recipe),c

@pytest.mark.parametrize('animal',['allo','tarbo'])
def test_support_is_frozen_free_foot_unloaded_and_stance_never_crosses(animal):
    p,_=planner(animal);previous=None
    assert [e['side'] for e in p.events]==['right','left','left','right']
    for t in np.linspace(0,p.duration,801):
        sample=p.sample(t);feet=sample['feet'];loads=contact_loads(p,t)
        assert any(f['contact'] for f in feet.values())
        assert feet['right']['position'][0]-feet['left']['position'][0]>=.72-1e-10
        for side,f in feet.items():
            if not f['contact']:assert loads[side]==0.
            if previous and f['contact'] and previous[side]['contact']:
                np.testing.assert_allclose(f['position'],previous[side]['position'],atol=1e-12)
                assert f['heading']==previous[side]['heading']
        previous=feet
    for side in p.anchors:
        np.testing.assert_allclose(p.sample(p.duration)['feet'][side]['position'],p.anchors[side],atol=1e-12)

def test_lateral_path_uses_force_per_mass_budget_and_continuous_boundaries():
    p,c=planner();heavy,_=planner(acceleration_scale=.5)
    assert heavy.duration>p.duration
    for b in p.blocks:
        ts=np.linspace(b['start'],b['end'],501);dt=ts[1]-ts[0]
        x=np.array([p.body(t)[0][0] for t in ts])
        assert np.max(np.abs(np.gradient(np.gradient(x,dt),dt)))<=c['lateralAccelerationMps2']*1.001
    for e in p.events:
        for t in (e['start'],e['end']):
            assert np.linalg.norm(p.sample(t+1e-6)['center']-p.sample(t-1e-6)['center'])<1e-5
