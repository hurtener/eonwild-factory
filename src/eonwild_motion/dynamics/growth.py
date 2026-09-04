"""Growth, condition and allometric scaling with hysteresis.

Engine contract (section 12): motion tiers are authored regimes, not
discontinuous body states. The **structural mass ratio** (neutral-condition
mass over reviewed adult reference) selects the tier — age fraction is a
morphology descriptor and must never silently stand in for weight.
Condition constrains capacity without changing the ontogenetic body.

Configurable first-pass defaults (starting assumptions, profile-driven
where reviewed):

* ``mass ~ length³``, ``inertia ~ mass · length²``,
  ``muscle force ~ length²``;
* Froude number (``v² / gL``) holds cadence across sizes at equal gait;
* tier switches use hysteresis and preserve gait phase, contacts,
  root/COM velocity, angular momentum, tail state, target commitment and
  interruption state (the carry-over checklist travels with the verdict).
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence

from ..errors import ContractError
from .centroidal import _finite

CARRY_OVER = (
    "gait_phase",
    "contacts",
    "root_velocity",
    "angular_momentum",
    "tail_state",
    "target_commitment",
    "interruption_state",
)


@dataclass(frozen=True)
class GrowthTier:
    name: str
    mass_ratio_min: float
    mass_ratio_max: float
    length_ratio: float
    cadence_scale: float | None = None  # derived via Froude when None
    strength_scale: float | None = None  # derived via L² when None

    def __post_init__(self) -> None:
        if not self.mass_ratio_min < self.mass_ratio_max:
            raise ContractError(f"tier {self.name}: mass range must be ordered")
        if self.length_ratio <= 0.0:
            raise ContractError(f"tier {self.name}: length ratio must be positive")


DEFAULT_TIERS: tuple[GrowthTier, ...] = (
    GrowthTier("juvenile", 0.0, 0.30, 0.62),
    GrowthTier("subadult", 0.30, 0.70, 0.82),
    GrowthTier("adult", 0.70, 1.25, 1.0),
    GrowthTier("heavy_adult", 1.25, 2.5, 1.12),
)


def allometric_scale(length_ratio: float) -> dict[str, float]:
    """Continuous-trait scales from a linear size ratio (Froude-baseline).

    Semantics per trait (all relative to the reviewed adult reference):

    * ``mass_ratio`` — body mass (volume scales with ``L³``);
    * ``inertia_ratio`` — rotational inertia (``m·L²``);
    * ``force_ratio`` — muscle force (cross-section ``L²``);
    * ``cadence_ratio`` — stride frequency at equal Froude number
      (``v²/gL`` constant implies ``f ∝ 1/√L``);
    * ``stride_ratio`` — stride length (``∝ L``);
    * ``turn_authority_ratio`` — friction-limited yaw moment (``∝ L²``);
    * ``jump_authority_ratio`` — specific launch impulse (force per mass);
    * ``impact_stress_ratio`` — peak tissue stress on a size-matched
      impact (``∝ m/L²``; higher is *worse*, budgets must shrink);
    * ``braking_ratio`` — specific braking force;
    * ``tail_frequency_ratio`` — tail pendulum frequency (``∝ 1/√L``).
    """
    ratio = _finite(length_ratio, label="length_ratio")
    if ratio <= 0.0:
        raise ContractError("length ratio must be positive")
    mass = ratio**3
    return {
        "length_ratio": ratio,
        "mass_ratio": mass,
        "inertia_ratio": mass * ratio**2,
        "force_ratio": ratio**2,
        "cadence_ratio": 1.0 / math.sqrt(ratio),  # Froude-constant cadence
        "stride_ratio": ratio,
        "turn_authority_ratio": ratio**2,  # friction-limited yaw ~ weight arm
        "jump_authority_ratio": ratio**2 / mass,  # specific launch impulse
        "impact_stress_ratio": mass / ratio**2,  # stress scales against area
        "braking_ratio": ratio**2 / mass,
        "tail_frequency_ratio": 1.0 / math.sqrt(ratio),
    }


def tier_for_mass_ratio(
    tiers: Sequence[GrowthTier],
    mass_ratio: float,
) -> GrowthTier:
    if not tiers:
        raise ContractError("growth tier table is empty")
    ratio = _finite(mass_ratio, label="mass_ratio")
    for tier in tiers:
        if tier.mass_ratio_min <= ratio < tier.mass_ratio_max:
            return tier
    if ratio >= tiers[-1].mass_ratio_max:
        return tiers[-1]
    raise ContractError("no growth tier covers the mass ratio")


def select_tier(
    tiers: Sequence[GrowthTier],
    mass_ratio: float,
    current: str | None,
    *,
    hysteresis: float = 0.05,
) -> dict[str, Any]:
    """Hysteresis-guarded tier selection preserving switch continuity.

    A switch fires only when the ratio clears the соседней tier boundary
    by ``hysteresis`` (in mass-ratio units), preventing regime chatter at
    the boundary. Every verdict carries the continuity checklist the
    caller must preserve across the switch.
    """
    ratio = _finite(mass_ratio, label="mass_ratio")
    band = _finite(hysteresis, label="hysteresis")
    if band < 0.0:
        raise ContractError("hysteresis must be non-negative")
    if not tiers:
        raise ContractError("growth tier table is empty")
    names = [t.name for t in tiers]
    if current is not None and current not in names:
        raise ContractError(f"unknown current tier {current!r}")
    target = tier_for_mass_ratio(tiers, ratio).name
    switched = True
    if current is not None and current != target:
        current_idx, target_idx = names.index(current), names.index(target)
        boundary = (
            tiers[target_idx].mass_ratio_min
            if target_idx > current_idx
            else tiers[current_idx].mass_ratio_min
        )
        if abs(ratio - boundary) < band:
            target, switched = current, False
    return {
        "tier": target,
        "switched": switched,
        "mass_ratio": ratio,
        "clamped": bool(ratio >= tiers[-1].mass_ratio_max),
        "carry_over": list(CARRY_OVER),
        "length_ratio": next(t.length_ratio for t in tiers if t.name == target),
    }


def apply_condition(capacity_value: float, condition: float) -> float:
    """Condition (0..1, 1 = prime) constrains capacity, never morphology."""
    value = _finite(capacity_value, label="capacity_value")
    factor = _finite(condition, label="condition")
    if not 0.0 <= factor <= 1.0:
        raise ContractError("condition must lie in [0, 1]")
    return value * (0.35 + 0.65 * factor)


__all__ = [
    "CARRY_OVER",
    "DEFAULT_TIERS",
    "GrowthTier",
    "allometric_scale",
    "apply_condition",
    "select_tier",
    "tier_for_mass_ratio",
]
