"""Grounded alternating support with independently authored digitigrade recovery.

Distances are body-height normalized. The support schedule belongs to this
program; articulation is emitted by the shared rotation-only V9 limb solver.
The optional centered placement coordinates touchdown with distance traveled
DURING stance; increasing stride no longer leaves almost all reach behind the
body. Old fixed-reach recipes retain their exact choreography.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping

from ..errors import ContractError
from .airborne_gait import rounded_swing_height, sampled_handoff_phase
from .foot_articulation import rate_limited_recovery_gain, recovery_pitch
from .parameters import gait_parameters


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
    pelvis_height_carrier: str | None = None
    cycles: int = 2
    sample_hz: int = 60
    toe_flex_degrees: float = 0.0
    toe_recovery_peak_fraction: float | None = None
    foot_recovery_pitch_degrees: float = 0.0
    metatarsal_recovery_world_degrees_from_down: float | None = None
    metatarsal_recovery_release_fraction: float | None = None
    metatarsal_recovery_carrier: str | None = None
    pad_recovery_pitch_degrees: float | None = None
    push_off_pitch_degrees: float = 0.0
    push_off_start_fraction: float = 0.60
    swing_hip_lift_degrees: float = 0.0
    rounded_swing_peak_fraction: float = 0.0
    centered_stance: bool = False
    handoff_phase_fraction: float | None = None
    handoff_sample_hz: int | None = None

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if key in ('handoff_phase_fraction', 'handoff_sample_hz') and value is None:
                continue
            if key == 'pelvis_height_carrier':
                if value is not None and value != 'stance_vault_proxy':
                    raise ContractError(
                        "grounded pelvis height carrier must be stance_vault_proxy or null")
                continue
            if key == 'metatarsal_recovery_carrier':
                if value is not None and value != 'rate_limited_c2':
                    raise ContractError(
                        'grounded metatarsal recovery carrier must be rate_limited_c2 or null')
                continue
            if key == 'centered_stance':
                if type(value) is not bool:
                    raise ContractError('centered_stance must be boolean')
            elif key in ('toe_recovery_peak_fraction', 'metatarsal_recovery_world_degrees_from_down',
                         'metatarsal_recovery_release_fraction', 'pad_recovery_pitch_degrees'):
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                          or not math.isfinite(value)):
                    raise ContractError(f'grounded optional control {key} must be finite numeric or null')
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
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
        if self.pad_recovery_pitch_degrees is not None and not -60 <= self.pad_recovery_pitch_degrees <= 60:
            raise ContractError("grounded pad recovery pitch exceeds the signed articulation envelope")
        if (self.metatarsal_recovery_world_degrees_from_down is not None
                and not -90 <= self.metatarsal_recovery_world_degrees_from_down <= 90):
            raise ContractError("grounded world metatarsal recovery target must lie within -90..90 degrees")
        if ((self.metatarsal_recovery_world_degrees_from_down is None)
            != (self.metatarsal_recovery_release_fraction is None)):
            raise ContractError("grounded world metatarsal recovery target and release must be authored together")
        if (self.metatarsal_recovery_carrier is not None
            and self.metatarsal_recovery_world_degrees_from_down is None):
            raise ContractError("grounded metatarsal recovery carrier requires a world target and release")
        if self.metatarsal_recovery_release_fraction is not None:
            peak = self.toe_recovery_peak_fraction or self.rounded_swing_peak_fraction or .42
            if not peak < self.metatarsal_recovery_release_fraction <= .9:
                raise ContractError("grounded world metatarsal recovery release must follow its peak and not exceed .9")
        if self.toe_recovery_peak_fraction is not None and not .3 <= self.toe_recovery_peak_fraction <= .5:
            raise ContractError("grounded toe recovery peak must lie in [.3,.5]")
        if not 0 < self.push_off_start_fraction < 1:
            raise ContractError("grounded push-off landmark must lie inside stance")
        if self.rounded_swing_peak_fraction and not .3 <= self.rounded_swing_peak_fraction <= .5:
            raise ContractError("grounded swing peak must be zero or in [.3,.5]")
        if int(self.cycles) != self.cycles or self.cycles < 1:
            raise ContractError("grounded cycles must be a positive integer")
        if int(self.sample_hz) != self.sample_hz or self.sample_hz < 24:
            raise ContractError("grounded sample_hz must be an integer >=24")
        if (self.handoff_phase_fraction is not None
            and not 0 <= self.handoff_phase_fraction <= .25):
            raise ContractError("grounded handoff phase must be within the first quarter cycle")
        if ((self.handoff_phase_fraction is None) != (self.handoff_sample_hz is None)
            or (self.handoff_sample_hz is not None
                and (type(self.handoff_sample_hz) is not int
                     or not self.sample_hz <= self.handoff_sample_hz <= 1920))):
            raise ContractError("grounded handoff sampling requires a paired rate at or above the base clock")


def touchdown_reach(gait: GroundedGait, body_height_m: float) -> float:
    """Signed reach at touchdown, used by steady gait AND its transitions.

    Centered mode derives half of stance travel from the bounded stride and
    duty. The fixed-reach parameter is used only in the legacy placement mode.
    This is choreography, not a relaxation of any anatomical/contact gate.
    """
    if gait.centered_stance:
        return gait.step_length_body_heights * gait.duty_factor * body_height_m
    return math.copysign(gait.touchdown_reach_body_heights * body_height_m, gait.step_length_body_heights)


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
    reach = touchdown_reach(gait, body_height_m)
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
            recovery = math.sin(math.pi * smooth(swing)) ** 2
            push_off = gait.push_off_pitch_degrees * (1 - smooth(swing / .35))
            pitch = (push_off - gait.foot_recovery_pitch_degrees * recovery
                     if gait.metatarsal_recovery_world_degrees_from_down is None
                     else push_off)
            flex = (-recovery_pitch(swing, gait.toe_flex_degrees, gait.toe_recovery_peak_fraction)
                    if gait.toe_recovery_peak_fraction is not None else gait.toe_flex_degrees * recovery)
            crown = (rounded_swing_height(swing, gait.rounded_swing_peak_fraction)
                     if gait.rounded_swing_peak_fraction else recovery)
            height = body_height_m * gait.swing_clearance_body_heights * crown
        feet[side] = {"contact": contact, "forward_m": anchor + (0 if contact else velocity * period * smooth(swing)),
            "height_m": height, "toe_flex_degrees": flex, "foot_pitch_degrees": pitch,
            "swing_phase": swing, "touchdown_time_s": touchdown}
        if not contact and gait.metatarsal_recovery_world_degrees_from_down is not None:
            peak = gait.toe_recovery_peak_fraction or gait.rounded_swing_peak_fraction or .42
            feet[side]["metatarsal_recovery_world_degrees_from_down"] = gait.metatarsal_recovery_world_degrees_from_down
            feet[side]["metatarsal_recovery_gain"] = (
                rate_limited_recovery_gain(swing, peak, gait.metatarsal_recovery_release_fraction)
                if gait.metatarsal_recovery_carrier == 'rate_limited_c2' else
                -recovery_pitch(swing, 1.0, peak, gait.metatarsal_recovery_release_fraction))
    support = sum(int(foot["contact"]) for foot in feet.values())
    if support == 0:
        raise ContractError("grounded program produced unsupported flight")
    phase = time_s / gait.step_period_s
    # The opt-in walking carrier places the pelvis-height proxy at its high
    # point at each declared stance midpoint and its low point at each
    # double-support midpoint. It is kinematic choreography, not a COM or
    # force model. The omitted field retains the original clock exactly.
    height_phase = (phase if gait.pelvis_height_carrier is None
                    else phase - gait.duty_factor)
    amplitude = gait.pelvis_excursion_body_heights * body_height_m
    return {"time_s": time_s, "root_forward_m": velocity * time_s,
        "pelvis_height_offset_m": -gait.pelvis_crouch_body_heights * body_height_m - amplitude * (1 - math.cos(2 * math.pi * height_phase)) / 2,
        "pelvis_vertical_velocity_mps": -amplitude * math.pi / gait.step_period_s * math.sin(2 * math.pi * height_phase),
        "flight": False, "support_count": support, "feet": feet,
        "stage": "DOUBLE_SUPPORT" if support == 2 else "SINGLE_SUPPORT"}


def grounded_phase_sample_counts(samples: Any) -> dict[str, dict[str, int]]:
    """Count actual support/swing witnesses for each grounded leg."""
    if not isinstance(samples, list):
        raise ContractError("grounded phase coverage requires a sample list")
    counts = {
        side: {"support": 0, "swing": 0}
        for side in ("left", "right")
    }
    for row in samples:
        if not isinstance(row, Mapping) or not isinstance(row.get("feet"), Mapping):
            raise ContractError("grounded phase coverage requires complete feet")
        for side in counts:
            foot = row["feet"].get(side)
            if not isinstance(foot, Mapping) or type(foot.get("contact")) is not bool:
                raise ContractError("grounded phase coverage requires boolean per-leg contact")
            phase = "support" if foot["contact"] else "swing"
            counts[side][phase] += 1
    return counts


def require_grounded_phase_coverage(samples: Any) -> None:
    """Reject an alternating gait whose emitted clock omits a required phase."""
    counts = grounded_phase_sample_counts(samples)
    missing = [
        f"{side}:{phase}"
        for side in ("left", "right")
        for phase in ("support", "swing")
        if counts[side][phase] == 0
    ]
    if missing:
        raise ContractError(
            "grounded locomotion sampling must observe support and swing for each leg; "
            f"missing {', '.join(missing)}"
        )


def build_grounded_plan(gait: GroundedGait, body_height_m: float) -> dict[str, Any]:
    duration = 2 * gait.step_period_s * gait.cycles
    intervals = int(math.ceil(duration * gait.sample_hz))
    times = {duration * i / intervals for i in range(intervals + 1)}
    interface = sampled_handoff_phase(gait)
    if interface is not None:
        for cycle in range(gait.cycles):
            boundary = interface + cycle * 2 * gait.step_period_s
            times.update(boundary + k / gait.handoff_sample_hz for k in range(-4, 5)
                         if 0 <= boundary + k / gait.handoff_sample_hz <= duration)
    unique_times = []
    for time_s in sorted(times):
        if not unique_times or time_s - unique_times[-1] > 1e-7:
            unique_times.append(time_s)
    samples = [sample_grounded_gait(gait, time_s, body_height_m) for time_s in unique_times]
    require_grounded_phase_coverage(samples)
    return {"schema": "eonwild.motion.v9.contact-plan.v1", "program": "grounded_gait",
        "classification": "authored engineering contact plan; not force simulation",
        "body_height_m": body_height_m, "duration_s": duration,
        "same_foot_cycle_s": 2 * gait.step_period_s, "parameters": gait_parameters(gait),
        "samples": samples}
