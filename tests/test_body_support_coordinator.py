from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from eonwild_motion.dynamics.body_support_coordinator import (
    COEFFICIENT_COUNT,
    CoordinatorSample,
    TrialEvaluation,
    periodic_body_delta,
    solve_body_support_trajectory,
    solve_contact_wrench,
)
from eonwild_motion.errors import ContractError


ANCHOR = "a" * 64
SQUARE = ((-0.2, 0.0, -0.2), (-0.2, 0.0, 0.2), (0.2, 0.0, 0.2), (0.2, 0.0, -0.2))


def test_periodic_basis_has_exact_value_and_derivative_seams():
    coefficients = np.linspace(-0.02, 0.02, COEFFICIENT_COUNT)
    duration = 2.46
    start = periodic_body_delta(coefficients, 0.0, duration)
    end = periodic_body_delta(coefficients, duration, duration)
    assert start.translation_m == pytest.approx(end.translation_m, abs=1e-14)
    assert start.rotation_radians == pytest.approx(end.rotation_radians, abs=1e-14)
    epsilon = 1e-6
    left = periodic_body_delta(coefficients, -epsilon, duration)
    right = periodic_body_delta(coefficients, epsilon, duration)
    end_left = periodic_body_delta(coefficients, duration - epsilon, duration)
    end_right = periodic_body_delta(coefficients, duration + epsilon, duration)
    assert (np.asarray(right.translation_m) - np.asarray(left.translation_m)) == pytest.approx(
        np.asarray(end_right.translation_m) - np.asarray(end_left.translation_m), abs=1e-13
    )
    assert (np.asarray(right.rotation_radians) - np.asarray(left.rotation_radians)) == pytest.approx(
        np.asarray(end_right.rotation_radians) - np.asarray(end_left.rotation_radians), abs=1e-13
    )


def test_contact_wrench_recovers_force_and_centered_moment_with_positive_forces():
    solution = solve_contact_wrench(
        support_points_m=SQUARE,
        com_m=(0.0, 1.0, 0.0),
        required_force_n=(120.0, 1000.0, -80.0),
        required_moment_nm=(80.0, 0.0, 120.0),
        total_mass_kg=100.0,
        body_height_m=2.0,
    )
    assert solution.status == "AVAILABLE"
    assert solution.normalized_force_residual < 1e-8
    assert solution.normalized_moment_residual < 1e-8
    assert solution.kkt_residual < 1e-8
    assert min(solution.coefficients_n) >= 0.0
    forces = np.asarray(solution.forces_n)
    assert np.all(forces[:, 1] >= 0.0)
    assert np.sum(forces, axis=0) == pytest.approx((120.0, 1000.0, -80.0), abs=2e-5)
    points = np.asarray(solution.support_points_m)
    moment = np.sum(np.cross(points - np.asarray((0.0, 1.0, 0.0)), forces), axis=0)
    assert moment == pytest.approx((80.0, 0.0, 120.0), abs=2e-4)
    tangential = np.linalg.norm(forces[:, (0, 2)], axis=1)
    assert np.all(tangential <= 0.5 * forces[:, 1] + 1e-10)


def test_cop_outside_support_polygon_is_infeasible():
    # A vertical force applied 0.6 m forward requires a COP outside the 0.2 m hull.
    solution = solve_contact_wrench(
        support_points_m=SQUARE,
        com_m=(0.0, 1.0, 0.0),
        required_force_n=(0.0, 1000.0, 0.0),
        required_moment_nm=(-600.0, 0.0, 0.0),
        total_mass_kg=100.0,
        body_height_m=2.0,
    )
    assert solution.status == "UNAVAILABLE"
    assert solution.normalized_moment_residual > 1e-2


def test_mass_scaling_doubles_contact_forces_and_preserves_normalized_solution():
    first = solve_contact_wrench(
        support_points_m=SQUARE,
        com_m=(0.0, 1.0, 0.0),
        required_force_n=(50.0, 981.0, 0.0),
        required_moment_nm=(0.0, 0.0, 50.0),
        total_mass_kg=100.0,
        body_height_m=2.0,
    )
    second = solve_contact_wrench(
        support_points_m=SQUARE,
        com_m=(0.0, 1.0, 0.0),
        required_force_n=(100.0, 1962.0, 0.0),
        required_moment_nm=(0.0, 0.0, 100.0),
        total_mass_kg=200.0,
        body_height_m=2.0,
    )
    assert first.status == second.status == "AVAILABLE"
    assert np.asarray(second.forces_n) == pytest.approx(2.0 * np.asarray(first.forces_n), rel=1e-10, abs=1e-8)
    assert second.normalized_wrench_residual == pytest.approx(first.normalized_wrench_residual, abs=1e-12)


