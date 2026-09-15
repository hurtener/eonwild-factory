"""Loaded leg plane errors must be accommodated at the pelvis."""
import numpy as np
from eonwild_motion.solve.turn_support import accommodate_support_planes
from eonwild_motion.solve.turn_support import contact_loads, loaded_hip_roll, TurnLoadResponse
from eonwild_motion.planning.directional_steps import DirectionalSteps
from eonwild_motion.solve.turn_contact import material_patch_correction, material_patch_drift


def turn():
    return DirectionalSteps([0,2,0],[0,0,1],[1,0,0],[0,1,0],2.,
        {'left':-.36,'right':.36},{'left':0.,'right':0.},
        [{'steps':4,'step_length_body_heights':0.,'turn_degrees':100,'label':'turn'}])


def test_load_transfer_never_uses_a_free_foot_and_has_no_switch_jump():
    p=turn()
    for t in np.linspace(0,p.duration,501):
        loads=contact_loads(p,t)
        assert abs(sum(loads.values())-1)<1e-12
        for side,f in p.sample(t)['feet'].items():
            if not f['contact']:assert loads[side]<1e-12
    for e in p.events:
        for phase in (.1,.9):
            t=e['start']+phase*e['duration']
            a=contact_loads(p,t-1e-6);b=contact_loads(p,t+1e-6)
            assert max(abs(a[s]-b[s]) for s in a)<1e-5


def test_loaded_hip_keeps_height_while_recovery_side_drops():
    hips={'left':np.array([-.2,2.,0.]),'right':np.array([.2,2.,0.])}
    for side,sign in [('left',-1),('right',1)]:
        loads={s:float(s==side) for s in hips}
        turned,delta=loaded_hip_roll(hips,[0,2,0],loads,[0,0,1],[0,1,0],sign*np.radians(2))
        assert abs(turned[side][1]-2)<1e-12
        assert turned[next(s for s in hips if s!=side)][1]<2
        assert delta[1]<0 and delta[0]==delta[2]==0


def test_more_mass_at_same_force_lengthens_pelvis_preparation():
    p=turn();policy={'transfer_fraction_of_step':.35,'maximum_roll_degrees':2.,'response_scale':.1}
    a=TurnLoadResponse(p,{'lateralAccelerationMps2':1.},policy)
    b=TurnLoadResponse(p,{'lateralAccelerationMps2':.5},policy)
    assert abs(b.response_seconds/a.response_seconds-np.sqrt(2))<1e-12
    assert max(abs(b.roll(t)) for t in b.times)<=np.radians(2)


def test_material_correction_preserves_floor_axis_and_exposes_vertex_drift():
    reference=np.array([[0.,0.,0.],[1.,0.,0.]])
    patch=reference+[.01,.2,-.02]
    correction=material_patch_correction(patch,reference,[0,1,0])
    np.testing.assert_allclose(correction,[-.01,0.,.02],atol=1e-12)
    assert material_patch_drift(patch+correction,reference,[0,1,0])['centroid_m']<1e-12
    patch=reference.copy();patch[0,0]+=.02;patch[1,0]-=.02
    drift=material_patch_drift(patch,reference,[0,1,0])
    assert drift['centroid_m']<1e-12 and drift['maximum_vertex_m']>.019


def test_loaded_plane_moves_pelvis_without_vertical_lift():
    hip={'left':np.array([.1,2.,0.])}
    ankle={'left':np.array([0.,0.,0.])}
    normal={'left':np.array([1.,0.,0.])}
    correction=accommodate_support_planes(hip,ankle,normal,{'left':1.},
        np.array([0.,1.,0.]),np.array([0.,0.,1.]),np.array([1.,0.,0.]),2.)
    assert abs((hip['left']+correction-ankle['left'])@normal['left'])<.0003
    assert correction[1]==0


def test_unloaded_leg_does_not_drive_pelvis():
    hip={'left':np.array([.1,2.,0.])}
    correction=accommodate_support_planes(hip,{'left':np.zeros(3)},
        {'left':np.array([1.,0.,0.])},{'left':0.},np.array([0.,1.,0.]),
        np.array([0.,0.,1.]),np.array([1.,0.,0.]),2.)
    np.testing.assert_array_equal(correction,np.zeros(3))


def test_impact_path_is_not_cancelled_until_the_next_support_change():
    from eonwild_motion.solve.turn_support import impact_plane_accommodation
    policy={'support_plane_accommodation_fraction':0.,
            'support_plane_release_seconds':.065}
    correction=np.array([-.2,0.,.01])
    np.testing.assert_array_equal(impact_plane_accommodation(correction,-.1,policy),correction)
    np.testing.assert_array_equal(impact_plane_accommodation(correction,.2,{}),correction)
    # During a planted interval, growing neutral-plane corrections must no
    # longer cancel the continuous body displacement and form a plateau.
    for position in [.10,.15,.20,.25]:
        planned=np.array([position,0.,0.])
        emitted=planned+impact_plane_accommodation(-planned,.2,policy)
        np.testing.assert_array_equal(emitted,planned)
