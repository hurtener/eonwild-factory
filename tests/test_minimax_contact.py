import itertools

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.solve.minimax_contact import minimum_enclosing_residual_ball


def test_two_point_allosaurus_residual_uses_physical_minimax_center():
    first = np.array([-0.00022393357287153748, 0.00005479735207889117, 4.7502658639952955e-8])
    second = np.array([0.00015150213868975193, -0.00003249890292007936, 4.5790586988836424e-8])
    rows = np.vstack([first, second, second, second, first])
    result = minimum_enclosing_residual_ball(rows)
    assert result.unique_residual_count == 2
    assert result.center_m == pytest.approx(0.5 * (first + second), abs=1e-15)
    assert result.radius_m == pytest.approx(0.5 * np.linalg.norm(first - second), abs=1e-15)
    assert result.radius_m == pytest.approx(0.0001927255883732802, abs=1e-15)


def test_known_triangle_tetrahedron_and_degenerate_sets():
    triangle = np.array([[1., 0., 0.], [-1., 0., 0.], [0., 1., 0.]])
    tetrahedron = np.array([[1., 1., 1.], [1., -1., -1.], [-1., 1., -1.], [-1., -1., 1.]])
    coplanar = np.array([[1., 1., 0.], [1., -1., 0.], [-1., 1., 0.], [-1., -1., 0.]])
    collinear = np.array([[-2., 0., 0.], [-1., 0., 0.], [2., 0., 0.]])
    coincident = np.repeat([[3., -4., 5.]], 8, axis=0)
    assert minimum_enclosing_residual_ball(triangle).radius_m == pytest.approx(1.)
    assert minimum_enclosing_residual_ball(tetrahedron).radius_m == pytest.approx(np.sqrt(3.))
    assert minimum_enclosing_residual_ball(coplanar).radius_m == pytest.approx(np.sqrt(2.))
    assert minimum_enclosing_residual_ball(collinear).center_m == pytest.approx((0., 0., 0.))
    assert minimum_enclosing_residual_ball(collinear).radius_m == pytest.approx(2.)
    assert minimum_enclosing_residual_ball(coincident).radius_m == 0.


def test_translation_rotation_duplicates_and_order_preserve_solution():
    points = np.array([[1., 0., 0.], [-1., 0., 0.], [0., .5, 0.], [0., 0., .25]])
    angle = 0.73
    rotation = np.array([[np.cos(angle), -np.sin(angle), 0.],
                         [np.sin(angle), np.cos(angle), 0.], [0., 0., 1.]])
    shift = np.array([7., -3., 2.])
    expected = minimum_enclosing_residual_ball(points)
    transformed = np.vstack([(points @ rotation.T) + shift,
                             (points[::-1] @ rotation.T) + shift])
    actual = minimum_enclosing_residual_ball(transformed[::-1])
    assert actual.unique_residual_count == len(points)
    assert actual.radius_m == pytest.approx(expected.radius_m, abs=1e-13)
    assert actual.center_m == pytest.approx(np.asarray(expected.center_m) @ rotation.T + shift, abs=1e-13)
    for permutation in itertools.permutations(points[:3]):
        replay = minimum_enclosing_residual_ball(np.asarray(permutation))
        baseline = minimum_enclosing_residual_ball(points[:3])
        assert replay == baseline


@pytest.mark.parametrize("value", [[], [[1., 2.]], [[1., 2., np.nan]], [[1., 2., np.inf]]])
def test_invalid_residuals_fail_closed(value):
    with pytest.raises(ContractError, match="contact residuals"):
        minimum_enclosing_residual_ball(value)


def test_count_is_unique_residual_rows_not_physical_contact_cardinality():
    # The API receives no contact IDs. These could be three different contacts
    # undergoing the same translation, so this count must never define a hull.
    result = minimum_enclosing_residual_ball([[1., 2., 3.]] * 3)
    assert result.unique_residual_count == 1


def test_finite_extreme_values_that_would_overflow_geometry_fail_closed():
    limit = np.finfo(float).max
    with pytest.raises(ContractError, match="finite arithmetic bound"):
        minimum_enclosing_residual_ball([[limit, 0., 0.], [-limit, 0., 0.]])
