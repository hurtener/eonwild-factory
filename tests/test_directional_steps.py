"""Check the defining turn constraint: loaded feet cannot spin or skate."""
import numpy as np
from eonwild_motion.planning.directional_steps import DirectionalSteps

def planner():
    return DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,{'left':-.22,'right':.22},{'left':.1,'right':.1},[{'steps':n,'step_length_body_heights':d,'turn_degrees':a,'label':l} for n,d,a,l in [(6,.25,35,'gentle walking turn'),(4,.15,-40,'tight walking turn'),(6,0,75,'turn in place')]])

def test_support_is_stationary_and_heading_frozen():
    p=planner();previous=None
    for t in np.linspace(0,p.duration,4001):
        sample=p.sample(t)
        assert any(f['contact'] for f in sample['feet'].values())
        if previous:
            for s,f in sample['feet'].items():
                old=previous['feet'][s]
                if old['contact'] and f['contact']:
                    np.testing.assert_allclose(f['position'],old['position'],atol=1e-12)
                    assert abs(f['heading']-old['heading'])<1e-12
        previous=sample

def test_in_place_has_no_path_translation_and_alternates():
    p=planner();events=[e for e in p.events if e['label']=='turn in place']
    a,_=p.body(events[0]['start']);b,_=p.body(events[-1]['end'])
    np.testing.assert_allclose(a,b,atol=1e-12)
    assert all(x['side']!=y['side'] for x,y in zip(events,events[1:]))

def test_path_is_continuous_at_block_boundaries():
    p=planner()
    for e in p.events:
        for t in [e['start'],e['end']]:
            a,ya=p.body(t-1e-6);b,yb=p.body(t+1e-6)
            assert np.linalg.norm(a-b)<1e-5
            assert abs(ya-yb)<1e-5


def test_attention_leads_turns_and_settles():
    from eonwild_motion.solve.turn_attention import turn_look_yaw
    p=planner()
    assert p.body(.5)[1]==0
    assert turn_look_yaw(p,.5,1.6,32)>0
    assert turn_look_yaw(p,10,1.6,32)<0
    assert turn_look_yaw(p,17,1.6,32)>0
    assert abs(turn_look_yaw(p,p.duration,1.6,32))<1e-12
    assert max(abs(turn_look_yaw(p,t,1.6,32)) for t in np.linspace(0,p.duration,400))<np.radians(32)


def test_turn_body_waits_for_leading_foot_support():
    p=planner()
    b=next(b for b in p.blocks if b['stationary'])
    start=b['start']
    assert p.body(start+.80*p.period)[1]==b['heading']
    assert p.body(start+1.3*p.period)[1]>b['heading']
    lead=next(e for e in p.events if e['block'] is b)
    planted=p.sample(start+.83*p.period)['feet'][lead['side']]
    assert planted['contact']
    assert planted['heading']>p.body(start+.83*p.period)[1]


def test_turn_heel_release_is_continuous_and_recovery_is_low():
    p=planner();b=next(b for b in p.blocks if b['stationary'])
    e=next(e for e in p.events if e['block'] is b);side=e['side']
    t=e['start']+.18*p.period
    a=p.sample(t-1e-6)['feet'][side];z=p.sample(t+1e-6)['feet'][side]
    assert abs(a['roll_degrees']-z['roll_degrees'])<1e-6
    max_height=max(p.sample(t)['feet'][side]['position'][1] for t in np.linspace(e['start'],e['end'],100))
    assert max_height-p.foot_heights[side]<=.018*p.height+1e-12
