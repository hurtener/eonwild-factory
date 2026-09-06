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
    skin_refinement: bool = True

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key in ("center_tail", "skin_refinement"):
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
    if document.get("schema") != "eonwild.motion.performance.v1" or set(document) - {"schema", "parameters", "reference", "classification"}:
        raise ContractError("unsupported performance profile")
    parameters = document.get("parameters")
    if not isinstance(parameters, Mapping) or set(parameters) - set(Performance.__dataclass_fields__):
        raise ContractError("unknown performance parameters")
    return Performance(**parameters)


def decorate_plan(plan: dict, performance: Performance) -> dict:
    # Plan and state are per-request. Never cache or monkey-patch a rig/module.
    from copy import deepcopy
    result = deepcopy(plan)
    result["performance"] = asdict(performance)
    result["loop"] = plan.get("loop", True)
    return result


def _world_delta(source, translations, rotations, scales, node, axis, degrees):
    if abs(degrees) < 1e-12:
        return
    worlds = _world_matrices(source, translations, rotations, scales)
    delta = _qrotvec(tuple(np.asarray(axis) * math.radians(degrees)))
    rotations[node] = _world_rotation(source, worlds, node, _qmul(delta, _rotation_from_matrix(worlds[node])))


def apply_performance(source, translations, rotations, scales, base_worlds, roles, plan, row, up, forward):
    """Resolve tail rest bias, support-alternating body response and gaze.

    The following leg solve restores contacts after pelvis/body rotation. Yaw
    centres only the tail's horizontal curvature; its sagittal shape is kept.
    Head direction is a calibrated neutral-relative attention vector, not a
    claim about an unmeasured anatomical optic axis.
    """
    if "performance" not in plan:
        return
    p = Performance(**plan["performance"])
    lateral = _unit(np.cross(up, forward))
    pelvis = source.name_to_node[roles["pelvis"]]
    cycle = float(plan["same_foot_cycle_s"])
    angle = 2 * math.pi * row["time_s"] / cycle
    pulse = math.sin(angle)
    parent = source.parents[pelvis]
    parent_basis = np.eye(3) if parent is None else np.asarray(base_worlds[parent])[:3, :3]
    shift = lateral * (p.pelvis_sway_body_heights * plan["body_height_m"] * pulse)
    translations[pelvis] = tuple(np.asarray(translations[pelvis]) + np.linalg.solve(parent_basis, shift))
    _world_delta(source, translations, rotations, scales, pelvis, up, p.pelvis_yaw_degrees * pulse)
    _world_delta(source, translations, rotations, scales, pelvis, forward, p.pelvis_roll_degrees * pulse)
    chest = source.name_to_node[roles["chest"]]
    _world_delta(source, translations, rotations, scales, chest, up, -.65 * p.pelvis_yaw_degrees * pulse)
    tail = [source.name_to_node[n] for n in roles["tail"]]
    if p.center_tail:
        for node, child in zip(tail, tail[1:]):
            worlds = _world_matrices(source, translations, rotations, scales)
            delta = np.asarray(_world_position(worlds[child])) - _world_position(worlds[node])
            ground = delta - up * float(delta @ up)
            direction = _unit(ground)
            target = -np.asarray(forward)
            yaw = math.degrees(math.atan2(float(up @ np.cross(direction, target)), float(direction @ target)))
            _world_delta(source, translations, rotations, scales, node, up, yaw)
    # A travelling phase and increasing distal delay, not one rigid wag.
    weights = np.linspace(.6, 1.4, len(tail)); weights /= weights.sum()
    for i, node in enumerate(tail):
        lag = p.tail_lag_fraction * i / max(1, len(tail) - 1)
        degrees = -p.tail_yaw_degrees * weights[i] * math.sin(angle - 2 * math.pi * lag)
        _world_delta(source, translations, rotations, scales, node, up, degrees)
    head = source.name_to_node[roles["head"]]
    neutral_forward = _qrotate(_qinv(_rotation_from_matrix(base_worlds[head])), tuple(forward))
    worlds = _world_matrices(source, translations, rotations, scales)
    current = np.asarray(_qrotate(_rotation_from_matrix(worlds[head]), neutral_forward))
    elevation = math.degrees(math.atan2(float(current @ up), float(current @ forward)))
    # World lateral positive rotation lowers a +forward head; signs explicit.
    error = elevation - p.gaze_elevation_degrees
    neck = [source.name_to_node[n] for n in roles.get("neck", [])]
    for node in neck:
        _world_delta(source, translations, rotations, scales, node, lateral, .6 * error / len(neck))
    worlds = _world_matrices(source, translations, rotations, scales)
    current = np.asarray(_qrotate(_rotation_from_matrix(worlds[head]), neutral_forward))
    elevation = math.degrees(math.atan2(float(current @ up), float(current @ forward)))
    _world_delta(source, translations, rotations, scales, head, lateral, elevation - p.gaze_elevation_degrees)
