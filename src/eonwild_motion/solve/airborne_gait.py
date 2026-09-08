"""Semantic, geometry-derived rotation-only IK emission for airborne gait.

No species names, fixed bone IDs, per-bone translation offsets, or scaled
limbs. Root travel and pelvis bounce are the only translated degrees of
freedom. In-place is a projection of the solved root-motion authority.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import (
    _clip_state, _pose, _world_matrices, _world_position, _rotation_from_matrix,
    _qmul, _qinv, _qrotate as _scalar_qrotate, _qrotvec as _scalar_qrotvec,
)
from ..planning.airborne_gait import AirborneGait, build_airborne_plan, sample_airborne_gait, jaw_breathing_angle, _smooth
from ..planning.articulation_profile import ArticulationProfile
from .whole_body_gait_transition import _build_glb, _encode


def _qrotate(q, point):
    # Keep NumPy scalars out of the shared pure-Python matrix evaluator: each
    # NumPy scalar multiply otherwise allocates inside its nested FK loops.
    return _scalar_qrotate(tuple(float(v) for v in q), tuple(float(v) for v in point))


def _qrotvec(vector):
    return _scalar_qrotvec(tuple(float(v) for v in vector))


def _unit(v: Any) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    length = np.linalg.norm(a)
    if length < 1e-10:
        raise ContractError("airborne geometry has a degenerate direction")
    return a / length


def _between(a: Any, b: Any) -> tuple[float, ...]:
    a, b = _unit(a), _unit(b)
    dot = float(np.clip(a @ b, -1, 1))
    if dot < -0.999999:
        candidate = np.eye(3)[int(np.argmin(np.abs(a)))]
        axis = _unit(np.cross(a, candidate))
        return tuple(axis) + (0.0,)
    q = np.r_[np.cross(a, b), 1 + dot]
    return tuple(float(v) for v in q / np.linalg.norm(q))


def _world_rotation(glb: Glb, worlds: Any, node: int, desired: Any) -> tuple[float, ...]:
    parent = glb.parents[node]
    pq = (0, 0, 0, 1) if parent is None else _rotation_from_matrix(worlds[parent])
    return _qmul(_qinv(pq), tuple(desired))


def _local_delta(glb: Glb, worlds: Any, node: int, world_delta: Any) -> np.ndarray:
    parent = glb.parents[node]
    basis = np.eye(3) if parent is None else np.asarray(worlds[parent])[:3, :3]
    return np.linalg.solve(basis, np.asarray(world_delta))


def stable_knee_geometry(hip: np.ndarray, target: np.ndarray, upper: float, lower: float, anatomical_normal: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Unique anatomical branch, without projecting a moving hip-knee pole.

    The oriented source bend normal is projected onto the target plane. This
    remains on one knee branch as the target passes the old source-pole ray.
    """
    direction = _unit(target - hip)
    distance0 = float(np.linalg.norm(target - hip))
    distance = float(np.clip(distance0, abs(upper - lower) + 1e-7, upper + lower - 1e-7))
    bend = _unit(np.cross(direction, anatomical_normal))
    along = (upper * upper - lower * lower + distance * distance) / (2 * distance)
    knee = hip + direction * along + bend * math.sqrt(max(0, upper * upper - along * along))
    return knee, hip + direction * distance, abs(distance0 - distance)


def _interior(a: np.ndarray, b: np.ndarray) -> float:
    return math.degrees(math.acos(float(np.clip(_unit(a) @ _unit(b), -1, 1))))


def _world_sagittal_degrees(direction: Any, forward: np.ndarray, up: np.ndarray) -> float:
    """Signed direction from down: positive points toward declared forward."""
    vector = _unit(direction)
    return math.degrees(math.atan2(float(vector @ forward), -float(vector @ up)))


