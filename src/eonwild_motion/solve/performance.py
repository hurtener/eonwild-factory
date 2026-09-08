"""Bounded semantic performance, applied BEFORE the V9 limb/contact solve.

These are art-directed coordination controls, not simulated muscle forces.
No rig names or species branches occur here. Source geometry stays immutable.
"""
from __future__ import annotations

from collections.abc import Sequence
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
    upper_trunk_counterroll_degrees: float | None = None
    support_timed_sagittal_carrier: bool | None = None
    pelvis_support_pitch_degrees: float | None = None
    upper_trunk_counterpitch_degrees: float | None = None
    neck_counterpitch_degrees: float | None = None
    tail_counterpitch_degrees: float | None = None
    skin_refinement: bool = True

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key in ("center_lanes_on_bilateral_hip_midpoint",
                       "support_directed_pelvis_carrier",
                       "upper_trunk_counterroll_degrees",
                       "support_timed_sagittal_carrier",
                       "pelvis_support_pitch_degrees",
                       "upper_trunk_counterpitch_degrees",
                       "neck_counterpitch_degrees",
                       "tail_counterpitch_degrees") and value is None:
                continue
            if key in ("center_tail", "center_lanes_on_bilateral_hip_midpoint",
                       "support_directed_pelvis_carrier",
                       "support_timed_sagittal_carrier", "skin_refinement"):
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
        if (self.upper_trunk_counterroll_degrees is not None
                and not 0 <= self.upper_trunk_counterroll_degrees <= 3):
            raise ContractError("upper-trunk counterroll exceeds the authored envelope")
        if (self.upper_trunk_counterroll_degrees is not None
                and self.support_directed_pelvis_carrier is not True):
            raise ContractError(
                "upper-trunk counterroll requires the support-directed pelvis carrier")
        sagittal = (
            self.pelvis_support_pitch_degrees,
            self.upper_trunk_counterpitch_degrees,
            self.neck_counterpitch_degrees,
            self.tail_counterpitch_degrees,
        )
        if self.support_timed_sagittal_carrier is True:
            if any(value is None for value in sagittal):
                raise ContractError(
                    "support-timed sagittal carrier requires all pitch amplitudes")
        elif any(value is not None for value in sagittal):
            raise ContractError(
                "sagittal pitch amplitudes require the support-timed carrier")
        sagittal_limits = (
            (self.pelvis_support_pitch_degrees, 3., "pelvis support pitch"),
            (self.upper_trunk_counterpitch_degrees, 3., "upper-trunk counterpitch"),
            (self.neck_counterpitch_degrees, 2., "neck counterpitch"),
            (self.tail_counterpitch_degrees, 4., "tail counterpitch"),
        )
        for value, limit, label in sagittal_limits:
            if value is not None and not 0 <= value <= limit:
                raise ContractError(f"{label} exceeds the authored envelope")


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
    if performance.support_timed_sagittal_carrier is not None:
        grounded = (plan.get("program") == "grounded_gait"
                    or plan.get("locomotion_program") == "grounded_gait")
        if not grounded:
            raise ContractError(
                "support-timed sagittal carrier requires grounded locomotion")
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
    grounded = (plan.get("program") == "grounded_gait"
                or plan.get("locomotion_program") == "grounded_gait")
    if not grounded:
        raise ContractError(
            "support-directed pelvis carrier requires grounded locomotion")
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


def _support_timed_sagittal_pulse(plan, phase, gain):
    """C2 support clock shared by both sides of a grounded gait.

    Positive values occur at declared double-support midpoints and negative
    values at declared single-support midpoints. This is an authored kinematic
    clock, not a load, force, energy, or center-of-mass estimate.
    """
    grounded = (plan.get("program") == "grounded_gait"
                or plan.get("locomotion_program") == "grounded_gait")
    if not grounded:
        raise ContractError(
            "support-timed sagittal carrier requires grounded locomotion")
    parameters = plan.get("parameters")
    if not isinstance(parameters, Mapping):
        raise ContractError(
            "support-timed sagittal carrier requires gait parameters")
    duty = parameters.get("duty_factor")
    cycle = plan.get("same_foot_cycle_s")
    if (isinstance(duty, bool) or not isinstance(duty, (int, float))
            or not math.isfinite(duty) or not .5 < duty < 1
            or isinstance(cycle, bool) or not isinstance(cycle, (int, float))
            or not math.isfinite(cycle) or cycle <= 0):
        raise ContractError(
            "support-timed sagittal carrier requires finite grounded timing")
    step = float(cycle) / 2
    stance_clock = phase / step - float(duty)
    return -gain * math.cos(2 * math.pi * stance_clock)


