"""Exact one-sided tangents for emitted glTF LINEAR animation channels.

This module measures the interpolation actually serialized in a GLB.  It does
not alter animation keys, timing, limits, or source artifacts.  Translation and
scale are differentiated over their adjacent LINEAR segment; rotations use the
shortest SLERP angular velocity.  FK and LBS derivatives use the product rule.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from ..contact_gauge import _column_major_matrix, _normalize_skin_weights, _read_glb_accessor
from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _qinv, _qmatrix, _qmul, _q_to_rotvec

_PATHS = ("translation", "rotation", "scale")


def _numeric(value: Any, label: str) -> np.ndarray:
    result = np.asarray(value)
    if result.dtype.kind not in "fiu" or not np.isfinite(result).all():
        raise ContractError(f"{label} must be finite real values")
    return result.astype(float, copy=False)


def _names(glb: Glb) -> list[str]:
    names = [node.get("name", f"node_{index}") for index, node in enumerate(glb.nodes)]
    if any(not isinstance(name, str) for name in names) or len(set(names)) != len(names):
        raise ContractError("exact tangent witness requires unique node names")
    return names


def _tracks(glb: Glb, animation_name: str) -> tuple[dict[tuple[int, str], np.ndarray], np.ndarray]:
    animations = [animation for animation in glb.document.get("animations", []) if animation.get("name") == animation_name]
    if len(animations) != 1:
        raise ContractError("exact tangent witness requires one named animation")
    tracks: dict[tuple[int, str], np.ndarray] = {}
    timeline: np.ndarray | None = None
    for channel in animations[0].get("channels", []):
        if not isinstance(channel, Mapping) or not isinstance(channel.get("target"), Mapping):
            raise ContractError("exact tangent animation channel is malformed")
        target = channel["target"]
        node, path = target.get("node"), target.get("path")
        sampler_index = channel.get("sampler")
        if (isinstance(node, bool) or not isinstance(node, int) or node < 0 or node >= len(glb.nodes)
                or path not in _PATHS or isinstance(sampler_index, bool) or not isinstance(sampler_index, int)):
            raise ContractError("exact tangent animation target is invalid")
        samplers = animations[0].get("samplers", [])
        if sampler_index < 0 or sampler_index >= len(samplers):
            raise ContractError("exact tangent sampler is invalid")
        sampler = samplers[sampler_index]
        if sampler.get("interpolation", "LINEAR") != "LINEAR":
            raise ContractError("exact tangent witness requires emitted LINEAR channels")
        times = _numeric(glb.accessor_values(sampler["input"]), "exact tangent timestamps").reshape(-1)
        values = _numeric(glb.accessor_values(sampler["output"]), "exact tangent channel")
        width = 4 if path == "rotation" else 3
        if len(times) < 2 or values.shape != (len(times), width) or np.any(np.diff(times) <= 0):
            raise ContractError("exact tangent channel timeline is invalid")
        if timeline is None:
            timeline = times
        elif not np.array_equal(timeline, times):
            raise ContractError("exact tangent channels must share one timeline")
        key = (node, path)
        if key in tracks:
            raise ContractError("exact tangent animation duplicates a node path")
        tracks[key] = values
    if timeline is None:
        raise ContractError("exact tangent witness has no animated channels")
    _names(glb)
    return tracks, timeline


def _rotation_matrix(quaternion: np.ndarray) -> np.ndarray:
    return np.asarray(_qmatrix(tuple(float(value) for value in quaternion)), dtype=float)


def _skew(value: np.ndarray) -> np.ndarray:
    x, y, z = value
    return np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))


def _local_matrix(translation: np.ndarray, rotation: np.ndarray, scale: np.ndarray) -> np.ndarray:
    result = np.eye(4)
    result[:3, :3] = _rotation_matrix(rotation) @ np.diag(scale)
    result[:3, 3] = translation
    return result


@dataclass(frozen=True)
class EndpointTangent:
    time_s: float
    neighbor_time_s: float
    translations: np.ndarray
    rotations: np.ndarray
    scales: np.ndarray
    translation_velocity: np.ndarray
    angular_velocity: np.ndarray
    scale_velocity: np.ndarray
    world: np.ndarray
    world_velocity: np.ndarray
    names: tuple[str, ...]


def endpoint_tangent(glb: Glb, animation_name: str, *, endpoint: int, terminal: bool) -> EndpointTangent:
    """Return the actual one-sided tangent at an emitted endpoint/key.

    ``terminal`` selects the segment ending at ``endpoint``; otherwise it
    selects the segment beginning there.  Quaternion sign-equivalent encodings
    are normalized by the shared shortest-rotation conversion.
    """
    tracks, times = _tracks(glb, animation_name)
    if endpoint < 0 or endpoint >= len(times):
        raise ContractError("exact tangent endpoint is outside timeline")
    neighbor = endpoint - 1 if terminal else endpoint + 1
    if neighbor < 0 or neighbor >= len(times):
        raise ContractError("exact tangent endpoint has no adjacent segment")
    dt = abs(float(times[endpoint] - times[neighbor]))
    if not math.isfinite(dt) or dt <= 0:
        raise ContractError("exact tangent adjacent duration is invalid")
    count = len(glb.nodes)
    translation = _numeric(glb.rest_translation, "rest translation").copy()
    rotation = _numeric(glb.rest_rotation, "rest rotation").copy()
    scale = _numeric(glb.rest_scale, "rest scale").copy()
    if translation.shape != (count, 3) or rotation.shape != (count, 4) or scale.shape != (count, 3):
        raise ContractError("exact tangent rest TRS is invalid")
    other_t, other_q, other_s = translation.copy(), rotation.copy(), scale.copy()
    for node in range(count):
        for path, target, other in (("translation", translation, other_t), ("rotation", rotation, other_q), ("scale", scale, other_s)):
            values = tracks.get((node, path))
            if values is not None:
                target[node], other[node] = values[endpoint], values[neighbor]
    norms = np.linalg.norm(rotation, axis=1)
    other_norms = np.linalg.norm(other_q, axis=1)
    if np.any(norms <= 1e-15) or np.any(other_norms <= 1e-15):
        raise ContractError("exact tangent quaternion is zero")
    rotation /= norms[:, None]
    other_q /= other_norms[:, None]
    if terminal:
        tdot, sdot, first, second = (translation - other_t) / dt, (scale - other_s) / dt, other_q, rotation
    else:
        tdot, sdot, first, second = (other_t - translation) / dt, (other_s - scale) / dt, rotation, other_q
    omega = np.asarray([
        _q_to_rotvec(_qmul(_qinv(tuple(a)), tuple(b))) for a, b in zip(first, second)
    ], dtype=float) / dt
    local, local_dot = [], []
    for node in range(count):
        r = _rotation_matrix(rotation[node])
        matrix = _local_matrix(translation[node], rotation[node], scale[node])
        derivative = np.zeros((4, 4))
        derivative[:3, :3] = r @ _skew(omega[node]) @ np.diag(scale[node]) + r @ np.diag(sdot[node])
        derivative[:3, 3] = tdot[node]
        local.append(matrix)
        local_dot.append(derivative)
    world: list[np.ndarray | None] = [None] * count
    derivative: list[np.ndarray | None] = [None] * count
    visiting: set[int] = set()
    def resolve(node: int) -> tuple[np.ndarray, np.ndarray]:
        if world[node] is not None:
            return world[node], derivative[node]  # type: ignore[return-value]
        if node in visiting:
            raise ContractError("exact tangent node topology contains a cycle")
        visiting.add(node)
        parent = glb.parents[node]
        if parent is None:
            world[node], derivative[node] = local[node], local_dot[node]
        else:
            parent_world, parent_dot = resolve(int(parent))
            world[node] = parent_world @ local[node]
            derivative[node] = parent_dot @ local[node] + parent_world @ local_dot[node]
        visiting.remove(node)
        return world[node], derivative[node]  # type: ignore[return-value]
    for node in range(count):
        resolve(node)
    return EndpointTangent(float(times[endpoint]), float(times[neighbor]), translation, rotation, scale,
        tdot, omega, sdot, np.asarray(world), np.asarray(derivative), tuple(_names(glb)))


def descendant_indices(glb: Glb, root: int) -> list[int]:
    if root < 0 or root >= len(glb.nodes):
        raise ContractError("exact tangent root is invalid")
    result: list[int] = []
    for node in range(len(glb.nodes)):
        cursor, seen = node, set()
        while cursor is not None:
            if cursor in seen:
                raise ContractError("exact tangent node topology contains a cycle")
            seen.add(cursor)
            if cursor == root:
                result.append(node)
                break
            cursor = glb.parents[cursor]
    if not result:
        raise ContractError("exact tangent has no motion-owned nodes")
    return result


def _skin_influences(glb: Glb, profile: Mapping[str, Any]) -> tuple[np.ndarray, tuple[tuple[tuple[int, float], ...], ...], list[int], np.ndarray, list[tuple[str, int]]]:
    try:
        geometry = profile["geometry"]
        positions = _numeric(_read_glb_accessor(glb, geometry["position_accessor"], label="exact tangent position"), "exact tangent positions")
        joint_rows = [_read_glb_accessor(glb, index, label="exact tangent joints") for index in geometry["joint_accessors"]]
        weight_rows = [_read_glb_accessor(glb, index, label="exact tangent weights") for index in geometry["weight_accessors"]]
        skin = glb.document["skins"][int(geometry["skin_index"])]
        joint_nodes = [int(value) for value in skin["joints"]]
        inverse = np.asarray([_column_major_matrix(row) for row in _read_glb_accessor(glb, skin["inverseBindMatrices"], label="exact tangent inverse bind")], dtype=float)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ContractError("exact tangent skin binding is invalid") from exc
    if positions.ndim != 2 or positions.shape[1] != 3 or not joint_nodes or inverse.shape != (len(joint_nodes), 4, 4):
        raise ContractError("exact tangent skin geometry is invalid")
    if any(node < 0 or node >= len(glb.nodes) for node in joint_nodes):
        raise ContractError("exact tangent skin joint is invalid")
    influences = _normalize_skin_weights(joint_rows, weight_rows, vertex_count=len(positions), joint_count=len(joint_nodes))
    names = {name: index for index, name in enumerate(_names(glb))}
    selected: list[tuple[str, int]] = []
    for side in ("left", "right"):
        try:
            mask = geometry["feet"][side]
            threshold = float(mask["weight_threshold"])
            regions = (("sole", mask["sole_joints"]), ("toe", mask["toe_joints"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError("exact tangent skin mask is invalid") from exc
        for region, names_for_region in regions:
            try:
                targets = {names[name] for name in names_for_region}
            except (KeyError, TypeError) as exc:
                raise ContractError("exact tangent skin mask references unknown node") from exc
            matches = [vertex for vertex, rows in enumerate(influences) if max((weight for slot, weight in rows if joint_nodes[slot] in targets), default=0.) >= threshold]
            if not matches:
                raise ContractError("exact tangent skin mask selected no vertices")
            selected.extend((f"{side}:{region}:vertex-{vertex}", vertex) for vertex in matches)
    return positions, influences, joint_nodes, inverse, selected


def skinned_velocity(glb: Glb, profile: Mapping[str, Any], tangent: EndpointTangent) -> tuple[list[str], np.ndarray]:
    positions, influences, joint_nodes, inverse, selected = _skin_influences(glb, profile)
    result: list[np.ndarray] = []
    for _, vertex in selected:
        point = np.append(positions[vertex], 1.)
        velocity = np.zeros(3)
        for slot, weight in influences[vertex]:
            velocity += weight * (tangent.world_velocity[joint_nodes[slot]] @ inverse[slot] @ point)[:3]
        result.append(velocity)
    return [label for label, _ in selected], np.asarray(result)


def local_cyclic_tangents(glb: Glb, animation_name: str) -> dict[str, Any]:
    """Exact local-channel loop metric; intentionally does not claim world/LBS scope."""
    tracks, times = _tracks(glb, animation_name)
    for (node, path), values in tracks.items():
        if path == "scale" and not np.all(values == values[0]):
            raise ContractError("cyclic tangent witness does not govern nonconstant animated scale channels")
    end = endpoint_tangent(glb, animation_name, endpoint=len(times) - 1, terminal=True)
    start = endpoint_tangent(glb, animation_name, endpoint=0, terminal=False)
    translation = np.linalg.norm(end.translation_velocity - start.translation_velocity, axis=1)
    angular = np.degrees(np.linalg.norm(end.angular_velocity - start.angular_velocity, axis=1))
    def maximum(values: np.ndarray, incoming: np.ndarray, outgoing: np.ndarray, unit: str) -> tuple[float, dict[str, Any]]:
        index = int(np.argmax(values))
        return float(values[index]), {
            "node": index, "bone": end.names[index], "incoming": incoming[index].tolist(), "outgoing": outgoing[index].tolist(),
            "incoming_key": {"time_s": end.time_s, "neighbor_time_s": end.neighbor_time_s},
            "outgoing_key": {"time_s": start.time_s, "neighbor_time_s": start.neighbor_time_s}, "unit": unit,
        }
    linear, linear_witness = maximum(translation, end.translation_velocity, start.translation_velocity, "m/s")
    rotation, angular_witness = maximum(angular, end.angular_velocity, start.angular_velocity, "rad/s")
    return {"linear_m_per_s": linear, "angular_degrees_per_s": rotation,
            "witnesses": {"linear": linear_witness, "angular": angular_witness},
            "classification": "exact adjacent LINEAR translation and shortest-SLERP local-channel tangents; constant scale is admitted and nonconstant animated scale rejects; not a world or skinned-loop claim"}
