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


JOINT_CONTACT_POLICY_ID = "source_joint_contact_minimax.v1"
LOADED_MATERIAL_TOLERANCE_M = 0.0002
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
        value.minimum_skin_gap_m >= 0.0001
        and value.ik_residual_m <= 0.001
        and value.unreachable_extension_m <= 0.001
        and value.articulation_violation_degrees <= 1e-8
    )


def _max_error(value: JointContactTrial) -> float:
    _admit_trial(value)
    return float(np.linalg.norm(value.material_errors_m, axis=1).max())


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
        residual = np.asarray(best.material_errors_m)[unique].reshape(-1)
        columns = []
        for local, coordinate in enumerate((1, 2, 3)):
            plus, minus = x.copy(), x.copy()
            plus[coordinate] += steps[local]
            minus[coordinate] -= steps[local]
            p, m = evaluate(plus), evaluate(minus)
            _admit_trial(p); _admit_trial(m)
            columns.append(
                (np.asarray(p.material_errors_m)[unique].reshape(-1)
                 - np.asarray(m.material_errors_m)[unique].reshape(-1))
                / (2 * steps[local])
            )
        jacobian = np.column_stack(columns)
        scaled = jacobian * scale[None, :]
        delta = np.linalg.lstsq(scaled, -residual, rcond=1e-6)[0]
        delta = np.clip(delta, -1.0, 1.0)
        accepted = False
        for fraction in (1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625):
            candidate = x.copy()
            candidate[1:] += fraction * delta * scale
            candidate[1] = float(np.clip(candidate[1], -45.0, 45.0))
            trial = evaluate(candidate)
            _admit_trial(trial)
            if _hard_feasible(trial) and _max_error(trial) < _max_error(best):
                x, best, accepted = candidate, trial, True
                break
        if not accepted:
            break

    # Chebyshev recenter in the two target-translation coordinates.  This is
    # based on extrema, so duplicated seam vertices cannot bias the result.
    for _ in range(4):
        unique = _unique_material_rows(best)
        errors = np.asarray(best.material_errors_m)[unique]
        shift = 0.5 * (errors.max(axis=0) + errors.min(axis=0))
        candidate = x.copy()
        candidate[2] += float(shift[0])
        candidate[3] += float(shift[1])
        trial = evaluate(candidate)
        _admit_trial(trial)
        if _hard_feasible(trial) and _max_error(trial) < _max_error(best):
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
