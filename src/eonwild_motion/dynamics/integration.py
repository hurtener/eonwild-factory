"""Leg+axial unified solve: one planner, one receipt.

The leg solver (``solve/airborne_gait.py``) owns root/pelvis/legs/toes;
the axial solver (``dynamics/whole_body.py``) owns spine/neck/head/tail
target tracking with momentum-coupled tails. This module runs both and
emits a single GLB plus a unified receipt with cross-contract checks:

* non-axial channels are byte-identical to the leg-only output;
* contact flags come from the one shared plan (never re-derived);
* replaced axial channels close the loop seam and sit inside hard
  envelopes;
* the unified receipt hashes the leg receipt, the axial solution and
  the checks together.

Authority order is explicit: the dynamics axial plan *replaces* the
kinematic presentation overlay (chest/head/tail sine or lagged
response) on bound axial nodes. Everything else is untouched.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..hashing import sha256_json
from .centroidal import _finite, quat_to_matrix
from .whole_body import _axis_angle_quat, solve_bite_window


def _read_clip_channels(glb: Glb, clip: str) -> tuple[np.ndarray, dict[tuple[int, str], np.ndarray]]:
    """All animation channels as float arrays plus the shared timeline."""
    animation = glb.animation(clip)
    times: np.ndarray | None = None
    channels: dict[tuple[int, str], np.ndarray] = {}
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        node, path = int(channel["target"]["node"]), channel["target"]["path"]
        values = np.asarray(glb.accessor_values(int(sampler["output"])), dtype=float)
        sample_times = np.asarray(glb.accessor_values(int(sampler["input"])), dtype=float).reshape(-1)
        if times is None:
            times = sample_times
        elif not np.array_equal(times, sample_times):
            raise ContractError("unified overlay needs a single shared timeline")
        channels[(node, path)] = values
    if times is None or not channels:
        raise ContractError("clip has no channels to integrate")
    return times, channels


def _quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Hamilton product a*b (apply b first, then a)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return np.array([
        a[3] * b[0] + a[0] * b[3] + a[1] * b[2] - a[2] * b[1],
        a[3] * b[1] - a[0] * b[2] + a[1] * b[3] + a[2] * b[0],
        a[3] * b[2] + a[0] * b[1] - a[1] * b[0] + a[2] * b[3],
        a[3] * b[3] - a[0] * b[0] - a[1] * b[1] - a[2] * b[2],
    ])


def _quat_angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    dot = max(-1.0, min(1.0, abs(float(np.asarray(a, dtype=float) @ np.asarray(b, dtype=float)))))
    return math.degrees(2.0 * math.acos(dot))


def replace_axial_rotations(
    glb: Glb,
    *,
    clip: str,
    chains: Sequence[Mapping[str, Any]],
    pitch_tracks: Sequence[Sequence[Sequence[float]]],
    yaw_tracks: Sequence[Sequence[Sequence[float]]] | None = None,
) -> tuple[dict[tuple[int, str], np.ndarray], dict[str, Any]]:
    """Swap bound axial rotation channels for rest-pose-plus-pitch tracks.

    ``chains[i]`` is ``{"nodes": [names...], "lateral": [x, y, z]}`` and
    ``pitch_tracks[i][k][j]`` is the pitch (radians) of joint ``j`` at
    frame ``k``. Returns the full channel map plus an overlay report.
    Rest orientation comes from the GLB (never assumed identity).

    Optional ``yaw_tracks`` (same shape as ``pitch_tracks``) adds a
    second rotation about ``chains[i]["yaw_axis"]`` (default ``[0,0,1]``)
    composed as ``pitch * yaw * rest``. When omitted the output is
    exactly the legacy pitch-only overlay.
    """
    if len(chains) != len(pitch_tracks):
        raise ContractError("axial chains and pitch tracks must align")
    if yaw_tracks is not None and len(yaw_tracks) != len(chains):
        raise ContractError("axial yaw tracks must align with chains")
    times, channels = _read_clip_channels(glb, clip)
    frames = len(times)
    replaced: list[str] = []
    yawed: list[str] = []
    max_change_deg = 0.0
    for i, (spec, track) in enumerate(zip(chains, pitch_tracks)):
        names = [str(n) for n in spec["nodes"]]
        lateral = np.asarray(spec["lateral"], dtype=float)
        if lateral.shape != (3,) or float(np.linalg.norm(lateral)) <= 1e-12:
            raise ContractError("axial lateral axis must be a non-zero 3-vector")
        lateral = lateral / float(np.linalg.norm(lateral))
        yaw_axis = None
        yaw_track = yaw_tracks[i] if yaw_tracks is not None else None
        if yaw_track is not None:
            yaw_axis = np.asarray(spec.get("yaw_axis", [0.0, 0.0, 1.0]), dtype=float)
            if yaw_axis.shape != (3,) or float(np.linalg.norm(yaw_axis)) <= 1e-12:
                raise ContractError("axial yaw axis must be a non-zero 3-vector")
            yaw_axis = yaw_axis / float(np.linalg.norm(yaw_axis))
            if len(yaw_track) != frames:
                raise ContractError("axial yaw track length must match the clip")
        if len(track) != frames:
            raise ContractError("axial pitch track length must match the clip")
        for j, name in enumerate(names):
            if name not in glb.name_to_node:
                raise ContractError(f"axial node {name!r} is not in the rig")
            node = glb.name_to_node[name]
            key = (node, "rotation")
            if key not in channels:
                raise ContractError(f"axial node {name!r} has no rotation channel")
            rest = np.asarray(glb.rest_rotation[node], dtype=float)
            rows = []
            for k in range(frames):
                pitch = _finite(float(track[k][j]), label=f"axial pitch {name}[{k}]")
                oriented = _axis_angle_quat(lateral, pitch)
                if yaw_track is not None:
                    yaw = _finite(float(yaw_track[k][j]), label=f"axial yaw {name}[{k}]")
                    # Yaw first in the parent frame, then pitch: q = pitch * yaw.
                    oriented = _quat_mul(oriented, _axis_angle_quat(yaw_axis, yaw))
                    if name not in yawed:
                        yawed.append(name)
                # Parent-frame orientation premultiplied on rest orientation.
                q = _quat_mul(oriented, rest)
                rows.append(q / float(np.linalg.norm(q)))
            rows_arr = np.asarray(rows)
            for old, new in zip(channels[key], rows_arr):
                max_change_deg = max(max_change_deg, _quat_angle_deg(old, new))
            channels[key] = rows_arr
            replaced.append(name)
    # Loop seam on replaced channels (cyclic gaits must close).
    seam_deg = 0.0
    for name in replaced:
        rows = channels[(glb.name_to_node[name], "rotation")]
        seam_deg = max(seam_deg, _quat_angle_deg(rows[0], rows[-1]))
    report: dict[str, Any] = {
        "channels_replaced": replaced,
        "max_replace_deg": max_change_deg,
        "loop_seam_deg": seam_deg,
    }
    if yawed:
        report["channels_yawed"] = yawed
    return channels, report


def solve_gaze_targets(
    root_positions: Sequence[Sequence[float]],
    *,
    forward: Sequence[float],
    distance_m: float = 3.0,
    height_offset_m: float = 0.0,
) -> list[list[float]]:
    """Forward gaze points: pelvis-height targets ahead of the root."""
    fwd = np.asarray(forward, dtype=float)
    if fwd.shape != (3,) or float(np.linalg.norm(fwd)) <= 1e-12:
        raise ContractError("gaze forward axis must be a non-zero 3-vector")
    fwd = fwd / float(np.linalg.norm(fwd))
    distance = _finite(distance_m, label="gaze distance")
    height = _finite(height_offset_m, label="gaze height offset")
    return [
        [float(p[0] + fwd[0] * distance), float(p[1] + height), float(p[2] + fwd[2] * distance)]
        for p in (np.asarray(pos, dtype=float) for pos in root_positions)
    ]


def tail_step_asymmetry(
    plan: Mapping[str, Any],
    times_s: Sequence[float],
) -> list[float]:
    """Per-frame stance asymmetry from the shared contact plan.

    +1 when only the left foot is in stance, -1 when only the right
    foot is, 0 for double support or flight. Plan samples are matched
    to clip frames by nearest time (fail-closed on empty timelines).
    This is the step-coupled drive for lateral tail counter-sway: the
    tail answers footfalls instead of QuickTime-wobbling on a sine.
    """
    samples = list(plan.get("samples", []))
    if not samples:
        raise ContractError("tail drive needs plan samples")
    plan_times = [float(s["time_s"]) for s in samples]
    drive: list[float] = []
    for t in times_s:
        t = float(t)
        best = min(range(len(plan_times)), key=lambda i: abs(plan_times[i] - t))
        feet = samples[best].get("feet", {})
        left = bool(feet.get("left", {}).get("contact", False))
        right = bool(feet.get("right", {}).get("contact", False))
        drive.append(1.0 if left and not right else (-1.0 if right and not left else 0.0))
    return drive


def _tail_linkage(source: Glb, names: Sequence[str]) -> tuple[list[int], list[int]]:
    """Validate base-to-tip linkage; return (ancestor_indices, tail_indices)."""
    tail = [source.name_to_node[str(n)] for n in names]
    for prev, cur in zip(tail, tail[1:]):
        if source.parents[cur] != prev:
            raise ContractError(
                f"tail chain must be linked base-to-tip: {names}")
    ancestors: list[int] = []
    parent = source.parents[tail[0]]
    while parent is not None:
        ancestors.append(parent)
        parent = source.parents[parent]
    return ancestors[::-1], tail


def tail_recenter_yaws(
    source: Glb,
    tail_names: Sequence[str],
    yaw_axis: Sequence[float],
    fraction: float,
    world_lateral: Sequence[float] = (1.0, 0.0, 0.0),
    channels: Mapping[tuple[int, str], np.ndarray] | None = None,
    base_rotations: Mapping[int, Sequence[Sequence[float]]] | None = None,
) -> list[float]:
    """Static per-bone yaw cancelling ``fraction`` of the tail lean.

    The overlay bakes a frozen pose in, so any lean that pose carries
    (rest bias, or a source-frame offset the leg solve froze in) stays
    forever under pitch-only overlays. This runs a full FK from the
    root — through every ancestor, so twisted pelvis frames cannot fool
    it —     measures the tip's world-frame offset from the tail attachment along
    ``world_lateral``, and Newton-solves (finite-difference slope,
    deterministic) the uniform per-bone yaw that zeroes it. Centered
    means tip-above-attachment laterally, not tip-at-origin.

    With ``channels`` (a ``(node, path) -> frames`` map as returned by
    :func:`_read_clip_channels`) the offset is averaged over the
    animated frames, so the constant yaw cancels the animated mean —
    the case that actually matters for overlays on solved motion.
    Without it the rest pose is used. With ``base_rotations`` (tail
    node index -> per-frame pitch-only quats, as applied by
    :func:`replace_axial_rotations`) the tail base pose comes from the
    overlay itself — step ``P·Y·R`` exactly as emitted — so calibration
    lands precisely on the output channels. This is the normal
    unified-solve path. ``fraction`` 0 returns zeros; 1 fully centers. Yaw moves the tip perpendicular
    to the chain to first order, so recentering never shortens or
    pitches the tail.
    """
    from .whole_body import _axis_angle_quat, _rotate_vec

    fraction = _finite(fraction, label="tail_recenter")
    if not 0.0 <= fraction <= 1.0:
        raise ContractError("tail_recenter must be within [0, 1]")
    names = [str(n) for n in tail_names]
    if not names:
        raise ContractError("tail recenter needs tail nodes")
    ancestors, tail = _tail_linkage(source, names)
    yaw = np.asarray([_finite(float(v), label="yaw axis") for v in yaw_axis], dtype=float)
    yaw = yaw / float(np.linalg.norm(yaw))
    lateral = np.asarray([_finite(float(v), label="world lateral") for v in world_lateral],
                         dtype=float)
    lateral = lateral / float(np.linalg.norm(lateral))
    tail_set = set(tail)
    chain = ancestors + tail

    if channels is None:
        poses: list[tuple[list, list]] = [
            (list(source.rest_translation), list(source.rest_rotation))]
    else:
        frames = None
        for key in list(channels):
            frames = len(channels[key]) if frames is None else frames
            if len(channels[key]) != frames:
                raise ContractError("recenter channels must share one timeline")
        if not frames:
            raise ContractError("recenter channels are empty")
        poses = []
        count = len(source.nodes)
        for k in range(frames):
            trans = [list(source.rest_translation[i]) for i in range(count)]
            rot = [list(source.rest_rotation[i]) for i in range(count)]
            for (node, path), values in channels.items():
                if path == "translation":
                    trans[node] = [float(v) for v in values[k]]
                elif path == "rotation":
                    rot[node] = [float(v) for v in values[k]]
            poses.append((trans, rot))

    def mean_offset(uniform_yaw: float) -> float:
        """Mean tip-minus-attachment along world lateral with extra yaw."""
        total = 0.0
        yaw_step = _axis_angle_quat(yaw, uniform_yaw)
        for frame, (trans, rot) in enumerate(poses):
            orientation = np.array([0.0, 0.0, 0.0, 1.0])
            position = np.zeros(3)
            base_position: np.ndarray | None = None
            for index in chain:
                if index == tail[0] and base_position is None:
                    # Attachment point: the base joint BEFORE its own
                    # translation (which may itself carry the lean).
                    base_position = position.copy()
                position = position + _rotate_vec(
                    orientation, np.asarray(trans[index], dtype=float))
                if index in tail_set and base_rotations is not None and index in base_rotations:
                    # Exact overlay composition: q = P.Y.R (see
                    # replace_axial_rotations).
                    pitch_step = np.asarray(base_rotations[index][frame], dtype=float)
                    rest_step = np.asarray(source.rest_rotation[index], dtype=float)
                    step = _quat_mul(pitch_step, _quat_mul(yaw_step, rest_step))
                else:
                    step = np.asarray(rot[index], dtype=float)
                    if index in tail_set:
                        step = _quat_mul(yaw_step, step)
                orientation = _quat_mul(orientation, step)
            assert base_position is not None
            total += float((position - base_position) @ lateral)
        return total / len(poses)

    if fraction == 0.0:
        return [0.0] * len(names)
    probe = math.radians(0.5)
    solved = 0.0
    for _ in range(12):
        current = mean_offset(solved)
        if abs(current) < 1e-6:
            break
        slope = (mean_offset(solved + probe) - mean_offset(solved - probe)) / (2.0 * probe)
        if abs(slope) <= 1e-9:
            break
        # Damped Newton: the tip lever makes raw steps overshoot.
        solved -= 0.5 * current / slope
        if abs(solved) * len(names) > math.radians(90.0):
            raise ContractError("tail recenter diverged; check yaw/world-lateral axes")
    # `solved` is already the uniform per-bone yaw (the objective applies
    # it to every tail bone); distribute the fraction unchanged.
    return [fraction * solved] * len(names)


def solve_unified_run(
    *,
    source: Glb,
    source_clip: str,
    semantic_roles: Mapping[str, Any],
    gait: Any,
    axial_lateral: Sequence[float] = (0.0, 0.0, 1.0),
    gaze_distance_m: float = 3.0,
    gaze_height_offset_m: float = 0.0,
    envelopes: Mapping[str, Any] | None = None,
    tail_params: Mapping[str, Any] | None = None,
    clip_prefix: str = "V9_UNIFIED_RUN",
    axial_posture_weight: float = 0.05,
    tail_yaw_axis: Sequence[float] = (0.0, 0.0, 1.0),
    tail_lateral_peak_deg: float = 0.0,
    tail_lateral_damping: float = 0.5,
    tail_lateral_freq_hz: float | None = None,
    tail_lateral_sign: float = 1.0,
    tail_recenter: float = 0.0,
    tail_yaw_weights: Sequence[float] | None = None,
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    """Leg solve, axial gaze solve, single re-emit, unified receipt.

    Returns ``(root_motion_bytes, in_place_bytes, unified_receipt,
    detail)`` where detail carries the leg receipt, axial solution and
    overlay report for audit. Without axial chains resolvable in
    ``semantic_roles`` (no chest/neck/head/tail), raises ContractError
    instead of silently emitting leg-only output as unified.

    Lateral tail (all defaults off, legacy byte-identical): when
    ``tail_lateral_peak_deg`` is nonzero the tail also yaws side to
    side, driven by stance asymmetry from the shared contact plan
    through the damped ODE at stride frequency — counter-sway locked
    to footfalls, not a sine. ``tail_recenter`` (0..1) statically
    cancels that fraction of the rig's rest-pose lean. ``tail_yaw_axis``
    is the parent-frame yaw axis; ``tail_yaw_weights`` distributes the
    total yaw across tail bones (default uniform).
    """
    from ..solve.airborne_gait import solve_airborne_gait
    from ..solve.whole_body_gait_transition import _build_glb, _encode
    from .whole_body import solve_bite_window

    roles = semantic_roles
    chain_names: list[str] = []
    if isinstance(roles.get("chest"), str):
        chain_names.append(roles["chest"])
    chain_names.extend(roles.get("neck", []) or [])
    if isinstance(roles.get("head"), str):
        chain_names.append(roles["head"])
    tail_names: list[str] = list(roles.get("tail", []) or [])
    if not chain_names:
        raise ContractError("unified solve needs a head chain (chest/neck/head roles)")
    try:
        chain = [source.name_to_node[name] for name in chain_names]
    except KeyError as exc:
        raise ContractError(f"axial chain node missing in rig: {exc}") from exc

    authority_bytes, _, plan, leg_receipt = solve_airborne_gait(
        source, source_clip=source_clip, semantic_roles=roles, gait=gait
    )
    leg_glb = Glb.from_bytes(authority_bytes)
    leg_clip = leg_glb.document["animations"][0]["name"]
    times, channels = _read_clip_channels(leg_glb, leg_clip)
    root_idx = source.name_to_node[roles["root"]]
    root_positions = [list(map(float, row)) for row in channels[(root_idx, "translation")]]
    root_rotations = [quat_to_matrix(np.asarray(row, dtype=float)) for row in channels[(root_idx, "rotation")]]

    # Gaze targets anchor to the chain base (chest rest world position
    # carried by root displacement) — never to the root itself, which
    # sits ~2 m behind the head on a theropod rig.
    from .centroidal import fk_world_frames

    rest_t = [list(map(float, t)) for t in source.rest_translation]
    rest_r = [list(map(float, q)) for q in source.rest_rotation]
    base_rest_world, _ = fk_world_frames(source.parents, rest_t, rest_r)
    base0 = np.asarray(base_rest_world[chain[0]], dtype=float)
    root0 = np.asarray(root_positions[0], dtype=float)
    fwd = np.asarray(leg_receipt["forward_axis"], dtype=float)
    fwd = fwd / float(np.linalg.norm(fwd))
    gaze_d = _finite(gaze_distance_m, label="gaze distance")
    gaze_h = _finite(gaze_height_offset_m, label="gaze height offset")
    targets = [
        list(base0 + (np.asarray(pos, dtype=float) - root0) + fwd * gaze_d + np.array([0.0, gaze_h, 0.0]))
        for pos in root_positions
    ]
    envelope_map = dict(envelopes or {})
    lateral_active = bool(tail_names) and (
        _finite(tail_lateral_peak_deg, label="tail_lateral_peak_deg") != 0.0
        or _finite(tail_recenter, label="tail_recenter") != 0.0
    )
    tail_params_map = dict(tail_params or {})
    if lateral_active:
        peak_rad = math.radians(abs(float(tail_lateral_peak_deg)))
        sign = 1.0 if float(tail_lateral_sign) >= 0.0 else -1.0
        if "lateral_moments" not in tail_params_map:
            asym = tail_step_asymmetry(plan, [float(t) for t in times])
            inertia = float(tail_params_map.get("lateral_inertia_kg_m2",
                                                tail_params_map.get("inertia_kg_m2", 750.0)))
            freq = (float(tail_lateral_freq_hz) if tail_lateral_freq_hz is not None
                    else 1.0 / float(getattr(gait, "step_period_s", 1.25)))
            omega = 2.0 * math.pi * _finite(freq, label="tail_lateral_freq_hz")
            # Scale so a sustained single-side stance settles at the peak:
            # ODE steady state θ = M / (I·ω²).
            scale = peak_rad * inertia * omega * omega
            tail_params_map["lateral_moments"] = [sign * scale * a for a in asym]
            tail_params_map["lateral_inertia_kg_m2"] = inertia
            tail_params_map["lateral_damping_ratio"] = float(tail_lateral_damping)
            tail_params_map["lateral_natural_freq_hz"] = freq
    window = solve_bite_window(
        parents=source.parents,
        rest_translations=rest_t,
        rest_rotations=rest_r,
        chain=chain,
        root_node=root_idx,
        root_track=[{"root_position_m": pos} for pos in root_positions],
        root_rotations=root_rotations,
        lateral_axis=axial_lateral,
        targets_m=targets,
        times_s=[float(t) for t in times],
        envelopes={node: envelope_map[name] for node, name in zip(chain, chain_names) if name in envelope_map},
        tail_params=tail_params_map,
        posture_weight=axial_posture_weight,
    )
    pitch_by_node: dict[str, list[float]] = {
        name: [s["pitch_rad"][j] for s in window["samples"]] for j, name in enumerate(chain_names)
    }
    frames = len(times)
    # Pitch tracks are per-frame lists of per-joint angles.
    chain_track = [
        [pitch_by_node[name][k] for name in chain_names] for k in range(frames)
    ]
    tail_angles = [s["angle_rad"] for s in window["tail_track"]["samples"]]
    chains = [{"nodes": chain_names, "lateral": list(axial_lateral)}]
    tracks = [chain_track]
    yaw_tracks: list = [None]
    if tail_names:
        share = len(tail_names)
        tracks.append([[angle / share] * len(tail_names) for angle in tail_angles])
        chains.append({"nodes": tail_names, "lateral": list(axial_lateral)})
        if lateral_active and window.get("tail_lateral_track") is not None:
            lateral_angles = [s["angle_rad"] for s in window["tail_lateral_track"]["samples"]]
            weights = ([_finite(float(w), label="tail_yaw_weights") for w in tail_yaw_weights]
                       if tail_yaw_weights is not None else [1.0] * share)
            if len(weights) != share:
                raise ContractError("tail_yaw_weights must match the tail chain")
            total_weight = sum(weights)
            if total_weight <= 0.0:
                raise ContractError("tail_yaw_weights must sum positive")
            lateral_unit = np.asarray(list(axial_lateral), dtype=float)
            lateral_unit = lateral_unit / float(np.linalg.norm(lateral_unit))
            tail_nodes = [source.name_to_node[n] for n in tail_names]
            overlay_pitch = {
                node: [_axis_angle_quat(lateral_unit, angle / share).tolist()
                       for angle in tail_angles]
                for node in tail_nodes
            }
            recenter = tail_recenter_yaws(
                source, tail_names, tail_yaw_axis, float(tail_recenter),
                channels={key: np.asarray(values, dtype=float)
                          for key, values in channels.items()},
                base_rotations=overlay_pitch)
            chains[-1]["yaw_axis"] = list(tail_yaw_axis)
            yaw_tracks.append([
                [recenter[j] + lateral_angles[k] * weights[j] / total_weight
                 for j in range(share)]
                for k in range(frames)
            ])

    import hashlib
    import json as _json

    plan_sha = hashlib.sha256(_json.dumps(plan, sort_keys=True).encode()).hexdigest()
    state_track = dict(leg_glb.document.get("extras", {}).get("eonwildMotionStateTrack", {}))

    outputs = {}
    yaw_arg = yaw_tracks if lateral_active and any(y is not None for y in yaw_tracks) else None
    for view, clip_name, freeze_root in (
        ("root_motion", f"{clip_prefix}_ROOT_MOTION", False),
        ("in_place", f"{clip_prefix}_IN_PLACE", True),
    ):
        view_channels, overlay_report = replace_axial_rotations(
            leg_glb, clip=leg_clip, chains=chains, pitch_tracks=tracks,
            yaw_tracks=yaw_arg,
        )
        if freeze_root:
            frozen = view_channels[(root_idx, "translation")].copy()
            frozen[:, 0] = frozen[0, 0]
            frozen[:, 2] = frozen[0, 2]
            view_channels[(root_idx, "translation")] = frozen
        blob = Glb.from_bytes(_build_glb(leg_glb, clip_name, times, view_channels, plan_sha, state_track))
        blob.document["animations"][0]["extras"].update(program="unified_run", loop=True)
        outputs[view] = (_encode(blob.document, blob.binary), overlay_report)
    (root_out, overlay_report), (inplace_out, _) = outputs["root_motion"], outputs["in_place"]
    unified = unify_leg_and_axial(
        leg_glb_bytes=authority_bytes,
        leg_clip=leg_clip,
        leg_receipt=leg_receipt,
        axial=window,
        overlay_report=overlay_report,
        new_clip=f"{clip_prefix}_ROOT_MOTION",
        tail_lateral_peak_deg=float(tail_lateral_peak_deg) if lateral_active else None,
        tail_recenter=float(tail_recenter) if lateral_active else None,
    )
    detail = {"leg_receipt": leg_receipt, "axial": window, "overlay_report": overlay_report, "plan": plan}
    return root_out, inplace_out, unified, detail


def unify_leg_and_axial(
    *,
    leg_glb_bytes: bytes,
    leg_clip: str,
    leg_receipt: Mapping[str, Any],
    axial: Mapping[str, Any],
    overlay_report: Mapping[str, Any],
    new_clip: str,
    tail_lateral_peak_deg: float | None = None,
    tail_recenter: float | None = None,
) -> dict[str, Any]:
    """One receipt binding leg solve, axial solve and cross-checks."""
    body = {
        "schema": "eonwild.motion.v9.unified-solve.v1",
        "clip": new_clip,
        "leg_receipt_sha256": sha256_json(dict(leg_receipt)),
        "axial_schema": axial.get("schema"),
        "axial_worst_residual_m": axial.get("worst_residual_m"),
        "axial_all_reached": axial.get("all_reached"),
        "axial_all_inside_preferred": axial.get("all_inside_preferred"),
        "tail_conservation": (axial.get("tail_track") or {}).get("conservation"),
        "channels_replaced": list(overlay_report.get("channels_replaced", [])),
        "max_replace_deg": overlay_report.get("max_replace_deg"),
        "loop_seam_deg": overlay_report.get("loop_seam_deg"),
        "contact_source": "shared leg plan (not re-derived)",
        "claims": {
            "classification": "integrated_dynamics_candidate",
            "capacity_feasibility": "see leg receipt",
            "physical": False,
            "scientific": False,
            "biological": False,
        },
    }
    if tail_lateral_peak_deg is not None:
        body["tail_lateral_peak_deg"] = float(tail_lateral_peak_deg)
    if tail_recenter is not None:
        body["tail_recenter"] = float(tail_recenter)
    if overlay_report.get("channels_yawed"):
        body["channels_yawed"] = list(overlay_report["channels_yawed"])
    lateral_track = axial.get("tail_lateral_track") or {}
    if lateral_track.get("samples"):
        angles = [s["angle_rad"] for s in lateral_track["samples"]]
        body["tail_lateral_total_deg"] = math.degrees(max(angles) - min(angles))
    return {**body, "unified_sha256": sha256_json(body)}


__all__ = [
    "replace_axial_rotations",
    "solve_gaze_targets",
    "solve_unified_run",
    "tail_recenter_yaws",
    "tail_step_asymmetry",
    "unify_leg_and_axial",
]
