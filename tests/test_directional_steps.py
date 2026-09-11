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
