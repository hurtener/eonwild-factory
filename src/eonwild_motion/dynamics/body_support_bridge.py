"""Adapter from final solved skin geometry to centroidal support trials.

The adapter owns only timeline alignment.  Its geometry callback must run the
same final semantic foot-frame law and full-skin checks used for emission.
Material anchors are already frozen when this adapter is constructed; the
adapter verifies their digest on every callback and never recalibrates them.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from .body_support_coordinator import (
    BodyDelta,
    CoordinatorSample,
    TrialEvaluation,
    TrialEvaluator,
    TERMINAL_PARTICLE_TOLERANCE_M,
    periodic_body_delta,
)
from .surface_mass import (
    prepare_surface_mass_vertex_evaluator,
    surface_mass_interval_momentum,
)


SAMPLE_SEMANTICS = "full_lbs_interval_midpoints.v1"


@dataclass(frozen=True)
class FinalGeometrySample:
    """One exact result from the integration-owned final geometry evaluator.

    ``final_geometry_passed`` is evidence about this sample only.  The caller
    may set it true only after applying the final semantic foot-frame law and
    measuring its complete emitted skin.  ``support_points_m`` must be the
    active material contact patch from that same posed skin.
    """

    time_s: float
    joint_world_matrices: Mapping[str, Sequence[Sequence[float]]]
    support_points_m: tuple[tuple[float, float, float], ...]
    frozen_anchor_sha256: str
    final_geometry_passed: bool


FinalGeometryEvaluator = Callable[[BodyDelta, float], FinalGeometrySample]


def _vector3(value: Sequence[float], label: str) -> np.ndarray:
    result = np.asarray(value, dtype=np.float64)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractError(f"{label} must be a finite three-vector")
    return result


def _validate_geometry_sample(
    sample: FinalGeometrySample,
    *,
    expected_time_s: float,
    frozen_anchor_sha256: str,
) -> None:
    if not isinstance(sample, FinalGeometrySample):
        raise ContractError("body-support bridge requires final geometry samples")
    if not math.isclose(sample.time_s, expected_time_s, rel_tol=0.0, abs_tol=1e-12):
        raise ContractError("final geometry sample time differs from requested time")
    if not sample.final_geometry_passed:
        raise ContractError("body-support trial did not pass final full-skin geometry")
    if sample.frozen_anchor_sha256 != frozen_anchor_sha256:
        raise ContractError("body-support trial changed its frozen material anchors")
    points = np.asarray(sample.support_points_m, dtype=np.float64)
    if points.ndim != 2 or points.shape[1:] != (3,) or not np.isfinite(points).all():
        raise ContractError("final geometry support patch must contain finite three-vectors")


def _translated_vertex_state(
    state: Mapping[str, object], translation_m: np.ndarray
) -> dict[str, object]:
    positions = np.asarray(state.get("world_positions_m"), dtype=np.float64)
    masses = np.asarray(state.get("vertex_mass_kg"), dtype=np.float64)
    com = np.asarray(state.get("com_m"), dtype=np.float64)
    if (
        positions.ndim != 2
        or positions.shape[1:] != (3,)
        or masses.shape != (len(positions),)
        or com.shape != (3,)
        or not np.isfinite(positions).all()
        or not np.isfinite(masses).all()
        or not np.isfinite(com).all()
    ):
        raise ContractError("surface-mass vertex state is invalid")
    return {
        **state,
        "world_positions_m": positions + translation_m,
        "vertex_mass_kg": masses.copy(),
        "com_m": com + translation_m,
    }


def build_surface_mass_trial_evaluator(
    *,
    source_bytes: bytes,
    surface_mass_profile: Mapping[str, object],
    duration_s: float,
    body_height_m: float,
    sample_count: int,
    cycle_travel_m: Sequence[float],
    terminal_particle_tolerance_m: float,
    frozen_anchor_sha256: str,
    evaluate_final_geometry: FinalGeometryEvaluator,
) -> TrialEvaluator:
    """Build a coefficient evaluator on one aligned periodic particle clock.

    Boundary full-LBS particle states provide finite-interval momentum.  The
    active support patch is evaluated independently at each corresponding
    interval midpoint, after the same final geometry law.  For travelling
    clips, the actual terminal full skin must match phase zero plus travel under
    the versioned final skin-loop tolerance before it enters the last interval.
    """

    source = bytes(source_bytes)
    duration = float(duration_s)
    height = float(body_height_m)
    if not math.isfinite(duration) or duration <= 0:
        raise ContractError("body-support bridge duration must be positive")
    if not math.isfinite(height) or height <= 0:
        raise ContractError("body-support bridge body height must be positive")
    if type(sample_count) is not int or sample_count < 5:
        raise ContractError("body-support bridge requires at least five intervals")
    if (
        not isinstance(frozen_anchor_sha256, str)
        or len(frozen_anchor_sha256) != 64
        or any(character not in "0123456789abcdef" for character in frozen_anchor_sha256)
    ):
        raise ContractError("body-support bridge requires a frozen anchor digest")
    if not callable(evaluate_final_geometry):
        raise ContractError("body-support bridge requires a final geometry evaluator")
    travel = _vector3(cycle_travel_m, "cycle travel")
    terminal_tolerance = float(terminal_particle_tolerance_m)
    if not math.isfinite(terminal_tolerance) or not math.isclose(
        terminal_tolerance,
        TERMINAL_PARTICLE_TOLERANCE_M,
        rel_tol=0.0,
        abs_tol=1e-15,
    ):
        raise ContractError(
            "body-support terminal particle tolerance differs from versioned policy"
        )
    try:
        total_mass = float(surface_mass_profile["mass_model"]["total_mass_kg"])  # type: ignore[index]
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("surface-mass profile has no bound total mass") from exc
    if not math.isfinite(total_mass) or total_mass <= 0:
        raise ContractError("surface-mass profile total mass must be positive")
    dt = duration / sample_count
    vertex_evaluator = prepare_surface_mass_vertex_evaluator(
        source, surface_mass_profile
    )

    def evaluate(coefficients: tuple[float, ...]) -> TrialEvaluation:
        boundary_states: list[Mapping[str, object]] = []
        for index in range(sample_count):
            time_s = index * dt
            geometry = evaluate_final_geometry(
                periodic_body_delta(coefficients, time_s, duration), time_s
            )
            _validate_geometry_sample(
                geometry,
                expected_time_s=time_s,
                frozen_anchor_sha256=frozen_anchor_sha256,
            )
            state = vertex_evaluator(geometry.joint_world_matrices)
            state_mass = float(state.get("total_mass_kg", math.nan))
            if not math.isclose(state_mass, total_mass, rel_tol=0.0, abs_tol=1e-10):
                raise ContractError("surface-mass trial changed its bound total mass")
            boundary_states.append(state)

        terminal_geometry = evaluate_final_geometry(
            periodic_body_delta(coefficients, duration, duration), duration
        )
        _validate_geometry_sample(
            terminal_geometry,
            expected_time_s=duration,
            frozen_anchor_sha256=frozen_anchor_sha256,
        )
        terminal_state = vertex_evaluator(terminal_geometry.joint_world_matrices)
        terminal_mass = float(terminal_state.get("total_mass_kg", math.nan))
        if not math.isclose(terminal_mass, total_mass, rel_tol=0.0, abs_tol=1e-10):
            raise ContractError("surface-mass trial changed its bound total mass")
        next_cycle_zero = _translated_vertex_state(boundary_states[0], travel)
        actual_terminal = np.asarray(
            terminal_state.get("world_positions_m"), dtype=np.float64
        )
        expected_terminal = np.asarray(
            next_cycle_zero.get("world_positions_m"), dtype=np.float64
        )
        if (
            actual_terminal.shape != expected_terminal.shape
            or actual_terminal.ndim != 2
            or actual_terminal.shape[1:] != (3,)
            or not np.isfinite(actual_terminal).all()
            or not np.isfinite(expected_terminal).all()
        ):
            raise ContractError("terminal full-LBS particle states are incompatible")
        maximum_terminal_error = float(
            np.linalg.norm(actual_terminal - expected_terminal, axis=1).max(
                initial=0.0
            )
        )
        if maximum_terminal_error > terminal_tolerance:
            raise ContractError(
                "terminal full-LBS particles differ from phase zero plus cycle travel: "
                f"error_m={maximum_terminal_error!r} "
                f"tolerance_m={terminal_tolerance!r}"
            )
        samples: list[CoordinatorSample] = []
        for index in range(sample_count):
            midpoint_s = (index + 0.5) * dt
            geometry = evaluate_final_geometry(
                periodic_body_delta(coefficients, midpoint_s, duration), midpoint_s
            )
            _validate_geometry_sample(
                geometry,
                expected_time_s=midpoint_s,
                frozen_anchor_sha256=frozen_anchor_sha256,
            )
            midpoint_state = vertex_evaluator(geometry.joint_world_matrices)
            midpoint_mass = float(midpoint_state.get("total_mass_kg", math.nan))
            if not math.isclose(midpoint_mass, total_mass, rel_tol=0.0, abs_tol=1e-10):
                raise ContractError("surface-mass trial changed its bound total mass")
            after = (
                boundary_states[index + 1]
                if index + 1 < sample_count
                else terminal_state
            )
            momentum = surface_mass_interval_momentum(
                boundary_states[index], after, dt
            )
            interval_com = _vector3(momentum["sample_com_m"], "interval COM")
            sample_com = _vector3(midpoint_state.get("com_m"), "midpoint COM")
            linear_momentum = _vector3(
                momentum["linear_momentum_kg_mps"], "linear momentum"
            )
            angular_momentum = _vector3(
                momentum["centroidal_angular_momentum_kg_m2ps"],
                "centroidal angular momentum",
            )
            # surface_mass_interval_momentum measures H about the average of
            # its endpoint particles.  Shift that same particle momentum to
            # the exact final-law midpoint COM so body and support geometry
            # share one post-pose frame.
            angular_momentum += np.cross(
                interval_com - sample_com, linear_momentum
            )
            samples.append(
                CoordinatorSample(
                    time_s=midpoint_s,
                    total_mass_kg=total_mass,
                    com_m=tuple(float(value) for value in sample_com),
                    linear_momentum_kg_mps=tuple(
                        float(value) for value in linear_momentum
                    ),
                    angular_momentum_kg_m2ps=tuple(
                        float(value) for value in angular_momentum
                    ),
                    support_points_m=tuple(
                        tuple(float(value) for value in point)
                        for point in geometry.support_points_m
                    ),
                    frozen_anchor_sha256=frozen_anchor_sha256,
                    final_geometry_passed=True,
                )
            )
        return TrialEvaluation(
            duration_s=duration,
            body_height_m=height,
            samples=tuple(samples),
            sample_semantics=SAMPLE_SEMANTICS,
        )

    return evaluate


__all__ = [
    "FinalGeometryEvaluator",
    "FinalGeometrySample",
    "SAMPLE_SEMANTICS",
    "build_surface_mass_trial_evaluator",
]
