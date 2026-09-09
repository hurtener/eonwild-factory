"""Body-normalized alternating run with a real, explicitly scheduled flight.

Independent of the grounded alternating-gait contract. Distances are world
metres, cadence is seconds per *step*, duty is per foot over a two-step cycle.
The plan is an animation engineering trajectory, not a dynamics simulation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping

from ..errors import ContractError
from .parameters import gait_parameters
from .swing_transport import transport_progress, validate_transport_ramp


@dataclass(frozen=True)
class AirborneGait:
    step_period_s: float = 0.625
    flight_fraction: float = 4 / 15
    step_length_body_heights: float = 0.62
    touchdown_reach_body_heights: float = 0.30
    swing_clearance_body_heights: float = 0.24
    swing_lift_fraction: float = 0.5
    swing_lower_fraction: float = 0.5
    pelvis_compression_body_heights: float = 0.065
    pelvis_crouch_body_heights: float = 0.0
    flight_height_body_heights: float = 0.035
    toe_flex_degrees: float = 32.0
    foot_recovery_pitch_degrees: float = 24.0
    push_off_pitch_degrees: float = 14.4
    compression_peak_fraction: float = 0.32
    push_off_start_fraction: float = 0.68
    swing_hip_lift_degrees: float = 60.0
    swing_recovery_peak_fraction: float = 0.42
    hip_extension_limit_degrees: float = 45.0
    hip_flexion_limit_degrees: float = 80.0
    knee_min_interior_degrees: float = 65.0
    knee_max_interior_degrees: float = 165.0
    ankle_min_interior_degrees: float = 30.0
    ankle_max_interior_degrees: float = 165.0
    max_joint_angular_velocity_degrees_per_s: float = 1200.0
    max_ankle_pitch_velocity_degrees_per_s: float = 600.0
    articulation_preferred_margin_degrees: float = 0.0
    articulation_preferred_margin_weight: float = 25.0
    continuous_body_launch_fraction: float = 0.0
    rounded_swing_peak_fraction: float = 0.0
    swing_transport_ramp_fraction: float = 0.0
    chest_response_gain_degrees: float = 0.0
    head_stabilization_gain: float = 0.85
    tail_response_gain_degrees: float = 0.0
    body_response_time_s: float = 0.06
    front_body_pitch_degrees: float = 0.0
    tail_elevation_degrees: float = 0.0
    flight_foot_lift_body_heights: float = 0.0
    swing_approach_lift_body_heights: float = 0.0
    stance_ground_offset_left_m: float = 0.0
    stance_ground_offset_right_m: float = 0.0
    stance_pitch_lead_left_degrees: float = 0.0
    stance_pitch_lead_right_degrees: float = 0.0
    toe_stance_engage_left_degrees: float = 0.0
    toe_stance_engage_right_degrees: float = 0.0
    jaw_breathing_min_degrees: float = 0.0
    jaw_breathing_max_degrees: float = 0.0
    jaw_breathing_cycles_per_cycle: int = 1
    cycles: int = 2
    sample_hz: int = 120
    boundary_sample_hz: int = 0
    handoff_phase_fraction: float | None = None
    handoff_sample_hz: int | None = None

    def __post_init__(self) -> None:
        for key, value in asdict(self).items():
            if key in ("handoff_phase_fraction", "handoff_sample_hz") and value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ContractError(f"airborne gait {key} must be finite numeric")
        if self.step_period_s <= 0 or not 0 < self.flight_fraction < 0.7:
            raise ContractError("airborne gait requires a positive step and flight fraction in (0, .7)")
        for key in ("step_length_body_heights", "swing_clearance_body_heights", "flight_height_body_heights"):
            if getattr(self, key) <= 0:
                raise ContractError(f"airborne gait {key} must be positive")
        if min(self.touchdown_reach_body_heights, self.pelvis_compression_body_heights, self.pelvis_crouch_body_heights, self.toe_flex_degrees, self.foot_recovery_pitch_degrees, self.push_off_pitch_degrees) < 0:
            raise ContractError("airborne gait amplitudes must not be negative")
        if not 0 < self.compression_peak_fraction < self.push_off_start_fraction < 1:
            raise ContractError("compression and push-off landmarks must be ordered inside stance")
        if not 0 < self.swing_lift_fraction <= .5 or not 0 < self.swing_lower_fraction <= .5:
            raise ContractError("swing lift/lower fractions must be in (0, .5]")
        if not 0 <= self.swing_hip_lift_degrees <= self.hip_flexion_limit_degrees < 90 or not 0 < self.hip_extension_limit_degrees < 90:
            raise ContractError("hip engineering envelopes must lie within sagittal quarter turns")
        if not 0 < self.knee_min_interior_degrees < self.knee_max_interior_degrees < 180 or not 0 < self.ankle_min_interior_degrees < self.ankle_max_interior_degrees < 180:
            raise ContractError("joint interior engineering envelopes must be ordered within (0, 180)")
        if self.max_joint_angular_velocity_degrees_per_s <= 0:
            raise ContractError("joint angular velocity engineering limit must be positive")
        if self.max_ankle_pitch_velocity_degrees_per_s <= 0 or not 0 < self.swing_recovery_peak_fraction < 1:
            raise ContractError("recovery landmark and ankle pitch velocity limit are invalid")
        if self.articulation_preferred_margin_degrees < 0 or self.articulation_preferred_margin_weight < 0:
            raise ContractError("preferred articulation margins and weights must not be negative")
        if self.continuous_body_launch_fraction and not .8 <= self.continuous_body_launch_fraction <= .95:
            raise ContractError("continuous launch fraction must be zero (legacy) or in [.8, .95]")
        if self.rounded_swing_peak_fraction and not .3 <= self.rounded_swing_peak_fraction <= .5:
            raise ContractError("rounded swing peak must be zero (legacy) or in [.3, .5]")
        if self.rounded_swing_peak_fraction and not self.swing_lift_fraction <= self.rounded_swing_peak_fraction <= 1 - self.swing_lower_fraction:
            raise ContractError("rounded swing peak must lie between the lift/lower ramps")
        validate_transport_ramp(self.swing_transport_ramp_fraction)
        if self.continuous_body_launch_fraction:
            trough, rise = continuous_body_timing(self)
            if trough + rise >= 1:
                raise ContractError("continuous body apex must occur before next touchdown")
        if not 0 <= self.chest_response_gain_degrees <= 8 or not 0 <= self.tail_response_gain_degrees <= 25 or not 0 <= self.head_stabilization_gain <= 1.25:
            raise ContractError("driven body response gains exceed engineering bounds")
        if not 0 < self.body_response_time_s <= self.step_period_s:
            raise ContractError("response lag must be positive and at most one step")
        if not 0 <= self.front_body_pitch_degrees <= 20 or not 0 <= self.tail_elevation_degrees <= 30:
            raise ContractError("front body pitch and tail elevation exceed engineering bounds")
        if not 0 <= self.flight_foot_lift_body_heights <= .15:
            raise ContractError("flight foot lift exceeds body-normalized engineering bounds")
        if not 0 <= self.swing_approach_lift_body_heights <= .15:
            raise ContractError("approach lift exceeds body-normalized engineering bounds")
        if not 0 <= self.stance_ground_offset_left_m <= .05:
            raise ContractError("left ground offset exceeds the 5 cm regrounding bound")
        if not 0 <= self.stance_ground_offset_right_m <= .05:
            raise ContractError("right ground offset exceeds the 5 cm regrounding bound")
        for key, bound in (("stance_pitch_lead_left_degrees", 20), ("stance_pitch_lead_right_degrees", 20),
                           ("toe_stance_engage_left_degrees", 15), ("toe_stance_engage_right_degrees", 15)):
            if not 0 <= getattr(self, key) <= bound:
                raise ContractError(f"{key} exceeds its engagement bound")
        if not 0 <= self.jaw_breathing_min_degrees <= self.jaw_breathing_max_degrees <= 8:
            raise ContractError("subtle breathing gape must be ordered within zero to eight degrees")
        if self.jaw_breathing_cycles_per_cycle != int(self.jaw_breathing_cycles_per_cycle) or not 1 <= self.jaw_breathing_cycles_per_cycle <= 4:
            raise ContractError("breathing cycles must be an integer from one to four per same-foot cycle")
        if (self.chest_response_gain_degrees or self.tail_response_gain_degrees) and not self.continuous_body_launch_fraction:
            raise ContractError("driven body response requires the continuous carrier")
        if (type(self.boundary_sample_hz) is not int or self.boundary_sample_hz < 0
            or (self.boundary_sample_hz and not self.sample_hz <= self.boundary_sample_hz <= 1920)):
            raise ContractError("boundary sample rate must be zero or between sample_hz and 1920")
        if (self.handoff_phase_fraction is not None
            and not 0 <= self.handoff_phase_fraction <= .25):
            raise ContractError("airborne handoff phase must be within the first quarter cycle")
        if self.handoff_phase_fraction is not None and not self.boundary_sample_hz:
            raise ContractError("airborne handoff phase requires a boundary sample rate")
        if ((self.handoff_phase_fraction is None) != (self.handoff_sample_hz is None)
            or (self.handoff_sample_hz is not None
                and (type(self.handoff_sample_hz) is not int
                     or not self.boundary_sample_hz <= self.handoff_sample_hz <= 1920))):
            raise ContractError("airborne handoff sampling requires a paired rate within the boundary envelope")
        if int(self.cycles) != self.cycles or self.cycles < 1 or int(self.sample_hz) != self.sample_hz or self.sample_hz < 24:
            raise ContractError("cycles and sample_hz must be positive integers; sample_hz >= 24")

    @property
    def duty_factor(self) -> float:
        return (1 - self.flight_fraction) / 2


def load_airborne_gait(profile: Mapping[str, Any]) -> AirborneGait:
    if profile.get("schema") != "eonwild.motion.v9.airborne-gait.v1" or profile.get("program") != "airborne_gait":
        raise ContractError("unsupported airborne gait profile")
    if profile.get("body_branching") is not False:
        raise ContractError("airborne gait forbids body-specific branching")
    values = profile.get("parameters")
    if not isinstance(values, Mapping) or set(values) - set(AirborneGait.__dataclass_fields__):
        raise ContractError("unknown airborne gait parameters")
    return AirborneGait(**values)


_AIRBORNE_CHOREOGRAPHY_FIELDS = {
    "step_period_s", "flight_fraction", "step_length_body_heights",
    "touchdown_reach_body_heights", "swing_clearance_body_heights",
    "swing_lift_fraction", "swing_lower_fraction",
    "flight_height_body_heights", "toe_flex_degrees",
    "foot_recovery_pitch_degrees", "push_off_pitch_degrees",
    "push_off_start_fraction", "swing_hip_lift_degrees",
    "swing_recovery_peak_fraction", "rounded_swing_peak_fraction",
    "swing_transport_ramp_fraction", "flight_foot_lift_body_heights",
    "swing_approach_lift_body_heights", "cycles", "sample_hz",
    "boundary_sample_hz", "handoff_phase_fraction", "handoff_sample_hz",
}


def load_airborne_choreography(profile: Mapping[str, Any]) -> AirborneGait:
    """Load v2 event choreography without accepting body-style or ROM fields."""
    if (
        not isinstance(profile, Mapping)
        or set(profile) != {
            "schema", "program", "parameters", "classification"
        }
        or profile.get("schema")
        != "eonwild.motion.airborne-choreography.v1"
        or profile.get("program") != "airborne_gait"
        or not isinstance(profile.get("classification"), str)
        or not profile["classification"]
    ):
        raise ContractError("unsupported airborne choreography profile")
    values = profile.get("parameters")
    if (
        not isinstance(values, Mapping)
        or set(values) - _AIRBORNE_CHOREOGRAPHY_FIELDS
        or not {
            "step_period_s", "flight_fraction", "step_length_body_heights",
            "touchdown_reach_body_heights", "swing_clearance_body_heights",
            "flight_height_body_heights", "cycles", "sample_hz",
        } <= set(values)
    ):
        raise ContractError(
            "airborne choreography contains missing or body-owned parameters"
        )
    # Support compression is supplied by the shared performance style through
    # the regime response. Flight height and foot events remain choreography.
    return AirborneGait(
        **dict(values),
        pelvis_compression_body_heights=0.0,
        pelvis_crouch_body_heights=0.0,
    )


def _smooth(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * x * (10 + x * (-15 + 6 * x))


def _smooth_derivatives(x: float) -> tuple[float, float, float]:
    x = max(0.0, min(1.0, x))
    return _smooth(x), 30 * x * x * (1 - x) ** 2, 60 * x * (1 - x) * (1 - 2 * x)


def sampled_handoff_phase(gait: Any) -> float | None:
    """Resolve the gait-owned interface on its unchanged base sampling clock."""
    fraction = gait.handoff_phase_fraction
    if fraction is None:
        return None
    period = 2 * gait.step_period_s
    duration = gait.cycles * period
    count = math.ceil(duration * gait.sample_hz)
    dt = duration / count
    return round(fraction * period / dt) * dt


def continuous_body_timing(gait: AirborneGait) -> tuple[float, float]:
    """Trough and rise duration in step fractions; launch lies inside the rise."""
    contact = 1 - gait.flight_fraction
    trough = contact * gait.compression_peak_fraction
    lo, hi = 0., 1.
    for _ in range(48):
        mid = (lo + hi) * .5
        if _smooth(mid) < gait.continuous_body_launch_fraction:
            lo = mid
        else:
            hi = mid
    return trough, (contact - trough) / ((lo + hi) * .5)


def continuous_body_state(gait: AirborneGait, time_s: float, body_height_m: float) -> tuple[float, float, float]:
    """Periodic C2 trough→launch→apex→catch carrier, not a force simulation.

    Low/apex heights remain the old compression/flight extrema. Catch is
    inside the descending curve, not a zero-speed restart at the seam.
    """
    trough, rise = continuous_body_timing(gait)
    phase = (time_s / gait.step_period_s - trough) % 1
    low = -gait.pelvis_compression_body_heights
    total = gait.pelvis_compression_body_heights + gait.flight_height_body_heights
    if phase < rise:
        duration, sign = rise, 1.
        s, velocity, acceleration = _smooth_derivatives(phase / duration)
    else:
        duration, sign = 1 - rise, -1.
        value, velocity, acceleration = _smooth_derivatives((phase - rise) / duration)
        s = 1 - value
    seconds = duration * gait.step_period_s
    return ((low + total * s - gait.pelvis_crouch_body_heights) * body_height_m, sign * total * velocity * body_height_m / seconds, sign * total * acceleration * body_height_m / (seconds * seconds))


def rounded_swing_height(phase: float, peak: float, lift_fraction: float = .24, lower_fraction: float = .32) -> float:
    """Single rounded maximum with C2 zero-height contact endpoints; no plateau."""
    if phase <= 0 or phase >= 1:
        return 0.0
    # Fast-enough release/catch ramps retain distal articulation clearance.
    # Multiplication by a smooth crown removes the old flat height plateau;
    # all first/second derivatives agree where either ramp becomes constant.
    lift, lower = _smooth(phase / lift_fraction), _smooth((1 - phase) / lower_fraction)
    return lift * lower * math.exp(-2 * (phase - peak) ** 2)


def sample_airborne_gait(gait: AirborneGait, time_s: float, body_height_m: float) -> dict[str, Any]:
    if not math.isfinite(time_s) or not math.isfinite(body_height_m) or body_height_m <= 0:
        raise ContractError("airborne sample requires finite time and positive body height")
    step = gait.step_period_s
    cycle = 2 * step
    contact_s = step * (1 - gait.flight_fraction)
    travel = gait.step_length_body_heights * body_height_m
    speed = travel / step
    p = (time_s / step) % 1
    # Smooth compression then push-off; the flight arc is zero at takeoff and
    # landing, positive strictly between. This is a kinematic arc, not gravity.
    contact_fraction = 1 - gait.flight_fraction
    if p < contact_fraction:
        c = p / contact_fraction
        peak = gait.compression_peak_fraction
        compression = _smooth(c / peak) if c <= peak else 1 - _smooth((c - peak) / (1 - peak))
        body_y = -gait.pelvis_compression_body_heights * body_height_m * compression
        stage = "LANDING_COMPRESSION" if c < peak else "PUSH_OFF" if c >= gait.push_off_start_fraction else "SUPPORT_EXTENSION"
    else:
        f = (p - contact_fraction) / gait.flight_fraction
        body_y = gait.flight_height_body_heights * body_height_m * math.sin(math.pi * f) ** 2
        stage = "FLIGHT"
    body_y -= gait.pelvis_crouch_body_heights * body_height_m
    body_derivatives = None
    if gait.continuous_body_launch_fraction:
        body_y, body_velocity, body_acceleration = continuous_body_state(gait, time_s, body_height_m)
        body_derivatives = {"pelvis_vertical_velocity_mps": body_velocity, "pelvis_vertical_acceleration_mps2": body_acceleration}
    feet = {}
    for side, offset in (("left", 0.0), ("right", step)):
        local = (time_s - offset) % cycle
        # Modulo at an exact cycle boundary can return cycle-epsilon.
        # Canonicalize the existing 1e-10 contact boundary precision so
        # equivalent clocks cannot disagree about which foot is loaded.
        if min(local, cycle-local) < 1e-10:
            local = 0.0
        touchdown = time_s - local
        anchor = speed * touchdown + gait.touchdown_reach_body_heights * body_height_m
        stance = local < contact_s - 1e-10
        if stance:
            load = _smooth((local / contact_s - gait.push_off_start_fraction) / (1 - gait.push_off_start_fraction))
            # Toe-engagement ramp: zero at touchdown (continuity with the
            # swing release), full by 15% of stance, so early-stance lead
            # never steps the contact. Per-side: touchdown attitudes differ
            # with bind asymmetry, so engagement is calibrated per foot.
            engage = _smooth(local / contact_s / 0.15)
            if side == "left":
                lead_deg, curl_deg = gait.stance_pitch_lead_left_degrees, gait.toe_stance_engage_left_degrees
            else:
                lead_deg, curl_deg = gait.stance_pitch_lead_right_degrees, gait.toe_stance_engage_right_degrees
            x, y = anchor, 0.0
            toe = gait.toe_flex_degrees * 0.55 * load + curl_deg * (1 - load) * engage
            pitch = gait.push_off_pitch_degrees * load + lead_deg * (1 - load) * engage
            swing_phase = 0.0
        else:
            swing_phase = (local - contact_s) / (cycle - contact_s)
            progress = (transport_progress(swing_phase, gait.swing_transport_ramp_fraction)
                        if gait.swing_transport_ramp_fraction else _smooth(swing_phase))
            x = anchor + 2 * travel * progress
            lift = math.sin(.5 * math.pi * min(1, swing_phase / gait.swing_lift_fraction)) ** 2
            lower = math.sin(.5 * math.pi * min(1, (1 - swing_phase) / gait.swing_lower_fraction)) ** 2
            y = gait.swing_clearance_body_heights * body_height_m * lift * lower
            if gait.rounded_swing_peak_fraction:
                y = gait.swing_clearance_body_heights * body_height_m * rounded_swing_height(swing_phase, gait.rounded_swing_peak_fraction, gait.swing_lift_fraction, gait.swing_lower_fraction)
            # Open the leading leg along an elevated approach before lowering
            # it into contact. This avoids forcing maximal forward reach and
            # a nearly grounded foot simultaneously, without shortening step.
            approach = _smooth((swing_phase - .55) / .23) * (1 - _smooth((swing_phase - .78) / .22))
            y += gait.swing_approach_lift_body_heights * body_height_m * approach
            toe = gait.toe_flex_degrees * (0.55 * (1 - _smooth(swing_phase)) + 0.65 * math.sin(math.pi * swing_phase) ** 2)
            # Release heel-up push-off before the foot passes under the hip.
            # Holding plantarflexion into mid-recovery folds the shank upward
            # into the thigh even if the toe target itself looks reasonable.
            peak = gait.swing_recovery_peak_fraction
            if swing_phase <= peak:
                recover = _smooth(swing_phase / peak)
                pitch = gait.push_off_pitch_degrees * (1 - recover) - gait.foot_recovery_pitch_degrees * recover
            else:
                pitch = -gait.foot_recovery_pitch_degrees * (1 - _smooth((swing_phase - peak) / (1 - peak)))
        feet[side] = {"contact": stance, "touchdown_time_s": touchdown, "forward_m": x, "height_m": y, "toe_flex_degrees": toe, "foot_pitch_degrees": pitch, "swing_phase": swing_phase}
    support = sum(int(foot["contact"]) for foot in feet.values())
    if support == 0 and gait.flight_foot_lift_body_heights:
        # Coordinated leg exchange only while both feet are free. Fourth-power
        # sine has zero position, velocity and acceleration at both joins.
        # The rotation-only solver realizes this trajectory; no bone stretches.
        flight_phase = (p - contact_fraction) / gait.flight_fraction
        extra = gait.flight_foot_lift_body_heights * body_height_m * math.sin(math.pi * flight_phase) ** 4
        for foot in feet.values():
            foot["height_m"] += extra
    return {"time_s": time_s, "root_forward_m": speed * time_s, "pelvis_height_offset_m": body_y, "stage": stage, "support_count": support, "flight": support == 0, "feet": feet, **(body_derivatives or {})}


def jaw_breathing_angle(gait: AirborneGait, time_s: float) -> float:
    """Small smooth opening/closing; authored breath style, not respiration physics."""
    phase = time_s * gait.jaw_breathing_cycles_per_cycle / (2 * gait.step_period_s)
    pulse = .5 - .5 * math.cos(2 * math.pi * phase)
    return gait.jaw_breathing_min_degrees + (gait.jaw_breathing_max_degrees - gait.jaw_breathing_min_degrees) * pulse


def build_airborne_plan(gait: AirborneGait, body_height_m: float) -> dict[str, Any]:
    duration = 2 * gait.cycles * gait.step_period_s
    count = int(math.ceil(duration * gait.sample_hz))
    times = {duration * i / count for i in range(count + 1)}
    # Preserve exact touchdown and toe-off boundaries even for noninteger fps.
    for i in range(2 * gait.cycles):
        times.update((i * gait.step_period_s, (i + 1 - gait.flight_fraction) * gait.step_period_s))
    if gait.boundary_sample_hz:
        # Densify native-time witnesses around actual load boundaries. A fast
        # C2 carrier's third derivative can bias coarse one-sided differences;
        # no cadence, stride, pose or failing tolerance is changed here.
        boundaries = {0., duration}
        for i in range(2*gait.cycles):
            boundaries.update((i*gait.step_period_s, (i+1-gait.flight_fraction)*gait.step_period_s))
        interface = sampled_handoff_phase(gait)
        if interface is not None:
            for cycle in range(gait.cycles):
                handoff = interface + cycle * 2 * gait.step_period_s
                times.update(handoff + k / gait.handoff_sample_hz for k in range(-4, 5)
                             if 0 <= handoff + k / gait.handoff_sample_hz <= duration)
        for boundary in boundaries:
            times.update(boundary+k/gait.boundary_sample_hz for k in range(-4,5)
                         if 0 <= boundary+k/gait.boundary_sample_hz <= duration)
    unique_times = []
    for time_s in sorted(times):
        if not unique_times or time_s - unique_times[-1] > 1e-7:
            unique_times.append(time_s)
    return {"schema": "eonwild.motion.v9.airborne-gait-plan.v1", "program": "airborne_gait", "parameters": gait_parameters(gait), "body_height_m": body_height_m, "step_period_s": gait.step_period_s, "same_foot_cycle_s": 2 * gait.step_period_s, "per_foot_duty_factor": gait.duty_factor, "flight_seconds_per_step": gait.flight_fraction * gait.step_period_s, "duration_s": duration, "root_motion_authority": True, "claims": "kinematic engineering candidate; no physical or biological claim", "samples": [sample_airborne_gait(gait, t, body_height_m) for t in unique_times]}
