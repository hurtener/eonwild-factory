"""Capability effects on shared planning, distinct from actual-rig review."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.locomotion_capabilities import (
    resolve_capabilities, resolve_walk, advance_walk_speed, yaw_rate_at_speed,
    plan_directional,
)

ROOT=Path(__file__).resolve().parents[1]

def profile():
    return json.loads((ROOT/'catalog/embodiment/allo.v1.json').read_text())

def plan(d):
    c=resolve_capabilities(d);h=d['authoring']['bodyHeightM'];w=h*.18
    r=json.loads((ROOT/'catalog/behaviors/directional-review.v1.json').read_text())
    p,receipt=plan_directional(c,[0,h,0],[0,0,1],[1,0,0],[0,1,0],h,
        {'left':-w,'right':w},{'left':0,'right':0},r)
    return c,p,receipt

def test_mass_and_inertia_change_independent_capabilities_without_name_branches():
    d=profile();old=resolve_capabilities(d)
    d['id']='unseen-renamed-animal';d['authoring']['animalInstance']['taxon']='unseen'
    assert resolve_capabilities(d)==old
    d['authoring']['animalInstance']['measurements']['body_mass']['value']*=2
    d['locomotion']['body']['yawInertia']['value']*=3
    new=resolve_capabilities(d)
    assert new['forwardAccelerationMps2']==pytest.approx(old['forwardAccelerationMps2']/2)
    assert new['yawAccelerationRadps2']==pytest.approx(old['yawAccelerationRadps2']/3)
    assert new['responseSeconds']>old['responseSeconds']

def test_research_proxy_does_not_become_a_playback_speed():
    d=profile();old,p,_=plan(d)
    d['locomotion']['body']['iliumArea']['value']*=2
    new,q,_=plan(d)
    assert new['publishedTurningProxy']==old['publishedTurningProxy']*2
    assert q.duration==p.duration

def test_walk_preserves_stride_caps_speed_and_brakes_with_independent_budget():
    c=resolve_capabilities(profile());walk=resolve_walk(c,999)
    assert walk['limited'] and walk['speedMps']==c['maximumGroundedSpeedMps']
    assert walk['sameFootStrideM']==2*walk['stepLengthM']
    assert walk['stepSeconds']*walk['speedMps']==pytest.approx(walk['stepLengthM'])
    assert advance_walk_speed(c,0,999,.1)==pytest.approx(c['forwardAccelerationMps2']*.1)
    assert advance_walk_speed(c,1,0,.1)==pytest.approx(1-c['brakingAccelerationMps2']*.1)
    assert yaw_rate_at_speed(c,2)<yaw_rate_at_speed(c,.1)
    assert resolve_walk(c,0)['stepSeconds'] is None

def test_turn_budgets_keep_contact_and_continuous_rotation():
    c,p,_=plan(profile())
    for b in p.blocks:
        ts=np.linspace(b['start'],b['end'],501);dt=ts[1]-ts[0]
        h=np.array([p.body(t)[1] for t in ts]);v=np.gradient(h,dt)
        acc=np.gradient(v,dt)*np.sign(b['angle'])
        assert max(abs(v))<=c['maximumYawRateRadps']*1.02
        assert max(acc)<=c['yawAccelerationRadps2']*1.02
        assert -min(acc)<=c['yawBrakingRadps2']*1.02
        assert np.all(v[5:-5]*np.sign(b['angle'])>0)
    previous=None
    for t in np.linspace(0,p.duration,1000):
        sample=p.sample(t)
        assert any(f['contact'] for f in sample['feet'].values())
        if previous:
            for side,f in sample['feet'].items():
                if f['contact'] and previous['feet'][side]['contact']:
                    np.testing.assert_allclose(f['position'],previous['feet'][side]['position'],atol=1e-12)
        previous=sample

def test_less_turning_torque_requires_more_time_with_same_target():
    d=profile();_,old,_=plan(d)
    d['locomotion']['control']['yawTorque']['value']*=.2
    _,new,_=plan(d)
    assert new.duration>old.duration
    assert new.blocks[0]['angle']==old.blocks[0]['angle']

def test_short_travel_steps_respect_cadence_budget():
    d=profile();c=resolve_capabilities(d);h=d['authoring']['bodyHeightM']
    r=json.loads((ROOT/'catalog/behaviors/directional-review.v1.json').read_text())
    for block in r['blocks']:block['step_length_body_heights']=.001
    _,receipt=plan_directional(c,[0,h,0],[0,0,1],[1,0,0],[0,1,0],h,
        {'left':-h*.18,'right':h*.18},{'left':0,'right':0},r)
    assert all(b['step_seconds']>=1/c['maximumStepFrequencyHz'] for b in receipt['blocks'])

def test_similarity_prior_keeps_target_binding_and_labels_inherited_evidence():
    import runpy
    seed=runpy.run_path(str(ROOT/'tools/seed_locomotion_capabilities.py'))['seed']
    target=profile();reference=json.loads((ROOT/'catalog/embodiment/tarbo.v1.json').read_text())
    output=seed(target,reference,'reference-hash')
    assert output['source']==target['source']
    assert output['bindings']==target['bindings']
    assert output['authoring']==target['authoring']
    for group in ('body','control','walk','style'):
        assert all(v['classification']=='derived_estimate' for v in output['locomotion'][group].values())
    assert output['locomotion']['body']['yawInertia']['source']['referenceProfileSha256']=='reference-hash'
    target['authoring']['animalInstance']['measurements']['hindlimb_length']['unit']='cm'
    with pytest.raises(ValueError,match='metres'):seed(target,reference,'reference-hash')

@pytest.mark.parametrize('mutation',['units','infinity','provenance','stride'])
def test_bad_capabilities_are_not_silently_used(mutation):
    d=deepcopy(profile());v=d['locomotion']['control']['forwardForce']
    if mutation=='units':v['unit']='kg'
    elif mutation=='infinity':v['value']=float('inf')
    elif mutation=='provenance':v['source']={}
    else:d['authoring']['sameFootStrideM']*=.5
    with pytest.raises(ValueError):resolve_capabilities(d)
