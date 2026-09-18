"""Rotation-first, pelvis-attached contact resolver for V9.

The rejected WALK-001 implementation moved both complete leg chains through
identity-rest parent translation controls.  This layer has no control-node or
leg-root translation degree of freedom.  It keeps the source sockets attached
to the pelvis, then distributes the requested lane correction across the
semantic hip, knee, and ankle rotations with bounded damped least squares.

The local foot translation and toe-chain channels are deliberately untouched;
the solver targets a hash-bound rigid contact patch attached to the foot
instead of the animated foot-root point alone.  The source rocker and toe
articulation remain the contact authority.  A separate, small
``support_balance_proxy`` may provide a pelvis-local translation and bounded
body rotations.  That response is a phase proxy, never a physical COM solve.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import Any, Mapping, Sequence

from ..errors import ContractError, ValidationFailure
from ..glb.animation import read_animation_tracks
from .narrow_gauge_target_space_v1 import TargetSample


Vec3 = tuple[float, float, float]
Quat = tuple[float, float, float, float]
Mat4 = tuple[tuple[float, float, float, float], ...]

# Keep this order stable in receipts and in the over-determined solve.  The
# order is part of the contact contract: the foot origin is not an implicit
# replacement for any of these measured witnesses.
CONTACT_WITNESS_NAMES = ("anchor", "contact", "sole", "toe", "foot_reference")
# Numerical reconstruction tolerance for normalized world matrices.  This is
# not an art/heading envelope; the profile-owned 15-degree limits remain the
# actual correction and measured-output gates.
WORLD_ROTATION_NUMERICAL_TOLERANCE_DEGREES = 1.0e-5


def _number(value: Any, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be a finite number")
    return result


def _vec3(value: Sequence[float], *, label: str) -> Vec3:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ContractError(f"{label} must contain three numbers")
    return tuple(_number(item, label=f"{label}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]


def _q(value: Sequence[float], *, label: str) -> Quat:
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ContractError(f"{label} must contain four numbers")
    output = tuple(_number(item, label=f"{label}[{index}]") for index, item in enumerate(value))
    length = math.sqrt(sum(item * item for item in output))
    if length <= 1.0e-15:
        raise ContractError(f"{label} is zero")
    return tuple(item / length for item in output)  # type: ignore[return-value]


def _add(left: Vec3, right: Vec3) -> Vec3:
    return tuple(a + b for a, b in zip(left, right))  # type: ignore[return-value]


def _sub(left: Vec3, right: Vec3) -> Vec3:
    return tuple(a - b for a, b in zip(left, right))  # type: ignore[return-value]


def _scale(value: Vec3, factor: float) -> Vec3:
    return tuple(item * factor for item in value)  # type: ignore[return-value]


def _dot(left: Vec3, right: Vec3) -> float:
    return sum(a * b for a, b in zip(left, right))


def _norm(value: Vec3) -> float:
    return math.sqrt(_dot(value, value))


def _unit(value: Vec3, *, label: str) -> Vec3:
    length = _norm(value)
    if length <= 1.0e-15:
        raise ContractError(f"{label} is zero")
    return _scale(value, 1.0 / length)


def _qmul(left: Quat, right: Quat) -> Quat:
    lx, ly, lz, lw = left
    rx, ry, rz, rw = right
    value = (
        lw * rx + rw * lx + ly * rz - lz * ry,
        lw * ry + rw * ly + lz * rx - lx * rz,
        lw * rz + rw * lz + lx * ry - ly * rx,
        lw * rw - lx * rx - ly * ry - lz * rz,
    )
    return _q(value, label="quaternion multiplication")


def _qinv(value: Quat) -> Quat:
    unit = _q(value, label="quaternion inverse")
    return (-unit[0], -unit[1], -unit[2], unit[3])


def _q_to_rotvec(value: Quat) -> Vec3:
    quaternion = _q(value, label="rotation-vector source")
    if quaternion[3] < 0.0:
        quaternion = tuple(-item for item in quaternion)  # type: ignore[assignment]
    vector = quaternion[:3]
    sine = _norm(vector)  # type: ignore[arg-type]
    if sine <= 1.0e-12:
        return tuple(2.0 * item for item in vector)  # type: ignore[return-value]
    angle = 2.0 * math.atan2(sine, max(-1.0, min(1.0, quaternion[3])))
    return _scale(vector, angle / sine)  # type: ignore[arg-type]


def _qrotvec(value: Vec3) -> Quat:
    angle = _norm(value)
    half = 0.5 * angle
    if angle <= 1.0e-12:
        factor = 0.5 - angle * angle / 48.0
    else:
        factor = math.sin(half) / angle
    return _q(
        (value[0] * factor, value[1] * factor, value[2] * factor, math.cos(half)),
        label="rotation-vector quaternion",
    )


def _qmatrix(value: Quat) -> tuple[tuple[float, float, float], ...]:
    x, y, z, w = _q(value, label="rotation matrix quaternion")
    return (
        (1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)),
        (2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)),
        (2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)),
    )


def _qrotate(value: Quat, point: Vec3) -> Vec3:
    matrix = _qmatrix(value)
    return tuple(
        sum(matrix[row][column] * point[column] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def _rotate_about_pivot(point: Vec3, pivot: Vec3, rotation: Quat) -> Vec3:
    return _add(pivot, _qrotate(rotation, _sub(point, pivot)))


def derive_constant_cyclic_heading_corrections(
    source_heading_degrees: Mapping[str, Sequence[float]],
    heading_policy: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    """Derive the closest-to-zero constant per-side yaw that fits the cap.

    A constant correction is cyclic by construction.  The feasible interval
    is the exact intersection of every sample's signed heading interval, so a
    clip whose heading span cannot fit below the profile-owned solve limit is
    rejected instead of clamped or phase-warped.
    """

    required_policy = {
        "mode",
        "target_abs_max_degrees",
        "solve_target_abs_max_degrees",
        "max_correction_degrees",
        "preserve_toe_metatarsal_local_articulation",
    }
    missing = sorted(required_policy - set(heading_policy))
    if missing:
        raise ContractError(f"whole-foot heading policy is missing {missing}")
    if heading_policy.get("mode") != "preserve_source_world_heading_and_local_toe_articulation":
        raise ContractError("whole-foot heading mode is unsupported")
    if heading_policy.get("preserve_toe_metatarsal_local_articulation") is not True:
        raise ContractError("whole-foot heading must preserve toe/metatarsal articulation")
    extended_policy = "safety_margin_degrees" in heading_policy
    if extended_policy and "strategy" not in heading_policy:
        raise ContractError("whole-foot heading strategy is missing")
    if extended_policy and "pivot_witness" not in heading_policy:
        raise ContractError("whole-foot heading pivot witness is missing")
    strategy = heading_policy.get("strategy", "minimal_constant_cyclic_per_side")
    pivot = heading_policy.get("pivot_witness", "distal_toe_centroid")
    if strategy != "minimal_constant_cyclic_per_side":
        raise ContractError("whole-foot heading strategy must be minimal constant cyclic per side")
    if pivot != "distal_toe_centroid":
        raise ContractError("whole-foot heading pivot must be the distal toe centroid")
    target_limit = _number(
        heading_policy["target_abs_max_degrees"],
        label="whole-foot heading target limit",
    )
    solve_limit = _number(
        heading_policy["solve_target_abs_max_degrees"],
        label="whole-foot heading solve limit",
    )
    correction_cap = _number(
        heading_policy["max_correction_degrees"],
        label="whole-foot heading correction cap",
    )
    safety_margin = _number(
        heading_policy.get("safety_margin_degrees", 0.0),
        label="whole-foot heading safety margin",
    )
    if min(target_limit, solve_limit, correction_cap) <= 0.0 or safety_margin < 0.0:
        raise ContractError("whole-foot heading limits are outside their positive domain")
    effective_limit = min(target_limit, solve_limit) - safety_margin
    if effective_limit <= 0.0:
        raise ContractError("whole-foot heading safety margin consumes the solve domain")

    corrections: dict[str, float] = {}
    per_side: dict[str, Any] = {}
    for side in ("left", "right"):
        raw_values = source_heading_degrees.get(side)
        if not isinstance(raw_values, Sequence) or isinstance(raw_values, (str, bytes)) or len(raw_values) < 2:
            raise ContractError(f"whole-foot heading samples are missing {side}")
        values = tuple(
            _number(value, label=f"whole-foot heading {side}[{index}]")
            for index, value in enumerate(raw_values)
        )
        lower = max(-effective_limit - value for value in values)
        upper = min(effective_limit - value for value in values)
        if lower > upper + 1.0e-12:
            raise ValidationFailure(
                f"whole-foot heading has no constant cyclic solution for {side}"
            )
        correction = min(max(0.0, lower), upper)
        if abs(correction) > correction_cap + 1.0e-12:
            raise ValidationFailure(
                f"whole-foot heading correction exceeds the profile cap for {side}"
            )
        candidate = tuple(value + correction for value in values)
        maximum_abs = max(abs(value) for value in candidate)
        if maximum_abs > effective_limit + 1.0e-10:
            raise ValidationFailure(
                f"whole-foot heading correction does not satisfy the solve target for {side}"
            )
        corrections[side] = correction
        per_side[side] = {
            "source_minimum_degrees": min(values),
            "source_maximum_degrees": max(values),
            "source_maximum_abs_degrees": max(abs(value) for value in values),
            "feasible_correction_interval_degrees": [lower, upper],
            "correction_degrees": correction,
            "candidate_minimum_degrees": min(candidate),
            "candidate_maximum_degrees": max(candidate),
            "candidate_maximum_abs_degrees": maximum_abs,
            "sample_count": len(values),
            "constant": True,
            "cyclic_correction_seam_degrees": 0.0,
            "within_correction_cap": True,
            "within_effective_solve_limit": True,
        }
    receipt = {
        "status": "PASS",
        "strategy": strategy,
        "pivot_witness": pivot,
        "target_abs_max_degrees": target_limit,
        "solve_target_abs_max_degrees": solve_limit,
        "safety_margin_degrees": safety_margin,
        "effective_solve_abs_max_degrees": effective_limit,
        "max_correction_degrees": correction_cap,
        "constant_cyclic_per_side": True,
        "per_side": per_side,
    }
    return corrections, receipt


def _local_matrix(translation: Vec3, rotation: Quat, scale: Vec3) -> Mat4:
    basis = _qmatrix(rotation)
    return tuple(
        tuple(basis[row][column] * scale[column] for column in range(3)) + (translation[row],)
        for row in range(3)
    ) + ((0.0, 0.0, 0.0, 1.0),)  # type: ignore[return-value]


def _q_angle_degrees(left: Quat, right: Quat) -> float:
    """Shortest actual angular distance between two unit quaternions."""

    first = _q(left, label="frame-angle left")
    second = _q(right, label="frame-angle right")
    dot = abs(sum(a * b for a, b in zip(first, second)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, dot))))


def _max_correction_frame_change_degrees(
    source_rows: Sequence[Sequence[float]],
    candidate_rows: Sequence[Sequence[float]],
    *,
    label: str,
) -> float:
    """Measure temporal change introduced by a correction, not source motion."""

    if len(source_rows) != len(candidate_rows) or len(source_rows) < 2:
        raise ContractError(f"{label}: source and candidate rotation rows are not aligned")
    deltas = [
        _qmul(
            _qinv(_q(source, label=f"{label} source rotation")),
            _q(candidate, label=f"{label} candidate rotation"),
        )
        for source, candidate in zip(source_rows, candidate_rows)
    ]
    maximum = max(
        (_q_angle_degrees(left, right) for left, right in zip(deltas, deltas[1:])),
        default=0.0,
    )
    if len(deltas) > 2:
        maximum = max(maximum, _q_angle_degrees(deltas[-2], deltas[0]))
    return maximum


def _matmul(left: Mat4, right: Mat4) -> Mat4:
    return tuple(
        tuple(sum(left[row][k] * right[k][column] for k in range(4)) for column in range(4))
        for row in range(4)
    )  # type: ignore[return-value]


def _mat_point(matrix: Mat4, point: Vec3) -> Vec3:
    return tuple(
        sum(matrix[row][column] * point[column] for column in range(3)) + matrix[row][3]
        for row in range(3)
    )  # type: ignore[return-value]


def _inverse_point(matrix: Mat4, point: Vec3) -> Vec3:
    """Transform a world-space contact witness into a node-local point.

    Contact witnesses are measured in world space by the immutable source
    analyzer.  The solver keeps their rigid offsets from the source foot node
    and moves that whole patch through the pelvis-attached chain.  Solving the
    affine basis also preserves this contract when a source has non-unit
    scale, while a singular basis fails closed through ``_solve_linear``.
    """

    right = tuple(float(point[index]) - matrix[index][3] for index in range(3))
    basis = tuple(
        tuple(float(matrix[row][column]) for column in range(3))
        for row in range(3)
    )
    return tuple(_solve_linear(basis, right))  # type: ignore[return-value]


def _contact_patch_points(sample: TargetSample, *, label: str) -> tuple[tuple[str, Vec3], ...]:
    """Return the complete rigid contact patch required by the V9 solver.

    All four witnesses are intentionally required at the solver boundary.
    The source planner may make an explicit swing fallback (for example, use
    the toe centroid for a frame without active contact), but an incomplete
    target must never silently fall back to a foot-bone origin here.
    """

    values = (
        ("anchor", sample.anchor_point_m),
        ("contact", sample.contact_point_m),
        ("sole", sample.sole_centroid_m),
        ("toe", sample.toe_centroid_m),
        ("foot_reference", sample.foot_root_m),
    )
    if any(value is None for _, value in values):
        missing = [name for name, value in values if value is None]
        raise ContractError(f"{label}: contact patch is missing {missing}")
    return tuple(
        (name, _vec3(value, label=f"{label}.{name}"))
        for name, value in values
    )  # type: ignore[arg-type]


def _witness_residual_receipt(
    candidate_patch: Mapping[str, Sequence[float]],
    required_patch: Mapping[str, Sequence[float]],
    *,
    tolerance_m: float,
    label: str = "contact patch",
    raise_on_failure: bool = False,
) -> dict[str, Any]:
    """Compare every contact witness in one post-body root/world basis.

    ``candidate_patch`` and ``required_patch`` are deliberately mappings rather
    than a single foot point.  This prevents an anchor-only solve from hiding
    a sole/toe miss.  Missing or malformed witnesses are contract errors; a
    measured residual above tolerance is represented per witness and can be
    promoted to :class:`ValidationFailure` by callers that need fail-closed
    admission (the frame solver uses the receipt to mark the clip rejected).
    """

    tolerance = _number(tolerance_m, label=f"{label} tolerance")
    if tolerance <= 0.0:
        raise ContractError(f"{label} tolerance must be positive")
    if not isinstance(candidate_patch, Mapping) or not isinstance(required_patch, Mapping):
        raise ContractError(f"{label} candidate and required patches must be mappings")
    missing_candidate = [name for name in CONTACT_WITNESS_NAMES if name not in candidate_patch]
    missing_required = [name for name in CONTACT_WITNESS_NAMES if name not in required_patch]
    if missing_candidate:
        raise ContractError(f"{label}: candidate patch is missing {missing_candidate}")
    if missing_required:
        raise ContractError(f"{label}: required patch is missing {missing_required}")
    witnesses: dict[str, dict[str, Any]] = {}
    failed: list[str] = []
    for name in CONTACT_WITNESS_NAMES:
        candidate = _vec3(candidate_patch[name], label=f"{label}.candidate.{name}")
        required = _vec3(required_patch[name], label=f"{label}.required.{name}")
        residual = _norm(_sub(candidate, required))
        passed = residual <= tolerance + 1.0e-12
        if not passed:
            failed.append(name)
        witnesses[name] = {
            "candidate_m": list(candidate),
            "required_m": list(required),
            "residual_m": residual,
            "tolerance_m": tolerance,
            "status": "PASS" if passed else "FAIL",
        }
    receipt: dict[str, Any] = {
        "status": "PASS" if not failed else "FAIL",
        "basis": "pre_body_source_world_plus_declared_lane_offset",
        "witness_order": list(CONTACT_WITNESS_NAMES),
        "witnesses": witnesses,
        # Keep these names explicit at the receipt boundary.  Consumers should
        # not need to infer which side of the residual was measured.
        "candidate_patch_m": {
            name: witnesses[name]["candidate_m"] for name in CONTACT_WITNESS_NAMES
        },
        "required_patch_m": {
            name: witnesses[name]["required_m"] for name in CONTACT_WITNESS_NAMES
        },
        "residual_m_by_witness": {
            name: witnesses[name]["residual_m"] for name in CONTACT_WITNESS_NAMES
        },
        "failed_witnesses": failed,
    }
    if failed and raise_on_failure:
        raise ValidationFailure(
            f"{label}: witness residual exceeds tolerance for {failed}"
        )
    return receipt


def validate_witness_residuals(
    candidate_patch: Mapping[str, Sequence[float]],
    required_patch: Mapping[str, Sequence[float]],
    *,
    tolerance_m: float,
    label: str = "contact patch",
) -> dict[str, Any]:
    """Return a receipt or fail closed when any named witness drifts."""

    return _witness_residual_receipt(
        candidate_patch,
        required_patch,
        tolerance_m=tolerance_m,
        label=label,
        raise_on_failure=True,
    )


def _world_matrices(
    glb: Any,
    translations: Sequence[Vec3],
    rotations: Sequence[Quat],
    scales: Sequence[Vec3],
) -> tuple[Mat4, ...]:
    worlds: list[Mat4 | None] = [None] * len(glb.nodes)

    def resolve(index: int) -> Mat4:
        if worlds[index] is None:
            local = _local_matrix(translations[index], rotations[index], scales[index])
            parent = glb.parents[index]
            worlds[index] = local if parent is None else _matmul(resolve(int(parent)), local)
        return worlds[index]  # type: ignore[return-value]

    return tuple(resolve(index) for index in range(len(glb.nodes)))


def _world_path_matrices(
    glb: Any,
    path: Sequence[int],
    translations: Sequence[Vec3],
    rotations: Sequence[Quat],
    scales: Sequence[Vec3],
) -> tuple[Mat4, ...]:
    if not path:
        raise ContractError("cannot evaluate an empty ancestor path")
    worlds: list[Mat4] = []
    for index in path:
        local = _local_matrix(translations[index], rotations[index], scales[index])
        worlds.append(local if not worlds else _matmul(worlds[-1], local))
    return tuple(worlds)


def _world_position(matrix: Mat4) -> Vec3:
    return matrix[0][3], matrix[1][3], matrix[2][3]


def _ancestor_path(glb: Any, index: int) -> tuple[int, ...]:
    path: list[int] = []
    seen: set[int] = set()
    cursor: int | None = int(index)
    while cursor is not None:
        if cursor in seen:
            raise ContractError("node hierarchy contains a cycle")
        if cursor < 0 or cursor >= len(glb.nodes):
            raise ContractError("node hierarchy references an invalid parent")
        seen.add(cursor)
        path.append(cursor)
        parent = glb.parents[cursor]
        cursor = None if parent is None else int(parent)
    path.reverse()
    return tuple(path)


def _rotation_from_matrix(matrix: Mat4) -> Quat:
    basis = [[matrix[row][column] for column in range(3)] for row in range(3)]
    for column in range(3):
        length = math.sqrt(sum(basis[row][column] ** 2 for row in range(3)))
        if length <= 1.0e-15:
            raise ContractError("world rotation matrix has a zero scale axis")
        for row in range(3):
            basis[row][column] /= length
    trace = basis[0][0] + basis[1][1] + basis[2][2]
    if trace > 0.0:
        factor = math.sqrt(trace + 1.0) * 2.0
        result = (
            (basis[2][1] - basis[1][2]) / factor,
            (basis[0][2] - basis[2][0]) / factor,
            (basis[1][0] - basis[0][1]) / factor,
            0.25 * factor,
        )
    else:
        diagonal = (basis[0][0], basis[1][1], basis[2][2])
        largest = max(range(3), key=diagonal.__getitem__)
        if largest == 0:
            factor = math.sqrt(max(1.0e-15, 1.0 + basis[0][0] - basis[1][1] - basis[2][2])) * 2.0
            result = (
                0.25 * factor,
                (basis[0][1] + basis[1][0]) / factor,
                (basis[0][2] + basis[2][0]) / factor,
                (basis[2][1] - basis[1][2]) / factor,
            )
        elif largest == 1:
            factor = math.sqrt(max(1.0e-15, 1.0 + basis[1][1] - basis[0][0] - basis[2][2])) * 2.0
            result = (
                (basis[0][1] + basis[1][0]) / factor,
                0.25 * factor,
                (basis[1][2] + basis[2][1]) / factor,
                (basis[0][2] - basis[2][0]) / factor,
            )
        else:
            factor = math.sqrt(max(1.0e-15, 1.0 + basis[2][2] - basis[0][0] - basis[1][1])) * 2.0
            result = (
                (basis[0][2] + basis[2][0]) / factor,
                (basis[1][2] + basis[2][1]) / factor,
                0.25 * factor,
                (basis[1][0] - basis[0][1]) / factor,
            )
    return _q(result, label="world rotation")


def _clip_state(
    glb: Any,
    clip_name: str,
) -> tuple[dict[tuple[str, str], tuple[tuple[float, ...], ...]], tuple[float, ...]]:
    parsed, timeline = read_animation_tracks(glb, clip_name, require_common_timeline=True)
    tracks: dict[tuple[str, str], tuple[tuple[float, ...], ...]] = {}
    names: dict[str, int] = {}
    for (index, property_name), track in parsed.items():
        name = glb.nodes[index].get("name")
        if not isinstance(name, str) or (name in names and names[name] != index):
            raise ContractError(f"{clip_name}: animation targets require unique named nodes")
        names[name] = index
        tracks[(name, property_name)] = tuple(
            tuple(float(item) for item in row) for row in track.values
        )
    return tracks, tuple(float(value) for value in timeline)


def _pose(
    glb: Any,
    tracks: Mapping[tuple[str, str], Sequence[Sequence[float]]],
    sample: int,
) -> tuple[list[Vec3], list[Quat], list[Vec3]]:
    translations = [_vec3(value, label="rest translation") for value in glb.rest_translation]
    rotations = [_q(value, label="rest rotation") for value in glb.rest_rotation]
    scales = [_vec3(value, label="rest scale") for value in glb.rest_scale]
    for index, node in enumerate(glb.nodes):
        name = node.get("name", f"node_{index}")
        for property_name, target in (
            ("translation", translations),
            ("rotation", rotations),
            ("scale", scales),
        ):
            values = tracks.get((name, property_name))
            if values is None:
                continue
            if sample >= len(values):
                raise ContractError(f"animation sample exceeds {name}.{property_name} track")
            target[index] = (
                _vec3(values[sample], label=f"{name}.{property_name}")
                if property_name in {"translation", "scale"}
                else _q(values[sample], label=f"{name}.{property_name}")
            )
    return translations, rotations, scales


def _solve_linear(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    size = len(vector)
    if len(matrix) != size or any(len(row) != size for row in matrix):
        raise ContractError("rotation Jacobian normal matrix is not square")
    augmented = [
        list(row) + [float(vector[row_index])]
        for row_index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= 1.0e-14:
            raise ValidationFailure("rotation-first target Jacobian is singular")
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [item / divisor for item in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            augmented[row] = [
                augmented[row][index] - factor * augmented[column][index]
                for index in range(size + 1)
            ]
    return [augmented[row][-1] for row in range(size)]


def _clamp_rotation(value: Vec3, limit_radians: float) -> Vec3:
    length = _norm(value)
    if length <= limit_radians:
        return value
    return _scale(value, limit_radians / length)


def _interpolate_vec3(samples: Sequence[TargetSample], time_s: float, *, attribute: str) -> Vec3:
    if not samples:
        raise ContractError("cannot interpolate an empty target plan")
    value = _number(time_s, label="target interpolation time")
    if value <= samples[0].time_s:
        return _vec3(getattr(samples[0], attribute), label=f"target {attribute}")
    if value >= samples[-1].time_s:
        return _vec3(getattr(samples[-1], attribute), label=f"target {attribute}")
    for left, right in zip(samples, samples[1:]):
        if left.time_s <= value <= right.time_s:
            amount = (value - left.time_s) / (right.time_s - left.time_s)
            first = _vec3(getattr(left, attribute), label=f"target {attribute}")
            second = _vec3(getattr(right, attribute), label=f"target {attribute}")
            return _add(first, _scale(_sub(second, first), amount))
    raise ContractError("target interpolation failed")


@dataclass(frozen=True)
class FrameSolve:
    sample: int
    time_s: float
    side: str
    fraction: float
    target_m: Vec3
    baseline_m: Vec3
    residual_m: float
    joint_delta_degrees: tuple[float, ...]
    rotations: Mapping[str, Quat]
    # The four contact witnesses are retained individually.  ``target_patch``
    # and ``baseline_patch`` are both expressed in the post-body world basis
    # used by the DLS evaluation, so a balance response cannot be mistaken for
    # an unbound foot-origin target.
    witness_residuals_m: Mapping[str, float]
    target_patch_m: Mapping[str, Vec3]
    required_patch_m: Mapping[str, Vec3]
    baseline_patch_m: Mapping[str, Vec3]
    candidate_patch_m: Mapping[str, Vec3]
    witness_receipt: Mapping[str, Any]
    foot_heading_correction_degrees: float
    foot_local_delta_degrees: float
    foot_world_orientation_error_degrees: float
    heading_patch_receipt: Mapping[str, Any]
    contact_activation: float = 1.0


@dataclass(frozen=True)
class SkinnedCentroidTerm:
    """One exact joint contribution to a canonical skinned centroid."""

    joint_node: int
    coefficient: float
    inverse_bound_point_m: Vec3


@dataclass(frozen=True)
class SkinnedCentroidBinding:
    """Compressed exact linear skinning authority for one weighted mask."""

    terms: tuple[SkinnedCentroidTerm, ...]
    selected_vertex_count: int
    influence_count: int
    binding_sha256: str
    selected_vertex_terms: tuple[tuple[SkinnedCentroidTerm, ...], ...] = ()


def evaluate_skinned_centroid(
    binding: SkinnedCentroidBinding,
    joint_worlds: Sequence[Mat4],
    *,
    label: str = "skinned centroid",
) -> Vec3:
    """Evaluate a compressed centroid with every normalized skin influence."""

    if not isinstance(binding, SkinnedCentroidBinding) or not binding.terms:
        raise ContractError(f"{label} binding is empty or malformed")
    coefficient_sum = math.fsum(
        _number(term.coefficient, label=f"{label} coefficient")
        for term in binding.terms
    )
    if abs(coefficient_sum - 1.0) > 1.0e-9:
        raise ContractError(f"{label} coefficients do not sum to one")
    result = [0.0, 0.0, 0.0]
    for term in binding.terms:
        if term.joint_node < 0 or term.joint_node >= len(joint_worlds):
            raise ContractError(f"{label} references an invalid joint node")
        point = _mat_point(
            joint_worlds[term.joint_node],
            _vec3(term.inverse_bound_point_m, label=f"{label} inverse-bound point"),
        )
        for axis in range(3):
            result[axis] += term.coefficient * point[axis]
    return tuple(result)  # type: ignore[return-value]


def _evaluate_skinned_terms(
    terms: Sequence[SkinnedCentroidTerm],
    joint_worlds: Sequence[Mat4],
    *,
    label: str,
) -> Vec3:
    binding = SkinnedCentroidBinding(
        terms=tuple(terms),
        selected_vertex_count=1,
        influence_count=len(terms),
        binding_sha256=f"{label}:runtime",
    )
    return evaluate_skinned_centroid(binding, joint_worlds, label=label)


def _is_descendant_or_self(
    parents: Sequence[int | None],
    node: int,
    ancestor: int,
) -> bool:
    """Return whether ``node`` inherits the complete transform of ``ancestor``."""

    current: int | None = node
    visited: set[int] = set()
    while current is not None:
        if current == ancestor:
            return True
        if current in visited or current < 0 or current >= len(parents):
            raise ContractError("skin binding ancestry is cyclic or malformed")
        visited.add(current)
        current = parents[current]
    return False


@dataclass(frozen=True)
class ClipSolve:
    clip_name: str
    fraction: float
    tracks: Mapping[str, tuple[Quat, ...]]
    frame_solves: tuple[FrameSolve, ...]
    max_residual_m: float
    max_joint_delta_degrees: float
    max_joint_frame_change_degrees: float
    target_distance_m: float
    achieved_distance_m: float
    accepted: bool
    source_timeline: tuple[float, ...]
    body_translation_deltas: tuple[Vec3, ...]
    body_translation_node: str | None
    changed_body_nodes: tuple[str, ...]
    heading_correction_receipt: Mapping[str, Any] | None = None
    body_translation_cyclic: bool = True
    body_translation_deltas_by_node: Mapping[str, tuple[Vec3, ...]] | None = None

    def diagnostics(self) -> dict[str, Any]:
        witness_names = CONTACT_WITNESS_NAMES
        witness_maxima = {
            name: max(
                (
                    float(frame.witness_residuals_m.get(name, math.inf))
                    for frame in self.frame_solves
                    if frame.side in {"left", "right"}
                ),
                default=math.inf,
            )
            for name in witness_names
        }
        return {
            "clip": self.clip_name,
            "fraction": self.fraction,
            "accepted": self.accepted,
            "frame_count": len(self.source_timeline),
            "max_position_residual_m": self.max_residual_m,
            "max_joint_delta_degrees": self.max_joint_delta_degrees,
            "max_joint_frame_change_degrees": self.max_joint_frame_change_degrees,
            "target_distance_m": self.target_distance_m,
            "achieved_distance_m": self.achieved_distance_m,
            "joint_distribution": "pelvis-attached bounded hip-knee-ankle rotation-first solve",
            "gauge_mechanism": "none; no identity-rest leg-root controls or leg-chain translations",
            "protected_channels": "source foot translation and local metatarsal/toe articulation exact",
            "contact_patch": {
                "witness_order": list(witness_names),
                "target_basis": "pre_body_source_world_plus_declared_lane_offset",
                "required_basis": "pre_body_source_world_plus_declared_lane_offset",
                "max_residual_m_by_witness": witness_maxima,
                "per_frame_residuals_m": [
                    {
                        "sample": frame.sample,
                        "side": frame.side,
                        "residuals": {
                            name: float(frame.witness_residuals_m[name])
                            for name in witness_names
                        },
                    }
                    for frame in self.frame_solves
                ],
                "per_frame_receipts": [
                    {
                        "sample": frame.sample,
                        "side": frame.side,
                        **dict(frame.witness_receipt),
                    }
                    for frame in self.frame_solves
                ],
                "per_frame_candidate_patch_m": [
                    {
                        "sample": frame.sample,
                        "side": frame.side,
                        "candidate_patch_m": {
                            name: list(frame.candidate_patch_m[name])
                            for name in witness_names
                        },
                    }
                    for frame in self.frame_solves
                ],
                "per_frame_required_patch_m": [
                    {
                        "sample": frame.sample,
                        "side": frame.side,
                        "required_patch_m": {
                            name: list(frame.required_patch_m[name])
                            for name in witness_names
                        },
                    }
                    for frame in self.frame_solves
                ],
                "all_witnesses_individually_tolerance_gated": True,
                "rigid_yaw_pivot": "distal_toe_centroid",
            },
            "whole_foot_heading_correction": (
                {"status": "DISABLED_NOT_REQUESTED"}
                if self.heading_correction_receipt is None
                else dict(self.heading_correction_receipt)
            ),
            "per_frame_heading_patch_receipts": [
                {
                    "sample": frame.sample,
                    "side": frame.side,
                    **dict(frame.heading_patch_receipt),
                }
                for frame in self.frame_solves
            ],
            "support_balance_proxy": "phase-coupled pelvis-local shift with bounded body counter-response",
            "changed_body_nodes": list(self.changed_body_nodes),
        }


def _validate_inputs(
    glb: Any,
    clip_name: str,
    chains: Mapping[str, Sequence[str]],
    target_plans: Mapping[str, Sequence[TargetSample]],
    body_rotations: Mapping[str, Sequence[Quat]] | None,
    body_translation_deltas: Sequence[Vec3] | None,
    body_translation_node: str | None,
) -> tuple[
    dict[str, tuple[int, ...]],
    dict[str, tuple[int, ...]],
    dict[tuple[str, str], tuple[tuple[float, ...], ...]],
    tuple[float, ...],
]:
    tracks, timeline = _clip_state(glb, clip_name)
    resolved: dict[str, tuple[int, ...]] = {}
    paths: dict[str, tuple[int, ...]] = {}
    for side in ("left", "right"):
        chain = tuple(chains.get(side, ()))
        if len(chain) != 4 or len(set(chain)) != 4:
            raise ContractError(f"{clip_name}/{side}: chain must contain four unique nodes")
        if len(target_plans.get(side, ())) != len(timeline):
            raise ContractError(f"{clip_name}/{side}: target plan is not aligned to source timeline")
        try:
            indices = tuple(glb.name_to_node[name] for name in chain)
        except (KeyError, TypeError) as exc:
            raise ContractError(f"{clip_name}/{side}: chain references an unknown node") from exc
        if any((name, "rotation") not in tracks for name in chain):
            raise ContractError(f"{clip_name}/{side}: chain is missing a rotation channel")
        path = _ancestor_path(glb, indices[-1])
        if any(index not in path for index in indices):
            raise ContractError(f"{clip_name}/{side}: chain is not an ancestor chain")
        resolved[side] = indices
        paths[side] = path
    if body_rotations is not None:
        for name, rows in body_rotations.items():
            if name not in glb.name_to_node or (name, "rotation") not in tracks:
                raise ContractError(f"support balance body node is not an animated source node: {name}")
            if len(rows) != len(timeline):
                raise ContractError(f"support balance body node is not timeline aligned: {name}")
            if name in {item for chain in chains.values() for item in chain}:
                raise ContractError(f"support balance body node overlaps a leg chain: {name}")
    if body_translation_deltas is not None and len(body_translation_deltas) != len(timeline):
        raise ContractError("support balance pelvis translation deltas are not timeline aligned")
    if body_translation_deltas is not None:
        if not isinstance(body_translation_node, str) or not body_translation_node:
            raise ContractError("support balance translation deltas require a pelvis node")
        if body_translation_node not in glb.name_to_node or (body_translation_node, "translation") not in tracks:
            raise ContractError("support balance pelvis node has no source translation channel")
    return resolved, paths, tracks, timeline


def solve_clip(
    glb: Any,
    clip_name: str,
    *,
    chains: Mapping[str, Sequence[str]],
    target_plans: Mapping[str, Sequence[TargetSample]],
    lateral_axis: Sequence[float],
    fraction: float,
    joint_delta_limits_degrees: Sequence[float],
    damping: float,
    finite_difference_radians: float,
    iterations: int,
    position_tolerance_m: float,
    body_rotations: Mapping[str, Sequence[Quat]] | None = None,
    body_translation_deltas: Sequence[Vec3] | None = None,
    body_translation_node: str | None = None,
    max_joint_frame_change_degrees: float = 12.0,
    source_heading_degrees: Mapping[str, Sequence[float]] | None = None,
    heading_policy: Mapping[str, Any] | None = None,
    heading_up_axis: Sequence[float] = (0.0, 1.0, 0.0),
    skinned_sole_bindings: Mapping[str, SkinnedCentroidBinding] | None = None,
    contact_activation_by_side: Mapping[str, Sequence[float]] | None = None,
    body_translation_cyclic: bool = True,
    rotation_cyclic: bool = True,
    contact_target_offsets_by_side: Mapping[str, Sequence[Vec3]] | None = None,
    unlocked_target_offsets_by_side: Mapping[str, Sequence[Vec3]] | None = None,
    body_translation_deltas_by_node: Mapping[str, Sequence[Vec3]] | None = None,
    body_translation_cyclic_by_node: Mapping[str, bool] | None = None,
) -> ClipSolve:
    """Solve one source clip without adding or translating any leg parent."""

    fraction_value = _number(fraction, label="homotopy fraction")
    if not 0.0 <= fraction_value <= 1.0:
        raise ContractError("homotopy fraction must be between zero and one")
    axis = _unit(_vec3(lateral_axis, label="measured lateral axis"), label="measured lateral axis")
    limits = tuple(math.radians(_number(value, label="joint delta limit")) for value in joint_delta_limits_degrees)
    if len(limits) != 3 or any(value <= 0.0 for value in limits):
        raise ContractError("rotation-first solve requires three positive hip/knee/ankle limits")
    damping_value = _number(damping, label="rotation-first damping")
    epsilon = _number(finite_difference_radians, label="rotation-first finite difference")
    tolerance = _number(position_tolerance_m, label="rotation-first position tolerance")
    if damping_value <= 0.0 or epsilon <= 0.0 or iterations < 1 or tolerance <= 0.0:
        raise ContractError("rotation-first solver parameters are outside their domain")
    resolved, paths, source_tracks, timeline = _validate_inputs(
        glb,
        clip_name,
        chains,
        target_plans,
        body_rotations,
        body_translation_deltas,
        body_translation_node,
    )
    if body_translation_deltas_by_node is not None and body_translation_deltas is not None:
        raise ContractError(
            "provide either the legacy body translation delta or the per-node mapping"
        )
    translation_rows_by_node: dict[str, tuple[Vec3, ...]] = {}
    if body_translation_deltas_by_node is not None:
        chain_names_for_translation = {
            name for chain in chains.values() for name in chain
        }
        for name, raw_rows in body_translation_deltas_by_node.items():
            if (
                name not in glb.name_to_node
                or (name, "translation") not in source_tracks
                or len(raw_rows) != len(timeline)
            ):
                raise ContractError(
                    f"{clip_name}: body translation mapping is invalid for {name}"
                )
            if name in chain_names_for_translation:
                raise ContractError(
                    f"{clip_name}: body translation node overlaps a leg chain: {name}"
                )
            translation_rows_by_node[name] = tuple(
                _vec3(row, label=f"{clip_name}/{name} translation delta[{sample}]")
                for sample, row in enumerate(raw_rows)
            )
    if body_translation_cyclic_by_node is not None and set(
        body_translation_cyclic_by_node
    ) != set(translation_rows_by_node):
        raise ContractError(
            "body translation cyclic policy must exactly match translated nodes"
        )
    if body_translation_cyclic_by_node is not None and any(
        not isinstance(value, bool)
        for value in body_translation_cyclic_by_node.values()
    ):
        raise ContractError("body translation cyclic policies must be booleans")
    translation_cyclic_by_node = {
        name: (
            True
            if body_translation_cyclic_by_node is None
            else bool(body_translation_cyclic_by_node.get(name, True))
        )
        for name in translation_rows_by_node
    }
    if contact_activation_by_side is not None:
        for side in ("left", "right"):
            if len(contact_activation_by_side.get(side, ())) != len(timeline):
                raise ContractError(
                    f"{clip_name}/{side}: contact activation is not aligned to source timeline"
                )
    contact_activation = {
        side: tuple(
            1.0
            if contact_activation_by_side is None
            else _number(
                contact_activation_by_side[side][sample],
                label=f"{clip_name}/{side} contact activation[{sample}]",
            )
            for sample in range(len(timeline))
        )
        for side in ("left", "right")
    }
    for side, rows in contact_activation.items():
        if any(value < 0.0 or value > 1.0 for value in rows):
            raise ContractError(
                f"{clip_name}/{side}: contact activation must remain between zero and one"
            )
    target_offsets: dict[str, tuple[Vec3, ...]] = {}
    unlocked_offsets: dict[str, tuple[Vec3, ...]] = {}
    for supplied, destination, label in (
        (contact_target_offsets_by_side, target_offsets, "contact target offset"),
        (unlocked_target_offsets_by_side, unlocked_offsets, "unlocked target offset"),
    ):
        for side in ("left", "right"):
            raw_rows = (
                [(0.0, 0.0, 0.0)] * len(timeline)
                if supplied is None
                else supplied.get(side, ())
            )
            if len(raw_rows) != len(timeline):
                raise ContractError(
                    f"{clip_name}/{side}: {label} is not aligned to source timeline"
                )
            destination[side] = tuple(
                _vec3(row, label=f"{clip_name}/{side} {label}[{sample}]")
                for sample, row in enumerate(raw_rows)
            )
    body_rows = {} if body_rotations is None else {
        name: tuple(_q(row, label=f"{clip_name}/{name} body rotation") for row in rows)
        for name, rows in body_rotations.items()
    }
    translation_rows = (
        tuple()
        if body_translation_deltas is None
        else tuple(_vec3(row, label=f"{clip_name} pelvis translation delta") for row in body_translation_deltas)
    )
    if (source_heading_degrees is None) != (heading_policy is None):
        raise ContractError(
            "whole-foot heading samples and policy must be supplied together"
        )
    heading_corrections: dict[str, float]
    heading_receipt: Mapping[str, Any] | None
    if source_heading_degrees is None or heading_policy is None:
        heading_corrections = {"left": 0.0, "right": 0.0}
        heading_receipt = None
    else:
        for side in ("left", "right"):
            values = source_heading_degrees.get(side)
            if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or len(values) != len(timeline):
                raise ContractError(
                    f"{clip_name}/{side}: heading samples are not aligned to source timeline"
                )
        heading_corrections, heading_receipt = derive_constant_cyclic_heading_corrections(
            source_heading_degrees,
            heading_policy,
        )
    heading_axis = _unit(
        _vec3(heading_up_axis, label="whole-foot heading up axis"),
        label="whole-foot heading up axis",
    )
    if skinned_sole_bindings is not None:
        if set(skinned_sole_bindings) != {"left", "right"}:
            raise ContractError("skinned sole bindings must provide left and right")
        for side, binding in skinned_sole_bindings.items():
            if not isinstance(binding, SkinnedCentroidBinding) or not binding.terms:
                raise ContractError(f"{clip_name}/{side}: skinned sole binding is malformed")
    sole_boundary_by_side: dict[str, int | None] = {"left": None, "right": None}
    if skinned_sole_bindings is not None:
        for side in ("left", "right"):
            foot_index = resolved[side][-1]
            articulated = resolved[side][:-1]
            external_influences = {
                term.joint_node
                for term in skinned_sole_bindings[side].terms
                if not _is_descendant_or_self(
                    glb.parents,
                    term.joint_node,
                    foot_index,
                )
            }
            # When the only external skin influence is the articulated joint
            # directly above the foot, preserving that joint under the same
            # declared lane+yaw transform makes every sole-mask influence
            # coherent: the foot and all descendants inherit the foot world
            # transform, and the boundary receives that transform explicitly.
            # This is derived solely from binding/topology; no rig names are
            # embedded. Other topologies retain the exact centroid evaluator.
            if external_influences == {articulated[-1]}:
                sole_boundary_by_side[side] = articulated[-1]
    chain_names = {name for chain in chains.values() for name in chain}
    output_names = set(chain_names) | set(body_rows)
    outputs: dict[str, list[Quat]] = {
        name: [_q(row, label=f"{clip_name}/{name}.rotation") for row in source_tracks[(name, "rotation")]]
        for name in output_names
    }
    frame_solves: list[FrameSolve] = []
    max_residual = 0.0
    max_joint_delta = 0.0
    max_frame_change = 0.0
    target_distance = 0.0
    achieved_distance = 0.0
    accepted = True
    previous_joint: dict[str, tuple[float, ...]] = {}
    previous_variable: dict[str, list[float]] = {}

    for sample, time_s in enumerate(timeline):
        # Keep an unmodified source pose so the measured patch witnesses can
        # be converted to rigid foot-local offsets before the support-balance
        # proxy is applied.  Otherwise a body response would be mistaken for
        # contact drift and the target would be anchored to the wrong frame.
        translations, rotations, scales = _pose(glb, source_tracks, sample)
        source_worlds = _world_matrices(glb, translations, rotations, scales)
        if body_translation_deltas is not None:
            # The profile resolves this node through the body adapter and
            # passes the local delta.  It is intentionally not a leg-root
            # translation.
            if not isinstance(body_translation_node, str) or body_translation_node not in glb.name_to_node:
                raise ContractError("support balance pelvis translation node is not bound")
            translations[glb.name_to_node[body_translation_node]] = _add(
                translations[glb.name_to_node[body_translation_node]], translation_rows[sample]
            )
        for name, rows in translation_rows_by_node.items():
            translations[glb.name_to_node[name]] = _add(
                translations[glb.name_to_node[name]], rows[sample]
            )
        for name, rows in body_rows.items():
            index = glb.name_to_node[name]
            rotations[index] = rows[sample]
            outputs[name][sample] = rotations[index]
        for side in ("left", "right"):
            indices = resolved[side]
            chain = tuple(chains[side])
            path = paths[side]
            foot_index = indices[-1]
            articulated = indices[:-1]
            sole_boundary_index = sole_boundary_by_side[side]
            variable_articulated = tuple(
                index for index in articulated if index != sole_boundary_index
            )
            variable_limits = tuple(
                limit
                for index, limit in zip(articulated, limits)
                if index != sole_boundary_index
            )
            sole_binding = (
                None
                if skinned_sole_bindings is None
                else skinned_sole_bindings[side]
            )
            plan = target_plans[side]
            if sample >= len(plan):
                raise ContractError(f"{clip_name}/{side}: target plan exceeds source timeline")
            target_sample = plan[sample]
            activation = contact_activation[side][sample]
            contact_target_offset = target_offsets[side][sample]
            unlocked_target_offset = unlocked_offsets[side][sample]
            patch = _contact_patch_points(
                target_sample,
                label=f"{clip_name}/{side}/sample[{sample}]",
            )
            patch_local = tuple(
                (name, _inverse_point(source_worlds[foot_index], point))
                for name, point in patch
            )
            solve_reference = (
                (
                    "foot_reference",
                    _vec3(
                        target_sample.foot_root_m,
                        label=f"{clip_name}/{side}/sample[{sample}].foot_reference",
                    ),
                ),
                (
                    "sole",
                    _vec3(
                        target_sample.sole_centroid_m,
                        label=f"{clip_name}/{side}/sample[{sample}].sole_reference",
                    ),
                ),
                (
                    "toe",
                    _vec3(
                        target_sample.toe_centroid_m,
                        label=f"{clip_name}/{side}/sample[{sample}].toe_reference",
                    ),
                ),
            )
            solve_reference_local = tuple(
                (name, _inverse_point(source_worlds[foot_index], point))
                for name, point in solve_reference
            )
            reference_local_by_name = dict(solve_reference_local)
            if sole_binding is not None:
                source_skinned_sole = evaluate_skinned_centroid(
                    sole_binding,
                    source_worlds,
                    label=f"{clip_name}/{side}/sample[{sample}] source sole",
                )
                declared_source_sole = _vec3(
                    target_sample.sole_centroid_m,
                    label=f"{clip_name}/{side}/sample[{sample}] declared source sole",
                )
                # The analyzer samples uniform time while this resolver uses
                # the source channel keys. Their floats can differ by a few
                # microseconds, so require agreement inside the unchanged
                # mechanical position tolerance rather than bit identity.
                if _norm(_sub(source_skinned_sole, declared_source_sole)) > tolerance:
                    raise ContractError(
                        f"{clip_name}/{side}/sample[{sample}]: skinned sole binding "
                        "does not reproduce the canonical source analyzer"
                    )
            source_floor_points: tuple[Vec3, ...] = ()
            if sole_binding is not None and sole_binding.selected_vertex_terms:
                source_floor_points = tuple(
                    _evaluate_skinned_terms(
                        terms,
                        source_worlds,
                        label=(
                            f"{clip_name}/{side}/sample[{sample}] "
                            f"source sole vertex[{vertex_index}]"
                        ),
                    )
                    for vertex_index, terms in enumerate(
                        sole_binding.selected_vertex_terms
                    )
                )
            correction = _number(target_sample.correction_lateral_m, label=f"{clip_name}/{side} correction") * fraction_value
            heading_correction = heading_corrections[side] * fraction_value
            # The analyzer defines signed heading with cross(footAxis,
            # travel), so positive physical yaw about +up subtracts from the
            # reported metric.  Invert the physical sign to realize the
            # receipt's source_heading + metric_correction prediction.
            heading_rotation = _qrotvec(
                _scale(heading_axis, math.radians(-heading_correction))
            )
            variable = list(
                previous_variable.get(
                    side,
                    [0.0] * (len(variable_articulated) * 3),
                )
            )

            # Every witness first receives the same measured lateral lane
            # correction and then rotates as one rigid patch around the
            # translated distal-toe pivot.  The proximal DLS solve targets the
            # resulting foot-root position while retaining an untranslated
            # source-shaped reference patch.  The parent-foot local rotation
            # is solved only after that proximal placement, which preserves
            # the pivot without adding a foot or leg-parent translation.
            # The required patch is locked against the immutable pre-body
            # source pose.  The candidate is evaluated after the pelvis/body
            # response, so the leg solve must compensate that motion instead
            # of carrying a planted foot along with the pelvis.
            baseline_patch = tuple(
                _mat_point(source_worlds[foot_index], point)
                for _, point in patch_local
            )
            witness_names = tuple(name for name, _ in patch)
            baseline_patch_by_name = {
                name: point for name, point in zip(witness_names, baseline_patch)
            }
            baseline_pivot = baseline_patch_by_name["toe"]
            target_pivot = _add(
                _add(baseline_pivot, contact_target_offset),
                _scale(axis, correction),
            )
            target_patch = tuple(
                _rotate_about_pivot(
                    _add(
                        _add(point, contact_target_offset),
                        _scale(axis, correction),
                    ),
                    target_pivot,
                    heading_rotation,
                )
                for point in baseline_patch
            )
            baseline_foot_reference = baseline_patch_by_name["foot_reference"]
            target_foot_reference = _rotate_about_pivot(
                _add(
                    _add(baseline_foot_reference, contact_target_offset),
                    _scale(axis, correction),
                ),
                target_pivot,
                heading_rotation,
            )
            baseline_world_rotation = _rotation_from_matrix(
                source_worlds[foot_index]
            )
            target_world_rotation = _qmul(
                heading_rotation,
                baseline_world_rotation,
            )
            post_body_worlds = _world_matrices(
                glb,
                translations,
                rotations,
                scales,
            )
            post_body_patch = tuple(
                _mat_point(post_body_worlds[foot_index], point)
                for _, point in patch_local
            )
            target_patch = tuple(
                _add(
                    _add(
                        current,
                        _scale(_sub(required, current), activation),
                    ),
                    _scale(unlocked_target_offset, 1.0 - activation),
                )
                for current, required in zip(post_body_patch, target_patch)
            )
            post_body_foot_reference = _mat_point(
                post_body_worlds[foot_index],
                reference_local_by_name["foot_reference"],
            )
            target_foot_reference = _add(
                _add(
                    post_body_foot_reference,
                    _scale(
                        _sub(target_foot_reference, post_body_foot_reference),
                        activation,
                    ),
                ),
                _scale(unlocked_target_offset, 1.0 - activation),
            )
            post_body_world_rotation = _rotation_from_matrix(
                post_body_worlds[foot_index]
            )
            world_rotation_delta = _qmul(
                target_world_rotation,
                _qinv(post_body_world_rotation),
            )
            target_world_rotation = _qmul(
                _qrotvec(
                    _scale(_q_to_rotvec(world_rotation_delta), activation)
                ),
                post_body_world_rotation,
            )
            target_boundary_position: Vec3 | None = None
            target_boundary_world_rotation: Quat | None = None
            if sole_boundary_index is not None:
                source_boundary_position = _world_position(
                    source_worlds[sole_boundary_index]
                )
                target_boundary_position = _rotate_about_pivot(
                    _add(
                        _add(source_boundary_position, contact_target_offset),
                        _scale(axis, correction),
                    ),
                    target_pivot,
                    heading_rotation,
                )
                target_boundary_world_rotation = _qmul(
                    heading_rotation,
                    _rotation_from_matrix(source_worlds[sole_boundary_index]),
                )
                post_body_boundary_position = _world_position(
                    post_body_worlds[sole_boundary_index]
                )
                target_boundary_position = _add(
                    _add(
                        post_body_boundary_position,
                        _scale(
                            _sub(target_boundary_position, post_body_boundary_position),
                            activation,
                        ),
                    ),
                    _scale(unlocked_target_offset, 1.0 - activation),
                )
                post_body_boundary_rotation = _rotation_from_matrix(
                    post_body_worlds[sole_boundary_index]
                )
                boundary_rotation_delta = _qmul(
                    target_boundary_world_rotation,
                    _qinv(post_body_boundary_rotation),
                )
                target_boundary_world_rotation = _qmul(
                    _qrotvec(
                        _scale(_q_to_rotvec(boundary_rotation_delta), activation)
                    ),
                    post_body_boundary_rotation,
                )
            target_reference = (
                target_foot_reference,
                target_patch[witness_names.index("sole")],
                target_patch[witness_names.index("toe")],
            )
            boundary_reference_index: int | None = None
            if target_boundary_position is not None:
                target_reference = (*target_reference, target_boundary_position)
                boundary_reference_index = len(target_reference) - 1
            target_floor_minimum_y = (
                None
                if not source_floor_points
                else min(
                    _rotate_about_pivot(
                        _add(point, _scale(axis, correction)),
                        target_pivot,
                        heading_rotation,
                    )[1]
                    for point in source_floor_points
                )
            )
            if target_floor_minimum_y is not None:
                target_floor_minimum_y += contact_target_offset[1]
            floor_reference_index: int | None = None
            if target_floor_minimum_y is not None:
                post_body_floor_minimum_y = min(
                    _evaluate_skinned_terms(
                        terms,
                        post_body_worlds,
                        label=(
                            f"{clip_name}/{side}/sample[{sample}] "
                            f"post-body sole vertex[{vertex_index}]"
                        ),
                    )[1]
                    for vertex_index, terms in enumerate(
                        sole_binding.selected_vertex_terms  # type: ignore[union-attr]
                    )
                )
                target_floor_minimum_y = post_body_floor_minimum_y + activation * (
                    target_floor_minimum_y - post_body_floor_minimum_y
                ) + (1.0 - activation) * unlocked_target_offset[1]
                # The dense analyzer's floor channel is the minimum height of
                # the complete canonical skinned sole mask.  Encode that one
                # scalar as a Y-only pseudo-witness: constraining the full XYZ
                # location of whichever vertex happened to be lowest in the
                # source overconstrains the contact solve and is not equivalent
                # when the minimum vertex changes after articulation.
                target_reference = (
                    *target_reference,
                    (0.0, target_floor_minimum_y, 0.0),
                )
                floor_reference_index = len(target_reference) - 1

            def evaluate_final_reference(
                values: Sequence[float],
            ) -> tuple[tuple[Vec3, ...], list[Quat], tuple[Mat4, ...], Quat]:
                candidate_rotations = list(rotations)
                for offset, index in enumerate(variable_articulated):
                    delta = tuple(
                        values[offset * 3 + axis_index]
                        for axis_index in range(3)
                    )
                    candidate_rotations[index] = _qmul(
                        candidate_rotations[index],
                        _qrotvec(delta),
                    )
                if sole_boundary_index is not None:
                    if target_boundary_world_rotation is None:
                        raise ContractError("sole boundary rotation target is missing")
                    boundary_parent = glb.parents[sole_boundary_index]
                    if boundary_parent is None:
                        raise ContractError("sole boundary influence cannot be a scene root")
                    preliminary_worlds = _world_matrices(
                        glb,
                        translations,
                        candidate_rotations,
                        scales,
                    )
                    boundary_parent_world_rotation = _rotation_from_matrix(
                        preliminary_worlds[int(boundary_parent)]
                    )
                    candidate_rotations[sole_boundary_index] = _qmul(
                        _qinv(boundary_parent_world_rotation),
                        target_boundary_world_rotation,
                    )
                proximal_worlds = _world_path_matrices(
                    glb,
                    path,
                    translations,
                    candidate_rotations,
                    scales,
                )
                parent_index = glb.parents[foot_index]
                if parent_index is None or int(parent_index) not in path:
                    raise ContractError("declared foot must have an in-path parent")
                parent_world_rotation = _rotation_from_matrix(
                    proximal_worlds[path.index(int(parent_index))]
                )
                foot_rotation = _qmul(
                    _qinv(parent_world_rotation),
                    target_world_rotation,
                )
                candidate_rotations[foot_index] = foot_rotation
                worlds = _world_matrices(
                    glb,
                    translations,
                    candidate_rotations,
                    scales,
                )
                foot_world = worlds[foot_index]
                sole = (
                    _mat_point(foot_world, reference_local_by_name["sole"])
                    if sole_binding is None
                    else evaluate_skinned_centroid(
                        sole_binding,
                        worlds,
                        label=f"{clip_name}/{side}/sample[{sample}] candidate sole",
                    )
                )
                floor_minimum_y = (
                    None
                    if sole_binding is None
                    or not sole_binding.selected_vertex_terms
                    else min(
                        _evaluate_skinned_terms(
                            terms,
                            worlds,
                            label=(
                                f"{clip_name}/{side}/sample[{sample}] "
                                f"candidate sole vertex[{vertex_index}]"
                            ),
                        )[1]
                        for vertex_index, terms in enumerate(
                            sole_binding.selected_vertex_terms
                        )
                    )
                )
                reference = (
                    _mat_point(foot_world, reference_local_by_name["foot_reference"]),
                    sole,
                    _mat_point(foot_world, reference_local_by_name["toe"]),
                )
                if sole_boundary_index is not None:
                    reference = (
                        *reference,
                        _world_position(worlds[sole_boundary_index]),
                    )
                if floor_minimum_y is not None:
                    reference = (*reference, (0.0, floor_minimum_y, 0.0))
                return (
                    reference,
                    candidate_rotations,
                    worlds,
                    foot_rotation,
                )

            def flattened_residual(
                current: Sequence[Vec3],
                target: Sequence[Vec3],
            ) -> tuple[float, ...]:
                return tuple(
                    component
                    for current_point, target_point in zip(current, target)
                    for component in _sub(current_point, target_point)
                )

            def max_point_residual(
                current: Sequence[Vec3],
                target: Sequence[Vec3],
            ) -> float:
                return max(
                    (_norm(_sub(current_point, target_point)) for current_point, target_point in zip(current, target)),
                    default=math.inf,
                )

            for _ in range(int(iterations)):
                current, _, _, _ = evaluate_final_reference(variable)
                residual = flattened_residual(current, target_reference)
                if max_point_residual(current, target_reference) <= tolerance:
                    break
                columns = len(variable)
                jacobian = [[0.0] * columns for _ in range(len(residual))]
                for column in range(columns):
                    shifted = list(variable)
                    shifted[column] += epsilon
                    shifted_position, _, _, _ = evaluate_final_reference(shifted)
                    shifted_residual = flattened_residual(shifted_position, target_reference)
                    difference = tuple(
                        (shifted_value - current_value) / epsilon
                        for shifted_value, current_value in zip(shifted_residual, residual)
                    )
                    for row in range(len(residual)):
                        jacobian[row][column] = difference[row]
                normal = [
                    [
                        sum(jacobian[row][left] * jacobian[row][right] for row in range(len(residual)))
                        + (damping_value if left == right else 0.0)
                        for right in range(columns)
                    ]
                    for left in range(columns)
                ]
                gradient = [
                    -sum(jacobian[row][column] * residual[row] for row in range(len(residual)))
                    for column in range(columns)
                ]
                try:
                    step = _solve_linear(normal, gradient)
                except ValidationFailure:
                    accepted = False
                    break
                for offset in range(len(variable_articulated)):
                    section = tuple(step[offset * 3 + axis_index] for axis_index in range(3))  # type: ignore[assignment]
                    clamped = _clamp_rotation(section, variable_limits[offset])
                    for axis_index in range(3):
                        variable[offset * 3 + axis_index] += clamped[axis_index]
                    bounded = _clamp_rotation(
                        tuple(variable[offset * 3 + axis_index] for axis_index in range(3)),
                        variable_limits[offset],
                    )
                    for axis_index in range(3):
                        variable[offset * 3 + axis_index] = bounded[axis_index]
            current_reference, candidate_rotations, adjusted_worlds, foot_rotation = (
                evaluate_final_reference(variable)
            )
            foot_local_delta = math.degrees(
                _norm(
                    _q_to_rotvec(
                        _qmul(_qinv(rotations[foot_index]), foot_rotation)
                    )
                )
            )
            actual_world_rotation = _rotation_from_matrix(adjusted_worlds[foot_index])
            orientation_error = _q_angle_degrees(
                target_world_rotation,
                actual_world_rotation,
            )
            current_patch = tuple(
                _mat_point(adjusted_worlds[foot_index], point)
                for _, point in patch_local
            )
            candidate_patch_m = {
                name: current
                for name, current in zip(witness_names, current_patch)
            }
            candidate_patch_m["sole"] = current_reference[1]
            required_patch_m = {
                name: target
                for name, target in zip(witness_names, target_patch)
            }
            witness_receipt = _witness_residual_receipt(
                candidate_patch_m,
                required_patch_m,
                tolerance_m=tolerance,
                label=f"{clip_name}/{side}/sample[{sample}]",
            )
            witness_residuals = {
                name: float(witness_receipt["residual_m_by_witness"][name])
                for name in CONTACT_WITNESS_NAMES
            }
            floor_minimum_y_residual_m = (
                0.0
                if target_floor_minimum_y is None or floor_reference_index is None
                else abs(
                    current_reference[floor_reference_index][1]
                    - target_floor_minimum_y
                )
            )
            boundary_position_residual_m = (
                0.0
                if target_boundary_position is None
                or boundary_reference_index is None
                else _norm(
                    _sub(
                        current_reference[boundary_reference_index],
                        target_boundary_position,
                    )
                )
            )
            residual_m = max(
                max(witness_residuals.values(), default=math.inf),
                floor_minimum_y_residual_m,
                boundary_position_residual_m,
            )
            baseline_position = baseline_patch[0]
            target_position = target_patch[0]
            joint_deltas = tuple(
                math.degrees(
                    _norm(
                        tuple(
                            variable[
                                variable_articulated.index(index) * 3
                                + axis_index
                            ]
                            for axis_index in range(3)
                        )
                        if index in variable_articulated
                        else _q_to_rotvec(
                            _qmul(
                                _qinv(rotations[index]),
                                candidate_rotations[index],
                            )
                        )
                    )
                )
                for index in articulated
            )
            if any(
                delta > math.degrees(limit) + 1.0e-9
                for delta, limit in zip(joint_deltas, limits)
            ):
                accepted = False
            previous = previous_joint.get(side)
            magnitude_change = 0.0 if previous is None else max(
                abs(current_delta - old_delta)
                for current_delta, old_delta in zip(joint_deltas, previous)
            )
            previous_joint[side] = joint_deltas
            previous_variable[side] = list(variable)
            if magnitude_change > _number(max_joint_frame_change_degrees, label="max joint frame change") + 1.0e-9:
                accepted = False
            # Do not reduce this to a single foot-origin/max residual check:
            # every named witness is part of the rigid contact contract.  A
            # solution that happens to satisfy the anchor while missing the
            # sole or distal toe is rejected independently.
            if witness_receipt["status"] != "PASS":
                accepted = False
            if floor_minimum_y_residual_m > tolerance + 1.0e-12:
                accepted = False
            if boundary_position_residual_m > tolerance + 1.0e-12:
                accepted = False
            if orientation_error > WORLD_ROTATION_NUMERICAL_TOLERANCE_DEGREES:
                accepted = False
            target_distance += abs(correction)
            achieved_distance += max(0.0, abs(correction) - residual_m)
            for name, index in zip(chain, indices):
                outputs[name][sample] = (
                    foot_rotation if index == foot_index else candidate_rotations[index]
                )
            heading_patch_receipt = {
                "status": "PASS"
                if witness_receipt["status"] == "PASS"
                and floor_minimum_y_residual_m <= tolerance + 1.0e-12
                and boundary_position_residual_m <= tolerance + 1.0e-12
                and orientation_error <= WORLD_ROTATION_NUMERICAL_TOLERANCE_DEGREES
                else "FAIL",
                "pivot_witness": "distal_toe_centroid",
                "pivot_source_m": list(baseline_pivot),
                "pivot_target_m": list(target_pivot),
                "lateral_correction_m": correction,
                "heading_correction_degrees": heading_correction,
                "contact_activation": activation,
                "activation_basis": "profile_derived_contact_window",
                "contact_target_offset_m": list(contact_target_offset),
                "unlocked_target_offset_m": list(unlocked_target_offset),
                "foot_reference_target_m": list(target_foot_reference),
                "foot_translation_channel_modified": False,
                "toe_metatarsal_local_trs_modified": False,
                "rigid_witnesses": list(CONTACT_WITNESS_NAMES),
                "sole_witness_authority": (
                    "rigid_foot_proxy"
                    if sole_binding is None
                    else "canonical_mixed_weight_skinned_centroid"
                ),
                "sole_binding_sha256": (
                    None if sole_binding is None else sole_binding.binding_sha256
                ),
                "sole_external_influence_boundary_node": sole_boundary_index,
                "sole_external_influence_boundary_preserved": (
                    sole_boundary_index is not None
                ),
                "sole_external_influence_boundary_position_residual_m": (
                    boundary_position_residual_m
                ),
                "sole_floor_witness": "canonical_skinned_mask_minimum_y",
                "sole_floor_minimum_y_residual_m": floor_minimum_y_residual_m,
                "sole_floor_minimum_y_tolerance_m": tolerance,
                "world_orientation_error_degrees": orientation_error,
                "world_orientation_numerical_tolerance_degrees": WORLD_ROTATION_NUMERICAL_TOLERANCE_DEGREES,
            }
            frame_solves.append(
                FrameSolve(
                    sample=sample,
                    time_s=time_s,
                    side=side,
                    fraction=fraction_value,
                    target_m=target_position,
                    baseline_m=baseline_position,
                    residual_m=residual_m,
                    joint_delta_degrees=joint_deltas,
                    rotations={
                        name: outputs[name][sample]
                        for name in chain
                    },
                    witness_residuals_m=dict(witness_residuals),
                    target_patch_m={
                        name: target
                        for name, target in zip(witness_names, target_patch)
                    },
                    required_patch_m=dict(required_patch_m),
                    baseline_patch_m={
                        name: baseline
                        for name, baseline in zip(witness_names, baseline_patch)
                    },
                    candidate_patch_m=dict(candidate_patch_m),
                    witness_receipt=dict(witness_receipt),
                    foot_heading_correction_degrees=heading_correction,
                    foot_local_delta_degrees=foot_local_delta,
                    foot_world_orientation_error_degrees=orientation_error,
                    heading_patch_receipt=heading_patch_receipt,
                    contact_activation=activation,
                )
            )
            max_residual = max(max_residual, residual_m)
            max_joint_delta = max(max_joint_delta, max(joint_deltas))

    # Close the cyclic source's duplicated terminal key without changing its
    # timing.  Body proxy rows are periodic by construction; the terminal
    # rotation key follows the first exactly to avoid a seam quaternion.
    if rotation_cyclic:
        for rows in outputs.values():
            if _q_angle_degrees(rows[-1], rows[0]) <= WORLD_ROTATION_NUMERICAL_TOLERANCE_DEGREES:
                rows[-1] = rows[0]
            else:
                accepted = False
    if translation_rows and body_translation_cyclic:
        translation_list = list(translation_rows)
        translation_list[-1] = translation_list[0]
        translation_rows = tuple(translation_list)
    for name, rows in tuple(translation_rows_by_node.items()):
        if translation_cyclic_by_node[name]:
            closed = list(rows)
            closed[-1] = closed[0]
            translation_rows_by_node[name] = tuple(closed)
    # Gate the temporal rate introduced by this correction relative to the
    # immutable source. Applying the limit to absolute output rotations would
    # reject an identity correction whenever V8.2 itself has a larger step.
    # Quaternion-space deltas still catch equal-magnitude direction flips.
    actual_frame_limit = _number(max_joint_frame_change_degrees, label="max joint frame change")
    for name, rows in outputs.items():
        source_rows = source_tracks.get((name, "rotation"))
        if source_rows is None:
            raise ContractError(f"{clip_name}/{name}: correction rate has no source rotation track")
        max_frame_change = max(
            max_frame_change,
            _max_correction_frame_change_degrees(
                source_rows,
                rows,
                label=f"{clip_name}/{name}",
            ),
        )
    if max_frame_change > actual_frame_limit + 1.0e-9:
        accepted = False
    return ClipSolve(
        clip_name=clip_name,
        fraction=fraction_value,
        tracks={name: tuple(rows) for name, rows in outputs.items()},
        frame_solves=tuple(frame_solves),
        max_residual_m=max_residual,
        max_joint_delta_degrees=max_joint_delta,
        max_joint_frame_change_degrees=max_frame_change,
        target_distance_m=target_distance,
        achieved_distance_m=achieved_distance,
        accepted=accepted,
        source_timeline=tuple(timeline),
        body_translation_deltas=tuple(translation_rows),
        body_translation_node=body_translation_node,
        changed_body_nodes=tuple(
            sorted(
                set(body_rows)
                | set(translation_rows_by_node)
                | ({body_translation_node} if body_translation_deltas is not None else set())
            )
        ),
        heading_correction_receipt=heading_receipt,
        body_translation_cyclic=body_translation_cyclic,
        body_translation_deltas_by_node=dict(translation_rows_by_node),
    )


def patch_clip_bytes(glb: Any, solve: ClipSolve) -> bytes:
    """Patch only declared rotation channels and the optional pelvis translation."""

    raw = bytearray(glb.raw)
    rotation_accessors = glb.animation_accessors(solve.clip_name, "rotation")
    for node, rows in solve.tracks.items():
        accessor_index = rotation_accessors.get(node)
        if accessor_index is None:
            raise ContractError(f"{solve.clip_name}: solved node has no rotation accessor: {node}")
        item, _view, width, component_size, code = glb.accessor_layout(accessor_index)
        if item.get("componentType") != 5126 or item.get("type") != "VEC4" or width != 4 or component_size != 4 or code != "f":
            raise ContractError(f"{solve.clip_name}/{node}: rotation accessor is not packed float VEC4")
        offset, count, stride = glb.accessor_region(accessor_index)
        if count != len(rows) or stride != 16:
            raise ContractError(f"{solve.clip_name}/{node}: rotation accessor shape is not canonical")
        for row, quaternion in enumerate(rows):
            struct.pack_into("<ffff", raw, int(glb.bin_start) + offset + row * stride, *quaternion)
    if solve.body_translation_deltas:
        node_name = solve.body_translation_node
        if not isinstance(node_name, str):
            raise ContractError("support balance translation node is not bound for GLB patch")
        translation_accessors = glb.animation_accessors(solve.clip_name, "translation")
        accessor_index = translation_accessors.get(node_name)
        if accessor_index is None:
            raise ContractError(f"{solve.clip_name}: pelvis has no translation accessor: {node_name}")
        source_values = glb.accessor_values(accessor_index)
        item, _view, width, component_size, code = glb.accessor_layout(accessor_index)
        if item.get("componentType") != 5126 or item.get("type") != "VEC3" or width != 3 or component_size != 4 or code != "f":
            raise ContractError(f"{solve.clip_name}/{node_name}: translation accessor is not packed float VEC3")
        offset, count, stride = glb.accessor_region(accessor_index)
        if count != len(solve.body_translation_deltas) or stride != 12:
            raise ContractError(f"{solve.clip_name}/{node_name}: translation accessor shape is not canonical")
        for row, delta in enumerate(solve.body_translation_deltas):
            value = _add(_vec3(source_values[row], label="source pelvis translation"), delta)
            struct.pack_into("<fff", raw, int(glb.bin_start) + offset + row * stride, *value)
    for node_name, rows in (solve.body_translation_deltas_by_node or {}).items():
        translation_accessors = glb.animation_accessors(solve.clip_name, "translation")
        accessor_index = translation_accessors.get(node_name)
        if accessor_index is None:
            raise ContractError(
                f"{solve.clip_name}: body node has no translation accessor: {node_name}"
            )
        source_values = glb.accessor_values(accessor_index)
        item, _view, width, component_size, code = glb.accessor_layout(accessor_index)
        if (
            item.get("componentType") != 5126
            or item.get("type") != "VEC3"
            or width != 3
            or component_size != 4
            or code != "f"
        ):
            raise ContractError(
                f"{solve.clip_name}/{node_name}: translation accessor is not packed float VEC3"
            )
        offset, count, stride = glb.accessor_region(accessor_index)
        if count != len(rows) or stride != 12:
            raise ContractError(
                f"{solve.clip_name}/{node_name}: translation accessor shape is not canonical"
            )
        for row, delta in enumerate(rows):
            value = _add(
                _vec3(source_values[row], label="source body translation"),
                delta,
            )
            struct.pack_into(
                "<fff",
                raw,
                int(glb.bin_start) + offset + row * stride,
                *value,
            )
    return bytes(raw)


__all__ = [
    "CONTACT_WITNESS_NAMES",
    "ClipSolve",
    "FrameSolve",
    "derive_constant_cyclic_heading_corrections",
    "patch_clip_bytes",
    "solve_clip",
    "validate_witness_residuals",
]
