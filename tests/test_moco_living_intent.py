import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from eonwild_motion.solve.moco_living_intent import LivingIntent, keyed


def make(lengths):
    policy=json.loads(Path('catalog/behaviors/moco-c59-batch.v2.json').read_text())['families']['alert']['living_intent']
    chain=[dict(body=f'link{i}',length_m=v) for i,v in enumerate(lengths)]
    names=['height','knee_l','ankle_l','chest_yaw','chest_roll','chest','neck','neck_upper','head']
    names += [n for p in chain for n in (p['body'],p['body']+'_yaw')]
    plan=SimpleNamespace(specification={'duration_s':12.},attention_degrees=lambda t:0.,heading=lambda t:0.)
    return LivingIntent(policy,plan,names,chain,2.),names


def test_life_preserves_boundary_adoption_and_does_not_write_legs_or_root():
    life,names=make([1,.8,.6,.4])
    q=np.linspace(0,.1,len(names))
    for t in [0,12]:np.testing.assert_array_equal(life.apply(q,t),q)
    for t in np.linspace(0,12,97):
        a=life.apply(q,t)
        np.testing.assert_array_equal(a[:3],q[:3])
        np.testing.assert_array_equal(a,life.apply(q,t))
    assert abs(life.apply(q,3)[names.index('link0_yaw')]-q[names.index('link0_yaw')])>.005


def test_arc_length_distribution_does_not_multiply_motion_with_bone_count():
    # Constant delayed input makes the integral independent of subdivision.
    totals=[]
    for lengths in [[1,1],[.5]*4,[.25]*8]:
        life,names=make(lengths)
        life.policy=dict(life.policy,tail_sweep_degrees=[[0,10],[12,10]],
                         interest_degrees=[[0,0],[12,0]],tail_vertical_degrees=0)
        q=life.apply(np.zeros(len(names)),5)
        totals.append(sum(q[names.index(p['body']+'_yaw')] for p in life.chain))
    np.testing.assert_allclose(totals,totals[0],atol=1e-12)


def test_interest_events_are_stationary_at_keys_not_piecewise_linear():
    keys=[[0,0],[2,8],[4,-3]]
    h=1e-4
    assert abs((keyed(2+h,keys)-keyed(2-h,keys))/(2*h))<1e-5


def test_intent_near_joint_stop_is_bounded_without_a_release_snap():
    life,names=make([1,.8,.6,.4]);i=names.index('link0')
    life.bounds={'link0':(-.14,.14)}
    q=np.zeros(len(names));q[i]=-.1398
    t=np.linspace(0,12,1201)
    values=np.array([life.apply(q,v)[i] for v in t])
    assert values.min()>-.14 and values.max()<.14
    assert max(abs(np.gradient(np.gradient(values,t),t)))<.1
    np.testing.assert_array_equal(life.apply(q,0),q)
    np.testing.assert_array_equal(life.apply(q,12),q)
