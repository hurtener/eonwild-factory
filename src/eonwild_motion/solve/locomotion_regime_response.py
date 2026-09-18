"""Shared, event-bound kinematic body response for locomotion regimes.

The airborne model consumes the existing planner cadence and contact events.
It is an authored coordination rule, not a force, mass, COM, or biological
model.  Legacy plans do not opt into this module and retain their exact path.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping

from ..errors import ContractError
from ..planning.airborne_gait import AirborneGait
from ..planning.parameters import gait_parameters


POLICY_SCHEMA = "eonwild.motion.airborne-body-response.v1"
MODEL = "explicit_contact_flight_coordination.v1"
FORWARD_MODEL = "reference_scaled_support_exchange.v1"

_CARRIER_MAPPING = {
    "pelvis_sway": "bilateral_support_difference",
    "pelvis_roll": "bilateral_support_difference",
    "pelvis_yaw": "bilateral_support_difference",
    "pelvis_support_pitch": "early_late_support_exchange",
    "upper_trunk_counterpitch": "early_late_support_exchange",
    "neck_counterpitch": "early_late_support_exchange",
    "tail_counterpitch": "early_late_support_exchange",
    "pelvis_load_acceptance": "per_limb_early_support",
    "upper_trunk_load_acceptance_pitch": "per_limb_early_support",
    "tail_yaw": "lagged_bilateral_support_difference",
    "gaze_elevation": "constant_local_response",
    "pelvis_forward_velocity": "integrated_early_late_support_exchange",
}


@dataclass(frozen=True)
class AirborneBodyResponsePolicy:
    reference_speed_body_heights_per_s: float
    reference_pelvis_forward_velocity_modulation_fraction: float
    carrier_mapping: Mapping[str, str]


@dataclass(frozen=True)
class AirborneResponseState:
    phase_s: float
    performance_gain: float
    performance_gain_derivative_per_s: float
    lateral_support: float
    sagittal_support: float
    load_acceptance: float
    lagged_lateral_support: float
    pelvis_forward_displacement_m: float
    pelvis_forward_velocity_mps: float
    resolved_forward_modulation_fraction: float
    support_count: int


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{label} must be finite numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{label} must be finite numeric")
    return result


def load_airborne_body_response_policy(
    document: Mapping[str, Any],
) -> AirborneBodyResponsePolicy:
    fields = {"schema", "model", "carrier_mapping", "forward_speed"}
    if not isinstance(document, Mapping) or set(document) != fields:
        raise ContractError("airborne body-response policy contains missing or unknown fields")
    if document.get("schema") != POLICY_SCHEMA or document.get("model") != MODEL:
        raise ContractError("unsupported airborne body-response policy")
    mapping = document.get("carrier_mapping")
    if not isinstance(mapping, Mapping) or dict(mapping) != _CARRIER_MAPPING:
        raise ContractError("airborne body-response carrier mapping is incomplete or altered")
    forward = document.get("forward_speed")
    if (
        not isinstance(forward, Mapping)
        or set(forward) != {
            "model",
            "reference_speed_body_heights_per_s",
            "reference_pelvis_forward_velocity_modulation_fraction",
        }
        or forward.get("model") != FORWARD_MODEL
    ):
        raise ContractError("airborne forward-speed response is incomplete or unsupported")
    speed = _finite(
        forward.get("reference_speed_body_heights_per_s"),
        "airborne reference speed",
    )
    coefficient = _finite(
        forward.get("reference_pelvis_forward_velocity_modulation_fraction"),
        "airborne reference forward modulation",
    )
    if speed <= 0 or not 0 <= coefficient < 1:
        raise ContractError("airborne forward-speed reference exceeds its bounds")
    return AirborneBodyResponsePolicy(
        reference_speed_body_heights_per_s=speed,
        reference_pelvis_forward_velocity_modulation_fraction=coefficient,
        carrier_mapping=MappingProxyType(dict(mapping)),
    )


def _q(u: float) -> float:
    if not 0 <= u <= 1:
        raise ContractError("airborne stance coordinate is outside [0, 1]")
    return 64.0 * u**3 * (1.0 - u) ** 3


def _q_integral(u: float) -> float:
    if not 0 <= u <= 1:
        raise ContractError("airborne stance coordinate is outside [0, 1]")
    return 64.0 * (u**4 / 4.0 - 3.0 * u**5 / 5.0 + u**6 / 2.0 - u**7 / 7.0)


def _limb_state(gait: AirborneGait, phase_s: float, offset_s: float) -> tuple[float, float, float, float, bool]:
    cycle = 2.0 * gait.step_period_s
    stance_s = gait.step_period_s * (1.0 - gait.flight_fraction)
    local = (phase_s - offset_s) % cycle
    if min(local, cycle - local) < 1e-12:
        local = 0.0
    if local >= stance_s:
        return 0.0, 0.0, 0.0, 0.0, False
    u = local / stance_s
    support = _q(u)
    if u <= 0.5:
        exchange = _q(2.0 * u)
        early = exchange
        integral = 0.5 * _q_integral(2.0 * u)
    else:
        exchange = -_q(2.0 * u - 1.0)
        early = 0.0
        integral = 0.5 * (_q_integral(1.0) - _q_integral(2.0 * u - 1.0))
    return support, exchange, early, stance_s * integral, True


def resolved_airborne_forward_modulation(
    gait: AirborneGait, policy: AirborneBodyResponsePolicy
) -> float:
    if not isinstance(gait, AirborneGait) or not isinstance(
        policy, AirborneBodyResponsePolicy
    ):
        raise ContractError("airborne response requires validated gait and policy")
    speed = abs(gait.step_length_body_heights / gait.step_period_s)
    if not math.isfinite(speed) or speed <= 0:
        raise ContractError("airborne target speed must be positive finite")
    coefficient = (
        policy.reference_pelvis_forward_velocity_modulation_fraction
        * (policy.reference_speed_body_heights_per_s / speed) ** 2
    )
    if not math.isfinite(coefficient) or not 0 <= coefficient < 1:
        raise ContractError("resolved airborne forward modulation exceeds [0, 1)")
    return coefficient


def airborne_response_state(
    gait: AirborneGait,
    *,
    phase_s: float,
    body_height_m: float,
    tail_lag_fraction: float,
    policy: AirborneBodyResponsePolicy,
    performance_gain: float = 1.0,
    performance_gain_derivative_per_s: float = 0.0,
) -> AirborneResponseState:
    """Evaluate the exact per-limb event polynomials at an arbitrary time."""
    if not isinstance(gait, AirborneGait) or not isinstance(
        policy, AirborneBodyResponsePolicy
    ):
        raise ContractError("airborne response requires validated gait and policy")
    phase = _finite(phase_s, "airborne response phase")
    height = _finite(body_height_m, "airborne response body height")
    lag = _finite(tail_lag_fraction, "airborne response tail lag")
    gain = _finite(performance_gain, "airborne response performance gain")
    gain_derivative = _finite(
        performance_gain_derivative_per_s,
        "airborne response performance gain derivative",
    )
    if phase < 0 or height <= 0 or not 0 <= lag <= 0.4 or not 0 <= gain <= 1:
        raise ContractError("airborne response phase, height, lag, or gain exceeds bounds")

    left = _limb_state(gait, phase, 0.0)
    right = _limb_state(gait, phase, gait.step_period_s)
    lag_phase = (phase - lag * 2.0 * gait.step_period_s) % (
        2.0 * gait.step_period_s
    )
    lag_left = _limb_state(gait, lag_phase, 0.0)
    lag_right = _limb_state(gait, lag_phase, gait.step_period_s)
    lateral = left[0] - right[0]
    sagittal = 0.5 * (left[1] + right[1])
    acceptance = 0.5 * (left[2] + right[2])
    lagged_lateral = lag_left[0] - lag_right[0]

    coefficient = resolved_airborne_forward_modulation(gait, policy)
    speed_mps = gait.step_length_body_heights * height / gait.step_period_s
    unblended_displacement = -coefficient * speed_mps * 0.5 * (left[3] + right[3])
    unblended_velocity = -coefficient * speed_mps * sagittal
    displacement = gain * unblended_displacement
    velocity = gain * unblended_velocity + gain_derivative * unblended_displacement
    return AirborneResponseState(
        phase_s=phase,
        performance_gain=gain,
        performance_gain_derivative_per_s=gain_derivative,
        lateral_support=gain * lateral,
        sagittal_support=gain * sagittal,
        load_acceptance=gain * acceptance,
        lagged_lateral_support=gain * lagged_lateral,
        pelvis_forward_displacement_m=displacement,
        pelvis_forward_velocity_mps=velocity,
        resolved_forward_modulation_fraction=coefficient,
        support_count=int(left[4]) + int(right[4]),
    )


def airborne_response_receipt(
    gait: AirborneGait, policy: AirborneBodyResponsePolicy
) -> dict[str, Any]:
    """Return detached, JSON-ready resolution metadata for provenance."""
    coefficient = resolved_airborne_forward_modulation(gait, policy)
    return {
        "schema": "eonwild.motion.airborne-body-response-resolution.v1",
        "classification": "authored event-bound kinematic coordination; no dynamics or biological claim",
        "model": MODEL,
        "carrier_mapping": dict(policy.carrier_mapping),
        "reference_speed_body_heights_per_s": policy.reference_speed_body_heights_per_s,
        "target_speed_body_heights_per_s": abs(
            gait.step_length_body_heights / gait.step_period_s
        ),
        "forward_modulation_formula": "k_ref * (v_ref / abs(v_target)) ** 2",
        "resolved_pelvis_forward_velocity_modulation_fraction": coefficient,
        "transition_velocity_rule": "product_rule_gD_prime_plus_g_prime_D",
    }


def decorate_airborne_response_plan(
    plan: Mapping[str, Any],
    performance: Any,
    gait: AirborneGait,
    policy_document: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach one validated airborne response without changing legacy paths."""
    from .performance import Performance

    if not isinstance(plan, Mapping) or not isinstance(performance, Performance):
        raise ContractError("airborne plan decoration requires plan and performance")
    if not isinstance(gait, AirborneGait):
        raise ContractError("airborne plan decoration requires a validated gait")
    program = plan.get("program")
    locomotion = plan.get("locomotion_program", program)
    if program not in {"airborne_gait", "gait_transition"} or locomotion != "airborne_gait":
        raise ContractError("airborne body response requires airborne locomotion")
    policy = load_airborne_body_response_policy(policy_document)
    if plan.get("parameters") != gait_parameters(gait):
        raise ContractError("airborne response gait differs from authoritative plan parameters")
    result = deepcopy(dict(plan))
    result["performance"] = {
        key: value
        for key, value in asdict(performance).items()
        if value is not None
        and not (
            key == "pelvis_forward_velocity_modulation_fraction" and value == 0
        )
        and not (
            key == "neutral_jaw_calibration" and value["close_degrees"] == 0
        )
    }
    result["airborne_body_response"] = {
        "policy": deepcopy(dict(policy_document)),
        "resolution": airborne_response_receipt(gait, policy),
    }
    result["loop"] = bool(plan.get("loop", True))
    from ..planning.foot_articulation import declare_pad_recovery

    declare_pad_recovery(result)
    return result
