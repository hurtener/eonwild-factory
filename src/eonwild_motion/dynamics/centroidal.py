"""World-frame centroidal state from rig forward kinematics.

Implements the V9 engine contract (05_V9_BIOMECHANICAL_ENGINE.md sections
4-6, 9):

.. code-block:: text

    M   = Σ m_i
    c   = (1/M) Σ m_i p_i            (world-frame segment COM positions)
    P   = M c_dot
    L_c = Σ [ I_i ω_i + (p_i − c) × m_i (v_i − c_dot) ]

The COM path is planned first; the rig root is solved from it, never the
other way round::

    p_root(t) = c_world(t) − R_root(t) · c_rel(q(t))

Segments are bound to rig nodes by an explicit caller-supplied map
(``segment_id -> node name`` plus a node-local COM offset). No species
names, no per-taxon branching: the binding is data, validated and hashed
into every receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError

GRAVITY_MPS2 = np.array([0.0, -9.81, 0.0], dtype=float)


def _finite(value: float, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be a finite number")
    return result


def _vec3(value: Any, *, label: str) -> np.ndarray:
    if not isinstance(value, (list, tuple, np.ndarray)) or len(value) != 3:
        raise ContractError(f"{label} must contain exactly three numbers")
    return np.array([_finite(float(v), label=f"{label}[{i}]") for i, v in enumerate(value)], dtype=float)


def _quat(value: Any, *, label: str) -> np.ndarray:
    if not isinstance(value, (list, tuple, np.ndarray)) or len(value) != 4:
        raise ContractError(f"{label} must contain exactly four numbers")
    result = np.array([_finite(float(v), label=f"{label}[{i}]") for i, v in enumerate(value)], dtype=float)
    norm = float(np.linalg.norm(result))
    if norm <= 1e-15:
        raise ContractError(f"{label} is zero")
    return result / norm


def quat_to_matrix(q: np.ndarray) -> np.ndarray:
    """Unit quaternion (x, y, z, w) to 3x3 rotation matrix."""
    x, y, z, w = (float(v) for v in _quat(q, label="quaternion"))
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ],
        dtype=float,
    )


def quat_mul(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    lx, ly, lz, lw = (float(v) for v in left)
    rx, ry, rz, rw = (float(v) for v in right)
    return np.array(
        [
            lw * rx + rw * lx + ly * rz - lz * ry,
            lw * ry + rw * ly + lz * rx - lx * rz,
            lw * rz + rw * lz + lx * ry - ly * rx,
            lw * rw - lx * rx - ly * ry - lz * rz,
        ],
        dtype=float,
    )


def rotation_between_frames(previous: np.ndarray, current: np.ndarray, dt: float) -> np.ndarray:
    """Angular velocity (rad/s, world frame) taking R_prev -> R_curr over dt."""
    if dt <= 0.0:
        raise ContractError("angular velocity requires positive dt")
    delta = current @ previous.T
    trace = float(np.trace(delta))
    cos_angle = max(-1.0, min(1.0, (trace - 1.0) / 2.0))
    angle = math.acos(cos_angle)
    if angle < 1e-12:
        return np.zeros(3)
    axis = np.array([delta[2, 1] - delta[1, 2], delta[0, 2] - delta[2, 0], delta[1, 0] - delta[0, 1]])
    norm = float(np.linalg.norm(axis))
    if norm < 1e-12:
        return np.zeros(3)
    return axis / norm * (angle / dt)


def fk_world_frames(
    parents: Sequence[int | None],
    rest_translations: Sequence[Sequence[float]],
    rest_rotations: Sequence[Sequence[float]],
    local_translations: Sequence[Sequence[float]] | None = None,
    local_rotations: Sequence[Sequence[float]] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """One FK evaluation: world positions (N,3) and world rotations (N,3,3).

    ``local_*`` default to rest pose when omitted. Node order must match
    ``parents``. Raises :class:`ContractError` on topology or shape errors.
    """
    count = len(parents)
    if len(rest_translations) != count or len(rest_rotations) != count:
        raise ContractError("FK rest pose length must match node count")
    if local_translations is None:
        local_translations = list(rest_translations)
    if local_rotations is None:
        local_rotations = list(rest_rotations)
    if len(local_translations) != count or len(local_rotations) != count:
        raise ContractError("FK local pose length must match node count")

    world_rot = np.zeros((count, 3, 3))
    world_pos = np.zeros((count, 3))
    for node in range(count):
        parent = parents[node]
        if parent is not None and not 0 <= parent < count:
            raise ContractError(f"FK node {node} has an invalid parent")
        if parent is not None and parent >= node:
            raise ContractError("FK requires parents ordered before children")
        local_r = quat_to_matrix(np.asarray(local_rotations[node], dtype=float))
        local_t = np.asarray(local_translations[node], dtype=float).reshape(3)
        if parent is None:
            world_rot[node] = local_r
            world_pos[node] = local_t
        else:
            world_rot[node] = world_rot[parent] @ local_r
            world_pos[node] = world_pos[parent] + world_rot[parent] @ local_t
    return world_pos, world_rot


@dataclass(frozen=True)
class SegmentBinding:
    """One physical segment bound to a rig node.

    ``inertia_diag`` is the absolute diagonal inertia (kg·m²) expressed in
    the node frame. Use :func:`bind_profile_segments` to derive bindings
    from an admitted body-instance profile.
    """

    segment_id: str
    node_index: int
    mass_kg: float
    com_local_m: np.ndarray
    inertia_diag_kg_m2: np.ndarray


def bind_profile_segments(
    segments: Sequence[Mapping[str, Any]],
    *,
    name_to_node: Mapping[str, int],
    segment_to_node: Mapping[str, str],
    com_local_m: Mapping[str, Sequence[float]] | None = None,
    total_mass_kg: float | None,
    characteristic_height_m: float,
    absolute_dynamics_enabled: bool,
) -> tuple[SegmentBinding, ...]:
    """Bind profile segments to rig nodes with explicit, hashed inputs.

    Normalized profiles (``total_mass_kg=None``) bind with ``mass_kg`` as a
    mass *fraction*; downstream planners must then report normalized
    bookkeeping with physics unevaluated. Absolute inertia uses the
    first-pass engineering approximation ``I = diag_normalized · M · H²``,
    labeled as such in every receipt.
    """
    height = _finite(characteristic_height_m, label="characteristic height")
    if height <= 0.0:
        raise ContractError("characteristic height must be positive")
    mass_scale = 1.0 if total_mass_kg is None else _finite(total_mass_kg, label="total mass")
    if mass_scale <= 0.0:
        raise ContractError("total mass must be positive")
    if not absolute_dynamics_enabled and total_mass_kg is not None:
        raise ContractError("absolute mass requires an absolute-enabled profile")

    bound: list[SegmentBinding] = []
    seen: set[str] = set()
    for segment in segments:
        segment_id = str(segment["id"])
        if segment_id in seen:
            raise ContractError(f"duplicate segment {segment_id!r}")
        seen.add(segment_id)
        if segment_id not in segment_to_node:
            raise ContractError(f"segment {segment_id!r} has no rig binding")
        node_name = segment_to_node[segment_id]
        if node_name not in name_to_node:
            raise ContractError(f"segment {segment_id!r} binds unknown node {node_name!r}")
        fraction = _finite(float(segment["mass_fraction"]), label=f"segment {segment_id} mass_fraction")
        if fraction <= 0.0:
            raise ContractError(f"segment {segment_id!r} mass fraction must be positive")
        diag = _vec3(segment["inertia_diagonal_normalized"], label=f"segment {segment_id} inertia")
        if bool(np.any(diag <= 0.0)):
            raise ContractError(f"segment {segment_id!r} inertia diagonal must be positive")
        local = np.zeros(3)
        if com_local_m and segment_id in com_local_m:
            local = _vec3(com_local_m[segment_id], label=f"segment {segment_id} com_local")
        bound.append(
            SegmentBinding(
                segment_id=segment_id,
                node_index=int(name_to_node[node_name]),
                mass_kg=fraction * mass_scale,
                com_local_m=local,
                inertia_diag_kg_m2=diag * mass_scale * height * height,
            )
        )
    total = math.fsum(b.mass_kg for b in bound)
    expected = mass_scale if total_mass_kg is not None else 1.0
    if abs(total - expected) > 1e-9:
        raise ContractError(f"segment masses sum to {total}, expected {expected}")
    return tuple(bound)


@dataclass(frozen=True)
class CentroidalSample:
    time_s: float
    total_mass_kg: float
    com_m: tuple[float, float, float]
    com_velocity_mps: tuple[float, float, float]
    linear_momentum_kg_mps: tuple[float, float, float]
    angular_momentum_kg_m2ps: tuple[float, float, float]
    mass_mode: str  # "absolute" or "normalized"


def _finite_diff(values: np.ndarray, times: np.ndarray) -> np.ndarray:
    """Central differences on an irregular timeline (N,3) -> (N,3)."""
    count = len(times)
    out = np.zeros_like(values)
    for i in range(count):
        if i == 0:
            left, right = 0, 1
        elif i == count - 1:
            left, right = count - 2, count - 1
        else:
            left, right = i - 1, i + 1
        dt = float(times[right] - times[left])
        if dt <= 0.0:
            raise ContractError("centroidal timeline must be strictly increasing")
        out[i] = (values[right] - values[left]) / dt
    return out


def compute_centroidal_series(
    bindings: Sequence[SegmentBinding],
    *,
    times_s: Sequence[float],
    world_positions: Sequence[np.ndarray],
    world_rotations: Sequence[np.ndarray],
    mass_mode: str,
) -> tuple[CentroidalSample, ...]:
    """Whole-body centroidal series from per-frame FK evaluations.

    ``world_positions[k]`` / ``world_rotations[k]`` are the (N,3)/(N,3,3)
    FK outputs at ``times_s[k]``. Segment world COM = node position +
    node rotation applied to the node-local offset. Segment angular
    velocity comes from consecutive world rotation frames.
    """
    if mass_mode not in ("absolute", "normalized"):
        raise ContractError("mass mode must be 'absolute' or 'normalized'")
    times = np.asarray([_finite(float(t), label="sample time") for t in times_s], dtype=float)
    if len(times) < 2 or bool(np.any(np.diff(times) <= 0.0)):
        raise ContractError("centroidal series needs at least two increasing samples")
    frames = len(times)
    if len(world_positions) != frames or len(world_rotations) != frames:
        raise ContractError("FK frame count must match timeline")
    if not bindings:
        raise ContractError("centroidal series requires at least one segment")

    masses = np.array([b.mass_kg for b in bindings], dtype=float)
    total = float(masses.sum())
    seg_pos = np.zeros((frames, len(bindings), 3))
    for k in range(frames):
        pos, rot = world_positions[k], world_rotations[k]
        for j, binding in enumerate(bindings):
            seg_pos[k, j] = pos[binding.node_index] + rot[binding.node_index] @ binding.com_local_m
    com = (seg_pos * masses[None, :, None]).sum(axis=1) / total
    com_vel = _finite_diff(com, times)
    seg_vel = np.zeros_like(seg_pos)
    for j in range(len(bindings)):
        seg_vel[:, j] = _finite_diff(seg_pos[:, j], times)

    samples: list[CentroidalSample] = []
    for k in range(frames):
        angular = np.zeros(3)
        for j, binding in enumerate(bindings):
            if frames == 1:
                omega = np.zeros(3)
            elif k == 0:
                omega = rotation_between_frames(world_rotations[0][binding.node_index], world_rotations[1][binding.node_index], float(times[1] - times[0]))
            else:
                prev = max(0, k - 1)
                omega = rotation_between_frames(world_rotations[prev][binding.node_index], world_rotations[k][binding.node_index], float(times[k] - times[prev]))
            rot = world_rotations[k][binding.node_index]
            inertia_world = rot @ np.diag(binding.inertia_diag_kg_m2) @ rot.T
            r = seg_pos[k, j] - com[k]
            angular += inertia_world @ omega + np.cross(r, masses[j] * (seg_vel[k, j] - com_vel[k]))
        linear = total * com_vel[k]
        samples.append(
            CentroidalSample(
                time_s=float(times[k]),
                total_mass_kg=total,
                com_m=tuple(float(v) for v in com[k]),
                com_velocity_mps=tuple(float(v) for v in com_vel[k]),
                linear_momentum_kg_mps=tuple(float(v) for v in linear),
                angular_momentum_kg_m2ps=tuple(float(v) for v in angular),
                mass_mode=mass_mode,
            )
        )
    return tuple(samples)


def solve_root_from_com(
    com_world: Sequence[float],
    root_rotation: np.ndarray,
    com_relative_to_root: Sequence[float],
) -> tuple[float, float, float]:
    """``p_root = c_world − R_root · c_rel(q)`` (engine contract section 6).

    The pelvis/root is reconstructed from the planned whole-body COM and
    the pose-dependent COM offset in the root frame — never assumed to be
    the ballistic object itself.
    """
    com = _vec3(com_world, label="com_world")
    offset = _vec3(com_relative_to_root, label="com_relative_to_root")
    root = np.asarray(root_rotation, dtype=float).reshape(3, 3)
    solved = com - root @ offset
    return tuple(float(v) for v in solved)
