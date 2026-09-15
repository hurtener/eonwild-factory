"""Causal catch regression checks, using both canonical animal profiles."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities, plan_directional
from eonwild_motion.solve.turn_support import contact_loads

ROOT=Path(__file__).resolve().parents[1]


def make(animal='allo', case='A', overrides=None, mirror=False):
    profile=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    c=resolve_capabilities(profile); h=profile['authoring']['bodyHeightM']
    recipe=json.loads((ROOT/'catalog/behaviors/stumble-recovery-review.v3.json').read_text())
    recipe['blocks']=[b for b in recipe['blocks'] if b['case']==case]
    recipe['impact'].update(overrides or {})
    if mirror:
        recipe['blocks'][0]['impulse_lateral_up_forward_ns'][0]*=-1
        recipe['blocks'][0]['threat_lateral_forward'][0]*=-1
        recipe['blocks'][0]['side']='left'
    return plan_directional(c,[0,h,0],[0,0,1],[1,0,0],[0,1,0],h,
        {'left':-.18*h,'right':.18*h},{'left':.1,'right':.1},recipe)[0]


@pytest.mark.parametrize('animal',['allo','tarbo'])
def test_hit_catch_and_force_are_causal(animal):
    s=make(animal)
    for t in np.linspace(0,s.hit,31):
        np.testing.assert_allclose(s.body(t)[0],0,atol=1e-12)
        assert all(v==0 for v in s.response(t).values())
    e=s.catches[0]
    assert 0<e['lift']-s.hit<.08
    assert e['touch']-s.hit<.40
    # Momentum bookkeeping in the reduced model, including existing support.
    index=np.searchsorted(s.times,s.hit+.2)
    reaction=np.array([x['reactionAccelerationMps2'] for x in s.diagnostics[:index]])
    np.testing.assert_allclose(s.values[index,3:6],s.impulse_velocity+reaction.sum(axis=0)/240,atol=1e-10)
    assert any(d['catchLoad']>.3 for d in s.diagnostics)
    for d in s.diagnostics:
        assert abs(d['reactionAccelerationMps2'][0])<=s.c['lateralAccelerationMps2']+1e-10
    assert np.linalg.norm(s.values[-1,3:6])<.1


@pytest.mark.parametrize('animal',['allo','tarbo'])
def test_entry_phase_redirects_available_foot_without_reset(animal):
    selections=[]
    for case in ['C','D']:
        s=make(animal,case);e=s.catches[0];side=e['side'];selections.append(side)
        t=e['start'];eps=1e-5
        before=s.entry.sample(t)['feet'][side]
        after=s.sample(t)['feet'][side]
        np.testing.assert_allclose(after['position'],before['position'],atol=.003)
        assert after['swing_phase']==pytest.approx(before['swing_phase'],abs=.003)
        v=(s.sample(t+eps)['feet'][side]['position']-after['position'])/eps
        expected=(s.entry.sample(t+.0005)['feet'][side]['position']-s.entry.sample(t-.0005)['feet'][side]['position'])/.001
        np.testing.assert_allclose(v,expected,atol=.015)
        for time in np.linspace(0,s.duration,161):
            q=s.sample(time);load=contact_loads(s,time)
            assert any(f['contact'] for f in q['feet'].values())
            assert q['feet']['right']['position'][0]>q['feet']['left']['position'][0]
            for name,f in q['feet'].items():
                if not f['contact']: assert load[name]==0.
        assert all(s.sample(s.duration)['feet'][x]['contact'] for x in s.lanes)
    assert selections[0]!=selections[1]


def test_location_load_acceptance_and_mirroring_change_the_response():
    chest=make();hip=make(case='B');slow=make(overrides={'acceptance_seconds':.28})
    assert chest.angular_impulse>0>hip.angular_impulse
    assert abs(chest.response(chest.hit+.2)['torso_yaw_radians'])>abs(hip.response(hip.hit+.2)['torso_yaw_radians'])
    assert np.linalg.norm(chest.body(chest.hit+1)[0]-slow.body(slow.hit+1)[0])>.001
    mirrored=make(mirror=True)
    for t in np.linspace(0,chest.duration,51):
        np.testing.assert_allclose(chest.body(t)[0]*[-1,1,1],mirrored.body(t)[0],atol=1e-8)
    again=make()
    np.testing.assert_array_equal(chest.values,again.values)
    assert chest.exit_state['stance']=='alert_recovery'
    assert chest.exit_state['injury']=='not_inferred'


@pytest.mark.parametrize('animal',['allo','tarbo'])
@pytest.mark.parametrize('case',['A','B','C','D'])
def test_continuous_catches_keep_support_and_the_incoming_joint_clock(animal,case):
    s=make(animal,case,overrides={'next_catch_acceptance_fraction':.72,
                                'carry_entry_articulation':True})
    for t in np.arange(s.hit,s.duration,1/240):
        feet=s.sample(t)['feet'];loads=s.planned_loads(t)
        assert sum(loads.values())==pytest.approx(1.)
        assert any(f['contact'] for f in feet.values())
        for side,f in feet.items():
            if not f['contact']:assert loads[side]==0.
    assert any(b['start']<a['end'] for a,b in zip(s.catches,s.catches[1:]))
    for a,b in zip(s.catches,s.catches[1:]):
        if b['start']<a['end']:
            assert b['side']!=a['side']
            assert b['lift']>a['touch']
    if s.entry:
        e=s.catches[0];side=e['side']
        t=(e['lift']+e['touch'])/2
        foot=s.sample(t)['feet'][side]
        assert foot['walking_swing_phase']==s.entry.sample(t)['feet'][side]['swing_phase']
        assert foot['walking_swing_phase']!=pytest.approx(foot['swing_phase'])
        assert s.sample(e['touch'])['feet'][side]['entry_articulation_weight']==0.