def _world_metatarsus_recovery(foot_plan: Mapping[str, Any]) -> tuple[float, float] | None:
    """Return the common world target and its C2 recovery gain, when authored."""
    peak = foot_plan.get("metatarsal_recovery_world_degrees_from_down")
    gain = foot_plan.get("metatarsal_recovery_gain")
    if peak is None and gain is None:
        return None
    if (peak is None) != (gain is None):
        raise ContractError("world metatarsal recovery target and gain must be declared together")
    for value, label in ((peak, "world metatarsal recovery target"),
                         (gain, "world metatarsal recovery gain")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError(f"{label} must be finite numeric")
    if not -90 <= peak <= 90 or not 0 <= gain <= 1:
        raise ContractError("world metatarsal recovery target or gain is outside its authored envelope")
    return float(peak), float(gain)


def _recovery_pitch_target(gait: AirborneGait, foot_plan: Mapping[str, Any], *, airborne: bool) -> float:
    """Phase-pure pitch carrier for the returning half of swing.

    The carrier starts and ends with zero slope and derives its excursion from
    the authored hip-lift response. It keeps the articulation solve on one
    recovery branch without consulting a previously sampled pose.
    """
    authored = float(foot_plan["foot_pitch_degrees"])
    u = float(foot_plan["swing_phase"])
    peak = gait.swing_recovery_peak_fraction
    if not airborne or foot_plan["contact"] or u <= peak:
        return authored
    progress = (u - peak) / (1 - peak)
    recovery_fold = math.sin(math.pi * progress) ** 2
    scale = float(foot_plan.get("articulation_scale", 1.0))
    return authored - 0.5 * gait.swing_hip_lift_degrees * scale * recovery_fold


def _orientation_from_bend(source_upper: np.ndarray, source_normal: np.ndarray, target_upper: np.ndarray, target_normal: np.ndarray) -> tuple[float, ...]:
    """Map both the bone axis and its bend plane; a direction alone loses twist."""
    a, b = _unit(source_upper), _unit(target_upper)
    sn = _unit(source_normal - a * float(source_normal @ a))
    tn = _unit(target_normal - b * float(target_normal @ b))
    original = np.column_stack((a, sn, np.cross(a, sn)))
    desired = np.column_stack((b, tn, np.cross(b, tn)))
    matrix = np.eye(4)
    matrix[:3, :3] = desired @ original.T
    return _rotation_from_matrix(tuple(tuple(float(v) for v in row) for row in matrix))


def periodic_response(times: Any, drive: Any, response_time_s: float) -> np.ndarray:
    """Exact first-order lag for linearly sampled drive, initialized cyclically.

    This is a bounded kinematic response, not a force/momentum simulation.
    Its periodic initial state avoids startup decay and loop-reset jumps.
    """
    times, drive = np.asarray(times, dtype=float), np.asarray(drive, dtype=float)
    if len(times) != len(drive) or len(times) < 2 or response_time_s <= 0 or np.any(np.diff(times) <= 0):
        raise ContractError("periodic response needs ordered samples and positive lag")
    if abs(float(drive[-1] - drive[0])) > 1e-8:
        raise ContractError("periodic response drive must close at the seam")
    def advance(state, index):
        dt = times[index] - times[index - 1]
        decay = math.exp(-dt / response_time_s)
        return decay * state + (1 - decay) * drive[index - 1] + (1 - response_time_s * (1 - decay) / dt) * (drive[index] - drive[index - 1])
    state = 0.0
    for i in range(1, len(times)):
        state = advance(state, i)
    initial = state / -math.expm1(-(times[-1] - times[0]) / response_time_s)
    result = [initial]
    for i in range(1, len(times)):
        result.append(advance(result[-1], i))
    return np.asarray(result)


def sample_periodic_response(times: Any, drive: Any, response_time_s: float, sample_times: Any) -> np.ndarray:
    """Evaluate the lag's analytic interval solution at declared query times.

    Interpolating *states* would add velocity discontinuities. The same linear
    input and cyclic initial state define this continuous evaluation. Exact
    reference knots return the original states, not fitted replacements.
    """
    times, drive, query = (np.asarray(v, dtype=float) for v in (times, drive, sample_times))
    if (times.ndim != 1 or drive.shape != times.shape or query.ndim != 1
        or not all(np.isfinite(v).all() for v in (times, drive, query))
        or len(times) < 2 or not math.isfinite(response_time_s) or response_time_s <= 0
        or np.any(np.diff(times) <= 0) or np.any(query < times[0]) or np.any(query > times[-1])):
        raise ContractError("continuous periodic response needs finite ordered data and in-range queries")
    states = periodic_response(times, drive, response_time_s)
    index = np.clip(np.searchsorted(times, query, side="right") - 1, 0, len(times) - 2)
    dt = query - times[index]
    span = times[index + 1] - times[index]
    decay = np.exp(-dt / response_time_s)
    one_minus_decay = -np.expm1(-dt / response_time_s)
    slope = (drive[index + 1] - drive[index]) / span
    values = decay * states[index] + one_minus_decay * drive[index] + (dt - response_time_s * one_minus_decay) * slope
    # Keep the duplicated terminal reference state exact too.
    return np.where(query == times[-1], states[-1], values)


def driven_body_response(gait: AirborneGait, plan: Mapping[str, Any], roles: Mapping[str, Any]) -> dict[str, Any] | None:
    if not (gait.chest_response_gain_degrees or gait.tail_response_gain_degrees):
        return None
    if gait.chest_response_gain_degrees and not all(key in roles for key in ("chest", "head")):
        raise ContractError("driven chest/head response requires semantic roles")
    if gait.tail_response_gain_degrees and not roles.get("tail"):
        raise ContractError("driven tail response requires a semantic chain")
    rows = plan["samples"]
    if plan.get("program") == "gait_transition":
        # Evaluate the same cyclic lag continuously, not a piecewise-linear
        # interpolation of its output angles. Output-angle interpolation has a
        # velocity corner at every steady sample, amplified at the tail tip.
        # Reference samples and the sustained gait are unchanged.
        from .performance import phase_and_gain
        reference = build_airborne_plan(gait, plan["body_height_m"])
        clock = np.asarray([row["time_s"] for row in reference["samples"]])
        scale = 2 * (gait.pelvis_compression_body_heights + gait.flight_height_body_heights) * plan["body_height_m"] / gait.step_period_s
        drive = np.clip([row["pelvis_vertical_velocity_mps"] / scale for row in reference["samples"]], -1, 1)
        phases, gains = np.asarray([phase_and_gain(row) for row in rows]).T
        def response(values, tau):
            return sample_periodic_response(clock, values, tau, phases)
        chest_reference = -gait.chest_response_gain_degrees * periodic_response(clock, drive, gait.body_response_time_s)
        chest = -gait.chest_response_gain_degrees * response(drive, gait.body_response_time_s)
        counter_reference = -gait.head_stabilization_gain * chest_reference
        counter = -gait.head_stabilization_gain * chest
        neck = .65 * response(counter_reference, gait.body_response_time_s * 1.5) if roles.get("neck") else np.zeros(len(rows))
        head = counter - neck
        names = list(roles.get("tail", []))
        weights = np.asarray([(i + 1) ** .6 for i in range(len(names))])
        if len(weights):
            weights /= weights.sum()
        tail = {name: -gait.tail_response_gain_degrees * weights[i] * response(drive,
            gait.body_response_time_s * (1 + .6 * i / max(1, len(names) - 1))) for i, name in enumerate(names)}
        result = []
        for i, row in enumerate(rows):
            angles = {roles["chest"]: float(chest[i]), roles["head"]: float(head[i])} if gait.chest_response_gain_degrees else {}
            angles.update({name: float(neck[i] / len(roles["neck"])) for name in roles.get("neck", [])})
            angles.update({name: float(values[i]) for name, values in tail.items()})
            result.append({"time_s": row["time_s"], "support_count": row["support_count"],
                "normalized_vertical_motion_drive": float(gains[i] * np.interp(phases[i], clock, drive)),
                "sagittal_node_degrees": {name: float(gains[i] * value) for name, value in angles.items()}})
        return {"classification": "phase-preserving continuous bounded lag; no force or one-shot cyclic claim",
            "samples": result}
    times = [row["time_s"] for row in rows]
    # Normalize by the solved carrier's own excursion/time scale, not species
    # constants. Positive rise drives the tail down through launch; lag carries
    # the curve into early flight before it recovers upward on approach.
    scale = 2 * (gait.pelvis_compression_body_heights + gait.flight_height_body_heights) * plan["body_height_m"] / gait.step_period_s
    drive = np.clip([row["pelvis_vertical_velocity_mps"] / scale for row in rows], -1, 1)
    chest = -gait.chest_response_gain_degrees * periodic_response(times, drive, gait.body_response_time_s)
    counter = -gait.head_stabilization_gain * chest
    neck = .65 * periodic_response(times, counter, gait.body_response_time_s * 1.5) if roles.get("neck") else np.zeros(len(rows))
    head = counter - neck
    tail_names = list(roles.get("tail", []))
    weights = np.asarray([(i + 1) ** .6 for i in range(len(tail_names))])
    if len(weights):
        weights /= weights.sum()
    tail = {name: -gait.tail_response_gain_degrees * weights[i] * periodic_response(times, drive, gait.body_response_time_s * (1 + .6 * i / max(1, len(tail_names) - 1))) for i, name in enumerate(tail_names)}
    states = [chest, neck, head, *tail.values()]
    samples = []
    for i, row in enumerate(rows):
        angles = {roles["chest"]: float(chest[i]), roles["head"]: float(head[i])} if gait.chest_response_gain_degrees else {}
        angles.update({name: float(neck[i] / len(roles["neck"])) for name in roles.get("neck", [])})
        angles.update({name: float(values[i]) for name, values in tail.items()})
        samples.append({"time_s": row["time_s"], "support_count": row["support_count"], "normalized_vertical_motion_drive": float(drive[i]), "sagittal_node_degrees": angles})
    return {"classification": "bounded cyclic kinematic response to the solved carrier velocity; no force/conservation claim", "maximum_cyclic_state_seam_degrees": max(float(abs(values[-1] - values[0])) for values in states), "samples": samples}


def _validate_plan_override(plan: Mapping[str, Any], gait: AirborneGait) -> dict[str, Any]:
    """Fail-closed validation for caller-built (one-shot) plan samples."""
    from ..planning.airborne_gait import build_airborne_plan as _rebuild
    if not isinstance(plan, Mapping):
        raise ContractError("plan override must be a mapping")
    samples = plan.get("samples")
    if not isinstance(samples, list) or len(samples) < 2:
        raise ContractError("plan override needs at least two samples")
    required_row = ("time_s", "root_forward_m", "pelvis_height_offset_m", "flight", "support_count")
    required_foot = ("contact", "forward_m", "height_m", "toe_flex_degrees", "foot_pitch_degrees", "swing_phase")
    previous = None
    for row in samples:
        if not isinstance(row, Mapping):
            raise ContractError("plan override rows must be mappings")
        for key in required_row:
            if key not in row:
                raise ContractError(f"plan override row misses {key}")
        time_s = float(row["time_s"])
        if not math.isfinite(time_s):
            raise ContractError("plan override time must be finite")
        for key in ("root_forward_m", "pelvis_height_offset_m"):
            value = row[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ContractError(f"plan override {key} must be finite numeric")
        if previous is not None and time_s <= previous:
            raise ContractError("plan override times must be strictly increasing")
        previous = time_s
        feet = row.get("feet")
        if not isinstance(feet, Mapping):
            raise ContractError("plan override row misses feet")
        for side in ("left", "right"):
            foot = feet.get(side)
            if not isinstance(foot, Mapping):
                raise ContractError(f"plan override misses {side} foot")
            for key in required_foot:
                if key not in foot:
                    raise ContractError(f"plan override {side} foot misses {key}")
                if key == "contact":
                    continue
                value = foot[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ContractError(f"plan override {side} foot {key} must be finite numeric")
            if not isinstance(foot["contact"], bool):
                raise ContractError("plan override foot contact must be bool")
    out = dict(plan)
    out.setdefault("schema", "eonwild.motion.v9.airborne-gait-plan.v1")
    out.setdefault("program", "airborne_gait")
    out.setdefault("parameters", {})
    return out


def solve_airborne_gait(source: Glb, *, source_clip: str | None, semantic_roles: Mapping[str, Any], gait: AirborneGait, up_axis: tuple[float, float, float] = (0, 1, 0), plan_override: Mapping[str, Any] | None = None, forward_axis: tuple[float, float, float] | None = None, legacy_overlay: bool = True, articulation_profile: ArticulationProfile | None = None) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    """Emit one GLB authority and its derived in-place projection.

    Source supplies rig/skin/rest pose and body geometry only; source animation
    timing never controls the new gait. Reach failures remain visible in the
    receipt (no stretch). Ground witnesses here are skeleton proxies, so final
    skinned-ground/contact checks remain a separate mandatory acceptance gate.

    ``plan_override`` replaces the cyclic planner output with caller-built
    samples (one-shot moves: lunges, stumbles, recoveries). It must carry
    the same schema (samples with time_s, root_forward_m,
    pelvis_height_offset_m, flight, support_count and per-foot contact,
    forward_m, height_m, toe_flex_degrees, foot_pitch_degrees,
    swing_phase). Omitting it reproduces legacy output exactly.
    """
    if articulation_profile is not None and not isinstance(articulation_profile, ArticulationProfile):
        raise ContractError("articulation_profile must be a validated ArticulationProfile")
    roles = semantic_roles
    try:
        root, pelvis = (source.name_to_node[roles[k]] for k in ("root", "pelvis"))
        legs = {s: [source.name_to_node[n] for n in roles["legs"][s]["contactChain"]] for s in ("left", "right")}
        toes = {s: [[source.name_to_node[n] for n in chain] for chain in roles["legs"][s]["toeChains"]] for s in legs}
    except (KeyError, TypeError) as exc:
        raise ContractError("airborne gait needs complete semantic root/pelvis/leg/toe bindings") from exc
    if any(len(chain) != 4 for chain in legs.values()):
        raise ContractError("airborne gait requires hip/knee/ankle/foot chains")
    if any(len(chain) != 3 for digit_chains in toes.values() for chain in digit_chains):
        raise ContractError("airborne digit endpoint solve requires three-node toe chains")
    for chain in legs.values():
        if any(source.parents[b] != a for a, b in zip(chain, chain[1:])):
            raise ContractError("semantic contact chain must follow actual parent topology")
    for side, chains in toes.items():
        for chain in chains:
            if source.parents[chain[0]] != legs[side][-1] or any(source.parents[b] != a for a, b in zip(chain, chain[1:])):
                raise ContractError("semantic toe chains must follow actual foot-parent topology")
    up = _unit(up_axis)
    if source_clip is None:
        if forward_axis is None:
            raise ContractError("neutral geometry requires an explicit forward axis")
        translations, rotations, scales = source.rest_translation, source.rest_rotation, source.rest_scale
        worlds = _world_matrices(source, translations, rotations, scales)
        travel = np.asarray(forward_axis, dtype=float)
    else:
        tracks, source_times = _clip_state(source, source_clip)
        translations, rotations, scales = _pose(source, tracks, 0)
        worlds = _world_matrices(source, translations, rotations, scales)
        final_worlds = _world_matrices(source, *_pose(source, tracks, len(source_times) - 1))
        travel = (np.asarray(forward_axis, dtype=float) if forward_axis is not None else
                  np.asarray(_world_position(final_worlds[root])) - np.asarray(_world_position(worlds[root])))
    if travel.shape != (3,) or not np.isfinite(travel).all():
        raise ContractError("forward axis must be a finite three-vector")
    forward = _unit(travel - up * (travel @ up))
    lateral = _unit(np.cross(up, forward))
    origin = np.asarray(_world_position(worlds[pelvis]))
    hip_positions = {side: np.asarray(_world_position(worlds[chain[0]]))
                     for side, chain in legs.items()}
    hip_midpoint = .5 * (hip_positions["left"] + hip_positions["right"])
    hip_lane_center = float((hip_midpoint - origin) @ lateral)
    hip_offsets = {side: float((position - hip_midpoint) @ lateral)
                   for side, position in hip_positions.items()}
    # A common toe-joint plane is a provisional engineering carrier, never a
    # substitute for evaluating the final skinned sole/contact patches.
    toe_nodes = [n for chains in toes.values() for chain in chains for n in chain]
    ground = min(float(np.asarray(_world_position(worlds[n])) @ up) for n in toe_nodes)
    body_height = float(origin @ up - ground)
    if body_height <= 0:
        raise ContractError("semantic pelvis must be above the toe plane")
    # Behavior programs own support choreography; an override never runs
    # the airborne planner. Legacy calls retain their original default path.
    plan = (build_airborne_plan(gait, body_height) if plan_override is None else
            _validate_plan_override(plan_override, gait))
    body_response = driven_body_response(gait, plan, roles)
    base_t, base_r, base_s = translations[:], rotations[:], scales[:]
    base_w = worlds
    jaw = None
    if gait.jaw_breathing_max_degrees:
        if roles.get("jaw_lower") not in source.name_to_node:
            raise ContractError("breathing requires a bound semantic lower jaw")
        jaw = source.name_to_node[roles["jaw_lower"]]
        jaw_axis = _qrotate(_qinv(_rotation_from_matrix(base_w[jaw])), tuple(lateral))
    anatomical_normals = {}
    for side, (hip, knee, ankle, foot) in legs.items():
        hp, kp, ap = (np.asarray(_world_position(base_w[n])) for n in (hip, knee, ankle))
        anatomical_normals[side] = _unit(np.cross(kp - hp, ap - kp))
    # Digit bend planes belong to neutral anatomy. Projecting the *moving*
    # toe elbow becomes ill-conditioned at extension and can choose the other
    # branch on the last loop sample despite identical endpoint targets.
    toe_normals = {}
    if "performance" in plan:
        for side, chains in toes.items():
            for a, b, c in chains:
                pa, pb, pc = (np.asarray(_world_position(base_w[n])) for n in (a, b, c))
                normal = np.cross(pb - pa, pc - pb)
                toe_normals[a] = _unit(normal if np.linalg.norm(normal) > 1e-8 else lateral)
    frames_t, frames_r, emitted = [], [], []
    max_residual, max_extension = 0.0, 0.0
    max_envelope_violation = 0.0
    for frame_index, row in enumerate(plan["samples"]):
        tr, rot = base_t[:], base_r[:]
        from .performance import phase_and_gain
        motion_time, performance_gain = phase_and_gain(row)
        root_delta = forward * row["root_forward_m"]
        tr[root] = tuple(float(v) for v in np.asarray(base_t[root]) + _local_delta(source, base_w, root, root_delta))
        root_pitch = float(row.get("root_pitch_degrees", 0.0))
        if not math.isfinite(root_pitch):
            raise ContractError("plan root pitch must be finite numeric")
        if root_pitch:
            axis = _qrotate(_qinv(_rotation_from_matrix(base_w[root])), tuple(lateral))
            rot[root] = _qmul(base_r[root], _qrotvec(tuple(np.asarray(axis) * math.radians(root_pitch))))
        tr[pelvis] = tuple(float(v) for v in np.asarray(base_t[pelvis]) + _local_delta(source, base_w, pelvis, up * row["pelvis_height_offset_m"]))
        if body_response:
            for name, degrees in body_response["samples"][frame_index]["sagittal_node_degrees"].items():
                if name not in source.name_to_node:
                    raise ContractError("driven body response role is not present in the rig")
                n = source.name_to_node[name]
                axis = _qrotate(_qinv(_rotation_from_matrix(base_w[n])), tuple(lateral))
                rot[n] = _qmul(base_r[n], _qrotvec(tuple(np.asarray(axis) * math.radians(degrees))))
        elif legacy_overlay:
            # Preserve the pre-existing default path for accepted artifacts and
            # other profiles. The new driven response is explicitly opt-in.
            pulse = math.sin(2 * math.pi * row["time_s"] / gait.step_period_s)
            for role, amplitude in (("chest", -1.5), ("head", 0.8)):
                if role in roles and roles[role] in source.name_to_node:
                    n = source.name_to_node[roles[role]]
                    axis = _qrotate(_qinv(_rotation_from_matrix(base_w[n])), tuple(lateral))
                    rot[n] = _qmul(base_r[n], _qrotvec(tuple(np.asarray(axis) * math.radians(amplitude * pulse))))
            for nname in roles.get("tail", [])[:3]:
                n = source.name_to_node[nname]
                axis = _qrotate(_qinv(_rotation_from_matrix(base_w[n])), tuple(lateral))
                rot[n] = _qmul(base_r[n], _qrotvec(tuple(np.asarray(axis) * math.radians(0.8 * pulse))))
        # Profile-owned sagittal posture distributed over semantic chains.
        # A higher pelvis can retain leg reach while the front body inclines;
        # the tail is a distributed elevation, never an attachment offset.
        for names, total in ((list(roles.get("spine", [])) + ([roles["chest"]] if roles.get("chest") else []), gait.front_body_pitch_degrees), (list(roles.get("tail", [])), gait.tail_elevation_degrees)):
            if total and not names:
                raise ContractError("sagittal posture requires its semantic body chain")
            for name in names if total else []:
                n = source.name_to_node[name]
                axis = _qrotate(_qinv(_rotation_from_matrix(base_w[n])), tuple(lateral))
                rot[n] = _qmul(rot[n], _qrotvec(tuple(np.asarray(axis) * math.radians(performance_gain * total / len(names)))))
        if jaw is not None:
            # Rotate the lower jaw about the rig-derived sagittal axis only.
            # The full-cycle cosine is C2 at the loop; no head/neck compensation
            # is added, so the accepted whole-body motion remains unchanged.
            rot[jaw] = _qmul(base_r[jaw], _qrotvec(tuple(np.asarray(jaw_axis) * math.radians(performance_gain * jaw_breathing_angle(gait, motion_time)))))
        from .performance import apply_performance
        apply_performance(source, tr, rot, base_s, base_w, roles, plan, row, up, forward)
        facts = {}
        for side, chain in legs.items():
            hip, knee, ankle, foot = chain
            foot_plan = row["feet"][side]
            material_partition = "performance" in plan
            swing_phase = foot_plan["swing_phase"]
            support_lock = (1.0 if foot_plan["contact"] else
                            1 - _smooth(min(swing_phase, 1 - swing_phase) / .18))
            for toe_chain in toes[side]:
                for index, n in enumerate(toe_chain):
                    axis = _qrotate(_qinv(_rotation_from_matrix(base_w[n])), tuple(lateral))
                    flex = foot_plan["toe_flex_degrees"] * (0.45 if index == 0 else 0.275)
                    if material_partition:
                        flex *= 1 - support_lock
                    rot[n] = _qmul(base_r[n], _qrotvec(tuple(np.asarray(axis) * math.radians(flex))))
            w = _world_matrices(source, tr, rot, base_s)
            hp, kp, ap, fp = (np.asarray(_world_position(w[n])) for n in chain)
            side_lane = float((np.asarray(_world_position(base_w[foot])) - origin) @ lateral)
            if "performance" in plan:
                half_lane = .5 * plan["performance"]["lane_width_body_heights"] * body_height
                if plan["performance"].get("center_lanes_on_bilateral_hip_midpoint", False):
                    if min(abs(value) for value in hip_offsets.values()) < 1e-8 * body_height:
                        raise ContractError("bilateral hip midpoint lane calibration requires separated hip origins")
                    side_lane = hip_lane_center + math.copysign(half_lane, hip_offsets[side])
                else:
                    side_lane = math.copysign(half_lane, side_lane)
            foot_height = float(np.asarray(_world_position(base_w[foot])) @ up - ground)
            desired_foot = origin + forward * foot_plan["forward_m"] + lateral * side_lane
            desired_foot += up * (ground + foot_height + foot_plan["height_m"] - float(desired_foot @ up))
            # Regrounding: lower this foot's targets by a constant per-side
            # offset on EVERY frame (stance and swing). A constant shift
            # preserves C1 continuity, loop closure and the pelvis/root
            # motion exactly; only distal leg pose changes, bounded to 5 cm
            # by the gait contract. Zero (default) reproduces legacy output.
            ground_offset = (
                gait.stance_ground_offset_left_m if side == "left"
                else gait.stance_ground_offset_right_m
            )
            if ground_offset:
                desired_foot -= up * ground_offset
            correction = np.asarray(foot_plan.get("target_offset_m", [0., 0., 0.]), dtype=float)
            if correction.shape != (3,) or not np.isfinite(correction).all() or np.linalg.norm(correction) > .06 * body_height:
                raise ContractError("invalid bounded skin target correction")
            desired_foot += correction
            nominal_foot = desired_foot.copy()
            # Rock the articulated foot about the distal contact centroid,
            # not about the ankle: toe tips stay fixed during stance roll-off.
            tips = [tc[-1] for tc in toes[side]]
            initial_tip_offset = np.mean([np.asarray(_world_position(base_w[n])) for n in tips], axis=0) - np.asarray(_world_position(base_w[foot]))
            flexed_tip_offset = np.mean([np.asarray(_world_position(w[n])) for n in tips], axis=0) - fp
            u = foot_plan["swing_phase"]
            lock = 1.0 if foot_plan["contact"] else 1 - _smooth(min(u, 1 - u) / .18)
            # Keep the rolled foot inside every toe's unchanged-length reach
            # envelope before the leg solve. This small rigid foot adjustment
            # is realized by hip/knee/ankle rotations, never translations.
            base_offset = np.asarray(_world_position(base_w[foot])) - np.asarray(_world_position(base_w[ankle]))
            world_metatarsus_recovery = _world_metatarsus_recovery(foot_plan)
            upper, lower = np.linalg.norm(kp - hp), np.linalg.norm(ap - kp)
            toe_geometry = []
            for a, b, c in toes[side]:
                pa, pb, pc = (np.asarray(_world_position(w[n])) for n in (a, b, c))
                toe_geometry.append((pa - fp, np.asarray(_world_position(base_w[c])) + nominal_foot - np.asarray(_world_position(base_w[foot])), np.linalg.norm(pb - pa) + np.linalg.norm(pc - pb) - 1e-7))

            def pitch_candidate(degrees, world_metatarsus_target=None):
                candidate_q = _qrotvec(tuple(lateral * math.radians(degrees)))
                candidate_foot = (nominal_foot.copy() if material_partition else
                                  nominal_foot + initial_tip_offset - np.asarray(_qrotate(candidate_q, tuple(flexed_tip_offset))))
                rotated_roots = [(np.asarray(_qrotate(candidate_q, tuple(offset))), tip, reach) for offset, tip, reach in toe_geometry]
                for _ in range(18 if not material_partition and lock > 1e-12 else 0):
                    largest_correction = 0.0
                    for offset, tip, reach in rotated_roots:
                        delta = tip - (candidate_foot + offset)
                        distance = np.linalg.norm(delta)
                        if distance > reach:
                            correction = lock * delta * (1 - reach / distance)
                            candidate_foot += correction
                            largest_correction = max(largest_correction, float(np.linalg.norm(correction)))
                    if largest_correction < 1e-12:
                        break
                target_ankle = candidate_foot - np.asarray(_qrotate(candidate_q, tuple(base_offset)))
                candidate_knee, candidate_end, extension = stable_knee_geometry(hp, target_ankle, upper, lower, anatomical_normals[side])
                hip_angle = math.degrees(math.atan2(float((candidate_knee - hp) @ forward), -float((candidate_knee - hp) @ up)))
                knee_angle = _interior(hp - candidate_knee, candidate_end - candidate_knee)
                ankle_angle = _interior(candidate_knee - candidate_end, candidate_foot - candidate_end)
                metatarsus_world_degrees = _world_sagittal_degrees(
                    candidate_foot - candidate_end, forward, up)
                if articulation_profile is None:
                    slacks = [hip_angle + gait.hip_extension_limit_degrees, gait.hip_flexion_limit_degrees - hip_angle, knee_angle - gait.knee_min_interior_degrees, gait.knee_max_interior_degrees - knee_angle, ankle_angle - gait.ankle_min_interior_degrees, gait.ankle_max_interior_degrees - ankle_angle]
                    preferred = None
                else:
                    envelopes = articulation_profile.effective(
                        contact=foot_plan["contact"], swing_phase=u)
                    angles = {"hip_sagittal_degrees": hip_angle,
                              "knee_interior_degrees": knee_angle,
                              "ankle_interior_degrees": ankle_angle}
                    slacks = []
                    preferred = 0.0
                    for joint, angle in angles.items():
                        envelope = envelopes[joint]
                        slacks.extend((angle - envelope.hard_min_deg,
                                       envelope.hard_max_deg - angle))
                        departure = max(0.0, envelope.preferred_min_deg - angle,
                                        angle - envelope.preferred_max_deg)
                        scale = max(1.0, envelope.preferred_max_deg - envelope.preferred_min_deg)
                        preferred += departure ** 4 / (scale * scale)
                errors = [max(0, -slack) for slack in slacks]
                recovery = 0.0 if foot_plan["contact"] else math.sin(math.pi * u) ** 2
                hip_target = gait.swing_hip_lift_degrees * recovery * foot_plan.get("articulation_scale", 1.)
                # A C2 preferred-region penalty anticipates the hard corner
                # before ankle/knee limits become active. It coordinates the
                # pose solve itself; emitted rotations are never post-filtered.
                if preferred is None:
                    margin = gait.articulation_preferred_margin_degrees
                    preferred = sum(max(0, margin - slack) ** 4 / (margin * margin) for slack in slacks) if margin else 0.0
                pitch_target = _recovery_pitch_target(
                    gait, foot_plan,
                    # The recovery carrier coordinates the airborne material
                    # partition. Grounded performance and legacy reproduction
                    # retain their authored pitch target.
                    airborne=(material_partition
                              and "flight_fraction" in plan.get("parameters", {})),
                )
                preferred_gain = recovery if articulation_profile is None else 1.0
                authored_pitch_cost = (degrees - pitch_target) ** 2
                if world_metatarsus_target is None:
                    pitch_cost = authored_pitch_cost
                else:
                    # Blend the objectives, not only their targets. As the C2
                    # recovery gain tends to zero, both the value and gradient
                    # converge to the existing per-side authored-pitch solve.
                    world_cost = 100.0 * (
                        metatarsus_world_degrees - world_metatarsus_target) ** 2
                    pitch_cost = ((1 - world_metatarsus_gain) * authored_pitch_cost
                                  + world_metatarsus_gain * world_cost)
                score = pitch_cost + recovery * (hip_angle - hip_target) ** 2 + preferred_gain * gait.articulation_preferred_margin_weight * preferred + 1e5 * sum(e * e for e in errors) + 1e8 * extension * extension
                return (score, candidate_q, candidate_foot, target_ankle,
                        candidate_knee, candidate_end, extension, max(errors),
                        {"hip_sagittal_degrees": hip_angle,
                         "knee_interior_degrees": knee_angle,
                         "ankle_interior_degrees": ankle_angle},
                        metatarsus_world_degrees, degrees)

            # A one-dimensional sagittal articulation solve coordinates the
            # thigh and metatarsal around the unchanged toe target. It does not
            # raise feet, translate limb bones, or smooth over a branch flip.
            # Solve the articulated pose from this authored state alone. The
            # old bounds depended on the previously sampled pitch, so the same
            # gait phase could emit a different pose when a transition and a
            # sustained clip reached it through different sample histories.
            # Rate compliance is measured on the completed trajectory below;
            # it must never alter this pose as a function of query order.
            lo, hi = -45.0, 85.0

            def candidate_key(candidate):
                if articulation_profile is None:
                    return (candidate[0],)
                # Bound profiles are constraints, not score suggestions. A
                # feasible candidate always outranks one outside a hard bound;
                # only a genuinely infeasible pitch domain minimizes violation.
                violation = candidate[7]
                return ((0, candidate[0]) if violation <= 1e-10
                        else (1, violation, candidate[0]))

            def minimize_pitch(world_target=None):
                candidates = [pitch_candidate(degrees, world_target)
                              for degrees in np.linspace(lo, hi, 27)]
                # Preserve an exactly feasible authored pitch (especially flat
                # stance=0). A refined grid alone can leave a few millidegrees of
                # negative pitch and depress a distal joint on a straight toe rig.
                candidates.append(pitch_candidate(
                    float(np.clip(foot_plan["foot_pitch_degrees"], lo, hi)), world_target))
                best_candidate = min(candidates, key=candidate_key)
                step = (hi - lo) / 52
                # Resolve the actual articulation more accurately, rather than
                # filtering serialized rotations after contact validation. The
                # old reproduction path retains its exact seven refinements.
                for _ in range(22 if material_partition else 7):
                    best_candidate = min([
                        best_candidate,
                        pitch_candidate(max(lo, best_candidate[-1] - step), world_target),
                        pitch_candidate(min(hi, best_candidate[-1] + step), world_target),
                    ], key=candidate_key)
                    step *= .5
                return best_candidate

            baseline_best = minimize_pitch()
            if world_metatarsus_recovery is None:
                world_metatarsus_baseline = None
                world_metatarsus_target = None
                world_metatarsus_gain = None
                best = baseline_best
            else:
                peak_target, world_metatarsus_gain = world_metatarsus_recovery
                world_metatarsus_baseline = baseline_best[-2]
                world_metatarsus_target = ((1 - world_metatarsus_gain) * world_metatarsus_baseline
                                            + world_metatarsus_gain * peak_target)
                best = minimize_pitch(world_metatarsus_target)
            (_, pitch, desired_foot, target, desired_knee, desired_end,
             extension, envelope_error, articulation_angles,
             metatarsus_world_degrees, solved_pitch) = best
            max_extension = max(max_extension, extension)
            max_envelope_violation = max(max_envelope_violation, envelope_error)
            desired_normal = _unit(np.cross(desired_knee - hp, desired_end - desired_knee))
            source_normal = (_unit(np.cross(kp - hp, ap - kp)) if "performance" in plan else anatomical_normals[side])
            delta = _orientation_from_bend(kp - hp, source_normal, desired_knee - hp, desired_normal)
            hq = _qmul(delta, _rotation_from_matrix(w[hip]))
            rot[hip] = _world_rotation(source, w, hip, hq)
            w = _world_matrices(source, tr, rot, base_s)
            kp, ap = (np.asarray(_world_position(w[n])) for n in (knee, ankle))
            kq = _qmul(_between(ap - kp, desired_end - kp), _rotation_from_matrix(w[knee]))
            rot[knee] = _world_rotation(source, w, knee, kq)
            w = _world_matrices(source, tr, rot, base_s)
            desired_ankle_q = _qmul(pitch, _rotation_from_matrix(base_w[ankle]))
            rot[ankle] = _world_rotation(source, w, ankle, desired_ankle_q)
            w = _world_matrices(source, tr, rot, base_s)
            if material_partition:
                # The ankle/metatarsal is NOT the contact pad. Articulate it
                # around the stationary foot root while the MTP joint keeps
                # the load-bearing pad and digits in their calibrated frame.
                # Release that frame C2 during swing, allowing authored fold
                # and digit flex. No per-bone translation/scale is introduced.
                free_pitch = _qrotvec(tuple(lateral * math.radians(foot_plan.get("pad_pitch_degrees", 0.) * (1 - support_lock))))
                foot_world = _qmul(free_pitch, _rotation_from_matrix(base_w[foot]))
                rot[foot] = _world_rotation(source, w, foot, foot_world)
                w = _world_matrices(source, tr, rot, base_s)
            # During contact each distal digit endpoint stays independently
            # planted. A centroid alone can hide one penetrating toe. Release
            # these constraints smoothly after lift and restore before land.
            for tc in toes[side]:
                if material_partition:
                    # Calibrated FK, not a nearly straight two-link toe IK:
                    # at full support the fixed foot frame plus zero local
                    # flex makes EVERY toe landmark stationary. During swing
                    # the existing bounded flex is explicit choreography.
                    # Final material-point and skeleton checks remain required.
                    continue
                if len(tc) != 3:
                    raise ContractError("airborne digit endpoint solve requires three-node toe chains")
                a, b, c = tc
                pa, pb, pc = (np.asarray(_world_position(w[n])) for n in tc)
                desired_tip = np.asarray(_world_position(base_w[c])) + nominal_foot - np.asarray(_world_position(base_w[foot]))
                target_tip = pc + lock * (desired_tip - pc)
                direction = _unit(target_tip - pa)
                first_len, second_len = np.linalg.norm(pb - pa), np.linalg.norm(pc - pb)
                raw_dist = np.linalg.norm(target_tip - pa)
                dist = float(np.clip(raw_dist, abs(first_len - second_len) + 1e-8, first_len + second_len - 1e-8))
                max_extension = max(max_extension, float(abs(raw_dist - dist)))
                along = (first_len ** 2 - second_len ** 2 + dist ** 2) / (2 * dist)
                if "performance" in plan:
                    foot_delta = _qmul(_rotation_from_matrix(w[foot]), _qinv(_rotation_from_matrix(base_w[foot])))
                    normal = np.asarray(_qrotate(foot_delta, tuple(toe_normals[a])))
                    bend = np.cross(direction, normal)
                else:
                    # Immutable legacy path for accepted baseline builds.
                    bend = pb - pa - direction * float((pb - pa) @ direction)
                    if np.linalg.norm(bend) < 1e-8:
                        bend = up - direction * float(up @ direction)
                elbow = pa + direction * along + _unit(bend) * math.sqrt(max(0, first_len ** 2 - along ** 2))
                rot[a] = _world_rotation(source, w, a, _qmul(_between(pb - pa, elbow - pa), _rotation_from_matrix(w[a])))
                w = _world_matrices(source, tr, rot, base_s)
                pb, pc = (np.asarray(_world_position(w[n])) for n in (b, c))
                rot[b] = _world_rotation(source, w, b, _qmul(_between(pc - pb, pa + direction * dist - pb), _rotation_from_matrix(w[b])))
                w = _world_matrices(source, tr, rot, base_s)
                # A terminal joint has no downstream skeletal witness, yet
                # rotating it can drive the skinned claw through the floor.
                # Preserve its loaded world orientation, then progressively
                # permit distal flex only as the swing constraint releases.
                distal_flex = math.radians(foot_plan["toe_flex_degrees"] * .275 * (1 - lock))
                distal_world = _qmul(_qrotvec(tuple(lateral * distal_flex)), _rotation_from_matrix(base_w[c]))
                rot[c] = _world_rotation(source, w, c, distal_world)
                w = _world_matrices(source, tr, rot, base_s)
            actual = np.asarray(_world_position(w[foot]))
            residual = float(np.linalg.norm(actual - desired_foot))
            max_residual = max(max_residual, residual)
            toe_height = min(float(np.asarray(_world_position(w[n])) @ up - ground) for tc in toes[side] for n in tc)
            tip_centroid = np.mean([np.asarray(_world_position(w[n])) for n in tips], axis=0)
            facts[side] = {"contact": foot_plan["contact"], "foot_world_m": actual.tolist(), "distal_contact_centroid_m": tip_centroid.tolist(), "target_foot_world_m": desired_foot.tolist(), "foot_target_residual_m": residual, "minimum_toe_joint_height_m": toe_height, "solved_foot_pitch_degrees": solved_pitch, "articulation_envelope_violation_degrees": envelope_error}
            if articulation_profile is not None:
                facts[side]["articulation_phase"] = "support" if foot_plan["contact"] else "swing"
                facts[side]["articulation_angles_degrees"] = articulation_angles
            if world_metatarsus_target is not None:
                facts[side]["metatarsus_world_degrees_from_down"] = metatarsus_world_degrees
                facts[side]["metatarsus_world_baseline_degrees_from_down"] = world_metatarsus_baseline
                facts[side]["metatarsus_world_target_degrees_from_down"] = world_metatarsus_target
                facts[side]["metatarsus_world_target_gain"] = world_metatarsus_gain
        frames_t.append(tr)
        frames_r.append(rot)
        emitted.append({"time_s": row["time_s"], "flight": row["flight"], "feet": facts})
    times = np.asarray([r["time_s"] for r in plan["samples"]])
    ta, ra = np.asarray(frames_t), np.asarray(frames_r)
    # Quaternion sign continuity prevents long-path interpolation artifacts.
    for i in range(1, len(ra)):
        flip = np.sum(ra[i] * ra[i - 1], axis=1) < 0
        ra[i, flip] *= -1
    channels = {(i, "rotation"): ra[:, i] for i in range(len(source.nodes))}
    channels.update({(i, "translation"): ta[:, i] for i in range(len(source.nodes))})
    digest = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    state = {"program": "airborne_gait", "samples": [{"time_s": r["time_s"], "flight": r["flight"], "support_count": r["support_count"]} for r in plan["samples"]]}
    def encode(current: Any, name: str) -> bytes:
        blob = Glb.from_bytes(_build_glb(source, name, times, current, digest, state))
        blob.document["animations"][0]["extras"].update(program="airborne_gait", loop=True)
        return _encode(blob.document, blob.binary)
    authority = encode(channels, "V9_AIRBORNE_RUN_ROOT_MOTION")
    in_place_channels = deepcopy(channels)
    in_place_channels[root, "translation"] = np.repeat(ta[0:1, root], len(times), axis=0)
    in_place = encode(in_place_channels, "V9_AIRBORNE_RUN_IN_PLACE")
    # Measure the reopened float32 GLB, not merely the double-precision solve.
    reopened = Glb.from_bytes(authority)
    emitted_tracks, emitted_times = _clip_state(reopened, "V9_AIRBORNE_RUN_ROOT_MOTION")
    max_residual = 0.0
    for i, row in enumerate(emitted):
        w = _world_matrices(reopened, *_pose(reopened, emitted_tracks, i))
        row["time_s"] = emitted_times[i]
        for side, chain in legs.items():
            actual = np.asarray(_world_position(w[chain[-1]]))
            fact = row["feet"][side]
            fact["foot_world_m"] = actual.tolist()
            fact["foot_target_residual_m"] = float(np.linalg.norm(actual - np.asarray(fact["target_foot_world_m"])))
            max_residual = max(max_residual, fact["foot_target_residual_m"])
            fact["distal_contact_centroid_m"] = np.mean([np.asarray(_world_position(w[tc[-1]])) for tc in toes[side]], axis=0).tolist()
            fact["minimum_toe_joint_height_m"] = min(float(np.asarray(_world_position(w[n])) @ up - ground) for tc in toes[side] for n in tc)
    max_drift = 0.0
    max_velocity = 0.0
    for left, right in zip(emitted, emitted[1:]):
        for side in legs:
            if left["feet"][side]["contact"] and right["feet"][side]["contact"]:
                drift = float(np.linalg.norm(np.asarray(left["feet"][side]["distal_contact_centroid_m"]) - right["feet"][side]["distal_contact_centroid_m"]))
                max_drift = max(max_drift, drift)
                max_velocity = max(max_velocity, drift / (right["time_s"] - left["time_s"]))
    receipt = {"status": "PROVISIONAL_REQUIRES_SKINNED_AND_VISUAL_GATE", "semantic_binding": dict(roles), "body_height_m": body_height, "forward_axis": forward.tolist(), "up_axis": up.tolist(), "ground_toe_joint_plane_m": ground, "max_foot_target_residual_m": max_residual, "max_unreachable_extension_m": max_extension, "max_planted_distal_contact_step_drift_m": max_drift, "minimum_toe_joint_height_m": min(f["minimum_toe_joint_height_m"] for r in emitted for f in r["feet"].values()), "flight_sample_count": sum(r["flight"] for r in emitted), "leg_local_translations_constant": True, "in_place_derived_only_from_authority": True, "final_skinned_contact_gate": "NOT_YET_MEASURED", "emitted_proxy_samples": emitted}
    receipt["max_planted_distal_contact_velocity_mps"] = max_velocity
    receipt["maximum_articulation_envelope_violation_degrees"] = max_envelope_violation
    maximum_pitch_rate = 0.0
    pitch_rate_witness = None
    for side in legs:
        samples = [(row["time_s"], row["feet"][side]["solved_foot_pitch_degrees"])
                   for row in emitted]
        for (old_time, old_pitch), (new_time, new_pitch) in zip(samples, samples[1:]):
            rate = abs(new_pitch - old_pitch) / (new_time - old_time)
            if rate > maximum_pitch_rate:
                maximum_pitch_rate = rate
                pitch_rate_witness = {"side": side, "times_s": [old_time, new_time],
                                      "pitches_degrees": [old_pitch, new_pitch]}
    receipt["maximum_solved_foot_pitch_velocity_degrees_per_s"] = maximum_pitch_rate
    receipt["solved_foot_pitch_velocity_limit_degrees_per_s"] = gait.max_ankle_pitch_velocity_degrees_per_s
    receipt["maximum_solved_foot_pitch_velocity_witness"] = pitch_rate_witness
    receipt["articulation_limits_classification"] = "body-configurable engineering limits, not biologically certified; provisional-envelope consolidation deferred"
    if articulation_profile is not None:
        receipt["articulation_profile"] = articulation_profile.receipt()
    if body_response:
        receipt["body_response"] = body_response
    return authority, in_place, plan, receipt


def active_surface_velocity(old: np.ndarray, new: np.ndarray, *, up_axis: int, ground_m: float, floor_gap_m: float, delta_time_s: float, contact_band_m: float = .003) -> tuple[float, int]:
    """Speed of persistent lowest-surface vertices; omit lifted roll-off skin."""
    if delta_time_s <= 0 or len(old) != len(new) or len(old) == 0:
        raise ContractError("active surface velocity requires aligned points and positive dt")
    active = (old[:, up_axis] <= old[:, up_axis].min() + contact_band_m) & (new[:, up_axis] <= new[:, up_axis].min() + contact_band_m)
    active &= (old[:, up_axis] - ground_m <= floor_gap_m) & (new[:, up_axis] - ground_m <= floor_gap_m)
    if not active.any():
        return 0.0, 0
    return float(np.linalg.norm(new[active] - old[active], axis=1).max() / delta_time_s), int(active.sum())


def ground_plane_velocity_witness(old: np.ndarray, new: np.ndarray, *, up_axis: int, ground_m: float, tolerance_m: float, delta_time_s: float) -> dict[str, Any]:
    """Actual fixed-ground occupancy, not a band relative to a lifted patch.

    Empty occupancy is unknown contact velocity, not a zero-skate pass.
    """
    if delta_time_s <= 0 or len(old) != len(new) or tolerance_m <= 0:
        raise ContractError("ground-plane velocity needs aligned points, positive dt and tolerance")
    active = (np.abs(old[:, up_axis] - ground_m) <= tolerance_m) & (np.abs(new[:, up_axis] - ground_m) <= tolerance_m)
    ids = np.flatnonzero(active)
    if not len(ids):
        return {"persistent_point_count": 0, "maximum_velocity_mps": None, "maximum_tangential_velocity_mps": None}
    velocity = (new[ids] - old[ids]) / delta_time_s
    speeds = np.linalg.norm(velocity, axis=1)
    local = int(speeds.argmax())
    point = int(ids[local])
    tangential = velocity.copy()
    tangential[:, up_axis] = 0
    return {"persistent_point_count": int(len(ids)), "maximum_velocity_mps": float(speeds[local]), "maximum_tangential_velocity_mps": float(np.linalg.norm(tangential, axis=1).max()), "point_index": point, "previous_world_m": old[point].tolist(), "current_world_m": new[point].tolist(), "previous_ground_gap_m": float(old[point, up_axis] - ground_m), "current_ground_gap_m": float(new[point, up_axis] - ground_m)}


def evaluate_airborne_skin(glb: Glb, *, contact_profile: Mapping[str, Any], gait: AirborneGait, body_height_m: float, sample_hz: int = 120, include_contact_authority: bool = False, authority_thresholds: Any = None, clip_name: str = "V9_AIRBORNE_RUN_ROOT_MOTION", plan_override: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate actual skinned foot vertices against the bound source floor.

    Reuses the existing normalized multi-influence skinning/mask adapter;
    does not infer contact from the plan alone. Toe centroid velocity is
    reported separately from the skeletal endpoint lock (a deforming patch
    need not have a stationary centroid during legitimate roll-off).

    When ``include_contact_authority`` is true, the persistent
    ground-plane verdict from ``dynamics.contact_authority`` is appended
    under ``contact_authority_v1``. Default off: existing receipts are
    byte-identical.

    ``plan_override`` reads planned contact/stage from caller-built
    (one-shot) samples by nearest time instead of the cyclic sampler,
    and sizes the frame range from the plan span. Omitting it
    reproduces legacy output exactly.
    """
    from ..contact_gauge import _source_frames

    if plan_override is not None:
        override_samples = _validate_plan_override(plan_override, gait)["samples"]
        override_times = [float(s["time_s"]) for s in override_samples]
        duration = override_times[-1] - override_times[0]

        def _nearest_sample(time_s: float) -> dict[str, Any]:
            best = min(range(len(override_times)), key=lambda i: abs(override_times[i] - time_s))
            return override_samples[best]

        def _planned(time_s: float) -> dict[str, Any]:
            row = _nearest_sample(time_s)
            return {"flight": bool(row["flight"]),
                    "feet": {side: {"contact": bool(row["feet"][side]["contact"]),
                                    "height_m": float(row["feet"][side]["height_m"])}
                             for side in ("left", "right")},
                    "stage": row.get("stage", "ONE_SHOT")}
    else:
        def _planned(time_s: float) -> dict[str, Any]:
            sample = sample_airborne_gait(gait, time_s, body_height_m)
            return {"flight": bool(sample["flight"]),
                    "feet": {side: {"contact": bool(sample["feet"][side]["contact"]),
                                    "height_m": float(sample["feet"][side]["height_m"])}
                             for side in ("left", "right")},
                    "stage": sample.get("stage", "")}
        duration = 2 * gait.cycles * gait.step_period_s
    frames, metadata = _source_frames(glb, contact_profile, animation_name=clip_name, sample_count=int(math.ceil(duration * sample_hz)) + 1)
    ground = float(contact_profile["geometry"]["ground"]["level_m"])
    axis_name = contact_profile["geometry"]["ground"]["up_axis"]
    axis = {"X": 0, "Y": 1, "Z": 2}[axis_name]
    ground_gap = float(contact_profile["thresholds"]["floor_gap_tolerance_m"])
    facts = []
    max_penetration = 0.0
    contact_misses = 0
    airborne_misses = 0
    flight_interior = 0
    for frame in frames:
        planned = _planned(frame["time_s"])
        row = {"time_s": frame["time_s"], "planned_flight": planned["flight"], "feet": {}}
        for side, foot in frame["feet"].items():
            sole = np.asarray([p["point_m"] for p in foot["sole_points"]])
            toe = np.asarray([p["point_m"] for p in foot["toe_points"]])
            min_sole = float(sole[:, axis].min() - ground)
            min_toe = float(toe[:, axis].min() - ground)
            minimum = min(min_sole, min_toe)
            max_penetration = max(max_penetration, -minimum)
            contact = planned["feet"][side]["contact"]
            contact_misses += int(contact and minimum > ground_gap)
            row["feet"][side] = {"planned_contact": contact, "sole_minimum_gap_m": min_sole, "toe_minimum_gap_m": min_toe, "toe_surface_centroid_m": toe.mean(axis=0).tolist()}
        # Exclude the exact toe-off/landing boundary where zero clearance is
        # mathematically required; check interior flight rather than labels.
        if planned["flight"] and min(f["height_m"] for f in planned["feet"].values()) > .005 * body_height_m:
            flight_interior += 1
            airborne_misses += int(any(min(f["sole_minimum_gap_m"], f["toe_minimum_gap_m"]) <= 0 for f in row["feet"].values()))
        facts.append(row)
    max_surface_speed = 0.0
    max_distal_patch_speed = 0.0
    max_active_surface_speed = 0.0
    contact_band_scan = {str(band): 0.0 for band in (.0001, .0005, .001, .003)}
    proximity_witnesses = {}
    true_ground_scan = {str(band): {"stance_pair_count": 0, "occupied_stance_pair_count": 0, "persistent_point_pairs": 0, "maximum_velocity_mps": None, "maximum_tangential_velocity_mps": None} for band in (.0001, .0005, .001)}
    active_surface_pairs = 0
    patch_indices = {}
    for side in ("left", "right"):
        first_stance = next(i for i, row in enumerate(facts) if row["feet"][side]["planned_contact"])
        points = frames[first_stance]["feet"][side]["toe_points"]
        bottom = min(p["point_m"][axis] for p in points)
        patch_indices[side] = [i for i, p in enumerate(points) if p["point_m"][axis] <= bottom + .02]
    for index, (previous, current) in enumerate(zip(facts, facts[1:])):
        for side in ("left", "right"):
            a, b = previous["feet"][side], current["feet"][side]
            if a["planned_contact"] and b["planned_contact"]:
                dt = current["time_s"] - previous["time_s"]
                if plan_override is not None:
                    witness_context = {"side": side, "time_s": [previous["time_s"], current["time_s"]],
                                       "stance_phase": None,
                                       "body_stage": _planned(previous["time_s"])["stage"]}
                else:
                    local_stance = (previous["time_s"] - (0 if side == "left" else gait.step_period_s)) % (2 * gait.step_period_s)
                    witness_context = {"side": side, "time_s": [previous["time_s"], current["time_s"]], "stance_phase": local_stance / (gait.step_period_s * (1 - gait.flight_fraction)), "body_stage": sample_airborne_gait(gait, previous["time_s"], body_height_m)["stage"]}
                all_old = np.asarray([p["point_m"] for region in ("sole_points", "toe_points") for p in frames[index]["feet"][side][region]])
                all_new = np.asarray([p["point_m"] for region in ("sole_points", "toe_points") for p in frames[index + 1]["feet"][side][region]])
                for band, summary in true_ground_scan.items():
                    witness = ground_plane_velocity_witness(all_old, all_new, up_axis=axis, ground_m=ground, tolerance_m=float(band), delta_time_s=dt)
                    summary["stance_pair_count"] += 1
                    summary["occupied_stance_pair_count"] += int(witness["persistent_point_count"] > 0)
                    summary["persistent_point_pairs"] += witness["persistent_point_count"]
                    if witness["maximum_velocity_mps"] is not None:
                        summary["maximum_tangential_velocity_mps"] = max(summary["maximum_tangential_velocity_mps"] or 0, witness["maximum_tangential_velocity_mps"])
                        if summary["maximum_velocity_mps"] is None or witness["maximum_velocity_mps"] > summary["maximum_velocity_mps"]:
                            summary["maximum_velocity_mps"] = witness["maximum_velocity_mps"]
                            summary["peak_witness"] = {**witness, **witness_context}
                velocity = np.linalg.norm(np.asarray(b["toe_surface_centroid_m"]) - a["toe_surface_centroid_m"]) / (current["time_s"] - previous["time_s"])
                max_surface_speed = max(max_surface_speed, float(velocity))
                old = np.asarray([frames[index]["feet"][side]["toe_points"][i]["point_m"] for i in patch_indices[side]])
                new = np.asarray([frames[index + 1]["feet"][side]["toe_points"][i]["point_m"] for i in patch_indices[side]])
                speed = np.linalg.norm(new - old, axis=1).max() / (current["time_s"] - previous["time_s"])
                max_distal_patch_speed = max(max_distal_patch_speed, float(speed))
                # Contact means the persistent lower surface, not every
                # vertex merely within the broad 3cm proximity envelope.
                # A roll-off legitimately lifts most of the original patch.
                speed, count = active_surface_velocity(old, new, up_axis=axis, ground_m=ground, floor_gap_m=ground_gap, delta_time_s=current["time_s"] - previous["time_s"])
                active_surface_pairs += count
                max_active_surface_speed = max(max_active_surface_speed, speed)
                for band in contact_band_scan:
                    band_speed, _ = active_surface_velocity(old, new, up_axis=axis, ground_m=ground, floor_gap_m=ground_gap, delta_time_s=current["time_s"] - previous["time_s"], contact_band_m=float(band))
                    if band_speed > contact_band_scan[band]:
                        active = (old[:, axis] <= old[:, axis].min() + float(band)) & (new[:, axis] <= new[:, axis].min() + float(band)) & (old[:, axis] - ground <= ground_gap) & (new[:, axis] - ground <= ground_gap)
                        ids = np.flatnonzero(active)
                        point = int(ids[np.linalg.norm(new[ids] - old[ids], axis=1).argmax()])
                        proximity_witnesses[band] = {**witness_context, "previous_world_m": old[point].tolist(), "current_world_m": new[point].tolist(), "previous_ground_gap_m": float(old[point, axis] - ground), "current_ground_gap_m": float(new[point, axis] - ground), "maximum_velocity_mps": band_speed}
                    contact_band_scan[band] = max(contact_band_scan[band], band_speed)
    for summary in true_ground_scan.values():
        summary["status"] = "MEASURED_PERSISTENT_GROUND_POINTS" if summary["persistent_point_pairs"] else "NO_PERSISTENT_POINTS_AT_THIS_GROUND_TOLERANCE"
    extra_contact_evidence = {"relative_bottom_band_classification": "proximity deformation; not proof of contact at the fixed floor", "proximity_band_peak_witnesses": proximity_witnesses, "absolute_ground_plane_velocity": true_ground_scan}
    result = {**extra_contact_evidence, "status": "PASS_FOCUSED_SKIN_FLOOR" if max_penetration <= .0005 and contact_misses == 0 and airborne_misses == 0 and flight_interior > 0 else "FAIL_FOCUSED_SKIN_FLOOR", "ground_level_m": ground, "source_floor_not_recalibrated": True, "maximum_foot_surface_penetration_m": max_penetration, "planned_stance_without_surface_contact_samples": contact_misses, "interior_flight_samples": flight_interior, "interior_flight_with_surface_ground_intersection_samples": airborne_misses, "maximum_planted_toe_surface_centroid_velocity_mps": max_surface_speed, "maximum_planted_distal_surface_point_velocity_mps": max_distal_patch_speed, "maximum_active_ground_surface_point_velocity_mps": max_active_surface_speed, "contact_band_sensitivity_max_velocity_mps": contact_band_scan, "active_ground_surface_point_pairs": active_surface_pairs, "distal_patch_vertex_indices": {s: [metadata["mask_counts"][s]["toe_vertex_indices"][i] for i in ids] for s, ids in patch_indices.items()}, "skin_adapter": metadata, "frames": facts, "acceptance": "focused ground/flight evidence only; visual review and contact-patch drift gate still required"}
    if include_contact_authority:
        result["contact_authority_v1"] = _contact_authority_from_skin_frames(
            frames, facts, ground_m=ground, up_axis=axis, thresholds=authority_thresholds
        )
    return result


def _contact_authority_from_skin_frames(
    frames: Any, facts: Any, *, ground_m: float, up_axis: int, thresholds: Any = None
) -> dict[str, Any]:
    """Build the persistent ground-plane authority verdict from skin frames.

    Pure data adapter: skinned sole/toe vertices plus planned contact become
    per-foot :class:`PatchFrame` timelines evaluated by
    ``dynamics.contact_authority.evaluate_contact_authority``. Band-relative
    speeds are never consulted for the verdict.
    """
    from ..dynamics.contact_authority import (
        AuthorityThresholds,
        PatchFrame,
        evaluate_contact_authority,
    )

    per_foot: dict[str, Any] = {}
    if thresholds is None:
        thresholds = AuthorityThresholds(up_axis=up_axis, ground_m=ground_m)
    for side in ("left", "right"):
        patch_frames: list[PatchFrame] = []
        loaded: list[bool] = []
        for frame, row in zip(frames, facts):
            sole = tuple(tuple(float(v) for v in p["point_m"]) for p in frame["feet"][side]["sole_points"])
            toe = tuple(tuple(float(v) for v in p["point_m"]) for p in frame["feet"][side]["toe_points"])
            patch_frames.append(
                PatchFrame(time_s=float(frame["time_s"]), sole_m=sole, toe_m=toe)
            )
            loaded.append(bool(row["feet"][side]["planned_contact"]))
        try:
            kwargs: dict[str, Any] = {}
            if thresholds is not None:
                kwargs["thresholds"] = thresholds
            per_foot[side] = evaluate_contact_authority(
                patch_frames,
                loaded,
                **kwargs,
            )
        except ContractError as exc:
            per_foot[side] = {"verdict": "FAIL", "reasons": [str(exc)]}
    # A foot with zero loaded phases makes no contact claim (neutral); the
    # run fails only if no foot was ever loaded or a loaded foot fails.
    loaded_feet = [v for v in per_foot.values() if v.get("phase_count", 0) > 0]
    if not loaded_feet:
        overall = "FAIL"
    else:
        overall = "PASS" if all(v.get("verdict") == "PASS" for v in loaded_feet) else "FAIL"
    return {
        "schema": "eonwild.motion.v9.contact-authority.v1",
        "verdict": overall,
        "per_foot": per_foot,
        "classification": "persistent ground-plane semantics; band-relative speeds excluded from verdict",
    }


def evaluate_airborne_skin_with_authority(
    glb: Glb, *, contact_profile: Mapping[str, Any], gait: AirborneGait, body_height_m: float, sample_hz: int = 120, authority_thresholds: Any = None, clip_name: str = "V9_AIRBORNE_RUN_ROOT_MOTION", plan_override: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Sibling of :func:`evaluate_airborne_skin` with authority verdict on."""

    return evaluate_airborne_skin(
        glb,
        contact_profile=contact_profile,
        gait=gait,
        body_height_m=body_height_m,
        sample_hz=sample_hz,
        include_contact_authority=True,
        authority_thresholds=authority_thresholds,
        clip_name=clip_name,
        plan_override=plan_override,
    )
