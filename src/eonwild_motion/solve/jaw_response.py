"""Strict semantic neutral-jaw admission and one-time pose composition."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math

import numpy as np

from ..contact_gauge import _read_glb_accessor
from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import (
    _qinv,
    _qmul,
    _qrotvec,
    _qrotate,
    _rotation_from_matrix,
    _world_matrices,
)
from ..planning.jaw_response import NeutralJawCalibration


@dataclass(frozen=True)
class AdmittedNeutralJaw:
    node: int
    local_axis: tuple[float, float, float]
    close_degrees: float
    measured_source_minimum_gap_m: float
    current_minimum_gap_m: float


def _unit(value, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (3,) or not np.isfinite(array).all():
        raise ContractError(f"neutral jaw {label} must be a finite three-vector")
    length = float(np.linalg.norm(array))
    if length <= 1e-10:
        raise ContractError(f"neutral jaw {label} is degenerate")
    return array / length


def _semantic_jaw(source: Glb, roles: Mapping) -> tuple[int, int]:
    if not isinstance(roles, Mapping):
        raise ContractError("neutral jaw requires semantic rig roles")
    head_name, jaw_name = roles.get("head"), roles.get("jaw_lower")
    other_scalar_roles = {
        value for key, value in roles.items()
        if key not in {"head", "jaw_lower"} and isinstance(value, str)
    }
    if (not isinstance(head_name, str) or not head_name
            or not isinstance(jaw_name, str) or not jaw_name
            or head_name == jaw_name
            or head_name in other_scalar_roles
            or jaw_name in other_scalar_roles
            or head_name not in source.name_to_node
            or jaw_name not in source.name_to_node):
        raise ContractError("neutral jaw requires distinct admitted head and lower-jaw roles")
    head, jaw = source.name_to_node[head_name], source.name_to_node[jaw_name]
    parent = source.parents[jaw]
    visited = {jaw}
    while parent is not None and parent != head:
        if parent in visited:
            raise ContractError("neutral jaw hierarchy is cyclic")
        visited.add(parent)
        parent = source.parents[parent]
    if parent != head:
        raise ContractError("semantic lower jaw must descend from the semantic head")
    return head, jaw


def _bound_skin_data(source: Glb, calibration: NeutralJawCalibration):
    document = source.document
    skins = document.get("skins")
    meshes = document.get("meshes")
    if (not isinstance(skins, Sequence) or isinstance(skins, (str, bytes))
            or calibration.skin_index >= len(skins)
            or not isinstance(meshes, Sequence) or isinstance(meshes, (str, bytes))):
        raise ContractError("neutral jaw calibration skin binding is absent")
    skin = skins[calibration.skin_index]
    if not isinstance(skin, Mapping):
        raise ContractError("neutral jaw calibration skin is malformed")
    joints = skin.get("joints")
    inverse_accessor = skin.get("inverseBindMatrices")
    if (not isinstance(joints, Sequence) or isinstance(joints, (str, bytes))
            or not joints
            or any(type(value) is not int or value < 0 or value >= len(source.nodes)
                   for value in joints)
            or len(joints) != len(set(joints))
            or type(inverse_accessor) is not int):
        raise ContractError("neutral jaw calibration skin hierarchy is malformed")
    matches = []
    for node in source.nodes:
        if not isinstance(node, Mapping):
            raise ContractError("neutral jaw source node is malformed")
        if node.get("skin") != calibration.skin_index:
            continue
        mesh_index = node.get("mesh")
        if type(mesh_index) is not int or not 0 <= mesh_index < len(meshes):
            raise ContractError("neutral jaw skinned mesh binding is malformed")
        mesh = meshes[mesh_index]
        if not isinstance(mesh, Mapping):
            raise ContractError("neutral jaw skinned mesh is malformed")
        primitives = mesh.get("primitives")
        if not isinstance(primitives, Sequence) or isinstance(primitives, (str, bytes)):
            raise ContractError("neutral jaw skinned primitives are malformed")
        for primitive in primitives:
            attributes = primitive.get("attributes") if isinstance(primitive, Mapping) else None
            if not isinstance(attributes, Mapping):
                raise ContractError("neutral jaw primitive attributes are malformed")
            joint_accessors = tuple(
                attributes[key] for key in sorted(attributes)
                if key.startswith("JOINTS_")
            )
            weight_accessors = tuple(
                attributes[key] for key in sorted(attributes)
                if key.startswith("WEIGHTS_")
            )
            if (attributes.get("POSITION") == calibration.position_accessor
                    and joint_accessors == calibration.joint_accessors
                    and weight_accessors == calibration.weight_accessors):
                matches.append(primitive)
    if len(matches) != 1:
        raise ContractError("neutral jaw calibration does not identify one skinned primitive")

    def read(index: int) -> np.ndarray:
        try:
            return np.asarray(
                _read_glb_accessor(source, index, label="neutral-jaw accessor"),
                dtype=float,
            )
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            raise ContractError("neutral jaw calibration accessor is malformed") from exc

    positions = read(calibration.position_accessor)
    inverse = read(inverse_accessor)
    ids = np.concatenate([read(index) for index in calibration.joint_accessors], axis=1)
    weights = np.concatenate([read(index) for index in calibration.weight_accessors], axis=1)
    if (positions.ndim != 2 or positions.shape[1] != 3
            or inverse.shape != (len(joints), 16)
            or ids.shape != weights.shape
            or len(ids) != len(positions)
            or not np.isfinite(positions).all()
            or not np.isfinite(inverse).all()
            or not np.isfinite(ids).all()
            or not np.isfinite(weights).all()
            or (ids != np.floor(ids)).any()
            or (ids < 0).any()
            or (ids >= len(joints)).any()
            or (weights < 0).any()):
        raise ContractError("neutral jaw calibration skin arrays are malformed")
    totals = weights.sum(axis=1)
    if not np.isfinite(totals).all() or (totals <= 0).any():
        raise ContractError("neutral jaw calibration skin weights are empty")
    weights = weights / totals[:, None]
    return (
        np.c_[positions, np.ones(len(positions))],
        np.asarray(joints, dtype=int),
        inverse.reshape(-1, 4, 4).transpose(0, 2, 1),
        ids.astype(int),
        weights,
    )


def _posed_gap(
    source: Glb,
    roles: Mapping,
    calibration: NeutralJawCalibration,
    forward,
    up,
) -> tuple[int, tuple[float, float, float], float]:
    _, jaw = _semantic_jaw(source, roles)
    forward_array, up_array = _unit(forward, "forward axis"), _unit(up, "up axis")
    if abs(float(forward_array @ up_array)) > 1e-8:
        raise ContractError("neutral jaw declared axes must be orthogonal")
    lateral = _unit(np.cross(up_array, forward_array), "lateral axis")
    translations = list(source.rest_translation)
    rotations = list(source.rest_rotation)
    scales = list(source.rest_scale)
    base_worlds = _world_matrices(source, translations, rotations, scales)
    local_axis = _unit(
        _qrotate(_qinv(_rotation_from_matrix(base_worlds[jaw])), tuple(lateral)),
        "admitted local hinge axis",
    )
    rotations[jaw] = _qmul(
        rotations[jaw],
        _qrotvec(tuple(local_axis * math.radians(-calibration.close_degrees))),
    )
    worlds = np.asarray(_world_matrices(source, translations, rotations, scales))
    positions, joints, inverse, ids, weights = _bound_skin_data(source, calibration)
    transforms = worlds[joints] @ inverse
    gaps = []
    for surface_bin in calibration.surface_bins:
        lower = np.asarray(surface_bin.lower_vertex_indices, dtype=int)
        upper = np.asarray(surface_bin.upper_vertex_indices, dtype=int)
        indices = np.r_[lower, upper]
        if (indices >= len(positions)).any():
            raise ContractError("neutral jaw surface witness exceeds the vertex count")
        points = np.einsum(
            "nv,nvij,nj->ni",
            weights[indices],
            transforms[ids[indices]],
            positions[indices],
        )[:, :3]
        if not np.isfinite(points).all():
            raise ContractError("neutral jaw posed skin witness is non-finite")
        lower_height = points[:len(lower)] @ up_array
        upper_height = points[len(lower):] @ up_array
        gap = float(np.quantile(upper_height, .25) - np.quantile(lower_height, .75))
        if not math.isfinite(gap):
            raise ContractError("neutral jaw surface gap is non-finite")
        gaps.append(gap)
    minimum = min(gaps)
    if minimum <= 0:
        raise ContractError("neutral jaw calibrated pose closes its sampled surface gap")
    return jaw, tuple(float(value) for value in local_axis), minimum


def admit_neutral_jaw(
    source: Glb,
    roles: Mapping,
    calibration: NeutralJawCalibration,
    forward,
    up,
) -> AdmittedNeutralJaw:
    if not isinstance(calibration, NeutralJawCalibration):
        raise ContractError("neutral jaw calibration must be typed")
    source_sha256 = hashlib.sha256(source.raw).hexdigest()
    if source_sha256 != calibration.source_geometry_sha256:
        raise ContractError("neutral jaw calibration source geometry hash is stale")
    raw_source = Glb.from_bytes(source.raw)
    raw_jaw, raw_axis, measured_gap = _posed_gap(
        raw_source, roles, calibration, forward, up)
    tolerance = max(1e-9, calibration.measured_minimum_gap_m * 1e-7)
    if abs(measured_gap - calibration.measured_minimum_gap_m) > tolerance:
        raise ContractError("neutral jaw source gap evidence does not reproduce")
    jaw, local_axis, current_gap = _posed_gap(
        source, roles, calibration, forward, up)
    if jaw != raw_jaw:
        raise ContractError("neutral jaw semantic binding changed after source admission")
    return AdmittedNeutralJaw(
        node=jaw,
        local_axis=local_axis,
        close_degrees=float(calibration.close_degrees),
        measured_source_minimum_gap_m=measured_gap,
        current_minimum_gap_m=current_gap,
    )


def compose_jaw_rotation(
    base_rotation,
    local_axis,
    *,
    neutral_close_degrees: float,
    breathing_gape_degrees: float,
    gain: float,
):
    values = (neutral_close_degrees, breathing_gape_degrees, gain)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in values):
        raise ContractError("jaw response values must be finite numeric")
    if (not 0 <= neutral_close_degrees <= 70
            or not 0 <= breathing_gape_degrees <= 8
            or not 0 <= gain <= 1):
        raise ContractError("jaw response exceeds the authored envelope")
    axis = _unit(local_axis, "local hinge axis")
    degrees = gain * (breathing_gape_degrees - neutral_close_degrees)
    return _qmul(
        tuple(base_rotation),
        _qrotvec(tuple(axis * math.radians(degrees))),
    )
