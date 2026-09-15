"""Impact causality, intensity response and shared grounded support."""
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities, plan_directional
from eonwild_motion.solve.turn_support import contact_loads

ROOT=Path(__file__).resolve().parents[1]

def make(animal='allo', mass_scale=1., side='right', impulse=None):
    p=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    c=resolve_capabilities(p)
    c['massKg']*=mass_scale
    c['lateralAccelerationMps2']/=mass_scale
    r=json.loads((ROOT/'catalog/behaviors/stumble-recovery-review.v2.json').read_text())
    for b in r['blocks']:
        b['side']=side
        if impulse is not None:b['received_impulse_ns']=impulse
    h=p['authoring']['bodyHeightM']
    return plan_directional(c,[0,h,0],[0,0,1],[1,0,0],[0,1,0],h,
        {'left':-.18*h,'right':.18*h},{'left':.1,'right':.1},r)[0]

@pytest.mark.parametrize('animal',['allo','tarbo'])
def test_hit_arrives_before_foot_release_and_support_stays_grounded(animal):
    p=make(animal);hit=p.blocks[0]['start'];previous=None
    for t in np.linspace(0,hit,51):
        assert all(f['contact'] for f in p.sample(t)['feet'].values())
        assert all(v==0 for v in p.response(t).values())
    assert p.response(hit+.08)['drop_m']>0
    catching=p.sample(hit+.08)['feet']['right']
    assert not catching['contact']
    assert np.linalg.norm(catching['position']-p.anchors['right'])>.015
    assert p.response(hit+.10)['torso_yaw_radians']<0
    assert p.response(hit+.15)['tail_yaw_radians']>0
    for t in np.linspace(hit-.10,hit,31):
        assert contact_loads(p,t)=={'left':.5,'right':.5}
        np.testing.assert_allclose(p.sample(t)['center'],np.zeros(3),atol=1e-12)
    for t in np.linspace(0,p.duration,1201):
        feet=p.sample(t)['feet'];loads=contact_loads(p,t)
        assert any(f['contact'] for f in feet.values())
        assert feet['right']['position'][0]>feet['left']['position'][0]
        for s,f in feet.items():
            if not f['contact']:assert loads[s]==0.
            if previous and f['contact'] and previous[s]['contact']:
                np.testing.assert_allclose(f['position'],previous[s]['position'],atol=1e-12)
        previous=feet
    assert max(abs(v) for v in p.response(p.duration).values())<1e-10

def test_stronger_hit_and_receiver_mass_change_the_response():
    p=make();heavy=make(mass_scale=2)
    assert p.blocks[1]['length']>p.blocks[0]['length']*2
    assert p.blocks[1]['count']>p.blocks[0]['count']
    assert heavy.blocks[0]['velocity_change_mps']==p.blocks[0]['velocity_change_mps']/2
    assert heavy.blocks[0]['length']<p.blocks[0]['length']
    left=make(side='left')
    for t in np.linspace(0,p.duration,101):
        assert left.body(t)[0][0]==pytest.approx(-p.body(t)[0][0])
        assert left.response(t)['roll_radians']==pytest.approx(-p.response(t)['roll_radians'])

@pytest.mark.parametrize('impulse',[0,-1,float('nan'),float('inf'),True,100000])
def test_invalid_or_fall_scale_impacts_are_not_silently_clamped(impulse):
    with pytest.raises(ValueError):make(impulse=impulse)
