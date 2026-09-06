"""Grounded alternating support with independently authored digitigrade recovery.

Distances are body-height normalized. The support schedule belongs to this
program; articulation is emitted by the same rotation-only V9 limb solver as
running. Zero articulation settings preserve the original reverse-walk recipe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping

from ..errors import ContractError
from .airborne_gait import rounded_swing_height


def smooth(value: float) -> float:
    u = min(1.0, max(0.0, value))
    return u ** 3 * (10 + u * (-15 + 6 * u))


@dataclass(frozen=True)
class GroundedGait:
    step_period_s: float = 0.8
    duty_factor: float = 0.72
    step_length_body_heights: float = -0.08
    touchdown_reach_body_heights: float = 0.04
    swing_clearance_body_heights: float = 0.055
    pelvis_crouch_body_heights: float = 0.025
    pelvis_excursion_body_heights: float = 0.004
    cycles: int = 2
    sample_hz: int = 60
    toe_flex_degrees: float = 0.0
    foot_recovery_pitch_degrees: float = 0.0
    push_off_pitch_degrees: float = 0.0
    push_off_start_fraction: float = 0.60
    swing_hip_lift_degrees: float = 0.0
    rounded_swing_peak_fraction: float = 0.0

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ContractError(f"grounded gait {key} must be finite numeric")
        if self.step_period_s <= 0 or not 0.5 < self.duty_factor < 1:
            raise ContractError("grounded walking requires positive timing and double support")
        if not 0 < abs(self.step_length_body_heights) <= 0.6:
            raise ContractError("grounded signed step length must be nonzero and bounded")
        for key in ("touchdown_reach_body_heights", "swing_clearance_body_heights",
                    "pelvis_crouch_body_heights", "pelvis_excursion_body_heights"):
            if not 0 <= getattr(self, key) <= 0.25:
                raise ContractError(f"grounded {key} is outside engineering limits")
        for key in ("toe_flex_degrees", "foot_recovery_pitch_degrees", "push_off_pitch_degrees", "swing_hip_lift_degrees"):
            if not 0 <= getattr(self, key) <= 60:
                raise ContractError(f"grounded {key} exceeds the articulation envelope")
        if not 0 < self.push_off_start_fraction < 1:
            raise ContractError("grounded push-off landmark must lie inside stance")
        if self.rounded_swing_peak_fraction and not .3 <= self.rounded_swing_peak_fraction <= .5:
            raise ContractError("grounded swing peak must be zero or in [.3,.5]")
        if int(self.cycles) != self.cycles or self.cycles < 1:
            raise ContractError("grounded cycles must be a positive integer")
        if int(self.sample_hz) != self.sample_hz or self.sample_hz < 24:
            raise ContractError("grounded sample_hz must be an integer >=24")


def load_grounded_gait(document: Mapping[str, Any]) -> GroundedGait:
    if document.get("schema") != "eonwild.motion.v9.grounded-gait.v1":
        raise ContractError("unsupported grounded gait schema")
    params = document.get("parameters")
    if not isinstance(params, Mapping) or set(params) - set(GroundedGait.__dataclass_fields__):
        raise ContractError("unknown grounded parameters")
    return GroundedGait(**params)


def sample_grounded_gait(gait: GroundedGait, time_s: float, body_height_m: float) -> dict[str, Any]:
    if not math.isfinite(time_s) or not math.isfinite(body_height_m) or body_height_m <= 0:
        raise ContractError("grounded sampling requires finite time and positive height")
    period = 2 * gait.step_period_s
    velocity = gait.step_length_body_heights * body_height_m / gait.step_period_s
    reach = math.copysign(gait.touchdown_reach_body_heights * body_height_m, velocity)
    feet = {}
    for side, offset in (("left", 0.0), ("right", gait.step_period_s)):
        phase = ((time_s - offset) / period) % 1
        touchdown = time_s - phase * period
        anchor = velocity * touchdown + reach
        contact = phase < gait.duty_factor
        swing = 0.0 if contact else (phase - gait.duty_factor) / (1 - gait.duty_factor)
        if contact:
            amount = smooth((phase / gait.duty_factor - gait.push_off_start_fraction) / (1 - gait.push_off_start_fraction))
            pitch = gait.push_off_pitch_degrees * amount
            flex = 0.0
            height = 0.0
        else:
            # Unload/roll, fold the digitigrade ankle in early recovery, then
            # extend before touchdown. Both boundaries match stance, C2.
            recovery = math.sin(math.pi * smooth(swing)) ** 2
            pitch = gait.push_off_pitch_degrees * (1 - smooth(swing / .35)) - gait.foot_recovery_pitch_degrees * recovery
            flex = gait.toe_flex_degrees * recovery
            crown = (rounded_swing_height(swing, gait.rounded_swing_peak_fraction)
                     if gait.rounded_swing_peak_fraction else recovery)
            height = body_height_m * gait.swing_clearance_body_heights * crown
        feet[side] = {"contact": contact, "forward_m": anchor + (0 if contact else velocity * period * smooth(swing)),
            "height_m": height, "toe_flex_degrees": flex, "foot_pitch_degrees": pitch,
            "swing_phase": swing, "touchdown_time_s": touchdown}
    support = sum(int(foot["contact"]) for foot in feet.values())
    if support == 0:
        raise ContractError("grounded program produced unsupported flight")
    phase = time_s / gait.step_period_s
    amplitude = gait.pelvis_excursion_body_heights * body_height_m
    return {"time_s": time_s, "root_forward_m": velocity * time_s,
        "pelvis_height_offset_m": -gait.pelvis_crouch_body_heights * body_height_m - amplitude * (1 - math.cos(2 * math.pi * phase)) / 2,
        "pelvis_vertical_velocity_mps": -amplitude * math.pi / gait.step_period_s * math.sin(2 * math.pi * phase),
        "flight": False, "support_count": support, "feet": feet,
        "stage": "DOUBLE_SUPPORT" if support == 2 else "SINGLE_SUPPORT"}


def build_grounded_plan(gait: GroundedGait, body_height_m: float) -> dict[str, Any]:
    duration = 2 * gait.step_period_s * gait.cycles
    intervals = int(math.ceil(duration * gait.sample_hz))
    return {"schema": "eonwild.motion.v9.contact-plan.v1", "program": "grounded_gait",
        "classification": "authored engineering contact plan; not force simulation",
        "body_height_m": body_height_m, "duration_s": duration,
        "same_foot_cycle_s": 2 * gait.step_period_s, "parameters": asdict(gait),
        "samples": [sample_grounded_gait(gait, duration * i / intervals, body_height_m) for i in range(intervals + 1)]}