def _counterroll_trunk_names(roles: Mapping[str, Any]) -> list[str]:
    """Admit one semantic upper-body chain without accepting unrelated roles."""
    if not isinstance(roles, Mapping):
        raise ContractError("upper-trunk counterroll requires semantic rig roles")

    def name(value, label):
        if not isinstance(value, str) or not value:
            raise ContractError(
                f"upper-trunk counterroll requires a valid semantic {label} role")
        return value

    def names(value, label, *, nonempty=False):
        if (not isinstance(value, Sequence) or isinstance(value, (str, bytes))
                or (nonempty and not value)):
            raise ContractError(
                f"upper-trunk counterroll requires a valid semantic {label} sequence")
        result = [name(item, label) for item in value]
        if len(result) != len(set(result)):
            raise ContractError(
                f"upper-trunk counterroll requires unique semantic {label} roles")
        return result

    spine = names(roles.get("spine"), "spine", nonempty=True)
    chest = name(roles.get("chest"), "chest")
    trunk = [*spine, chest]
    if len(trunk) != len(set(trunk)):
        raise ContractError(
            "upper-trunk counterroll requires a unique semantic spine/chest chain")

    reserved = {
        name(roles.get("root"), "root"),
        name(roles.get("pelvis"), "pelvis"),
        name(roles.get("head"), "head"),
        *names(roles.get("neck"), "neck"),
        *names(roles.get("tail"), "tail"),
    }
    legs = roles.get("legs")
    if not isinstance(legs, Mapping):
        raise ContractError(
            "upper-trunk counterroll requires semantic bilateral leg roles")
    for side in ("left", "right"):
        leg = legs.get(side)
        if not isinstance(leg, Mapping):
            raise ContractError(
                "upper-trunk counterroll requires semantic bilateral leg roles")
        reserved.update(names(
            leg.get("contactChain"), f"{side} contact chain", nonempty=True))
        toe_chains = leg.get("toeChains")
        if (not isinstance(toe_chains, Sequence)
                or isinstance(toe_chains, (str, bytes))):
            raise ContractError(
                "upper-trunk counterroll requires semantic toe-chain roles")
        for index, toe_chain in enumerate(toe_chains):
            reserved.update(names(
                toe_chain, f"{side} toe chain {index}", nonempty=True))
    if set(trunk) & reserved:
        raise ContractError(
            "upper-trunk counterroll spine/chest must be disjoint from other semantic roles")
    return trunk


def _sagittal_body_chains(source, roles: Mapping[str, Any]):
    """Admit typed, disjoint body chains and their actual hierarchy."""
    trunk = _counterroll_trunk_names(roles)
    neck = list(roles["neck"])
    tail = list(roles["tail"])
    head = roles["head"]
    root = roles["root"]
    pelvis = roles["pelvis"]
    leg_names = []
    for side in ("left", "right"):
        leg = roles["legs"][side]
        leg_names.extend(leg["contactChain"])
        for toe_chain in leg["toeChains"]:
            leg_names.extend(toe_chain)
    all_names = [root, pelvis, *trunk, *neck, head, *tail, *leg_names]
    if len(all_names) != len(set(all_names)):
        raise ContractError(
            "sagittal body chains must be disjoint from other semantic roles")
    if any(name not in source.name_to_node for name in all_names):
        raise ContractError(
            "sagittal body chains require admitted semantic nodes")
    nodes = {
        "trunk": [source.name_to_node[name] for name in trunk],
        "neck": [source.name_to_node[name] for name in neck],
        "tail": [source.name_to_node[name] for name in tail],
    }
    pelvis_node = source.name_to_node[pelvis]
    chest_node = source.name_to_node[trunk[-1]]
    head_node = source.name_to_node[head]
    if (source.parents[nodes["trunk"][0]] != pelvis_node
            or any(source.parents[child] != parent
                   for parent, child in zip(nodes["trunk"], nodes["trunk"][1:]))
            or not nodes["neck"]
            or source.parents[nodes["neck"][0]] != chest_node
            or any(source.parents[child] != parent
                   for parent, child in zip(nodes["neck"], nodes["neck"][1:]))
            or source.parents[head_node] != nodes["neck"][-1]
            or not nodes["tail"]
            or source.parents[nodes["tail"][0]] != pelvis_node
            or any(source.parents[child] != parent
                   for parent, child in zip(nodes["tail"], nodes["tail"][1:]))):
        raise ContractError(
            "sagittal body semantic roles must follow actual topology")
    return nodes


