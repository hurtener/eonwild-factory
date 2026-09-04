"""Ballistic whole-body COM planning with impulse accounting.

Engine contract (sections 9-10): the *whole-body COM* is ballistic in
flight — never the pelvis curve. Takeoff and landing impulses are measured
(``J = M Δv``); the planner may not invent or delete net external impulse.
Infeasible airborne requests select a grounded fallback instead of emitting
an unphysical flight.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

import numpy as np

from ..contracts.v9_models import canonical_hash
from ..errors import ContractError
from .centroidal import GRAVITY_MPS2, _finite, _vec3

SCHEMA = "eonwild.motion.v9.ballistic-com-plan.v1"


@dataclass(frozen=True)
class BallisticRequest:
    launch_com_m: tuple[float, float, float]
    launch_velocity_mps: tuple[float, float, float]
    landing_com_m: tuple[float, float, float] | None = None
    apex_rise_m: float | None = None
    total_mass_kg: float | None = None
    preload_velocity_mps: tuple[float, float, float] = (0.0, 0.0, 0.0)
    post_landing_velocity_mps: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gravity_mps2: float = 9.81
    sample_hz: int = 120


@dataclass(frozen=True)
class BallisticPlan:
    variant: str  # "airborne" or "grounded_fallback"
    flight_time_s: float
    samples: tuple[dict[str, Any], ...]
    takeoff_impulse_ns: tuple[float, float, float] | None
    landing_impulse_ns: tuple[float, float, float] | None
    takeoff_speed_mps: float | None
    impact_speed_mps: float | None
    infeasibility: tuple[str, ...]
    plan_sha256: str


def _apex_velocity(apex_rise_m: float, gravity: float) -> float:
    if apex_rise_m <= 0.0:
        raise ContractError("apex rise must be positive for a ballistic plan")
    return math.sqrt(2.0 * gravity * apex_rise_m)


def flight_time(launch_vy: float, delta_y: float, gravity: float) -> float:
    """Flight duration solving ``Δy = vy·T − ½·g·T²``; rejects bad discriminant."""
    discriminant = launch_vy * launch_vy - 2.0 * gravity * delta_y
    if discriminant < 0.0:
        raise ContractError(
            "ballistic discriminant is negative: launch cannot reach landing height"
        )
    return (launch_vy + math.sqrt(discriminant)) / gravity


def plan_ballistic_com(request: BallisticRequest) -> BallisticPlan:
    """Plan a ballistic COM arc; fall back to grounded on infeasibility.

    Feasibility here covers trajectory existence (discriminant, positive
    flight time). Force/capacity feasibility is applied separately by
    :mod:`capacity` and recorded in the receipt — this planner never emits
    an airborne variant it cannot integrate.
    """
    gravity = _finite(request.gravity_mps2, label="gravity")
    if gravity <= 0.0:
        raise ContractError("gravity must be positive")
    sample_hz = int(request.sample_hz)
    if sample_hz < 24:
        raise ContractError("ballistic sample rate must be >= 24 Hz")
    c0 = _vec3(request.launch_com_m, label="launch_com_m")
    v0 = _vec3(request.launch_velocity_mps, label="launch_velocity_mps")
    problems: list[str] = []

    if request.landing_com_m is None:
        raise ContractError("ballistic plan requires a landing COM target")
    c_land = _vec3(request.landing_com_m, label="landing_com_m")
    delta_y = float(c_land[1] - c0[1])
    try:
        duration = flight_time(float(v0[1]), delta_y, gravity)
    except ContractError as exc:
        return _fallback(request, [str(exc)])
    if not math.isfinite(duration) or duration <= 0.0:
        return _fallback(request, ["non-positive ballistic flight time"])

    count = max(2, int(math.ceil(duration * sample_hz)) + 1)
    g_vec = np.array([0.0, -gravity, 0.0])
    samples: list[dict[str, Any]] = []
    for i in range(count):
        t = duration * i / (count - 1)
        pos = c0 + v0 * t + 0.5 * g_vec * t * t
        vel = v0 + g_vec * t
        samples.append(
            {
                "time_s": t,
                "com_m": [float(v) for v in pos],
                "com_velocity_mps": [float(v) for v in vel],
            }
        )
    impact_vel = v0 + g_vec * duration
    mass = request.total_mass_kg
    takeoff_j: tuple[float, float, float] | None = None
    landing_j: tuple[float, float, float] | None = None
    if mass is not None:
        preload = _vec3(request.preload_velocity_mps, label="preload_velocity_mps")
        post = _vec3(request.post_landing_velocity_mps, label="post_landing_velocity_mps")
        takeoff_j = tuple(float(v) for v in mass * (v0 - preload))
        landing_j = tuple(float(v) for v in mass * (post - impact_vel))
    body = {
        "schema": SCHEMA,
        "variant": "airborne",
        "gravity_mps2": gravity,
        "launch_com_m": [float(v) for v in c0],
        "launch_velocity_mps": [float(v) for v in v0],
        "landing_com_m": [float(v) for v in c_land],
        "flight_time_s": duration,
        "takeoff_impulse_ns": list(takeoff_j) if takeoff_j else None,
        "landing_impulse_ns": list(landing_j) if landing_j else None,
        "samples": samples,
        "infeasibility": [],
    }
    return BallisticPlan(
        variant="airborne",
        flight_time_s=duration,
        samples=tuple(samples),
        takeoff_impulse_ns=takeoff_j,
        landing_impulse_ns=landing_j,
        takeoff_speed_mps=float(np.linalg.norm(v0)),
        impact_speed_mps=float(np.linalg.norm(impact_vel)),
        infeasibility=tuple(problems),
        plan_sha256=canonical_hash(body),
    )


def _fallback(request: BallisticRequest, reasons: list[str]) -> BallisticPlan:
    body = {
        "schema": SCHEMA,
        "variant": "grounded_fallback",
        "gravity_mps2": float(request.gravity_mps2),
        "samples": [],
        "infeasibility": list(reasons),
    }
    return BallisticPlan(
        variant="grounded_fallback",
        flight_time_s=0.0,
        samples=(),
        takeoff_impulse_ns=None,
        landing_impulse_ns=None,
        takeoff_speed_mps=None,
        impact_speed_mps=None,
        infeasibility=tuple(reasons),
        plan_sha256=canonical_hash(body),
    )


def required_horizontal_launch_velocity(
    horizontal_displacement_m: Sequence[float],
    flight_time_s: float,
) -> tuple[float, float]:
    """Predicted horizontal launch velocity for a target-relative displacement."""
    duration = _finite(flight_time_s, label="flight_time_s")
    if duration <= 0.0:
        raise ContractError("flight time must be positive")
    disp = np.asarray([_finite(float(v), label="displacement") for v in horizontal_displacement_m], dtype=float)
    if disp.shape != (2,):
        raise ContractError("horizontal displacement must contain exactly two values")
    return tuple(float(v) for v in disp / duration)


def verify_ballistic_samples(
    samples: Sequence[Mapping[str, Any]],
    *,
    gravity_mps2: float = 9.81,
    tolerance_m: float = 1e-6,
) -> dict[str, Any]:
    """Independently verify samples integrate ballistically within tolerance.

    Returns max position residual and a PASS/FAIL verdict. The actual
    transformed segment COM (not the pelvis curve) is what must satisfy
    this check downstream.
    """
    if len(samples) < 2:
        raise ContractError("ballistic verification needs at least two samples")
    gravity = _finite(gravity_mps2, label="gravity")
    c0 = np.asarray(samples[0]["com_m"], dtype=float)
    v0 = np.asarray(samples[0]["com_velocity_mps"], dtype=float)
    t0 = float(samples[0]["time_s"])
    worst = 0.0
    for sample in samples[1:]:
        t = float(sample["time_s"]) - t0
        expected = c0 + v0 * t + 0.5 * np.array([0.0, -gravity, 0.0]) * t * t
        worst = max(worst, float(np.linalg.norm(np.asarray(sample["com_m"], dtype=float) - expected)))
    return {
        "max_position_residual_m": worst,
        "tolerance_m": tolerance_m,
        "verdict": "PASS" if worst <= tolerance_m else "FAIL",
    }


__all__ = [
    "BallisticPlan",
    "BallisticRequest",
    "flight_time",
    "plan_ballistic_com",
    "required_horizontal_launch_velocity",
    "verify_ballistic_samples",
]
