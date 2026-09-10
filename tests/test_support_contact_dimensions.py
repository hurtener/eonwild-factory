from __future__ import annotations

import numpy as np
import pytest

from eonwild_motion.dynamics.body_support_coordinator import (
    coordinator_policy,
    solve_contact_wrench,
)
from eonwild_motion.errors import ContractError


MASS_KG = 100.0
HEIGHT_M = 2.0
BODY_WEIGHT_N = MASS_KG * 9.80665
COM = (0.0, 1.0, 0.0)
POINT = (0.15, 0.0, 0.25)
LINE = ((-0.3, 0.0, 0.0), (0.3, 0.0, 0.0))
SQUARE = ((-0.2, 0.0, -0.2), (-0.2, 0.0, 0.2), (0.2, 0.0, 0.2), (0.2, 0.0, -0.2))


def _wrench_for_vertical_force(point, force_y=BODY_WEIGHT_N):
    force = np.asarray((0.0, force_y, 0.0))
    moment = np.cross(np.asarray(point) - np.asarray(COM), force)
    return tuple(float(value) for value in force), tuple(float(value) for value in moment)


def _solve(support_points, force, moment):
    return solve_contact_wrench(
        support_points_m=support_points,
        com_m=COM,
        required_force_n=force,
        required_moment_nm=moment,
        total_mass_kg=MASS_KG,
        body_height_m=HEIGHT_M,
    )


def test_point_contact_reports_dimension_rank_and_zero_area_for_feasible_wrench():
    force, moment = _wrench_for_vertical_force(POINT)
    solution = _solve((POINT, POINT, POINT), force, moment)

    assert solution.status == "AVAILABLE"
    assert solution.support_points_m == (POINT,)
    assert solution.support_dimension == 0
    assert solution.wrench_rank == 3
    assert solution.planar_area_m2 == 0.0
    assert solution.normalized_force_residual <= 1e-8
    assert solution.normalized_moment_residual <= 1e-8
    assert solution.kkt_residual <= 1e-8


def test_point_contact_rejects_torque_not_generated_at_the_contact():
    force, moment = _wrench_for_vertical_force(POINT)
    impossible_moment = tuple(np.asarray(moment) + np.asarray((0.0, 20.0, 0.0)))
    solution = _solve((POINT,), force, impossible_moment)

    assert solution.status == "UNAVAILABLE"
    assert solution.support_dimension == 0
    assert solution.wrench_rank == 3
    assert solution.planar_area_m2 == 0.0
    assert solution.normalized_moment_residual > 1e-4


def test_line_contact_uses_endpoints_and_reports_rank_without_area():
    force, _ = _wrench_for_vertical_force((0.0, 0.0, 0.0))
    moment = (0.0, 0.0, 98.1)
    solution = _solve(LINE, force, moment)

    assert solution.status == "AVAILABLE"
    assert solution.support_points_m == LINE
    assert solution.support_dimension == 1
    assert solution.wrench_rank == 5
    assert solution.planar_area_m2 == 0.0
    assert solution.normalized_force_residual <= 1e-8
    assert solution.normalized_moment_residual <= 1e-8
    assert solution.kkt_residual <= 1e-8


def test_line_contact_rejects_torque_about_line_direction():
    force, _ = _wrench_for_vertical_force((0.0, 0.0, 0.0))
    solution = _solve(LINE, force, (20.0, 0.0, 98.1))

    assert solution.status == "UNAVAILABLE"
    assert solution.support_dimension == 1
    assert solution.wrench_rank == 5
    assert solution.planar_area_m2 == 0.0
    assert solution.normalized_moment_residual > 1e-4


def test_duplicate_positions_and_input_order_have_one_deterministic_line_solution():
    force, _ = _wrench_for_vertical_force((0.0, 0.0, 0.0))
    moment = (0.0, 0.0, 98.1)
    first = _solve(
        ((0.3, 0.0, 0.0), (0.0, 0.0, 0.0), (-0.3, 0.0, 0.0), (0.3, 0.0, 0.0)),
        force,
        moment,
    )
    second = _solve(
        ((-0.3, 0.0, 0.0), (0.3, 0.0, 0.0), (0.0, 0.0, 0.0), (-0.3, 0.0, 0.0)),
        force,
        moment,
    )

    assert first == second
    assert first.support_points_m == LINE


def test_polygon_preserves_feasible_wrench_and_reports_planar_area():
    solution = _solve(
        SQUARE,
        (120.0, 1000.0, -80.0),
        (80.0, 0.0, 120.0),
    )

    assert solution.status == "AVAILABLE"
    assert solution.support_dimension == 2
    assert solution.wrench_rank == 6
    assert solution.planar_area_m2 == pytest.approx(0.16, abs=1e-14)
    assert solution.normalized_force_residual < 1e-8
    assert solution.normalized_moment_residual < 1e-8


def test_empty_support_remains_rejected_and_policy_identity_is_versioned():
    with pytest.raises(ContractError, match="at least one distinct point"):
        _solve(np.empty((0, 3)), (0.0, BODY_WEIGHT_N, 0.0), (0.0, 0.0, 0.0))
    assert coordinator_policy()["schema"] == "eonwild.motion.body-support-coordinator.v2"
