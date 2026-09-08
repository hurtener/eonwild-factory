"""Bounded semantic performance, applied BEFORE the V9 limb/contact solve.

These are art-directed coordination controls, not simulated muscle forces.
No rig names or species branches occur here. Source geometry stays immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Any, Mapping
import numpy as np

from ..errors import ContractError
from ..layers.leg_contact_resolve_v3 import _world_matrices, _world_position, _rotation_from_matrix, _qmul, _qinv
from .airborne_gait import _qrotate, _qrotvec, _world_rotation, _unit


@dataclass(frozen=True)
class Performance:
    lane_width_body_heights: float = .24
    pelvis_sway_body_heights: float = .008
    pelvis_yaw_degrees: float = 2.0
    pelvis_roll_degrees: float = .7
    tail_yaw_degrees: float = 12.0
    tail_lag_fraction: float = .12
    gaze_elevation_degrees: float = 3.0
    center_tail: bool = True
    center_lanes_on_bilateral_hip_midpoint: bool | None = None
    support_directed_pelvis_carrier: bool | None = None
    skin_refinement: bool = True

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key in ("center_lanes_on_bilateral_hip_midpoint",
                       "support_directed_pelvis_carrier") and value is None:
                continue
            if key in ("center_tail", "center_lanes_on_bilateral_hip_midpoint",
                       "support_directed_pelvis_carrier", "skin_refinement"):
                if type(value) is not bool:
                    raise ContractError(f"{key} must be boolean")
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ContractError(f"performance {key} must be finite numeric")
        if not .1 <= self.lane_width_body_heights <= .6 or not 0 <= self.pelvis_sway_body_heights <= .04:
            raise ContractError("performance lanes/sway exceed the family envelope")
        if not 0 <= self.pelvis_yaw_degrees <= 8 or not 0 <= self.pelvis_roll_degrees <= 4:
            raise ContractError("pelvis performance exceeds the envelope")
        if not 0 <= self.tail_yaw_degrees <= 25 or not 0 <= self.tail_lag_fraction <= .4:
            raise ContractError("tail performance exceeds the envelope")
        if not -10 <= self.gaze_elevation_degrees <= 20:
            raise ContractError("gaze performance exceeds the envelope")


def load_performance(document: Mapping[str, Any]) -> Performance:
    if not isinstance(document, Mapping) or document.get("schema") != "eonwild.motion.performance.v1" or set(document) - {"schema", "parameters", "reference", "classification"}:
        raise ContractError("unsupported performance profile")
    parameters = document.get("parameters")
    if not isinstance(parameters, Mapping) or set(parameters) - set(Performance.__dataclass_fields__):
        raise ContractError("unknown performance parameters")
    return Performance(**parameters)


def decorate_plan(plan: dict, performance: Performance) -> dict:
    from copy import deepcopy
    if performance.support_directed_pelvis_carrier is not None:
        grounded = (plan.get("program") == "grounded_gait"
                    or plan.get("locomotion_program") == "grounded_gait")
        if not grounded:
            raise ContractError(
                "support-directed pelvis carrier requires grounded locomotion")
    result = deepcopy(plan)
    result["performance"] = {key: value for key, value in asdict(performance).items()
                             if value is not None}
    result["loop"] = plan.get("loop", True)
    from ..planning.foot_articulation import declare_pad_recovery
    declare_pad_recovery(result)
    return result


def phase_and_gain(row):
    """One clock for limbs, body, tail and breathing across a gait handoff."""
    phase = row.get("locomotion_time_s", row["time_s"])
    gain = row.get("performance_gain", 1.)
    for value in (phase, gain):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError("performance phase and gain must be finite numeric")
    if phase < 0 or not 0 <= gain <= 1:
        raise ContractError("invalid performance phase or gain")
    return float(phase), float(gain)


def _world_delta(source, translations, rotations, scales, node, axis, degrees):
    if abs(degrees) < 1e-12:
        return
    worlds = _world_matrices(source, translations, rotations, scales)
    delta = _qrotvec(tuple(np.asarray(axis) * math.radians(degrees)))
    rotations[node] = _world_rotation(source, worlds, node, _qmul(delta, _rotation_from_matrix(worlds[node])))


def _support_directed_pulse(source, base_worlds, roles, plan, phase, gain, lateral):
    """Smooth signed support carrier derived from semantic bilateral hips.

    Positive values follow the declared lateral axis; which sign names the
    semantic left support comes from the admitted bilateral hip geometry.
    Extrema occur at declared stance midpoints, with zero at
    double-support midpoints. This is authored coordination, not load or COM.
    """
    parameters = plan.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ContractError("support-directed pelvis carrier requires gait parameters")
    duty = parameters.get("duty_factor")
    cycle = plan.get("same_foot_cycle_s")
    if (isinstance(duty, bool) or not isinstance(duty, (int, float))
            or not math.isfinite(duty) or not .5 < duty < 1
            or isinstance(cycle, bool) or not isinstance(cycle, (int, float))
            or not math.isfinite(cycle) or cycle <= 0):
        raise ContractError(
            "support-directed pelvis carrier requires finite grounded timing")
    try:
        hips = {side: source.name_to_node[roles["legs"][side]["contactChain"][0]]
                for side in ("left", "right")}
    except (KeyError, TypeError, IndexError) as exc:
        raise ContractError(
            "support-directed pelvis carrier requires semantic bilateral hips") from exc
    hip_positions = {side: np.asarray(_world_position(base_worlds[node]), dtype=float)
                     for side, node in hips.items()}
    separation = float((hip_positions["right"] - hip_positions["left"]) @ lateral)
    if not math.isfinite(separation) or abs(separation) <= 1e-8:
        raise ContractError(
            "semantic hips must be separated along the declared lateral axis")
    left_sign = -math.copysign(1.0, separation)
    step = float(cycle) / 2
    stance_clock = phase / step - float(duty)
    return gain * left_sign * math.cos(math.pi * stance_clock)


def apply_performance(source, translations, rotations, scales, base_worlds, roles, plan, row, up, forward):
    """Resolve rest-tail bias, lateral support response, and forward attention.

    The subsequent limb solve restores contacts after body rotation. The gaze
    axis is neutral-relative calibration, not a measured anatomical optic axis.
    Ready/start/stop poses share the same centered-tail calibration; authored
    oscillation, body sway, and elevated attention blend with locomotion gain.
    """
    if "performance" not in plan:
        return
    p = Performance(**plan["performance"])
    phase, gain = phase_and_gain(row)
    lateral = _unit(np.cross(up, forward))
    pelvis = source.name_to_node[roles["pelvis"]]
    cycle = float(plan["same_foot_cycle_s"])
    if not math.isfinite(cycle) or cycle <= 0:
        raise ContractError("performance requires a positive finite gait period")
    angle = 2 * math.pi * phase / cycle
    pulse = gain * math.sin(angle)
    sway_pulse = pulse
    roll_pulse = pulse
    if p.support_directed_pelvis_carrier:
        sway_pulse = _support_directed_pulse(
            source, base_worlds, roles, plan, phase, gain, lateral)
        # Positive world rotation about forward leans the pelvis top toward
        # negative lateral, so invert the translation carrier for the lean.
        roll_pulse = -sway_pulse
    parent = source.parents[pelvis]
    parent_basis = np.eye(3) if parent is None else np.asarray(base_worlds[parent])[:3, :3]
    shift = lateral * (p.pelvis_sway_body_heights * plan["body_height_m"] * sway_pulse)
    translations[pelvis] = tuple(np.asarray(translations[pelvis]) + np.linalg.solve(parent_basis, shift))
    _world_delta(source, translations, rotations, scales, pelvis, up, p.pelvis_yaw_degrees * pulse)
    _world_delta(source, translations, rotations, scales, pelvis, forward, p.pelvis_roll_degrees * roll_pulse)
    chest = source.name_to_node[roles["chest"]]
    _world_delta(source, translations, rotations, scales, chest, up, -.65 * p.pelvis_yaw_degrees * pulse)
    tail = [source.name_to_node[n] for n in roles["tail"]]
    if p.center_tail:
        for node, child in zip(tail, tail[1:]):
            worlds = _world_matrices(source, translations, rotations, scales)
            delta = np.asarray(_world_position(worlds[child])) - _world_position(worlds[node])
            direction = _unit(delta - up * float(delta @ up))
            target = -np.asarray(forward)
            yaw = math.degrees(math.atan2(float(up @ np.cross(direction, target)), float(direction @ target)))
            _world_delta(source, translations, rotations, scales, node, up, yaw)
    weights = np.linspace(.6, 1.4, len(tail))
    if len(weights):
        weights /= weights.sum()
    for i, node in enumerate(tail):
        lag = p.tail_lag_fraction * i / max(1, len(tail) - 1)
        degrees = -gain * p.tail_yaw_degrees * weights[i] * math.sin(angle - 2 * math.pi * lag)
        _world_delta(source, translations, rotations, scales, node, up, degrees)
    head = source.name_to_node[roles["head"]]
    neck = [source.name_to_node[n] for n in roles.get("neck", [])]
    calibration = plan.get("gaze_calibration")
    if calibration is None:
        # Preserve the low-level/synthetic compatibility path. The active
        # factory supplies a geometry-derived rostral axis explicitly.
        neutral_forward = _qrotate(_qinv(_rotation_from_matrix(base_worlds[head])), tuple(forward))
    else:
        from .gaze import load_rostral_calibration, relative_attention_elevation
        neutral_forward, neutral_elevation = load_rostral_calibration(calibration, roles["head"])

    def direction():
        worlds = _world_matrices(source, translations, rotations, scales)
        return np.asarray(_qrotate(_rotation_from_matrix(worlds[head]), neutral_forward))

    def yaw_error():
        current = direction()
        ground = _unit(current - up * float(current @ up))
        return math.degrees(math.atan2(float(up @ np.cross(ground, forward)), float(ground @ forward)))

    # Pitch-only stabilization could leave the head aimed beside the prey.
    # Resolve yaw through the neck and then the residual at the head.
    yaw = yaw_error()
    for node in neck:
        _world_delta(source, translations, rotations, scales, node, up, .6 * yaw / len(neck))
    _world_delta(source, translations, rotations, scales, head, up, yaw_error())
    # The authored value is a bounded offset from the admitted neutral rostral
    # direction, rather than a command to level (or raise) the muzzle in the
    # world frame.  This retains the source's ordinary neck curve while still
    # allowing a locomotion-gated forward-attention response.
    target_elevation = (gain * p.gaze_elevation_degrees if calibration is None
                        else relative_attention_elevation(calibration, roles["head"], gain * p.gaze_elevation_degrees))
    current = direction()
    error = math.degrees(math.atan2(float(current @ up), float(current @ forward))) - target_elevation
    for node in neck:
        _world_delta(source, translations, rotations, scales, node, lateral, .6 * error / len(neck))
    current = direction()
    error = math.degrees(math.atan2(float(current @ up), float(current @ forward))) - target_elevation
    _world_delta(source, translations, rotations, scales, head, lateral, error)
