"""Rostral attention calibration is geometry, not a generic world-forward axis."""
import math
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.solve.gaze import SCHEMA, local_rostral_axis, load_rostral_axis
from eonwild_motion.solve.airborne_gait import _qrotate
from eonwild_motion.layers.leg_contact_resolve_v3 import _rotation_from_matrix


def test_downward_source_snout_is_not_mistaken_for_level_attention():
    head=np.eye(4)
    angle=math.radians(25)
    surface=np.array([0,-math.sin(angle),math.cos(angle)])
    axis=local_rostral_axis(head,surface,[0,0,1])
    assert np.allclose(axis,surface)
    assert not np.allclose(axis,[0,0,1])


def test_calibration_survives_rotated_translated_and_scaled_world_frame():
    head=np.eye(4);head[:3,3]=[2,3,4]
    surface=head[:3,3]+np.array([0,-.4,1.])
    original=local_rostral_axis(head,surface,[0,0,1])
    rotation=np.array([[0,0,1],[0,1,0],[-1,0,0]],dtype=float)
    change=np.eye(4);change[:3,:3]=rotation;change[:3,3]=[-1,8,2]
    transformed=change@head
    target=(change@np.r_[surface,1])[:3]
    current=local_rostral_axis(transformed,target,rotation@np.array([0,0,1]))
    assert np.allclose(current,original,atol=1e-12)
    world=np.asarray(_qrotate(_rotation_from_matrix(transformed),tuple(current)))
    assert np.allclose(world,rotation@(surface-head[:3,3])/np.linalg.norm(surface-head[:3,3]))


@pytest.mark.parametrize('surface',[[0,0,0],[0,0,-1],[0,math.nan,1]])
def test_missing_backward_or_invalid_surface_cannot_be_used(surface):
    with pytest.raises(ContractError):local_rostral_axis(np.eye(4),surface,[0,0,1])


@pytest.mark.parametrize('axis',[[0,0,0],[0,0,2],[0,math.nan,1],[False,0,1],[0,1]])
def test_untrusted_calibration_cannot_silently_change_attention(axis):
    with pytest.raises(ContractError):
        load_rostral_axis({'schema':SCHEMA,'head_role':'head','axis_local':axis},'head')


def test_renamed_rig_is_bound_by_semantics_not_literal_bone_ids():
    assert load_rostral_axis({'schema':SCHEMA,'head_role':'renamed-head','axis_local':[0,0,1]},'renamed-head')==(0.,0.,1.)
    with pytest.raises(ContractError):
        load_rostral_axis({'schema':SCHEMA,'head_role':'other','axis_local':[0,0,1]},'renamed-head')
