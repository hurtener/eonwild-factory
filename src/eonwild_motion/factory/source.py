"""Admit calibrated geometry once; programs need no input animation.

A historical take can supply a declared reference pose at admission. Its
choreography, timing and root trajectory are not later compilation inputs.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import (
    _clip_state, _pose, _rotation_from_matrix, _world_matrices, _world_position,
)
from ..solve.whole_body_gait_transition import _encode
from .io import frame_axes
from .quality import require_supported_geometry


_BIND_NORMALIZED_ORTHOGONALITY_TOLERANCE = 1.0e-6
_BIND_LOCAL_PROJECTION_TOLERANCE = 1.0e-6
_BIND_REOPENED_WORLD_TOLERANCE_M = 2.0e-6
_BIND_REOPENED_SKIN_TOLERANCE_M = 3.0e-6


def _semantic_node_names(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(name for item in value.values() for name in _semantic_node_names(item))
    if isinstance(value, (list, tuple)):
        return tuple(name for item in value for name in _semantic_node_names(item))
    raise ContractError("bind-pose recovery semantic roles must contain only node names and containers")


def _matrix(values: Any, *, label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.shape != (4, 4) or not np.isfinite(array).all():
        raise ContractError(f"{label} must be a finite 4x4 matrix")
    if not np.allclose(array[3], (0, 0, 0, 1), rtol=0, atol=1e-7):
        raise ContractError(f"{label} must be affine")
    return array


def _column_major_matrix(values: Any, *, label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.shape != (16,) or not np.isfinite(array).all():
        raise ContractError(f"{label} must contain 16 finite values")
    return array.reshape(4, 4).T


def _decompose_bind_local(matrix: np.ndarray, *, label: str) -> tuple[list[float], list[float], list[float], dict[str, float]]:
    matrix = _matrix(matrix, label=label)
    linear = matrix[:3, :3]
    scales = np.linalg.norm(linear, axis=0)
    if np.any(scales <= 1e-12) or not np.isfinite(scales).all():
        raise ContractError(f"{label} has a singular scale axis")
    normalized = linear / scales
    determinant = float(np.linalg.det(normalized))
    if determinant <= 0:
        raise ContractError(f"{label} contains a reflection")
    orthogonality = float(np.max(np.abs(normalized.T @ normalized - np.eye(3))))
    if orthogonality > _BIND_NORMALIZED_ORTHOGONALITY_TOLERANCE:
        raise ContractError(f"{label} contains unsupported shear")
    left, _, right = np.linalg.svd(normalized)
    rotation = left @ right
    if float(np.linalg.det(rotation)) <= 0:
        raise ContractError(f"{label} rotation projection contains a reflection")
    projected = rotation * scales
    projection = float(np.max(np.abs(projected - linear)))
    if projection > _BIND_LOCAL_PROJECTION_TOLERANCE * max(1.0, float(np.max(np.abs(linear)))):
        raise ContractError(f"{label} TRS projection exceeds tolerance")
    rotation4 = np.eye(4)
    rotation4[:3, :3] = rotation
    quaternion = _rotation_from_matrix(tuple(tuple(float(value) for value in row) for row in rotation4))
    return (
        [float(value) for value in matrix[:3, 3]],
        [float(value) for value in quaternion],
        [float(value) for value in scales],
        {"normalized_orthogonality_error": orthogonality,
         "linear_projection_error": projection,
         "normalized_determinant": determinant},
    )


def _skin_reconstruction_error(glb: Glb, *, skin_index: int, mesh_node: int) -> tuple[float, int]:
    skin = glb.document["skins"][skin_index]
    joints = [int(value) for value in skin["joints"]]
    inverse_rows = glb.accessor_values(int(skin["inverseBindMatrices"]))
    inverse = [_column_major_matrix(row, label=f"inverse bind[{index}]") for index, row in enumerate(inverse_rows)]
    worlds = [np.asarray(value, dtype=float) for value in _world_matrices(
        glb, glb.rest_translation, glb.rest_rotation, glb.rest_scale)]
    mesh_world = worlds[mesh_node]
    maximum = 0.0
    vertices = 0
    mesh_index = int(glb.nodes[mesh_node]["mesh"])
    for primitive_index, primitive in enumerate(glb.document["meshes"][mesh_index]["primitives"]):
        attributes = primitive.get("attributes", {})
        if "POSITION" not in attributes:
            raise ContractError(f"skin mesh primitive[{primitive_index}] has no POSITION")
        sets = sorted(key.removeprefix("JOINTS_") for key in attributes if key.startswith("JOINTS_"))
        if not sets or any(f"WEIGHTS_{suffix}" not in attributes for suffix in sets):
            raise ContractError(f"skin mesh primitive[{primitive_index}] has incomplete joint weights")
        if any(key.startswith("WEIGHTS_") and key.removeprefix("WEIGHTS_") not in sets for key in attributes):
            raise ContractError(f"skin mesh primitive[{primitive_index}] has unmatched joint weights")
        positions = np.asarray(glb.accessor_values(int(attributes["POSITION"])), dtype=float)
        joint_rows = [np.asarray(glb.accessor_values(int(attributes[f"JOINTS_{suffix}"])), dtype=int) for suffix in sets]
        weight_rows = [np.asarray(glb.accessor_values(int(attributes[f"WEIGHTS_{suffix}"])), dtype=float) for suffix in sets]
        if any(len(rows) != len(positions) for rows in (*joint_rows, *weight_rows)):
            raise ContractError("skin POSITION, JOINTS and WEIGHTS counts differ")
        if positions.ndim != 2 or positions.shape[1] != 3 or any(
            joints.ndim != 2 or weights.shape != joints.shape
            for joints, weights in zip(joint_rows, weight_rows)
        ):
            raise ContractError("skin POSITION, JOINTS or WEIGHTS has an invalid shape")
        if any(not np.isfinite(weights).all() or np.any(weights < 0) for weights in weight_rows):
            raise ContractError("skin weights must be finite and nonnegative")
        weight_sum = sum(rows.sum(axis=1) for rows in weight_rows)
        if not np.isfinite(weight_sum).all() or float(np.max(np.abs(weight_sum - 1.0))) > 2e-6:
            raise ContractError("skin weights are nonfinite or do not sum to one")
        homogeneous = np.column_stack((positions, np.ones(len(positions))))
        expected = (mesh_world @ homogeneous.T).T[:, :3]
        actual = np.zeros_like(expected)
        for joint_set, weight_set in zip(joint_rows, weight_rows):
            for column in range(joint_set.shape[1]):
                slots = joint_set[:, column]
                if np.any(slots < 0) or np.any(slots >= len(joints)):
                    raise ContractError("skin joint weight references an invalid joint slot")
                weights = weight_set[:, column]
                for slot in np.unique(slots[weights != 0]):
                    mask = (slots == slot) & (weights != 0)
                    transformed = (worlds[joints[int(slot)]] @ inverse[int(slot)] @ homogeneous[mask].T).T[:, :3]
                    actual[mask] += weights[mask, None] * transformed
        maximum = max(maximum, float(np.max(np.linalg.norm(actual - expected, axis=1))))
        vertices += len(positions)
    return maximum, vertices


def _recover_bind_pose(source: Glb, roles: Mapping[str, Any], *, skin_index: int) -> tuple[list[Any], list[Any], list[Any], dict[str, Any]]:
    if isinstance(skin_index, bool) or not isinstance(skin_index, int):
        raise ContractError("bind-pose recovery requires an explicit integer skin index")
    skins = source.document.get("skins")
    if not isinstance(skins, list) or not 0 <= skin_index < len(skins):
        raise ContractError("bind-pose recovery skin index is outside the source")
    skin = skins[skin_index]
    joints_raw = skin.get("joints") if isinstance(skin, Mapping) else None
    inverse_accessor = skin.get("inverseBindMatrices") if isinstance(skin, Mapping) else None
    if not isinstance(joints_raw, list) or not joints_raw or not isinstance(inverse_accessor, int):
        raise ContractError("bind-pose recovery requires joints and inverse bind matrices")
    try:
        joints = [int(value) for value in joints_raw]
    except (TypeError, ValueError, OverflowError) as exc:
        raise ContractError("bind-pose recovery joints are malformed") from exc
    if len(set(joints)) != len(joints) or any(not 0 <= value < len(source.nodes) for value in joints):
        raise ContractError("bind-pose recovery joints must be unique valid nodes")
    for node in range(len(source.nodes)):
        seen: set[int] = set()
        cursor: int | None = node
        while cursor is not None:
            if cursor in seen:
                raise ContractError("bind-pose recovery hierarchy contains a cycle")
            seen.add(cursor)
            cursor = source.parents[cursor]
    semantic = _semantic_node_names(roles)
    if not semantic or any(name not in source.name_to_node for name in semantic):
        raise ContractError("bind-pose recovery semantic role references an unknown node")
    if any(source.name_to_node[name] not in set(joints) for name in semantic):
        raise ContractError("bind-pose recovery semantic roles must belong to the selected skin")
    mesh_nodes = [index for index, node in enumerate(source.nodes) if node.get("skin") == skin_index]
    if len(mesh_nodes) != 1 or not isinstance(source.nodes[mesh_nodes[0]].get("mesh"), int):
        raise ContractError("bind-pose recovery requires exactly one mesh node for the selected skin")
    mesh_node = mesh_nodes[0]
    inverse_rows = source.accessor_values(inverse_accessor)
    if len(inverse_rows) != len(joints):
        raise ContractError("bind-pose recovery inverse bind count differs from joints")
    current_worlds = [np.asarray(value, dtype=float) for value in _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)]
    mesh_world = _matrix(current_worlds[mesh_node], label="skin mesh world")
    if abs(float(np.linalg.det(mesh_world[:3, :3]))) <= 1e-12:
        raise ContractError("bind-pose recovery mesh world is singular")
    desired: dict[int, np.ndarray] = {}
    for slot, node in enumerate(joints):
        inverse = _column_major_matrix(inverse_rows[slot], label=f"inverse bind[{slot}]")
        if abs(float(np.linalg.det(inverse[:3, :3]))) <= 1e-12:
            raise ContractError(f"inverse bind[{slot}] is singular")
        desired[node] = _matrix(mesh_world @ np.linalg.inv(inverse), label=f"recovered joint world[{slot}]")
    depths: dict[int, int] = {}
    def depth(node: int) -> int:
        if node in depths:
            return depths[node]
        seen: set[int] = set()
        cursor: int | None = node
        value = 0
        while cursor is not None:
            if cursor in seen:
                raise ContractError("bind-pose recovery hierarchy contains a cycle")
            seen.add(cursor)
            cursor = source.parents[cursor]
            value += 1
        depths[node] = value
        return value
    translations = list(source.rest_translation)
    rotations = list(source.rest_rotation)
    scales = list(source.rest_scale)
    diagnostics = []
    for node in sorted(joints, key=depth):
        parent = source.parents[node]
        parent_world = np.eye(4) if parent is None else desired.get(parent, current_worlds[parent])
        if abs(float(np.linalg.det(parent_world[:3, :3]))) <= 1e-12:
            raise ContractError("bind-pose recovery parent world is singular")
        local = np.linalg.solve(parent_world, desired[node])
        translation, rotation, scale, row = _decompose_bind_local(local, label=f"recovered joint local[{node}]")
        translations[node], rotations[node], scales[node] = tuple(translation), tuple(rotation), tuple(scale)
        diagnostics.append(row)
    trial_document = deepcopy(source.document)
    for index, node in enumerate(trial_document["nodes"]):
        node.pop("matrix", None)
        node["translation"] = [float(value) for value in translations[index]]
        node["rotation"] = [float(value) for value in rotations[index]]
        node["scale"] = [float(value) for value in scales[index]]
    trial_document.pop("animations", None)
    trial = Glb.from_bytes(_encode(trial_document, source.binary))
    reopened_worlds = [np.asarray(value, dtype=float) for value in _world_matrices(
        trial, trial.rest_translation, trial.rest_rotation, trial.rest_scale)]
    world_errors = [float(np.max(np.abs(reopened_worlds[node] - desired[node]))) for node in joints]
    maximum_world = max(world_errors)
    if maximum_world > _BIND_REOPENED_WORLD_TOLERANCE_M:
        raise ContractError("reopened bind-pose FK exceeds tolerance")
    maximum_skin, vertex_count = _skin_reconstruction_error(trial, skin_index=skin_index, mesh_node=mesh_node)
    if maximum_skin > _BIND_REOPENED_SKIN_TOLERANCE_M:
        raise ContractError("reopened bind-pose skin reconstruction exceeds tolerance")
    return translations, rotations, scales, {
        "method": "skin_bind_pose_from_inverse_bind_matrices.v1",
        "skin_index": skin_index,
        "mesh_node": mesh_node,
        "joint_count": len(joints),
        "vertex_count": vertex_count,
        "binary_buffer_preserved": True,
        "inverse_bind_matrices_preserved": True,
        "input_animation_tracks_used": False,
        "tolerances": {
            "normalized_orthogonality": _BIND_NORMALIZED_ORTHOGONALITY_TOLERANCE,
            "local_projection": _BIND_LOCAL_PROJECTION_TOLERANCE,
            "reopened_world_matrix": _BIND_REOPENED_WORLD_TOLERANCE_M,
            "reopened_skin_position_m": _BIND_REOPENED_SKIN_TOLERANCE_M,
        },
        "measurements": {
            "maximum_input_normalized_orthogonality_error": max(row["normalized_orthogonality_error"] for row in diagnostics),
            "maximum_local_projection_error": max(row["linear_projection_error"] for row in diagnostics),
            "minimum_input_normalized_determinant": min(row["normalized_determinant"] for row in diagnostics),
            "maximum_reopened_world_matrix_error": maximum_world,
            "maximum_reopened_skin_position_error_m": maximum_skin,
        },
    }


def admit_geometry(source: Glb, roles: Mapping[str, Any], *, reference_clip: str | None = None,
                   forward_axis: Any = None, up_axis: Any = (0, 1, 0),
                   recover_bind_pose: bool = False, skin_index: int | None = None) -> tuple[bytes, dict[str, Any]]:
    require_supported_geometry(source)
    try:
        root = source.name_to_node[roles["root"]]
    except KeyError as exc:
        raise ContractError("admission requires a bound root") from exc
    recovery = None
    if type(recover_bind_pose) is not bool:
        raise ContractError("recover_bind_pose must be boolean")
    if recover_bind_pose:
        if reference_clip is not None:
            raise ContractError("bind-pose recovery cannot sample a reference clip")
        if forward_axis is None:
            raise ContractError("bind-pose recovery requires an explicit forward axis")
        if skin_index is None:
            raise ContractError("bind-pose recovery requires an explicit skin index")
        t, r, s, recovery = _recover_bind_pose(source, roles, skin_index=skin_index)
    elif skin_index is not None:
        raise ContractError("skin index is only valid for bind-pose recovery")
    elif reference_clip is None:
        t, r, s = source.rest_translation, source.rest_rotation, source.rest_scale
        if forward_axis is None:
            raise ContractError("neutral source admission requires an explicit forward axis")
    else:
        tracks, times = _clip_state(source, reference_clip)
        t, r, s = _pose(source, tracks, 0)
        if forward_axis is None:
            first = _world_matrices(source, t, r, s)
            last = _world_matrices(source, *_pose(source, tracks, len(times) - 1))
            forward_axis = np.asarray(_world_position(last[root])) - _world_position(first[root])
    forward, up = frame_axes(forward_axis, up_axis)
    doc = deepcopy(source.document)
    for i, node in enumerate(doc["nodes"]):
        node["translation"] = [float(v) for v in t[i]]
        node["rotation"] = [float(v) for v in r[i]]
        node["scale"] = [float(v) for v in s[i]]
    doc.pop("animations", None)
    doc.pop("extras", None)
    doc["extras"] = {"eonwildGeometry": {"schema": "eonwild.motion.geometry.v1",
        "reference_clip": reference_clip, "forward_axis": forward.tolist(), "up_axis": up.tolist(),
        "claim": "calibrated geometry; no behavioral or biological validation"}}
    if recovery is not None:
        doc["extras"]["eonwildGeometry"]["bind_pose_recovery"] = recovery
    encoded = _encode(doc, source.binary)
    reopened = Glb.from_bytes(encoded)
    if reopened.document.get("animations"):
        raise ContractError("admitted geometry must not contain animations")
    return encoded, doc["extras"]["eonwildGeometry"]


def geometry_height(source: Glb, roles: Mapping[str, Any], up_axis: Any) -> float:
    worlds = _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale)
    _, up = frame_axes(source.document["extras"]["eonwildGeometry"]["forward_axis"], up_axis)
    try:
        pelvis = np.asarray(_world_position(worlds[source.name_to_node[roles["pelvis"]]]))
        toes = [source.name_to_node[name] for leg in roles["legs"].values() for chain in leg["toeChains"] for name in chain]
    except (KeyError, TypeError) as exc:
        raise ContractError("incomplete biped geometry binding") from exc
    if not toes:
        raise ContractError("digit geometry is required")
    ground = min(float(np.asarray(_world_position(worlds[n])) @ up) for n in toes)
    height = float(pelvis @ up - ground)
    if height <= 0:
        raise ContractError("pelvis must be above the toe plane")
    return height