def test_contact_wrench_is_deterministic():
    kwargs = dict(
        support_points_m=SQUARE,
        com_m=(0.0, 1.0, 0.0),
        required_force_n=(0.0, 981.0, 0.0),
        required_moment_nm=(0.0, 0.0, 0.0),
        total_mass_kg=100.0,
        body_height_m=2.0,
    )
    assert solve_contact_wrench(**kwargs) == solve_contact_wrench(**kwargs)


def test_contact_wrench_rejects_zero_up_axis():
    with pytest.raises(ContractError, match="up axis must be nonzero"):
        solve_contact_wrench(
            support_points_m=SQUARE,
            com_m=(0.0, 1.0, 0.0),
            required_force_n=(0.0, 981.0, 0.0),
            required_moment_nm=(0.0, 0.0, 0.0),
            total_mass_kg=100.0,
            body_height_m=2.0,
            up_axis=(0.0, 0.0, 0.0),
        )


def _static_trial(coefficients, *, anchor=ANCHOR, geometry=True):
    duration = 1.0
    count = 8
    samples = tuple(
        CoordinatorSample(
            time_s=(index + 0.5) / count,
            total_mass_kg=100.0,
            com_m=(0.0, 1.0, 0.0),
            linear_momentum_kg_mps=(0.0, 0.0, 0.0),
            angular_momentum_kg_m2ps=(0.0, 0.0, 0.0),
            support_points_m=SQUARE,
            frozen_anchor_sha256=anchor,
            final_geometry_passed=geometry,
        )
        for index in range(count)
    )
    return TrialEvaluation(duration, 2.0, samples)


def test_coordinator_accepts_zero_minimum_change_when_baseline_is_feasible():
    solution = solve_body_support_trajectory(_static_trial, frozen_anchor_sha256=ANCHOR)
    assert solution.status == "AVAILABLE"
    assert solution.coefficients == (0.0,) * COEFFICIENT_COUNT
    assert solution.iterations == 0
    assert solution.evaluation_count == 1


@pytest.mark.parametrize(
    ("callback", "reason"),
    [
        (lambda coefficients: _static_trial(coefficients, anchor="b" * 64), "changed the frozen material anchors"),
        (lambda coefficients: _static_trial(coefficients, geometry=False), "final foot-frame and full-skin"),
    ],
)
def test_coordinator_rejects_invalid_final_geometry_trials(callback, reason):
    solution = solve_body_support_trajectory(callback, frozen_anchor_sha256=ANCHOR)
    assert solution.status == "UNAVAILABLE"
    assert reason in solution.reason


def test_coordinator_rejects_noncanonical_frame_and_bad_vector_shape():
    wrong_frame = _static_trial((0.0,) * COEFFICIENT_COUNT)
    wrong_frame = replace(wrong_frame, up_axis=(0.0, 0.0, 1.0))
    result = solve_body_support_trajectory(
        lambda _: wrong_frame, frozen_anchor_sha256=ANCHOR
    )
    assert result.status == "UNAVAILABLE"
    assert "+Y-up/+Z-forward" in result.reason

    malformed = _static_trial((0.0,) * COEFFICIENT_COUNT)
    malformed = replace(
        malformed,
        samples=(replace(malformed.samples[0], com_m=(0.0, 1.0)),) + malformed.samples[1:],
    )
    result = solve_body_support_trajectory(
        lambda _: malformed, frozen_anchor_sha256=ANCHOR
    )
    assert result.status == "UNAVAILABLE"
    assert "centroidal series is invalid" in result.reason


def test_coordinator_propagates_nnls_kkt_failure(monkeypatch):
    import eonwild_motion.dynamics.body_support_coordinator as module

    original = module.solve_contact_wrench

    def failed(**kwargs):
        return replace(original(**kwargs), status="UNAVAILABLE", kkt_residual=1.0)

    monkeypatch.setattr(module, "solve_contact_wrench", failed)
    result = solve_body_support_trajectory(_static_trial, frozen_anchor_sha256=ANCHOR)
    assert result.status == "UNAVAILABLE"
    assert "KKT" in result.reason


def test_coordinator_rejects_bounded_nonimproving_infeasible_trial():
    def infeasible(_coefficients):
        trial = _static_trial(_coefficients)
        return TrialEvaluation(
            trial.duration_s,
            trial.body_height_m,
            tuple(
                CoordinatorSample(
                    sample.time_s,
                    sample.total_mass_kg,
                    (0.0, 1.0, 0.8),
                    sample.linear_momentum_kg_mps,
                    sample.angular_momentum_kg_m2ps,
                    sample.support_points_m,
                    sample.frozen_anchor_sha256,
                    sample.final_geometry_passed,
                )
                for sample in trial.samples
            ),
        )

    solution = solve_body_support_trajectory(
        infeasible, frozen_anchor_sha256=ANCHOR, maximum_iterations=1
    )
    assert solution.status == "UNAVAILABLE"
    assert "improving valid trial" in solution.reason
    assert solution.evaluation_count == 17