def _distributed_world_delta(
        source, translations, rotations, scales, nodes, axis, total_degrees):
    weights = np.linspace(.6, 1.4, len(nodes))
    weights /= weights.sum()
    for node, weight in zip(nodes, weights):
        _world_delta(
            source, translations, rotations, scales, node, axis,
            total_degrees * float(weight))


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
    trunk_names = (_counterroll_trunk_names(roles)
                   if p.upper_trunk_counterroll_degrees is not None else None)
    sagittal_chains = (_sagittal_body_chains(source, roles)
                       if p.support_timed_sagittal_carrier is True else None)
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
    sagittal_pulse = 0.
    if p.support_directed_pelvis_carrier:
        sway_pulse = _support_directed_pulse(
            source, base_worlds, roles, plan, phase, gain, lateral)
        # Positive world rotation about forward leans the pelvis top toward
        # negative lateral, so invert the translation carrier for the lean.
        roll_pulse = -sway_pulse
    if p.support_timed_sagittal_carrier:
        sagittal_pulse = _support_timed_sagittal_pulse(
            plan, phase, gain)
    parent = source.parents[pelvis]
    parent_basis = np.eye(3) if parent is None else np.asarray(base_worlds[parent])[:3, :3]
    shift = lateral * (p.pelvis_sway_body_heights * plan["body_height_m"] * sway_pulse)
    translations[pelvis] = tuple(np.asarray(translations[pelvis]) + np.linalg.solve(parent_basis, shift))
    _world_delta(source, translations, rotations, scales, pelvis, up, p.pelvis_yaw_degrees * pulse)
    _world_delta(source, translations, rotations, scales, pelvis, forward, p.pelvis_roll_degrees * roll_pulse)
    if p.pelvis_support_pitch_degrees is not None:
        # Positive rotation about lateral tips the pelvis up axis toward
        # declared forward and its forward axis toward declared down.
        _world_delta(
            source, translations, rotations, scales, pelvis, lateral,
            p.pelvis_support_pitch_degrees * sagittal_pulse)
    chest = source.name_to_node[roles["chest"]]
    _world_delta(source, translations, rotations, scales, chest, up, -.65 * p.pelvis_yaw_degrees * pulse)
    if p.upper_trunk_counterroll_degrees is not None:
        assert trunk_names is not None
        if any(name not in source.name_to_node for name in trunk_names):
            raise ContractError(
                "upper-trunk counterroll requires a unique semantic spine/chest chain")
        trunk = [source.name_to_node[name] for name in trunk_names]
        if (source.parents[trunk[0]] != pelvis
                or any(source.parents[child] != parent
                       for parent, child in zip(trunk, trunk[1:]))):
            raise ContractError(
                "upper-trunk counterroll semantic roles must follow actual topology")
        weights = np.linspace(.6, 1.4, len(trunk))
        weights /= weights.sum()
        for node, weight in zip(trunk, weights):
            _world_delta(
                source, translations, rotations, scales, node, forward,
                p.upper_trunk_counterroll_degrees * sway_pulse * float(weight))
    if p.upper_trunk_counterpitch_degrees is not None:
        assert sagittal_chains is not None
        _distributed_world_delta(
            source, translations, rotations, scales,
            sagittal_chains["trunk"], lateral,
            -p.upper_trunk_counterpitch_degrees * sagittal_pulse)
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
    if p.tail_counterpitch_degrees is not None:
        assert sagittal_chains is not None
        _distributed_world_delta(
            source, translations, rotations, scales,
            sagittal_chains["tail"], lateral,
            -p.tail_counterpitch_degrees * sagittal_pulse)
    head = source.name_to_node[roles["head"]]
    neck = [source.name_to_node[n] for n in roles.get("neck", [])]
    if p.neck_counterpitch_degrees is not None:
        assert sagittal_chains is not None
        _distributed_world_delta(
            source, translations, rotations, scales,
            sagittal_chains["neck"], lateral,
            -p.neck_counterpitch_degrees * sagittal_pulse)
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
