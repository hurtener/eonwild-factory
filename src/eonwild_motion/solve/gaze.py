"""Geometry-derived rostral direction for explicit forward attention.

The direction from the head frame to the upper-rostrum surface is a geometric
presentation reference, NOT a fossil-derived optic axis. Calibrate once from
admitted geometry, never from a previous animation or a hardcoded bone name.
"""
from __future__ import annotations

import math
from typing import Mapping
import numpy as np

from ..errors import ContractError
from ..layers.leg_contact_resolve_v3 import _rotation_from_matrix, _qinv
from .airborne_gait import _qrotate

# v2 makes the elevation reference explicit.  A geometric rostral vector is
# normally not level with the world frame at rest; treating an authored
# attention offset as an absolute world elevation can therefore crank an
# otherwise neutral neck toward the sky.
SCHEMA = 'eonwild.motion.rostral-direction.v2'


def local_rostral_axis(head_world, rostrum_world, forward_axis):
    head = np.asarray(head_world, dtype=float)
    rostrum = np.asarray(rostrum_world, dtype=float)
    forward = np.asarray(forward_axis, dtype=float)
    if (head.shape != (4,4) or rostrum.shape != (3,) or forward.shape != (3,)
        or not all(np.isfinite(a).all() for a in (head,rostrum,forward))
        or abs(np.linalg.norm(forward)-1)>1e-8):
        raise ContractError('rostral calibration needs finite geometry and a unit forward axis')
    direction = rostrum-head[:3,3]
    length = float(np.linalg.norm(direction))
    if length<1e-8 or float(direction@forward)<=0:
        raise ContractError('upper-rostrum surface must be ahead of the head frame')
    direction/=length
    axis=np.asarray(_qrotate(_qinv(_rotation_from_matrix(head)),tuple(direction)))
    axis/=np.linalg.norm(axis)
    return axis


def calibrate_rostral_direction(source, *, roles, contact_profile, forward_axis, up_axis):
    from .skin_rig import SkinRig
    rig=SkinRig(source,roles,np.asarray(forward_axis),np.asarray(up_axis),contact_profile,oral=True)
    head=source.name_to_node[roles['head']]
    rostrum=rig.centroid(rig.neutral_world,'upper')
    axis=local_rostral_axis(rig.neutral_world[head],rostrum,forward_axis)
    direction=rostrum-rig.neutral_world[head,:3,3]
    neutral_elevation=math.degrees(math.atan2(float(direction@rig.up),float(direction@rig.forward)))
    return {'schema':SCHEMA,'head_role':roles['head'],'axis_local':axis.tolist(),
        'upper_rostrum_vertex_indices':rig.mouth_masks['upper'].tolist(),
        'neutral_rostrum_m':rostrum.tolist(),
        'neutral_elevation_degrees':neutral_elevation,
        'elevation_reference':'neutral head-to-upper-rostrum direction in the declared world frame',
        'classification':'admitted head-to-upper-rostrum geometric direction; not a measured optic axis'}


def load_rostral_calibration(calibration: Mapping, head_role: str):
    """Load a v2 rostral reference and its neutral world elevation.

    The elevation is a geometry fact for the admitted source, not a species
    rule.  Performance controls add a bounded authored offset to it; they do
    not redefine the neutral pose as world-level attention.
    """
    if (not isinstance(calibration,Mapping) or calibration.get('schema')!=SCHEMA
        or calibration.get('head_role')!=head_role
        or calibration.get('elevation_reference') != 'neutral head-to-upper-rostrum direction in the declared world frame'):
        raise ContractError('gaze calibration must match the semantic head role and v2 elevation reference')
    raw=calibration.get('axis_local')
    if (not isinstance(raw,(list,tuple)) or len(raw)!=3
        or any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in raw)):
        raise ContractError('gaze calibration needs three numeric local-axis components')
    axis=np.asarray(raw,dtype=float)
    if not np.isfinite(axis).all() or abs(np.linalg.norm(axis)-1)>1e-6:
        raise ContractError('gaze calibration axis must be finite and unit length')
    elevation=calibration.get('neutral_elevation_degrees')
    if (isinstance(elevation,bool) or not isinstance(elevation,(int,float))
        or not math.isfinite(elevation) or not -90.0 <= elevation <= 90.0):
        raise ContractError('gaze calibration needs a finite neutral elevation in [-90, 90] degrees')
    return tuple(float(v) for v in axis), float(elevation)


def load_rostral_axis(calibration: Mapping, head_role: str):
    return load_rostral_calibration(calibration, head_role)[0]


def relative_attention_elevation(calibration: Mapping, head_role: str, authored_offset_degrees: float) -> float:
    """Return the world elevation target for a neutral-relative authored cue."""
    _, neutral=load_rostral_calibration(calibration, head_role)
    if (isinstance(authored_offset_degrees,bool) or not isinstance(authored_offset_degrees,(int,float))
        or not math.isfinite(authored_offset_degrees)):
        raise ContractError('authored gaze elevation must be finite')
    target=neutral+float(authored_offset_degrees)
    if not -90.0 <= target <= 90.0:
        raise ContractError('neutral-relative gaze target exceeds the representable elevation range')
    return target
