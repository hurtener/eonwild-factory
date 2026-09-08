"""Fail-closed interval bounds for source-owned glTF CUBICSPLINE TRS data.

This module neither writes GLBs nor changes their admission. It supplies
conservative source-side bounds that a later emitter/whole-contact authority
may bind to an exact float32 export.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from ..errors import ContractError


_EPSILON = math.ulp(1.0)
_ROUNDING_FACTOR = 64.0 * _EPSILON


def _number(value: float, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be finite")
    return result


def _numbers(values: Sequence[float], *, width: int, label: str) -> tuple[float, ...]:
    if not isinstance(values, (tuple, list)) or len(values) != width:
        raise ContractError(f"{label} must contain {width} finite values")
    return tuple(_number(value, label=label) for value in values)


def _duration(value: float) -> float:
    duration = _number(value, label="cubic interval duration")
    if duration <= 0:
        raise ContractError("cubic interval duration must be finite and positive")
    return duration


def _error(*values: float) -> float:
    scale = max(1.0, *(abs(value) for value in values))
    error = _ROUNDING_FACTOR * scale + 8.0 * math.ulp(scale)
    if not math.isfinite(error):
        raise ContractError("cubic interval bounds overflow")
    return error


def _inflate(value: float, *scale: float) -> tuple[float, float]:
    error = _error(value, *scale)
    lower = math.nextafter(value - error, -math.inf)
    upper = math.nextafter(value + error, math.inf)
    if not math.isfinite(lower) or not math.isfinite(upper):
        raise ContractError("cubic interval bounds overflow")
    return lower, upper


def _source_scale(
    value0: Sequence[float], tangent0: Sequence[float],
    value1: Sequence[float], tangent1: Sequence[float], duration: float,
) -> float:
    scaled_tangents = tuple(duration * tangent for tangent in (*tangent0, *tangent1))
    if not all(math.isfinite(value) for value in scaled_tangents):
        raise ContractError("cubic interval tangent scale overflow")
    return max(1.0, *(abs(value) for value in (*value0, *value1, *scaled_tangents)))


def _derivative_scale(source_scale: float, duration: float) -> float:
    scale = source_scale / duration
    if not math.isfinite(scale):
        raise ContractError("cubic interval derivative scale overflow")
    return scale


def _bezier(value0: Sequence[float], tangent0: Sequence[float], value1: Sequence[float], tangent1: Sequence[float], duration: float) -> tuple[tuple[float, ...], ...]:
    controls = tuple(tuple(values[index] for index in range(len(value0))) for values in (
        value0,
        tuple(value0[index] + duration * tangent0[index] / 3.0 for index in range(len(value0))),
        tuple(value1[index] - duration * tangent1[index] / 3.0 for index in range(len(value0))),
        value1,
    ))
    if not all(math.isfinite(value) for row in controls for value in row):
        raise ContractError("cubic interval controls overflow")
    return controls


def _derivative_controls(control: Sequence[Sequence[float]], duration: float) -> tuple[tuple[float, ...], ...]:
    derivatives = tuple(
        tuple(3.0 * (right[index] - left[index]) / duration for index in range(len(left)))
        for left, right in zip(control, control[1:])
    )
    if not all(math.isfinite(value) for row in derivatives for value in row):
        raise ContractError("cubic interval derivative bounds overflow")
    return derivatives


def _control_box(
    control: Sequence[Sequence[float]], *, source_scale: float = 1.0,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    lower, upper = [], []
    for axis in range(len(control[0])):
        values = [row[axis] for row in control]
        lo, hi = (_inflate(min(values), *values, source_scale),
                  _inflate(max(values), *values, source_scale))
        lower.append(lo[0])
        upper.append(hi[1])
    return tuple(lower), tuple(upper)


def _speed_upper(lower: Sequence[float], upper: Sequence[float]) -> float:
    speed = math.hypot(*(max(abs(lo), abs(hi)) for lo, hi in zip(lower, upper)))
    if not math.isfinite(speed):
        raise ContractError("cubic interval speed bound overflow")
    return speed


@dataclass(frozen=True)
class CubicVectorBounds:
    value_lower: tuple[float, ...]
    value_upper: tuple[float, ...]
    derivative_lower_per_s: tuple[float, ...]
    derivative_upper_per_s: tuple[float, ...]
    speed_upper_per_s: float
    bezier_controls: tuple[tuple[float, ...], ...]


def cubic_vector_bounds(
    value0: Sequence[float], tangent0: Sequence[float],
    value1: Sequence[float], tangent1: Sequence[float], duration_s: float,
) -> CubicVectorBounds:
    """Bound finite Hermite data with 64-epsilon plus ULP outward envelopes."""
    width = len(value0) if isinstance(value0, (tuple, list)) else 0
    if width < 1:
        raise ContractError("cubic vector values must be nonempty")
    first = _numbers(value0, width=width, label="cubic first value")
    second = _numbers(value1, width=width, label="cubic second value")
    incoming = _numbers(tangent0, width=width, label="cubic first tangent")
    outgoing = _numbers(tangent1, width=width, label="cubic second tangent")
    duration = _duration(duration_s)
    controls = _bezier(first, incoming, second, outgoing, duration)
    source_scale = _source_scale(first, incoming, second, outgoing, duration)
    value_lower, value_upper = _control_box(controls, source_scale=source_scale)
    derivatives = _derivative_controls(controls, duration)
    derivative_lower, derivative_upper = _control_box(
        derivatives, source_scale=_derivative_scale(source_scale, duration),
    )
    return CubicVectorBounds(value_lower, value_upper, derivative_lower, derivative_upper,
                             _speed_upper(derivative_lower, derivative_upper), controls)


def _split(control: Sequence[Sequence[float]]) -> tuple[tuple[tuple[float, ...], ...], tuple[tuple[float, ...], ...]]:
    rows = [tuple(tuple(float(value) for value in row) for row in control)]
    while len(rows[-1]) > 1:
        rows.append(tuple(
            tuple(left[index] * .5 + right[index] * .5 for index in range(len(left)))
            for left, right in zip(rows[-1], rows[-1][1:])
        ))
        if not all(math.isfinite(value) for row in rows[-1] for value in row):
            raise ContractError("cubic quaternion subdivision overflow")
    return tuple(row[0] for row in rows), tuple(row[-1] for row in reversed(rows))


def _nonzero_leaves(
    control: Sequence[Sequence[float]], *, minimum_norm: float, depth: int,
    maximum_depth: int, remaining_nodes: list[int], source_scale: float,
) -> tuple[float, list[tuple[tuple[tuple[float, ...], ...], int]]]:
    remaining_nodes[0] -= 1
    if remaining_nodes[0] < 0:
        raise ContractError("cubic quaternion interval exceeds subdivision node budget")
    lower, upper = _control_box(control, source_scale=source_scale)
    proven = max((lo for lo in lower if lo > 0), default=0.0)
    proven = max(proven, max((-hi for hi in upper if hi < 0), default=0.0))
    if proven >= minimum_norm:
        return proven, [(tuple(tuple(row) for row in control), depth)]
    if depth >= maximum_depth:
        raise ContractError("cubic quaternion interval cannot prove a nonzero raw norm within subdivision budget")
    left, right = _split(control)
    left_lower, left_leaves = _nonzero_leaves(
        left, minimum_norm=minimum_norm, depth=depth + 1,
        maximum_depth=maximum_depth, remaining_nodes=remaining_nodes,
        source_scale=source_scale,
    )
    right_lower, right_leaves = _nonzero_leaves(
        right, minimum_norm=minimum_norm, depth=depth + 1,
        maximum_depth=maximum_depth, remaining_nodes=remaining_nodes,
        source_scale=source_scale,
    )
    return min(left_lower, right_lower), left_leaves + right_leaves


def _subdivision_derivative_upper(
    control: Sequence[Sequence[float]], duration: float, depth: int, *, source_scale: float,
) -> float:
    derivatives = _derivative_controls(control, duration / (2 ** depth))
    lower, upper = _control_box(
        derivatives, source_scale=_derivative_scale(source_scale, duration / (2 ** depth)),
    )
    return _speed_upper(lower, upper)


@dataclass(frozen=True)
class CubicQuaternionBounds:
    raw_norm_lower: float
    angular_speed_upper_rad_s: float
    maximum_subdivision_depth: int
    raw_derivative_upper_per_s: float
    bezier_controls_xyzw: tuple[tuple[float, ...], ...]


def cubic_quaternion_bounds(
    value0_xyzw: Sequence[float], out_tangent0_xyzw: Sequence[float],
    value1_xyzw: Sequence[float], in_tangent1_xyzw: Sequence[float], duration_s: float,
    *, minimum_raw_norm: float = 1.0e-10, maximum_depth: int = 20,
    maximum_nodes: int = 16_384,
) -> CubicQuaternionBounds:
    """Certify a nonzero normalized cubic quaternion and a rate upper bound.

    The bound is conservative: ``|omega| <= 2 |qdot| / min|q|``. It does not
    assert that a Hermite quaternion has constant angular speed or that radial
    raw derivatives contribute to physical angular velocity.
    """
    minimum_raw_norm = _number(minimum_raw_norm, label="minimum raw quaternion norm")
    if minimum_raw_norm <= 0:
        raise ContractError("minimum raw quaternion norm must be finite and positive")
    if type(maximum_depth) is not int or maximum_depth < 0 or maximum_depth > 40:
        raise ContractError("cubic quaternion subdivision depth must be an integer in 0..40")
    if type(maximum_nodes) is not int or maximum_nodes < 1 or maximum_nodes > 1_000_000:
        raise ContractError("cubic quaternion subdivision node budget must be an integer in 1..1000000")
    if not isinstance(value0_xyzw, (tuple, list)) or len(value0_xyzw) != 4:
        raise ContractError("cubic quaternion values must contain four xyzw values")
    bounds = cubic_vector_bounds(value0_xyzw, out_tangent0_xyzw, value1_xyzw, in_tangent1_xyzw, duration_s)
    controls = bounds.bezier_controls
    source_scale = _source_scale(
        _numbers(value0_xyzw, width=4, label="cubic first quaternion"),
        _numbers(out_tangent0_xyzw, width=4, label="cubic first quaternion tangent"),
        _numbers(value1_xyzw, width=4, label="cubic second quaternion"),
        _numbers(in_tangent1_xyzw, width=4, label="cubic second quaternion tangent"),
        _duration(duration_s),
    )
    raw_lower, leaves = _nonzero_leaves(
        controls, minimum_norm=minimum_raw_norm, depth=0,
        maximum_depth=maximum_depth, remaining_nodes=[maximum_nodes], source_scale=source_scale,
    )
    derivative_upper = max(
        _subdivision_derivative_upper(control, _duration(duration_s), depth, source_scale=source_scale)
        for control, depth in leaves
    )
    angular_upper = math.nextafter(2.0 * derivative_upper / raw_lower, math.inf)
    if not math.isfinite(angular_upper):
        raise ContractError("cubic quaternion angular-speed bound overflow")
    return CubicQuaternionBounds(raw_lower, angular_upper, max(depth for _, depth in leaves), derivative_upper, controls)
