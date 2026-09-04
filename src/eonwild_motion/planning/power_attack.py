"""Power-attack vertical slice: the first true dynamics pass in V9.

Pipeline (authored intent constrained by dynamics, never physics-as-director):

.. code-block:: text

    MotionIntent (bite variant, target, urgency, condition)
    + BodyInstanceProfile (admitted mass model)
    + CapacityProfile (review-labeled actuation envelope)
            ↓
    Ballistic COM plan (whole-body COM, takeoff/landing impulses)
            ↓
    Takeoff + landing feasibility (force / friction / power / work)
            ↓
    airborne variant  OR  grounded_lunge fallback (mandatory)
            ↓
    Root-from-COM solve (p_root = c − R·c_rel) + continuity packet
            ↓
    Receipt: hashes, margins, limiting factor, fallback branch

Normalized profiles (no absolute mass) exercise only trajectory
bookkeeping and report physics unevaluated — exactly like the stationary
slice. Absolute claims require an absolute-enabled fixture.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..contracts.v9_models import BodyInstanceProfile, canonical_hash
from ..dynamics.ballistic import (
    BallisticRequest,
    plan_ballistic_com,
    verify_ballistic_samples,
)
from ..dynamics.capacity import (
    CapacityProfile,
    assess_arrest,
    assess_landing,
    assess_takeoff,
    decide_attack_variant,
)
from ..dynamics.centroidal import _finite, _quat, _vec3, solve_root_from_com
from ..dynamics.transition import ContinuityPacket
from ..errors import ContractError

SCHEMA = "eonwild.motion.v9.power-attack-plan.v1"


@dataclass(frozen=True)
class PowerAttackRequest:
    body: BodyInstanceProfile
    capacity: CapacityProfile
    launch_com_m: tuple[float, float, float]
    launch_velocity_mps: tuple[float, float, float]
    landing_com_m: tuple[float, float, float]
    stance_time_s: float = 0.28
    preload_velocity_mps: tuple[float, float, float] = (0.0, 0.0, 0.0)
    bite_variant: str = "committed"
    gravity_mps2: float = 9.81
    sample_hz: int = 120


def total_mass_or_none(body: BodyInstanceProfile) -> float | None:
    return body.total_mass_kg if body.absolute_dynamics_enabled else None


def plan_power_attack(request: PowerAttackRequest) -> dict[str, Any]:
    """Plan one power attack; infeasible airborne falls back to grounded lunge."""
    mass = total_mass_or_none(request.body)
    ballistic = plan_ballistic_com(
        BallisticRequest(
            launch_com_m=request.launch_com_m,
            launch_velocity_mps=request.launch_velocity_mps,
            landing_com_m=request.landing_com_m,
            total_mass_kg=mass,
            preload_velocity_mps=request.preload_velocity_mps,
            gravity_mps2=request.gravity_mps2,
            sample_hz=request.sample_hz,
        )
    )
    if ballistic.variant != "airborne":
        return _receipt(request, ballistic, None, None, None, "grounded_lunge", "trajectory")

    verification = verify_ballistic_samples(ballistic.samples, gravity_mps2=request.gravity_mps2)
    if verification["verdict"] != "PASS":
        return _receipt(request, ballistic, None, None, None, "grounded_lunge", "integration")

    if mass is None:
        # Normalized profile: trajectory bookkeeping only, no force claims.
        return _receipt(request, ballistic, None, None, None, "airborne_normalized", None)

    takeoff = assess_takeoff(
        total_mass_kg=mass,
        takeoff_impulse_ns=ballistic.takeoff_impulse_ns or (0.0, 0.0, 0.0),
        stance_time_s=request.stance_time_s,
        capacity=request.capacity,
        preload_velocity_mps=request.preload_velocity_mps,
        gravity_mps2=request.gravity_mps2,
    )
    impact = np.asarray(ballistic.samples[-1]["com_velocity_mps"], dtype=float)
    landing = assess_landing(
        total_mass_kg=mass,
        impact_velocity_mps=tuple(float(v) for v in impact),
        capacity=request.capacity,
        gravity_mps2=request.gravity_mps2,
    )
    arrest = assess_arrest(
        horizontal_speed_mps=float(np.linalg.norm(impact[[0, 2]])),
        capacity=request.capacity,
        gravity_mps2=request.gravity_mps2,
    )
    verdict = decide_attack_variant(takeoff, landing, arrest)
    return _receipt(request, ballistic, takeoff, landing, arrest, verdict.variant, verdict.limiting_factor)


def _receipt(
    request: PowerAttackRequest,
    ballistic: Any,
    takeoff: Mapping[str, Any] | None,
    landing: Mapping[str, Any] | None,
    arrest: Mapping[str, Any] | None,
    variant: str,
    limiting_factor: str | None,
) -> dict[str, Any]:
    body = {
        "schema": SCHEMA,
        "variant": variant,
        "bite_variant": request.bite_variant,
        "body_profile_id": request.body.profile_id,
        "mass_mode": request.body.mass_mode,
        "absolute_dynamics_enabled": request.body.absolute_dynamics_enabled,
        "capacity_profile_id": request.capacity.profile_id,
        "capacity_status": request.capacity.status,
        "ballistic_plan_sha256": ballistic.plan_sha256,
        "flight_time_s": ballistic.flight_time_s,
        "takeoff_impulse_ns": list(ballistic.takeoff_impulse_ns) if ballistic.takeoff_impulse_ns else None,
        "landing_impulse_ns": list(ballistic.landing_impulse_ns) if ballistic.landing_impulse_ns else None,
        "takeoff": dict(takeoff) if takeoff else None,
        "landing": dict(landing) if landing else None,
        "arrest": dict(arrest) if arrest else None,
        "limiting_factor": limiting_factor,
        "physics_evaluated": bool(takeoff and landing and arrest),
    }
    return {**body, "plan_sha256": canonical_hash(body)}


def solve_attack_root_track(
    com_samples: Sequence[Mapping[str, Any]],
    *,
    root_rotations: Sequence[Sequence[Sequence[float]]],
    com_relative_to_root: Sequence[float],
) -> list[dict[str, Any]]:
    """Root track reconstructed from the COM plan (never the reverse)."""
    if len(com_samples) != len(root_rotations):
        raise ContractError("root solve needs one rotation per COM sample")
    track = []
    for sample, rotation in zip(com_samples, root_rotations):
        try:
            rot = np.asarray(rotation, dtype=float).reshape(3, 3)
        except (TypeError, ValueError) as exc:
            raise ContractError(f"root rotation must be a 3x3 matrix: {exc}") from exc
        track.append(
            {
                "time_s": float(sample["time_s"]),
                "root_position_m": list(
                    solve_root_from_com(sample["com_m"], rot, com_relative_to_root)
                ),
            }
        )
    return track


def attack_entry_packet(
    *,
    root_position_m: Sequence[float],
    root_orientation: Sequence[float],
    linear_velocity_mps: Sequence[float],
    angular_momentum: Sequence[float],
    contacts: Mapping[str, str],
    tail_angle_rad: float = 0.0,
    tail_angular_velocity_radps: float = 0.0,
    target_commitment: str | None = None,
) -> ContinuityPacket:
    """Boundary packet entering the attack (carries pre-launch momentum)."""
    _vec3(root_position_m, label="root_position_m")
    _vec3(linear_velocity_mps, label="linear_velocity_mps")
    _vec3(angular_momentum, label="angular_momentum")
    orientation = _quat(np.asarray(root_orientation, dtype=float), label="root_orientation")
    return ContinuityPacket(
        root_position_m=tuple(float(v) for v in root_position_m),
        root_orientation=tuple(float(v) for v in orientation),
        linear_velocity_mps=tuple(float(v) for v in linear_velocity_mps),
        angular_momentum_kg_m2ps=tuple(float(v) for v in angular_momentum),
        contacts=dict(contacts),
        tail_angle_rad=_finite(tail_angle_rad, label="tail_angle_rad"),
        tail_angular_velocity_radps=_finite(tail_angular_velocity_radps, label="tail_velocity"),
        target_commitment=target_commitment,
        interruptible=False,
    )


__all__ = [
    "PowerAttackRequest",
    "attack_entry_packet",
    "plan_power_attack",
    "solve_attack_root_track",
    "total_mass_or_none",
]
