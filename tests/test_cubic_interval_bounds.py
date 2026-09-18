from __future__ import annotations

from fractions import Fraction
import math

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.glb.cubic_bounds import cubic_quaternion_bounds, cubic_vector_bounds


def _hermite(v0, m0, v1, m1, duration, amount):
    t2, t3 = amount * amount, amount * amount * amount
    return tuple((2*t3 - 3*t2 + 1) * a + duration * (t3 - 2*t2 + amount) * b
                 + (-2*t3 + 3*t2) * c + duration * (t3 - t2) * d
                 for a, b, c, d in zip(v0, m0, v1, m1))


def _derivative(v0, m0, v1, m1, duration, amount):
    t2 = amount * amount
    return tuple(((6*t2 - 6*amount) * a / duration + (3*t2 - 4*amount + 1) * b
                 + (-6*t2 + 6*amount) * c / duration + (3*t2 - 2*amount) * d)
                 for a, b, c, d in zip(v0, m0, v1, m1))


def _exact_controls(v0, m0, v1, m1, duration):
    h = Fraction.from_float(duration)
    return tuple(
        (Fraction.from_float(start),
         Fraction.from_float(start) + h * Fraction.from_float(outgoing) / 3,
         Fraction.from_float(end) - h * Fraction.from_float(incoming) / 3,
         Fraction.from_float(end))
        for start, outgoing, end, incoming in zip(v0, m0, v1, m1)
    )


def _exact_derivatives(controls, duration):
    h = Fraction.from_float(duration)
    return tuple(tuple(3 * (right - left) / h for left, right in zip(axis, axis[1:]))
                 for axis in controls)


def test_scalar_hidden_overshoot_and_derivative_hull_are_bounded():
    bound = cubic_vector_bounds((0.,), (3.,), (1.,), (-1.,), .25)
    dense = [_hermite((0.,), (3.,), (1.,), (-1.,), .25, index / 10000)[0] for index in range(10001)]
    assert max(dense) > 1.
    assert min(bound.value_lower) <= min(dense) <= max(dense) <= max(bound.value_upper)
    dense_rate = [abs(_derivative((0.,), (3.,), (1.,), (-1.,), .25, index / 10000)[0]) for index in range(10001)]
    assert max(dense_rate) <= bound.speed_upper_per_s


def test_vector_bound_contains_dense_independent_samples_and_short_duration_rates():
    duration = 1 / 120
    values = ((.1, -.2, .3), (7., -5., 2.), (.4, .6, -.1), (-3., 4., .5))
    bound = cubic_vector_bounds(*values, duration)
    for index in range(1001):
        value = _hermite(*values, duration, index / 1000)
        derivative = _derivative(*values, duration, index / 1000)
        assert all(lo <= item <= hi for item, lo, hi in zip(value, bound.value_lower, bound.value_upper))
        assert math.sqrt(sum(item * item for item in derivative)) <= bound.speed_upper_per_s


def test_outward_rounding_envelope_contains_exact_constant_zero():
    bound = cubic_vector_bounds((0.,), (0.,), (0.,), (0.,), 1 / 120)
    assert bound.value_lower[0] < 0. < bound.value_upper[0]
    assert bound.derivative_lower_per_s[0] < 0. < bound.derivative_upper_per_s[0]


def test_directed_intervals_retain_source_scale_after_control_cancellation():
    """A unit tangent is lost in a 1e16 control addition but remains bounded."""
    bound = cubic_vector_bounds((1.e16,), (3.,), (1.e16,), (0.,), 1.)
    assert _derivative((1.e16,), (3.,), (1.e16,), (0.,), 1., 0.) == (3.,)
    assert bound.derivative_lower_per_s[0] <= 3. <= bound.derivative_upper_per_s[0]


def test_directed_vector_bounds_contain_exact_rational_controls_and_derivatives():
    duration = 1 / 120
    values = ((.1, -.2, .3), (7., -5., 2.), (.4, .6, -.1), (-3., 4., .5))
    bound = cubic_vector_bounds(*values, duration)
    controls = _exact_controls(*values, duration)
    derivatives = _exact_derivatives(controls, duration)
    for axis, control in enumerate(controls):
        lower, upper = map(Fraction.from_float, (bound.value_lower[axis], bound.value_upper[axis]))
        assert all(lower <= value <= upper for value in control)
    for axis, derivative in enumerate(derivatives):
        lower, upper = map(Fraction.from_float, (bound.derivative_lower_per_s[axis], bound.derivative_upper_per_s[axis]))
        assert all(lower <= value <= upper for value in derivative)


