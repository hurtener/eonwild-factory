"""Geometric support planning tests, not visual or biological approval."""
import math
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.support_balance import support_balance, positive_part


def solve(hips, anchors=None, **kwargs):
    if anchors is None: anchors=np.zeros_like(hips)
    return support_balance(hips,anchors,np.ones((len(hips),2)),up_axis=[0,1,0],
        knee_max_degrees=155,maximum_drop_m=.4,activation_band_m=.02,**kwargs)


def test_already_bent_support_is_unchanged():
    hips=np.array([[0.,1.5,.3],[0.,1.5,-.3]])
    shift,receipt=solve(hips)
    assert np.array_equal(shift,np.zeros(3))
    assert receipt['anchors_moved'] is False and receipt['floor_moved'] is False


def test_forward_load_lowers_one_common_pelvis_not_planted_anchors():
    hips=np.array([[0.,1.8,1.0],[0.,1.8,.2]])
    original=hips.copy()
    shift,receipt=solve(hips)
    assert shift[1]<0 and shift[0]==shift[2]==0
    radius=math.sqrt(2-2*math.cos(math.radians(155)))
    assert np.all(np.linalg.norm(hips+shift,axis=1)<=radius+1e-8)
    assert np.array_equal(hips,original)
    assert receipt['drop_m']<=.4


def test_mirrored_and_swapped_legs_have_same_balance():
    hips=np.array([[0.,1.8,1.0],[0.,1.8,.2]])
    a,_=solve(hips)
    b,_=solve(hips[::-1])
    c,_=solve(hips*[1,1,-1])
    assert np.allclose(a,b,atol=1e-12)
    assert np.allclose(a,c,atol=1e-12)


def test_balance_frame_can_be_rotated_without_changing_solution():
    hips=np.array([[0.,1.8,1.0],[0.,1.8,.2]])
    delta,_=solve(hips)
    rotation=np.array([[0,1,0],[0,0,1],[1,0,0]],dtype=float)
    other,_=support_balance(hips@rotation.T,np.zeros_like(hips),np.ones((2,2)),
        up_axis=rotation@np.array([0,1,0]),knee_max_degrees=155,maximum_drop_m=.4,activation_band_m=.02)
    assert np.allclose(other,rotation@delta,atol=1e-12)


@pytest.mark.parametrize('hips', [[[0,1,3],[0,1,0]], [[0,3,0],[0,3,0]]])
def test_infeasible_support_is_not_repaired_by_moving_feet(hips):
    with pytest.raises(ContractError,match='reposition'):
        solve(np.array(hips,dtype=float))


@pytest.mark.parametrize('value', [math.nan,math.inf])
def test_nonfinite_geometry_rejects(value):
    with pytest.raises(ContractError):solve(np.array([[0,value,1],[0,1,0]]))


def test_smoothing_is_conservative_and_has_matching_boundary_derivatives():
    band=.02
    for x in np.linspace(-.1,.1,101):
        assert positive_part(float(x),band)>=max(0,float(x))-1e-12
    h=1e-6
    for x,expected in ((-band,0.),(band,1.)):
        derivative=(positive_part(x+h,band)-positive_part(x-h,band))/(2*h)
        assert derivative==pytest.approx(expected,abs=1e-6)
        curvature=(positive_part(x+h,band)-2*positive_part(x,band)+positive_part(x-h,band))/h**2
        assert abs(curvature)<.002
