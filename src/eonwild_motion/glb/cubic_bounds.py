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


@dataclass(frozen=True)
class _Interval:
    lower: float
    upper: float


def _number(value: float, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be finite")
    try:
        result = float(value)
    except (OverflowError, ValueError) as error:
        raise ContractError(f"{label} must be finite") from error
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


def _interval(lower: float, upper: float, *, label: str) -> _Interval:
    if not math.isfinite(lower) or not math.isfinite(upper) or lower > upper:
        raise ContractError(f"{label} overflow")
    return _Interval(lower, upper)


def _singleton(value: float) -> _Interval:
    return _Interval(value, value)


def _directed(value: float, *, upward: bool, label: str) -> float:
    if not math.isfinite(value):
        raise ContractError(f"{label} overflow")
    result = math.nextafter(value, math.inf if upward else -math.inf)
    if not math.isfinite(result):
        raise ContractError(f"{label} overflow")
    return result


def _add(left: _Interval, right: _Interval, *, label: str) -> _Interval:
    return _interval(
        _directed(left.lower + right.lower, upward=False, label=label),
        _directed(left.upper + right.upper, upward=True, label=label),
        label=label,
    )


def _negate(value: _Interval) -> _Interval:
    return _Interval(-value.upper, -value.lower)


def _subtract(left: _Interval, right: _Interval, *, label: str) -> _Interval:
    return _add(left, _negate(right), label=label)


def _multiply(left: _Interval, right: _Interval, *, label: str) -> _Interval:
    products = (
        left.lower * right.lower,
        left.lower * right.upper,
        left.upper * right.lower,
        left.upper * right.upper,
    )
    return _interval(
        _directed(min(products), upward=False, label=label),
        _directed(max(products), upward=True, label=label),
        label=label,
    )


def _divide(left: _Interval, right: _Interval, *, label: str) -> _Interval:
    if right.lower <= 0.0 <= right.upper:
        raise ContractError(f"{label} divisor crosses zero")
    quotients = (
        left.lower / right.lower,
        left.lower / right.upper,
        left.upper / right.lower,
        left.upper / right.upper,
    )
    return _interval(
        _directed(min(quotients), upward=False, label=label),
        _directed(max(quotients), upward=True, label=label),
        label=label,
    )


def _midpoint(left: _Interval, right: _Interval) -> _Interval:
    half = _singleton(0.5)
    return _add(
        _multiply(left, half, label="cubic quaternion subdivision"),
        _multiply(right, half, label="cubic quaternion subdivision"),
        label="cubic quaternion subdivision",
    )


def _controls(
    value0: Sequence[float], tangent0: Sequence[float],
    value1: Sequence[float], tangent1: Sequence[float], duration: float,
) -> tuple[tuple[_Interval, ...], ...]:
    h = _singleton(duration)
    third = _singleton(3.0)
    first = tuple(_singleton(value) for value in value0)
    second = tuple(_singleton(value) for value in value1)
    outgoing = tuple(_singleton(value) for value in tangent0)
    incoming = tuple(_singleton(value) for value in tangent1)
    return (
        first,
        tuple(_add(value, _divide(_multiply(h, tangent, label="cubic control"), third, label="cubic control"), label="cubic control")
              for value, tangent in zip(first, outgoing)),
        tuple(_subtract(value, _divide(_multiply(h, tangent, label="cubic control"), third, label="cubic control"), label="cubic control")
              for value, tangent in zip(second, incoming)),
        second,
    )


def _derivative_controls(
    controls: Sequence[Sequence[_Interval]], duration: float,
) -> tuple[tuple[_Interval, ...], ...]:
    h = _singleton(duration)
    three = _singleton(3.0)
    return tuple(
        tuple(
            _divide(
                _multiply(_subtract(right, left, label="cubic derivative"), three, label="cubic derivative"),
                h,
                label="cubic derivative",
            )
            for left, right in zip(left_row, right_row)
        )
        for left_row, right_row in zip(controls, controls[1:])
    )


def _control_box(
    controls: Sequence[Sequence[_Interval]],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    return (
        tuple(min(row[axis].lower for row in controls) for axis in range(len(controls[0]))),
        tuple(max(row[axis].upper for row in controls) for axis in range(len(controls[0]))),
    )


def _speed_upper(lower: Sequence[float], upper: Sequence[float], *, label: str) -> float:
    # ``math.hypot`` is accurate to within one ulp; the directed successor
    # converts that finite nearest result into an enclosing upper endpoint.
    speed = math.hypot(*(max(abs(low), abs(high)) for low, high in zip(lower, upper)))
    return _directed(speed, upward=True, label=label)


def _display_controls(controls: Sequence[Sequence[_Interval]]) -> tuple[tuple[float, ...], ...]:
    """Return nominal diagnostic controls; interval endpoints remain authority."""
    return tuple(
        tuple(lower.lower * 0.5 + lower.upper * 0.5 for lower in row)
        for row in controls
    )


@dataclass(frozen=True)
class CubicVectorBounds:
    value_lower: tuple[float, ...]
    value_upper: tuple[float, ...]
    derivative_lower_per_s: tuple[float, ...]
    derivative_upper_per_s: tuple[float, ...]
    speed_upper_per_s: float
    bezier_controls: tuple[tuple[float, ...], ...]


def _vector_data(
    value0: Sequence[float], tangent0: Sequence[float],
    value1: Sequence[float], tangent1: Sequence[float], duration_s: float,
) -> tuple[tuple[tuple[_Interval, ...], ...], tuple[tuple[_Interval, ...], ...], float]:
    width = len(value0) if isinstance(value0, (tuple, list)) else 0
    if width < 1:
        raise ContractError("cubic vector values must be nonempty")
    first = _numbers(value0, width=width, label="cubic first value")
    second = _numbers(value1, width=width, label="cubic second value")
    outgoing = _numbers(tangent0, width=width, label="cubic first tangent")
    incoming = _numbers(tangent1, width=width, label="cubic second tangent")
    duration = _duration(duration_s)
    controls = _controls(first, outgoing, second, incoming, duration)
    return controls, _derivative_controls(controls, duration), duration


def cubic_vector_bounds(
    value0: Sequence[float], tangent0: Sequence[float],
    value1: Sequence[float], tangent1: Sequence[float], duration_s: float,
) -> CubicVectorBounds:
    """Bound finite Hermite data through directed binary64 interval arithmetic."""
    controls, derivatives, _ = _vector_data(value0, tangent0, value1, tangent1, duration_s)
    value_lower, value_upper = _control_box(controls)
    derivative_lower, derivative_upper = _control_box(derivatives)
    return CubicVectorBounds(
        value_lower,
        value_upper,
        derivative_lower,
        derivative_upper,
        _speed_upper(derivative_lower, derivative_upper, label="cubic interval speed bound"),
        _display_controls(controls),
    )


def _split(
    controls: Sequence[Sequence[_Interval]],
) -> tuple[tuple[tuple[_Interval, ...], ...], tuple[tuple[_Interval, ...], ...]]:
    rows = [tuple(tuple(value for value in row) for row in controls)]
    while len(rows[-1]) > 1:
        rows.append(tuple(
            tuple(_midpoint(left, right) for left, right in zip(left_row, right_row))
            for left_row, right_row in zip(rows[-1], rows[-1][1:])
        ))
    return tuple(row[0] for row in rows), tuple(row[-1] for row in reversed(rows))


def _nonzero_leaves(
    controls: Sequence[Sequence[_Interval]], *, minimum_norm: float, depth: int,
    maximum_depth: int, remaining_nodes: list[int],
) -> tuple[float, list[int]]:
    remaining_nodes[0] -= 1
    if remaining_nodes[0] < 0:
        raise ContractError("cubic quaternion interval exceeds subdivision node budget")
    lower, upper = _control_box(controls)
    proven = max((value for value in lower if value > 0.0), default=0.0)
    proven = max(proven, max((-value for value in upper if value < 0.0), default=0.0))
    if proven >= minimum_norm:
        return proven, [depth]
    if depth >= maximum_depth:
        raise ContractError("cubic quaternion interval cannot prove a nonzero raw norm within subdivision budget")
    left, right = _split(controls)
    left_lower, left_depths = _nonzero_leaves(
        left,
        minimum_norm=minimum_norm,
        depth=depth + 1,
        maximum_depth=maximum_depth,
        remaining_nodes=remaining_nodes,
    )
    right_lower, right_depths = _nonzero_leaves(
        right,
        minimum_norm=minimum_norm,
        depth=depth + 1,
        maximum_depth=maximum_depth,
        remaining_nodes=remaining_nodes,
    )
    return min(left_lower, right_lower), left_depths + right_depths


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
    controls, derivatives, _ = _vector_data(
        value0_xyzw,
        out_tangent0_xyzw,
        value1_xyzw,
        in_tangent1_xyzw,
        duration_s,
    )
    raw_lower, depths = _nonzero_leaves(
        controls,
        minimum_norm=minimum_raw_norm,
        depth=0,
        maximum_depth=maximum_depth,
        remaining_nodes=[maximum_nodes],
    )
    derivative_lower, derivative_upper = _control_box(derivatives)
    derivative_speed = _speed_upper(
        derivative_lower,
        derivative_upper,
        label="cubic quaternion derivative bound",
    )
    angular_upper = _divide(
        _multiply(_singleton(2.0), _singleton(derivative_speed), label="cubic quaternion angular-speed bound"),
        _singleton(raw_lower),
        label="cubic quaternion angular-speed bound",
    ).upper
    return CubicQuaternionBounds(
        raw_lower,
        angular_upper,
        max(depths),
        derivative_speed,
        _display_controls(controls),
    )