def test_quaternion_bound_subdivides_and_contains_dense_normalized_rate():
    duration, angle = 1 / 120, .06
    q0, q1 = (0., 0., 0., 1.), (0., math.sin(angle / 2), 0., math.cos(angle / 2))
    m0 = (0., angle / (2 * duration), 0., 0.)
    m1 = (0., math.cos(angle / 2) * angle / (2 * duration), 0., -math.sin(angle / 2) * angle / (2 * duration))
    bound = cubic_quaternion_bounds(q0, m0, q1, m1, duration)
    assert bound.raw_norm_lower > .99
    for index in range(1001):
        q = _hermite(q0, m0, q1, m1, duration, index / 1000)
        dot = _derivative(q0, m0, q1, m1, duration, index / 1000)
        length = math.sqrt(sum(value * value for value in q))
        normalized_dot = tuple((value - q[index2] * sum(a*b for a, b in zip(q, dot)) / (length * length)) / length for index2, value in enumerate(dot))
        omega = 2 * math.sqrt(sum(value * value for value in normalized_dot))
        assert omega <= bound.angular_speed_upper_rad_s


def test_quaternion_nonzero_proof_subdivides_without_treating_radial_motion_as_exact_rate():
    bound = cubic_quaternion_bounds(
        (0., 0., 0., 1.), (0., 0., 0., -1.8),
        (0., 0., 0., 1.), (0., 0., 0., 1.8), 1., minimum_raw_norm=.5,
    )
    assert bound.maximum_subdivision_depth == 1
    assert bound.raw_norm_lower >= .5
    assert bound.angular_speed_upper_rad_s > 0.


def test_quaternion_nonzero_proof_fails_closed_at_subdivision_node_budget():
    with pytest.raises(ContractError, match="node budget"):
        cubic_quaternion_bounds(
            (0., 0., 0., 1.), (0., 0., 0., -1.8),
            (0., 0., 0., 1.), (0., 0., 0., 1.8), 1.,
            minimum_raw_norm=.5, maximum_nodes=1,
        )


@pytest.mark.parametrize("values", [
    ((0., 0., 0., 1.), (0., 0., 0., 0.), (0., 0., 0., -1.), (0., 0., 0., 0.)),
    ((0., 0., 0., 1.e-14), (0., 0., 0., 0.), (0., 0., 0., 1.e-14), (0., 0., 0., 0.)),
])
def test_quaternion_zero_or_nearzero_intervals_fail_closed(values):
    with pytest.raises(ContractError, match="nonzero raw norm"):
        cubic_quaternion_bounds(*values, 1., maximum_depth=8)


def test_radial_quaternion_tangent_is_not_claimed_as_exact_angular_speed():
    bound = cubic_quaternion_bounds((0., 0., 0., 1.), (0., 0., 0., 5.), (0., 0., 0., 1.), (0., 0., 0., -5.), 1.)
    assert bound.angular_speed_upper_rad_s > 0.
    assert "conservative" in cubic_quaternion_bounds.__doc__


def test_quaternion_requires_actual_trs_xyzw_width():
    with pytest.raises(ContractError, match="four xyzw"):
        cubic_quaternion_bounds((0., 0., 1.), (0., 0., 0.), (0., 0., 1.), (0., 0., 0.), 1.)


@pytest.mark.parametrize("args", [
    ((0.,), (0.,), (1.,), (0.,), 0.),
    ((0., math.inf), (0., 0.), (1., 0.), (0., 0.), 1.),
    ((0.,), (False,), (1.,), (0.,), 1.),
])
def test_vector_input_validation_fails_closed(args):
    with pytest.raises(ContractError):
        cubic_vector_bounds(*args)


def test_bound_calculation_overflow_fails_closed():
    with pytest.raises(ContractError, match="overflow"):
        cubic_vector_bounds((1.e308,) * 3, (1.e308,) * 3, (1.e308,) * 3, (1.e308,) * 3, 1.)


def test_subnormal_duration_with_unbounded_rate_fails_closed():
    with pytest.raises(ContractError, match="overflow"):
        cubic_vector_bounds((1.,), (0.,), (0.,), (0.,), math.ulp(0.))


@pytest.mark.parametrize("call", [
    lambda: cubic_vector_bounds((10 ** 10000,), (0.,), (0.,), (0.,), 1.),
    lambda: cubic_vector_bounds((0.,), (0.,), (0.,), (0.,), 10 ** 10000),
    lambda: cubic_quaternion_bounds(
        (0., 0., 0., 1.), (0., 0., 0., 0.),
        (0., 0., 0., 1.), (0., 0., 0., 0.), 1., minimum_raw_norm=10 ** 10000,
    ),
])
def test_huge_numbers_fail_as_contract_inputs(call):
    with pytest.raises(ContractError):
        call()
