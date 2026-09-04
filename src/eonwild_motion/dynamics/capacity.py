"""First-pass actuation capacity, strictly separate from passive mass.

Engine contract (section 7.1): mass, COM, inertia, gravity, contacts and
the requested trajectory tell the planner what forces, moments, work,
power and impulses are *required*. They never tell it what the animal can
*produce or absorb*. That lives here, in a review-labeled envelope with
provenance and uncertainty — never inferred from tuning values.

Positive production (launch/takeoff) and negative absorption (landing/
braking) are separately bounded. While capacity values are unresolved or
gameplay hypotheses, absolute capability export stays disabled and the
planner reports normalized bookkeeping only.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from .centroidal import _finite, _vec3

SCHEMA = "eonwild.motion.v9.actuation-capacity.v1"


@dataclass(frozen=True)
class CapacityProfile:
    """Crude but explicit actuation envelope for one body fixture.

    * ``bodyweight_multiple`` — peak total leg force as a multiple of
      bodyweight (steady standing = 1.0).
    * ``friction_coefficient`` — Coulomb mu of the contact interface.
    * ``absorb_distance_m`` — crouch travel available for landing/braking.
    * ``absorb_load_multiple`` — peak tolerable deceleration as a multiple
      of bodyweight during absorption.
    * ``peak_power_w_per_kg`` — sustainable-peak mechanical power density.
    * ``provenance`` / ``status`` — review label; ``provisional`` values may
      exercise planning and fallback logic but never authoritative claims.
    """

    profile_id: str
    bodyweight_multiple: float = 2.5
    friction_coefficient: float = 0.8
    absorb_distance_m: float = 0.6
    absorb_load_multiple: float = 4.0
    peak_power_w_per_kg: float = 25.0
    provenance: str = "v9_first_pass_engineering_prior"
    status: str = "provisional"

    def __post_init__(self) -> None:
        for key in (
            "bodyweight_multiple",
            "friction_coefficient",
            "absorb_distance_m",
            "absorb_load_multiple",
            "peak_power_w_per_kg",
        ):
            value = float(getattr(self, key))
            if not math.isfinite(value) or value <= 0.0:
                raise ContractError(f"capacity {key} must be a positive finite number")


@dataclass(frozen=True)
class FeasibilityVerdict:
    feasible: bool
    variant: str  # "airborne" or "grounded_lunge"
    checks: dict[str, Any]
    limiting_factor: str | None


def assess_takeoff(
    *,
    total_mass_kg: float,
    takeoff_impulse_ns: tuple[float, float, float] | list[float],
    stance_time_s: float,
    capacity: CapacityProfile,
    gravity_mps2: float = 9.81,
) -> dict[str, Any]:
    """Can the fixture produce the takeoff impulse inside the stance time?"""
    mass = _finite(total_mass_kg, label="total_mass_kg")
    stance = _finite(stance_time_s, label="stance_time_s")
    if mass <= 0.0 or stance <= 0.0:
        raise ContractError("takeoff assessment needs positive mass and stance time")
    impulse = _vec3(takeoff_impulse_ns, label="takeoff_impulse_ns")
    horizontal = float(np.linalg.norm(impulse[[0, 2]]))
    vertical = float(impulse[1])
    avg_force = np.asarray(impulse, dtype=float) / stance
    avg_horizontal = float(np.linalg.norm(avg_force[[0, 2]]))
    avg_vertical = float(avg_force[1])
    weight = mass * gravity_mps2
    normal = weight + max(0.0, avg_vertical)
    friction_demand = avg_horizontal / normal if normal > 0 else math.inf
    force_limit = capacity.bodyweight_multiple * weight
    required_peak = float(np.linalg.norm(avg_force)) * 1.5  # shape factor: peak vs average
    power_w = float(np.linalg.norm(avg_force)) * float(np.linalg.norm(impulse / mass)) / 2.0
    power_limit = capacity.peak_power_w_per_kg * mass
    ok_force = required_peak <= force_limit
    ok_friction = friction_demand <= capacity.friction_coefficient
    ok_power = power_w <= power_limit
    return {
        "impulse_magnitude_ns": float(np.linalg.norm(impulse)),
        "horizontal_impulse_ns": horizontal,
        "vertical_impulse_ns": vertical,
        "average_force_n": [float(v) for v in avg_force],
        "required_peak_force_n": required_peak,
        "force_limit_n": force_limit,
        "friction_demand": friction_demand,
        "friction_limit": capacity.friction_coefficient,
        "required_power_w": power_w,
        "power_limit_w": power_limit,
        "force_ok": bool(ok_force),
        "friction_ok": bool(ok_friction),
        "power_ok": bool(ok_power),
        "verdict": "PASS" if (ok_force and ok_friction and ok_power) else "FAIL",
    }


def assess_landing(
    *,
    total_mass_kg: float,
    impact_velocity_mps: tuple[float, float, float] | list[float],
    capacity: CapacityProfile,
    gravity_mps2: float = 9.81,
) -> dict[str, Any]:
    """Can the fixture absorb the landing energy inside its crouch travel?"""
    mass = _finite(total_mass_kg, label="total_mass_kg")
    if mass <= 0.0:
        raise ContractError("landing assessment needs positive mass")
    velocity = _vec3(impact_velocity_mps, label="impact_velocity_mps")
    speed = float(np.linalg.norm(velocity))
    kinetic = 0.5 * mass * speed * speed
    weight = mass * gravity_mps2
    # Constant-deceleration absorption over the available crouch travel.
    required_decel = speed * speed / (2.0 * capacity.absorb_distance_m) if capacity.absorb_distance_m > 0 else math.inf
    allowed_decel = capacity.absorb_load_multiple * gravity_mps2
    settle_work = weight * capacity.absorb_distance_m
    budget = (capacity.absorb_load_multiple * weight) * capacity.absorb_distance_m
    required_work = kinetic + settle_work
    ok_decel = required_decel <= allowed_decel
    ok_work = required_work <= budget
    return {
        "impact_speed_mps": speed,
        "kinetic_energy_j": kinetic,
        "required_work_j": required_work,
        "absorption_budget_j": budget,
        "required_deceleration_mps2": required_decel,
        "allowed_deceleration_mps2": allowed_decel,
        "deceleration_ok": bool(ok_decel),
        "work_ok": bool(ok_work),
        "verdict": "PASS" if (ok_decel and ok_work) else "FAIL",
    }


def friction_cone_ok(
    force_n: tuple[float, float, float] | list[float],
    *,
    friction_coefficient: float,
) -> dict[str, Any]:
    """Coulomb friction-cone check for one contact force (up = +Y)."""
    force = _vec3(force_n, label="contact_force_n")
    mu = _finite(friction_coefficient, label="friction_coefficient")
    if mu <= 0.0:
        raise ContractError("friction coefficient must be positive")
    normal = float(force[1])
    tangential = float(np.linalg.norm(force[[0, 2]]))
    if normal <= 0.0:
        return {"normal_n": normal, "verdict": "FAIL", "reason": "no positive normal load"}
    ratio = tangential / normal
    return {
        "normal_n": normal,
        "tangential_n": tangential,
        "ratio": ratio,
        "limit": mu,
        "margin": mu - ratio,
        "verdict": "PASS" if ratio <= mu else "FAIL",
    }


def decide_attack_variant(
    takeoff: Mapping[str, Any],
    landing: Mapping[str, Any],
) -> FeasibilityVerdict:
    """Combine takeoff/landing assessments; infeasible airborne falls back.

    The grounded lunge is the mandatory fallback: it keeps the behavior
    (committed forward bite with body weight behind it) while refusing an
    unphysical flight.
    """
    checks = {"takeoff": dict(takeoff), "landing": dict(landing)}
    if takeoff.get("verdict") == "PASS" and landing.get("verdict") == "PASS":
        return FeasibilityVerdict(feasible=True, variant="airborne", checks=checks, limiting_factor=None)
    limiting: str | None = None
    for section in ("takeoff", "landing"):
        for key, value in checks[section].items():
            if key.endswith("_ok") and value is False:
                limiting = f"{section}.{key}"
                break
        if limiting:
            break
    return FeasibilityVerdict(
        feasible=False,
        variant="grounded_lunge",
        checks=checks,
        limiting_factor=limiting or "unknown",
    )


@dataclass(frozen=True)
class JointEnvelope:
    """Hard vs preferred limits for one articulation axis.

    * ``hard_min/max`` — bony/articular non-interpenetration boundary; the
      final safety projection. Never exceeded.
    * ``preferred_min/max`` — soft-tissue normal-performance range used by
      ordinary motion.
    * ``contraction_per_load`` — degrees the preferred envelope contracts
      per bodyweight of joint load; ``contraction_per_speed`` per rad/s.
    """

    joint: str
    hard_min_deg: float
    hard_max_deg: float
    preferred_min_deg: float
    preferred_max_deg: float
    contraction_per_load_bw: float = 2.0
    contraction_per_speed: float = 1.5  # degrees per rad/s

    def __post_init__(self) -> None:
        if not self.hard_min_deg < self.hard_max_deg:
            raise ContractError(f"joint {self.joint}: hard envelope must be ordered")
        if not self.hard_min_deg <= self.preferred_min_deg <= self.preferred_max_deg <= self.hard_max_deg:
            raise ContractError(f"joint {self.joint}: preferred envelope must sit inside hard")


def contracted_preferred_envelope(
    envelope: JointEnvelope,
    *,
    joint_load_bw: float = 0.0,
    joint_speed_radps: float = 0.0,
    injury_factor: float = 0.0,
) -> dict[str, Any]:
    """Preferred envelope contracted under load, speed and injury.

    Contraction never exceeds the hard bounds; when load/speed would push
    the preferred window shut, the joint reports zero preferred margin and
    the planner must slow down, add support, or refuse — never violate hard.
    """
    load = _finite(joint_load_bw, label="joint_load_bw")
    speed = _finite(joint_speed_radps, label="joint_speed_radps")
    injury = _finite(injury_factor, label="injury_factor")
    if load < 0.0 or speed < 0.0 or not 0.0 <= injury <= 1.0:
        raise ContractError("envelope conditioning inputs are out of range")
    contraction = (
        load * envelope.contraction_per_load_bw
        + speed * envelope.contraction_per_speed
        + injury * 10.0
    )
    low = min(envelope.preferred_min_deg + contraction, envelope.hard_max_deg)
    high = max(envelope.preferred_max_deg - contraction, envelope.hard_min_deg)
    if low > high:
        low, high = (low + high) / 2.0, (low + high) / 2.0
    return {
        "joint": envelope.joint,
        "hard_deg": [envelope.hard_min_deg, envelope.hard_max_deg],
        "preferred_nominal_deg": [envelope.preferred_min_deg, envelope.preferred_max_deg],
        "preferred_conditioned_deg": [low, high],
        "contraction_deg": contraction,
        "preferred_margin_deg": max(0.0, high - low),
    }


__all__ = [
    "CapacityProfile",
    "FeasibilityVerdict",
    "JointEnvelope",
    "assess_landing",
    "assess_takeoff",
    "contracted_preferred_envelope",
    "decide_attack_variant",
    "friction_cone_ok",
]
