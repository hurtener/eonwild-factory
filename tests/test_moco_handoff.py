import numpy as np
from eonwild_motion.solve.moco_handoff import StateCarry,FootCarry


def test_state_carry_preserves_position_velocity_acceleration_without_travel_snapback():
    outgoing=np.array([[4.,.3],[1.,.2],[.4,-.1]])
    incoming=np.array([[4.,.1],[3.,-.2],[0.,.1]])
    carry=StateCarry(outgoing,incoming,1.2,[0])
    for d in range(3):np.testing.assert_allclose(incoming[d]+carry(0.,d),outgoing[d],atol=1e-12)
    np.testing.assert_allclose(carry(1.2,1),0,atol=1e-12)
    np.testing.assert_allclose(carry(1.2,2),0,atol=1e-12)
    assert carry(1.2)[0]<0
    np.testing.assert_allclose(carry(1.2)[1],0,atol=1e-12)


def test_contact_carry_does_not_decay_while_inherited_foot_is_loaded():
    times=np.linspace(0,2,201);loaded=(times<.5)|(times>=1.)
    carry=FootCarry(times,loaded,lambda t:np.array([t*.1,0,0]),[.4,0,.1])
    for t in [0,.2,.499]:np.testing.assert_allclose(carry(t),[.4,0,.1])
    assert 0<carry.adoption_gain(.7)<1
    np.testing.assert_allclose(carry(1.1),carry(1.8))


def test_later_release_is_continuous_while_root_velocity_is_still_changing():
    t=np.linspace(0,3,301);loaded=(t<.4)|((t>=.9)&(t<1.4))|(t>=2.)
    carry=FootCarry(t,loaded,lambda x:np.array([x*x*.1,0,0]),[.3,0,0])
    for edge in [.4,.9,1.4,2.]:
        np.testing.assert_allclose(carry(edge-1e-7),carry(edge+1e-7),atol=1e-6)
    np.testing.assert_allclose(carry(1.),carry(1.3))
