"""Bounded centroidal support coordination for the shared walking solver.

The numerical core consumes callback results that have already passed the final
semantic foot-frame law and full-skin gates.  Linear and angular momenta must
come from the exact fixed-mass, full-LBS particle proxy; per-joint rigid inertia
is not an equivalent substitute.  This remains an engineering coordination
proxy, not anatomy, physiology, or capacity evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Callable, Sequence

import numpy as np

from ..errors import ContractError


SCHEMA = "eonwild.motion.body-support-coordinator.v1"
COEFFICIENT_COUNT = 12
COEFFICIENTS = (
    "pelvis_forward_k2_sin",
    "pelvis_forward_k2_cos",
    "pelvis_up_k2_sin",
    "pelvis_up_k2_cos",
    "pelvis_lateral_k1_sin",
    "pelvis_lateral_k1_cos",
    "pelvis_pitch_k2_sin",
    "pelvis_pitch_k2_cos",
    "pelvis_roll_k1_sin",
    "pelvis_roll_k1_cos",
    "pelvis_yaw_k1_sin",
    "pelvis_yaw_k1_cos",
)
FRICTION_COEFFICIENT = 0.5
NORMALIZED_WRENCH_TOLERANCE = 1e-4
_NNLS_KKT_TOLERANCE = 1e-10
_NNLS_MAX_ITERATIONS_FACTOR = 12


@dataclass(frozen=True)
class BodyDelta:
    translation_m: tuple[float, float, float]  # forward, up, lateral
    rotation_radians: tuple[float, float, float]  # pitch, roll, yaw


@dataclass(frozen=True)
class CoordinatorSample:
    """Integration adapter result, not an independent geometric proof.

    ``final_geometry_passed`` may be set only after the shared final foot-frame
    law and full-skin evaluator measure this exact trial pose.
    """

    time_s: float
    total_mass_kg: float
    com_m: tuple[float, float, float]
    linear_momentum_kg_mps: tuple[float, float, float]
    angular_momentum_kg_m2ps: tuple[float, float, float]
    support_points_m: tuple[tuple[float, float, float], ...]
    frozen_anchor_sha256: str
    final_geometry_passed: bool


@dataclass(frozen=True)
class TrialEvaluation:
    duration_s: float
    body_height_m: float
    samples: tuple[CoordinatorSample, ...]
    up_axis: tuple[float, float, float] = (0.0, 1.0, 0.0)
    forward_axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    sample_semantics: str = "full_lbs_interval_midpoints.v1"


@dataclass(frozen=True)
class ContactWrenchSolution:
    status: str
    support_points_m: tuple[tuple[float, float, float], ...]
    forces_n: tuple[tuple[float, float, float], ...]
    coefficients_n: tuple[float, ...]
    normalized_force_residual: float
    normalized_moment_residual: float
    kkt_residual: float
    normalized_wrench_residual: tuple[float, float, float, float, float, float]
    reason: str | None = None


@dataclass(frozen=True)
class BodySupportSolution:
    status: str
    coefficients: tuple[float, ...]
    objective: float
    maximum_normalized_force_residual: float
    maximum_normalized_moment_residual: float
    iterations: int
    evaluation_count: int
    reason: str | None = None


TrialEvaluator = Callable[[tuple[float, ...]], TrialEvaluation]


def coordinator_policy():
    """Return the immutable numerical policy that integration must hash-bind."""
    return MappingProxyType(
        {
            "schema": SCHEMA,
            "coefficients": COEFFICIENTS,
            "translation_coefficient_bound_body_heights": 0.03,
            "rotation_coefficient_bound_degrees": 4.0,
            "friction_coefficient": FRICTION_COEFFICIENT,
            "normalized_wrench_tolerance": NORMALIZED_WRENCH_TOLERANCE,
            "maximum_outer_iterations": 4,
            "mass_model": "fixed-neutral-area full-LBS vertex particles",
        }
    )


def _vector(value: Sequence[float], label: str) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractError(f"{label} must be a finite three-vector")
    return result


def _coefficients(value: Sequence[float]) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (COEFFICIENT_COUNT,) or not np.isfinite(result).all():
        raise ContractError("body-support coefficients must contain 12 finite values")
    return result


def periodic_body_delta(
    coefficients: Sequence[float], time_s: float, duration_s: float
) -> BodyDelta:
    """Evaluate the fixed C-infinity 12-DOF, zero-mean periodic body basis."""
    values = _coefficients(coefficients)
    time = float(time_s)
    duration = float(duration_s)
    if not math.isfinite(time) or not math.isfinite(duration) or duration <= 0:
        raise ContractError("periodic body delta needs finite time and positive duration")
    phase = 2.0 * math.pi * time / duration

    def harmonic(pair: int, order: int) -> float:
        return float(
            values[2 * pair] * math.sin(order * phase)
            + values[2 * pair + 1] * math.cos(order * phase)
        )

    return BodyDelta(
        translation_m=(harmonic(0, 2), harmonic(1, 2), harmonic(2, 1)),
        rotation_radians=(harmonic(3, 2), harmonic(4, 1), harmonic(5, 1)),
    )


def _convex_hull_indices(points: np.ndarray, lateral: np.ndarray, forward: np.ndarray) -> list[int]:
    projected = np.column_stack((points @ lateral, points @ forward))
    order = sorted(range(len(points)), key=lambda i: (projected[i, 0], projected[i, 1], i))
    unique = []
    for index in order:
        if not unique or not np.allclose(projected[index], projected[unique[-1]], atol=1e-12, rtol=0):
            unique.append(index)
    if len(unique) < 3:
        raise ContractError("support polygon needs at least three distinct points")

    def cross(o: int, a: int, b: int) -> float:
        oa, ob = projected[a] - projected[o], projected[b] - projected[o]
        return float(oa[0] * ob[1] - oa[1] * ob[0])

    lower: list[int] = []
    for index in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], index) <= 1e-14:
            lower.pop()
        lower.append(index)
    upper: list[int] = []
    for index in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], index) <= 1e-14:
            upper.pop()
        upper.append(index)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        raise ContractError("support polygon is degenerate")
    return hull


def _nnls(matrix: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float]:
    """Deterministic Lawson-Hanson active-set nonnegative least squares."""
    rows, columns = matrix.shape
    if rows == 0 or columns == 0 or target.shape != (rows,):
        raise ContractError("NNLS dimensions are invalid")
    x = np.zeros(columns)
    passive = np.zeros(columns, dtype=bool)
    limit = _NNLS_MAX_ITERATIONS_FACTOR * columns
    for _ in range(limit):
        gradient = matrix.T @ (target - matrix @ x)
        candidates = np.flatnonzero((~passive) & (gradient > _NNLS_KKT_TOLERANCE))
        if not len(candidates):
            inactive_violation = float(max(0.0, np.max(gradient[~passive], initial=0.0)))
            passive_violation = float(np.max(np.abs(gradient[passive]), initial=0.0))
            primal_violation = float(max(0.0, -np.min(x, initial=0.0)))
            kkt = max(inactive_violation, passive_violation, primal_violation)
            return x, kkt
        best_value = float(np.max(gradient[candidates]))
        entering = int(candidates[np.flatnonzero(gradient[candidates] >= best_value - 1e-15)[0]])
        passive[entering] = True
        while True:
            z = np.zeros(columns)
            z[passive] = np.linalg.lstsq(matrix[:, passive], target, rcond=None)[0]
            invalid = passive & (z <= _NNLS_KKT_TOLERANCE)
            if not np.any(invalid):
                x = z
                break
            denominators = x[invalid] - z[invalid]
            valid = denominators > 0
            if not np.any(valid):
                passive[invalid] = False
                x[invalid] = 0.0
                break
            alpha = float(np.min(x[invalid][valid] / denominators[valid]))
            x += alpha * (z - x)
            released = passive & (x <= _NNLS_KKT_TOLERANCE)
            passive[released] = False
            x[released] = 0.0
    raise ContractError("contact wrench NNLS iteration limit exceeded")


def solve_contact_wrench(
    *,
    support_points_m: Sequence[Sequence[float]],
    com_m: Sequence[float],
    required_force_n: Sequence[float],
    required_moment_nm: Sequence[float],
    total_mass_kg: float,
    body_height_m: float,
    up_axis: Sequence[float] = (0.0, 1.0, 0.0),
    forward_axis: Sequence[float] = (0.0, 0.0, 1.0),
) -> ContactWrenchSolution:
    """Distribute a required centroidal wrench over an actual support hull."""
    points = np.asarray(support_points_m, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ContractError("support points must be finite three-vectors")
    center = _vector(com_m, "center of mass")
    force = _vector(required_force_n, "required force")
    moment = _vector(required_moment_nm, "required moment")
    mass, height, friction = map(
        float, (total_mass_kg, body_height_m, FRICTION_COEFFICIENT)
    )
    if not all(math.isfinite(v) and v > 0 for v in (mass, height, friction)):
        raise ContractError("mass, body height, and friction must be positive finite values")
    up = _vector(up_axis, "up axis")
    up_norm = float(np.linalg.norm(up))
    if up_norm <= 1e-12:
        raise ContractError("up axis must be nonzero")
    up /= up_norm
    forward = _vector(forward_axis, "forward axis")
    forward -= up * float(forward @ up)
    if np.linalg.norm(forward) <= 1e-12:
        raise ContractError("forward axis must differ from up")
    forward /= np.linalg.norm(forward)
    lateral = np.cross(up, forward)
    hull = points[_convex_hull_indices(points, lateral, forward)]
    tangential = friction / math.sqrt(2.0)
    rays = tuple(
        up + tangential * (a * forward + b * lateral)
        for a, b in ((-1, -1), (-1, 1), (1, -1), (1, 1))
    )
    columns = []
    owners = []
    for point_index, point in enumerate(hull):
        for ray in rays:
            columns.append(np.concatenate((ray, np.cross(point - center, ray))))
            owners.append(point_index)
    matrix = np.column_stack(columns)
    target = np.concatenate((force, moment))
    force_scale = mass * 9.80665
    weights = np.diag([1 / force_scale] * 3 + [1 / (force_scale * height)] * 3)
    # Solve for coefficients normalized by body weight.  This preserves exact
    # dimensional mass scaling while keeping the tie-break dimensionless.
    weighted = weights @ matrix * force_scale
    weighted_target = weights @ target
    regularization = 1e-12
    augmented = np.vstack((weighted, math.sqrt(regularization) * np.eye(matrix.shape[1])))
    augmented_target = np.concatenate((weighted_target, np.zeros(matrix.shape[1])))
    normalized_coefficients, kkt = _nnls(augmented, augmented_target)
    coefficients = normalized_coefficients * force_scale
    achieved = matrix @ coefficients
    normalized = weights @ (achieved - target)
    force_residual = float(np.linalg.norm(normalized[:3]))
    moment_residual = float(
        np.linalg.norm(normalized[3:])
    )
    vertex_forces = np.zeros((len(hull), 3))
    for value, owner, ray in zip(coefficients, owners, rays * len(hull)):
        vertex_forces[owner] += value * ray
    available = (
        force_residual <= NORMALIZED_WRENCH_TOLERANCE
        and moment_residual <= NORMALIZED_WRENCH_TOLERANCE
        and kkt <= 1e-8
    )
    return ContactWrenchSolution(
        status="AVAILABLE" if available else "UNAVAILABLE",
        support_points_m=tuple(tuple(float(v) for v in row) for row in hull),
        forces_n=tuple(tuple(float(v) for v in row) for row in vertex_forces),
        coefficients_n=tuple(float(v) for v in coefficients),
        normalized_force_residual=force_residual,
        normalized_moment_residual=moment_residual,
        kkt_residual=kkt,
        normalized_wrench_residual=tuple(float(value) for value in normalized),
        reason=None if available else "required centroidal wrench is outside the bounded contact wrench cone",
    )


def _periodic_difference(values: np.ndarray, duration: float) -> np.ndarray:
    count = len(values)
    if count < 5:
        raise ContractError("coordinator needs at least five periodic samples")
    dt = duration / count
    return (np.roll(values, -1, axis=0) - np.roll(values, 1, axis=0)) / (2.0 * dt)


def _validate_trial(
    trial: TrialEvaluation, *, frozen_anchor_sha256: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    duration, height = float(trial.duration_s), float(trial.body_height_m)
    if not math.isfinite(duration) or duration <= 0 or not math.isfinite(height) or height <= 0:
        raise ContractError("trial duration and body height must be positive")
    if len(trial.samples) < 5:
        raise ContractError("trial needs at least five samples")
    if trial.up_axis != (0.0, 1.0, 0.0) or trial.forward_axis != (0.0, 0.0, 1.0):
        raise ContractError("coordinator admits only the factory +Y-up/+Z-forward frame")
    if trial.sample_semantics != "full_lbs_interval_midpoints.v1":
        raise ContractError("coordinator requires full-LBS interval-midpoint momentum samples")
    times = np.asarray([sample.time_s for sample in trial.samples], dtype=float)
    expected = (np.arange(len(times), dtype=float) + 0.5) * duration / len(times)
    if not np.allclose(times, expected, rtol=0, atol=1e-10):
        raise ContractError("trial must use an ordered uniform periodic midpoint clock")
    if any(not sample.final_geometry_passed for sample in trial.samples):
        raise ContractError("trial did not pass the final foot-frame and full-skin evaluator")
    if any(sample.frozen_anchor_sha256 != frozen_anchor_sha256 for sample in trial.samples):
        raise ContractError("trial changed the frozen material anchors")
    masses = np.asarray([sample.total_mass_kg for sample in trial.samples], dtype=float)
    if np.any(~np.isfinite(masses)) or np.any(masses <= 0) or not np.allclose(masses, masses[0], rtol=0, atol=1e-9):
        raise ContractError("trial mass must be one positive constant")
    try:
        com = np.asarray([sample.com_m for sample in trial.samples], dtype=float)
        linear = np.asarray(
            [sample.linear_momentum_kg_mps for sample in trial.samples], dtype=float
        )
        angular = np.asarray(
            [sample.angular_momentum_kg_m2ps for sample in trial.samples], dtype=float
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("trial centroidal series is invalid") from exc
    expected_shape = (len(trial.samples), 3)
    if (
        com.shape != expected_shape
        or linear.shape != expected_shape
        or angular.shape != expected_shape
        or not np.isfinite(com).all()
        or not np.isfinite(linear).all()
        or not np.isfinite(angular).all()
    ):
        raise ContractError("trial centroidal series is invalid")
    return com, linear, angular, float(masses[0]), height


def _trial_residuals(
    trial: TrialEvaluation, *, frozen_anchor_sha256: str
) -> tuple[np.ndarray, float, float]:
    com, linear, angular, mass, height = _validate_trial(
        trial, frozen_anchor_sha256=frozen_anchor_sha256
    )
    force = _periodic_difference(linear, trial.duration_s)
    force[:, 1] += mass * 9.80665
    moment = _periodic_difference(angular, trial.duration_s)
    residuals = []
    max_force = max_moment = 0.0
    for index, sample in enumerate(trial.samples):
        solution = solve_contact_wrench(
            support_points_m=sample.support_points_m,
            com_m=com[index],
            required_force_n=force[index],
            required_moment_nm=moment[index],
            total_mass_kg=mass,
            body_height_m=height,
        )
        if solution.kkt_residual > 1e-8:
            raise ContractError("contact wrench NNLS failed its KKT gate")
        # Six signed residual components are stable across changing hull sizes.
        residuals.extend(solution.normalized_wrench_residual)
        max_force = max(max_force, solution.normalized_force_residual)
        max_moment = max(max_moment, solution.normalized_moment_residual)
    return np.asarray(residuals, dtype=float), max_force, max_moment


def solve_body_support_trajectory(
    evaluator: TrialEvaluator,
    *,
    frozen_anchor_sha256: str,
    maximum_iterations: int = 4,
) -> BodySupportSolution:
    """Find the minimum-change bounded periodic body trajectory."""
    if (
        not isinstance(frozen_anchor_sha256, str)
        or len(frozen_anchor_sha256) != 64
        or any(character not in "0123456789abcdef" for character in frozen_anchor_sha256)
    ):
        raise ContractError("coordinator requires a frozen material-anchor SHA-256")
    if type(maximum_iterations) is not int or not 1 <= maximum_iterations <= 4:
        raise ContractError("coordinator iteration bound must be between one and four")
    coefficients = np.zeros(COEFFICIENT_COUNT)
    evaluations = 0

    def evaluate(values: np.ndarray):
        nonlocal evaluations
        trial = evaluator(tuple(float(v) for v in values))
        evaluations += 1
        residual, force_error, moment_error = _trial_residuals(
            trial, frozen_anchor_sha256=frozen_anchor_sha256
        )
        trial_bounds = np.asarray(
            [0.03 * trial.body_height_m] * 6 + [math.radians(4.0)] * 6
        )
        regularization = 1e-3 * float((values / trial_bounds) @ (values / trial_bounds))
        objective = float(residual @ residual + regularization)
        return trial, residual, force_error, moment_error, objective

    try:
        trial, residual, force_error, moment_error, objective = evaluate(coefficients)
    except ContractError as exc:
        return BodySupportSolution("UNAVAILABLE", tuple(coefficients), math.inf, math.inf, math.inf, 0, evaluations, str(exc))
    if max(force_error, moment_error) <= NORMALIZED_WRENCH_TOLERANCE:
        return BodySupportSolution("AVAILABLE", tuple(coefficients), objective, force_error, moment_error, 0, evaluations)
    translation_bound = 0.03 * trial.body_height_m
    rotation_bound = math.radians(4.0)
    bounds = np.asarray([translation_bound] * 6 + [rotation_bound] * 6)
    steps = np.asarray([1e-4 * trial.body_height_m] * 6 + [1e-4] * 6)
    for iteration in range(1, maximum_iterations + 1):
        jacobian = np.empty((len(residual), COEFFICIENT_COUNT))
        for column in range(COEFFICIENT_COUNT):
            candidate = coefficients.copy()
            candidate[column] += steps[column]
            try:
                _, shifted, _, _, _ = evaluate(candidate)
            except ContractError as exc:
                return BodySupportSolution("UNAVAILABLE", tuple(coefficients), objective, force_error, moment_error, iteration - 1, evaluations, f"invalid finite-difference trial: {exc}")
            jacobian[:, column] = (shifted - residual) / steps[column]
        regularization_hessian = 1e-3 * np.diag(1.0 / (bounds * bounds))
        damping = 1e-6 * np.eye(COEFFICIENT_COUNT)
        step = np.linalg.lstsq(
            jacobian.T @ jacobian + regularization_hessian + damping,
            -(jacobian.T @ residual + 1e-3 * coefficients / (bounds * bounds)),
            rcond=None,
        )[0]
        accepted = None
        for scale in (1.0, 0.5, 0.25, 0.125):
            candidate = np.clip(coefficients + scale * step, -bounds, bounds)
            try:
                result = evaluate(candidate)
            except ContractError:
                continue
            if result[-1] < objective:
                accepted = (candidate, result)
                break
        if accepted is None:
            return BodySupportSolution("UNAVAILABLE", tuple(coefficients), objective, force_error, moment_error, iteration, evaluations, "bounded outer solve did not find an improving valid trial")
        coefficients, (trial, residual, force_error, moment_error, objective) = accepted
        if max(force_error, moment_error) <= NORMALIZED_WRENCH_TOLERANCE:
            return BodySupportSolution("AVAILABLE", tuple(float(v) for v in coefficients), objective, force_error, moment_error, iteration, evaluations)
    return BodySupportSolution("UNAVAILABLE", tuple(float(v) for v in coefficients), objective, force_error, moment_error, maximum_iterations, evaluations, "bounded outer solve did not converge")


__all__ = [
    "BodyDelta",
    "BodySupportSolution",
    "COEFFICIENTS",
    "COEFFICIENT_COUNT",
    "ContactWrenchSolution",
    "CoordinatorSample",
    "FRICTION_COEFFICIENT",
    "NORMALIZED_WRENCH_TOLERANCE",
    "SCHEMA",
    "TrialEvaluation",
    "coordinator_policy",
    "periodic_body_delta",
    "solve_body_support_trajectory",
    "solve_contact_wrench",
]
