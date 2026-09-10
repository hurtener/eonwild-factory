"""Deterministic shared coordinates for exact-LBS planted contact.

This module owns numerical policy only.  The caller owns source FK/LBS, hard
ROM/reach/floor gates, and the behavior's declared contact intervals.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable

import numpy as np

from ..errors import ContractError
from .minimax_contact import minimum_enclosing_residual_ball


JOINT_CONTACT_POLICY_ID = "source_joint_contact_minimax.v1"
LOADED_MATERIAL_TOLERANCE_M = 0.0002
_MINIMUM_SKIN_GAP_M = 0.0001
_IK_RESIDUAL_TOLERANCE_M = 0.001
_UNREACHABLE_EXTENSION_TOLERANCE_M = 0.001
_ARTICULATION_TOLERANCE_DEGREES = 1e-8
_COUNTERROTATION_BOUNDS_DEGREES = (-45.0, 45.0)
_ANGLE_STEP_DEGREES = 0.01
_TARGET_STEP_M = 1e-5
_MAX_GAUSS_NEWTON_ITERATIONS = 18


@dataclass(frozen=True)
class JointContactTrial:
    material_errors_m: np.ndarray
    material_target_points_m: np.ndarray
    minimum_skin_gap_m: float
    ik_residual_m: float
    unreachable_extension_m: float
    articulation_violation_degrees: float
    solved_upstream_pitch_degrees: float


@dataclass(frozen=True)
class JointContactSolution:
    # authored pitch input, distal counterrotation, forward and up target shift
    coordinates: np.ndarray
    trial: JointContactTrial


def _admit_trial(value: JointContactTrial) -> None:
    errors = np.asarray(value.material_errors_m, dtype=float)
    targets = np.asarray(value.material_target_points_m, dtype=float)
    if errors.ndim != 2 or errors.shape[1] != 3 or errors.shape != targets.shape:
        raise ContractError("joint contact trial requires matching Nx3 material arrays")
    numeric = (
        value.minimum_skin_gap_m,
        value.ik_residual_m,
        value.unreachable_extension_m,
        value.articulation_violation_degrees,
        value.solved_upstream_pitch_degrees,
    )
    if len(errors) < 3 or not np.isfinite(errors).all() or not np.isfinite(targets).all() or not all(math.isfinite(float(v)) for v in numeric):
        raise ContractError("joint contact trial is incomplete or non-finite")


def _unique_material_rows(value: JointContactTrial) -> np.ndarray:
    """Remove coincident seam duplicates from the least-squares objective.

    Every original row remains present in the final max-error gate.
    """
    _admit_trial(value)
    chosen = []
    seen = set()
    for index, point in enumerate(np.asarray(value.material_target_points_m)):
        key = tuple(np.round(point, 12))
        if key not in seen:
            chosen.append(index)
            seen.add(key)
    return np.asarray(chosen, dtype=int)


def _hard_feasible(value: JointContactTrial) -> bool:
    return (
        value.minimum_skin_gap_m >= _MINIMUM_SKIN_GAP_M
        and value.ik_residual_m <= _IK_RESIDUAL_TOLERANCE_M
        and value.unreachable_extension_m <= _UNREACHABLE_EXTENSION_TOLERANCE_M
        and value.articulation_violation_degrees <= _ARTICULATION_TOLERANCE_DEGREES
    )


def _max_error(value: JointContactTrial) -> float:
    _admit_trial(value)
    return float(np.linalg.norm(value.material_errors_m, axis=1).max())


def _hard_violation(value: JointContactTrial) -> np.ndarray:
    """Return normalized positive hard-gate violations in a fixed order."""
    raw = np.asarray(
        (
            _MINIMUM_SKIN_GAP_M - value.minimum_skin_gap_m,
            value.ik_residual_m - _IK_RESIDUAL_TOLERANCE_M,
            value.unreachable_extension_m - _UNREACHABLE_EXTENSION_TOLERANCE_M,
            value.articulation_violation_degrees - _ARTICULATION_TOLERANCE_DEGREES,
        ),
        dtype=float,
    )
    scales = np.asarray(
        (
            _MINIMUM_SKIN_GAP_M,
            _IK_RESIDUAL_TOLERANCE_M,
            _UNREACHABLE_EXTENSION_TOLERANCE_M,
            _ARTICULATION_TOLERANCE_DEGREES,
        ),
        dtype=float,
    )
    return np.maximum(raw, 0.0) / scales


def _trial_merit(value: JointContactTrial) -> tuple[object, ...]:
    """Order trials by hard feasibility, then violation, then material error."""
    violation = _hard_violation(value)
    return (
        0 if _hard_feasible(value) else 1,
        float(violation.max()),
        float(violation.sum()),
        tuple(float(item) for item in violation),
        _max_error(value),
    )


def _bounded_stencil(
    evaluate: Callable[[np.ndarray], JointContactTrial],
    x: np.ndarray,
    coordinate: int,
    step: float,
    base: JointContactTrial,
) -> tuple[JointContactTrial, JointContactTrial, float, float]:
    """Evaluate a finite-difference stencil without leaving the known domain."""
    if coordinate == 1:
        lower, upper = _COUNTERROTATION_BOUNDS_DEGREES
        minus_step = min(step, max(0.0, float(x[coordinate] - lower)))
        plus_step = min(step, max(0.0, float(upper - x[coordinate])))
    else:
        minus_step = plus_step = step

    if plus_step:
        plus = x.copy()
        plus[coordinate] += plus_step
        plus_trial = evaluate(plus)
        _admit_trial(plus_trial)
    else:
        plus_trial = base
    if minus_step:
        minus = x.copy()
        minus[coordinate] -= minus_step
        minus_trial = evaluate(minus)
        _admit_trial(minus_trial)
    else:
        minus_trial = base
    return plus_trial, minus_trial, plus_step, minus_step


def _finite_difference(
    plus: np.ndarray,
    minus: np.ndarray,
    plus_step: float,
    minus_step: float,
) -> np.ndarray:
    """Differentiate central, asymmetric, or one-sided bounded samples."""
    if plus_step and minus_step:
        return (plus - minus) / (plus_step + minus_step)
    if plus_step:
        return (plus - minus) / plus_step
    if minus_step:
        return (plus - minus) / minus_step
    return np.zeros_like(plus, dtype=float)


def solve_fixed_authored_pitch(
    evaluate: Callable[[np.ndarray], JointContactTrial],
    *,
    authored_pitch_degrees: float,
    seed: Iterable[float] = (0.0, 0.0, 0.0),
) -> JointContactSolution:
    """Fit counterrotation and planar target shift for one pitch input."""
    tail = np.asarray(tuple(seed), dtype=float)
    if tail.shape != (3,) or not np.isfinite(tail).all() or not math.isfinite(authored_pitch_degrees):
        raise ContractError("joint contact solve requires finite coordinates")
    x = np.r_[float(authored_pitch_degrees), tail]
    scale = np.asarray([5.0, 0.01, 0.01])
    steps = np.asarray([_ANGLE_STEP_DEGREES, _TARGET_STEP_M, _TARGET_STEP_M])
    best = evaluate(x)
    _admit_trial(best)
    for _ in range(_MAX_GAUSS_NEWTON_ITERATIONS):
        unique = _unique_material_rows(best)
        columns = []
        if _hard_feasible(best):
            residual = np.asarray(best.material_errors_m)[unique].reshape(-1)
            for local, coordinate in enumerate((1, 2, 3)):
                p, m, plus_step, minus_step = _bounded_stencil(
                    evaluate, x, coordinate, steps[local], best
                )
                columns.append(
                    _finite_difference(
                        np.asarray(p.material_errors_m)[unique].reshape(-1),
                        np.asarray(m.material_errors_m)[unique].reshape(-1),
                        plus_step,
                        minus_step,
                    )
                )
        else:
            # Restore the callback's hard gates before optimizing material
            # residuals.  This uses the same bounded coordinates and line
            # search as the material solve, so a near-boundary GN step can
            # continue to an actually evaluated feasible trial.
            residual = _hard_violation(best)
            for local, coordinate in enumerate((1, 2, 3)):
                p, m, plus_step, minus_step = _bounded_stencil(
                    evaluate, x, coordinate, steps[local], best
                )
                columns.append(
                    _finite_difference(
                        _hard_violation(p),
                        _hard_violation(m),
                        plus_step,
                        minus_step,
                    )
                )
        jacobian = np.column_stack(columns)
        scaled = jacobian * scale[None, :]
        delta = np.linalg.lstsq(scaled, -residual, rcond=1e-6)[0]
        delta = np.clip(delta, -1.0, 1.0)
        accepted = False
        for fraction in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625):
            candidate = x.copy()
            candidate[1:] += fraction * delta * scale
            candidate[1] = float(np.clip(candidate[1], *_COUNTERROTATION_BOUNDS_DEGREES))
            trial = evaluate(candidate)
            _admit_trial(trial)
            if _trial_merit(trial) < _trial_merit(best):
                x, best, accepted = candidate, trial, True
                break
        if not accepted:
            break

    # Recenter the exact three-dimensional minimum enclosing residual ball
    # through the available planar translations. Duplicated seam rows are
    # removed by the minimax utility and every original row is regated below.
    for _ in range(4):
        ball = minimum_enclosing_residual_ball(best.material_errors_m)
        columns = []
        for coordinate in (2, 3):
            p, m, plus_step, minus_step = _bounded_stencil(
                evaluate, x, coordinate, _TARGET_STEP_M, best
            )
            columns.append(
                _finite_difference(
                    np.asarray(p.material_errors_m).mean(axis=0),
                    np.asarray(m.material_errors_m).mean(axis=0),
                    plus_step,
                    minus_step,
                )
            )
        translation_jacobian = np.column_stack(columns)
        shift = np.linalg.lstsq(
            translation_jacobian, -np.asarray(ball.center_m), rcond=1e-10
        )[0]
        candidate = x.copy()
        candidate[2:4] += shift
        trial = evaluate(candidate)
        _admit_trial(trial)
        if _trial_merit(trial) < _trial_merit(best):
            x, best = candidate, trial
        else:
            break
    frozen = np.array(x, copy=True); frozen.setflags(write=False)
    return JointContactSolution(frozen, best)


def solve_loaded_contact_controls(
    evaluate: Callable[[np.ndarray], JointContactTrial],
    *,
    declared_pitch_degrees: float,
) -> JointContactSolution:
    """Preserve the largest feasible authored pitch under exact final gates."""
    if not math.isfinite(declared_pitch_degrees):
        raise ContractError("loaded joint contact pitch must be finite")
    pitches = [float(declared_pitch_degrees)]
    candidate = math.floor(float(declared_pitch_degrees) / 2.0) * 2.0
    while candidate >= -20.0:
        if not math.isclose(candidate, pitches[-1], rel_tol=0, abs_tol=1e-12):
            pitches.append(candidate)
        candidate -= 2.0
    solved = []
    seed = np.zeros(3)
    first_feasible = None
    for pitch in pitches:
        value = solve_fixed_authored_pitch(
            evaluate, authored_pitch_degrees=pitch, seed=seed
        )
        solved.append(value)
        seed = np.asarray(value.coordinates[1:])
        if _hard_feasible(value.trial) and _max_error(value.trial) <= LOADED_MATERIAL_TOLERANCE_M:
            first_feasible = len(solved) - 1
            break
    if first_feasible is None:
        return min(solved, key=lambda value: (_max_error(value.trial), abs(value.trial.solved_upstream_pitch_degrees-declared_pitch_degrees)))
    if first_feasible == 0:
        return solved[0]
    low = pitches[first_feasible]
    high = pitches[first_feasible - 1]
    best = solved[first_feasible]
    for _ in range(9):
        mid = 0.5 * (low + high)
        value = solve_fixed_authored_pitch(
            evaluate,
            authored_pitch_degrees=mid,
            seed=best.coordinates[1:],
        )
        if _hard_feasible(value.trial) and _max_error(value.trial) <= LOADED_MATERIAL_TOLERANCE_M:
            low, best = mid, value
        else:
            high = mid
    return best


def quintic_boundary_transport(
    u: float,
    start: Iterable[float],
    start_velocity_per_u: Iterable[float],
    start_acceleration_per_u2: Iterable[float],
    end: Iterable[float],
    end_velocity_per_u: Iterable[float],
    end_acceleration_per_u2: Iterable[float],
) -> np.ndarray:
    """Quintic Hermite transport preserving both source-derived endpoint jets."""
    if not math.isfinite(u) or not 0.0 <= u <= 1.0:
        raise ContractError("joint contact transport phase must be in [0,1]")
    p0, v0, a0, p1, v1, a1 = (
        np.asarray(tuple(value), dtype=float)
        for value in (start, start_velocity_per_u, start_acceleration_per_u2,
                      end, end_velocity_per_u, end_acceleration_per_u2)
    )
    if any(value.shape != p0.shape or not np.isfinite(value).all()
           for value in (p0, v0, a0, p1, v1, a1)):
        raise ContractError("joint contact transport requires matching finite vectors")
    c0, c1, c2 = p0, v0, 0.5 * a0
    rhs = np.stack((p1-c0-c1-c2, v1-c1-2*c2, a1-2*c2))
    c3, c4, c5 = np.linalg.solve(
        np.asarray([[1.,1.,1.],[3.,4.,5.],[6.,12.,20.]]), rhs
    )
    return c0 + c1*u + c2*u*u + c3*u**3 + c4*u**4 + c5*u**5
