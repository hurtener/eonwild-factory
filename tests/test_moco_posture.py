from types import SimpleNamespace
import numpy as np
from eonwild_motion.solve.moco_posture import jaw_binding, living_standing
from eonwild_motion.solve.jaw_response import compose_jaw_rotation


def test_zero_closure_does_not_disable_a_semantic_breathing_jaw():
    context=SimpleNamespace(jaw=None,jaw_axis=None,jaw_neutral_close_degrees=0.)
    profile={'secondary':{'jaw':{'role':'jaw_lower','axis':[1,0,0]}}}
    node,axis,close=jaw_binding(context,profile,{'jaw_lower':7},{'maximum_gape_degrees':2.})
    assert node==7 and close==0
    closed=compose_jaw_rotation([0,0,0,1],axis,neutral_close_degrees=close,breathing_gape_degrees=0.,gain=1.)
    open_=compose_jaw_rotation([0,0,0,1],axis,neutral_close_degrees=close,breathing_gape_degrees=2.,gain=1.)
    assert not np.allclose(closed,open_)


def test_existing_calibrated_jaw_keeps_its_binding_and_closure():
    context=SimpleNamespace(jaw=4,jaw_axis=[1.,0,0],jaw_neutral_close_degrees=50.)
    node,axis,close=jaw_binding(context,{}, {},{'minimum_gape_degrees':.8})
    assert node==4 and close==50.
    np.testing.assert_array_equal(axis,context.jaw_axis)


def test_living_posture_does_not_change_bind_input_or_command_foot_motion():
    names=['height','chest','neck','head','tail_0','tail_0_yaw','tail_1','tail_1_yaw','mtp_l']
    ref=np.zeros(len(names));ref[-1]=.3
    chain=[{'body':'tail_0','length_m':1.},{'body':'tail_1','length_m':2.}]
    p={'coordinates_rad':{'chest':0.,'neck':0.,'head':0.},'hip_height_over_leg_length':.9,
       'tail_bend_density':{'arc':[0,1],'radians_per_arc':[-.2,.4]},'idle_period_s':4.,
       'breath_height_leg_lengths':.001,'chest_breath_radians':.002,
       'tail_sway_total_radians':.06,'tail_phase_lag_radians':1.}
    a=living_standing(ref,names,chain,0.,p,2.);b=living_standing(ref,names,chain,1.,p,2.)
    assert a[-1]==b[-1]==ref[-1] and ref[0]==0
    assert a[5]!=b[5] and a[7]!=b[7]
    np.testing.assert_allclose(a,living_standing(ref,names,chain,4.,p,2.),atol=1e-14)
