import numpy as np
import pytest
from eonwild_motion.solve.moco_behavior_intent import BehaviorIntent
from eonwild_motion.solve.moco_environment import submerged_fraction,water_load


def test_behavior_near_stop_preserves_continuous_bounds_and_root_units():
    spec=dict(duration_s=4,joint_offsets_degrees={'knee':[[0,0],[2,-40],[4,0]]},root_offsets_leg_lengths={'forward':[[0,0],[4,2]]})
    intent=BehaviorIntent(spec,['knee','forward'],3.,{'knee':(-2.,-.16)})
    values=np.array([intent.apply([-1.999,0],t) for t in np.linspace(0,4,401)])
    assert np.all(values[:,0]>=-2.) and np.all(values[:,0]<=-.16)
    assert values[-1,1]==6.
    assert np.max(abs(np.diff(values[:,0])))<.001


def test_malformed_behavior_keys_fail_before_generation():
    with pytest.raises(ValueError,match='strictly ordered'):
        BehaviorIntent(dict(duration_s=4,joint_offsets_degrees={'knee':[[0,0],[0,10]]}),['knee'],3.,{'knee':(-2.,-.16)})


def test_buoyancy_is_zero_above_water_and_density_scaled_when_submerged():
    segment=dict(radius_m=.4,mass_kg=100.)
    policy=dict(height_m=1.,body_density_kg_m3=1000.,water_density_kg_m3=1000.,drag_coefficient=.8)
    np.testing.assert_allclose(water_load(segment,[0,2,0],[0,0,0],policy),[0,0,0])
    np.testing.assert_allclose(water_load(segment,[0,0,0],[0,0,0],policy),[0,980.665,0])
    assert water_load(segment,[0,0,0],[2,0,0],policy)[0]<0
    assert submerged_fraction(1.,.4,1.)==.5


def test_earlier_unloading_is_monotone_and_c2_at_contact_keys():
    from eonwild_motion.solve.moco_behavior_intent import SupportRetime
    t=np.linspace(0,4,401);loaded=t%1<.6
    mapping=SupportRetime(t,loaded,.25)
    fine=np.linspace(0,4,4001);mapped=np.array([mapping(x) for x in fine])
    assert np.all(np.diff(mapped)>0)
    assert mapping(.5)>.5
    h=1e-5
    for a,_ in mapping.keys[1:-1]:
        assert abs((mapping(a+h)-mapping(a-h))/(2*h)-1)<1e-5
