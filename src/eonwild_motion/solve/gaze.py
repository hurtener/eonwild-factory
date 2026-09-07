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

SCHEMA = 'eonwild.motion.rostral-direction.v1'


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
    return {'schema':SCHEMA,'head_role':roles['head'],'axis_local':axis.tolist(),
        'upper_rostrum_vertex_indices':rig.mouth_masks['upper'].tolist(),
        'neutral_rostrum_m':rostrum.tolist(),
        'neutral_elevation_degrees':math.degrees(math.atan2(float(direction@rig.up),float(direction@rig.forward))),
        'classification':'admitted head-to-upper-rostrum geometric direction; not a measured optic axis'}


def load_rostral_axis(calibration: Mapping, head_role: str):
    if (not isinstance(calibration,Mapping) or calibration.get('schema')!=SCHEMA
        or calibration.get('head_role')!=head_role):
        raise ContractError('gaze calibration must match the semantic head role')
    raw=calibration.get('axis_local')
    if (not isinstance(raw,(list,tuple)) or len(raw)!=3
        or any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in raw)):
        raise ContractError('gaze calibration needs three numeric local-axis components')
    axis=np.asarray(raw,dtype=float)
    if not np.isfinite(axis).all() or abs(np.linalg.norm(axis)-1)>1e-6:
        raise ContractError('gaze calibration axis must be finite and unit length')
    return tuple(float(v) for v in axis)
