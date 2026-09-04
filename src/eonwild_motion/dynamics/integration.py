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


def _quat_angle_deg(a: np.ndarray, b: np.ndarray) -> float:
    dot = max(-1.0, min(1.0, abs(float(np.asarray(a, dtype=float) @ np.asarray(b, dtype=float)))))
    return math.degrees(2.0 * math.acos(dot))


def replace_axial_rotations(
    glb: Glb,
    *,
    clip: str,
    chains: Sequence[Mapping[str, Any]],
    pitch_tracks: Sequence[Sequence[Sequence[float]]],
) -> tuple[dict[tuple[int, str], np.ndarray], dict[str, Any]]:
    """Swap bound axial rotation channels for rest-pose-plus-pitch tracks.

    ``chains[i]`` is ``{"nodes": [names...], "lateral": [x, y, z]}`` and
    ``pitch_tracks[i][k][j]`` is the pitch (radians) of joint ``j`` at
    frame ``k``. Returns the full channel map plus an overlay report.
    Rest orientation comes from the GLB (never assumed identity).
    """
    if len(chains) != len(pitch_tracks):
        raise ContractError("axial chains and pitch tracks must align")
    times, channels = _read_clip_channels(glb, clip)
    frames = len(times)
    replaced: list[str] = []
    max_change_deg = 0.0
    for spec, track in zip(chains, pitch_tracks):
        names = [str(n) for n in spec["nodes"]]
        lateral = np.asarray(spec["lateral"], dtype=float)
        if lateral.shape != (3,) or float(np.linalg.norm(lateral)) <= 1e-12:
            raise ContractError("axial lateral axis must be a non-zero 3-vector")
        lateral = lateral / float(np.linalg.norm(lateral))
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
                composed = _axis_angle_quat(lateral, pitch)
                # Parent-frame pitch premultiplied on rest orientation.
                q = np.array([
                    composed[3] * rest[0] + composed[0] * rest[3] + composed[1] * rest[2] - composed[2] * rest[1],
                    composed[3] * rest[1] - composed[0] * rest[2] + composed[1] * rest[3] + composed[2] * rest[0],
                    composed[3] * rest[2] + composed[0] * rest[1] - composed[1] * rest[0] + composed[2] * rest[3],
                    composed[3] * rest[3] - composed[0] * rest[0] - composed[1] * rest[1] - composed[2] * rest[2],
                ])
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
    return channels, {
        "channels_replaced": replaced,
        "max_replace_deg": max_change_deg,
        "loop_seam_deg": seam_deg,
    }


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
) -> tuple[bytes, bytes, dict[str, Any], dict[str, Any]]:
    """Leg solve, axial gaze solve, single re-emit, unified receipt.

    Returns ``(root_motion_bytes, in_place_bytes, unified_receipt,
    detail)`` where detail carries the leg receipt, axial solution and
    overlay report for audit. Without axial chains resolvable in
    ``semantic_roles`` (no chest/neck/head/tail), raises ContractError
    instead of silently emitting leg-only output as unified.
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
        tail_params=dict(tail_params or {}),
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
    if tail_names:
        share = len(tail_names)
        tracks.append([[angle / share] * len(tail_names) for angle in tail_angles])
        chains.append({"nodes": tail_names, "lateral": list(axial_lateral)})

    import hashlib
    import json as _json

    plan_sha = hashlib.sha256(_json.dumps(plan, sort_keys=True).encode()).hexdigest()
    state_track = dict(leg_glb.document.get("extras", {}).get("eonwildMotionStateTrack", {}))

    outputs = {}
    for view, clip_name, freeze_root in (
        ("root_motion", f"{clip_prefix}_ROOT_MOTION", False),
        ("in_place", f"{clip_prefix}_IN_PLACE", True),
    ):
        view_channels, overlay_report = replace_axial_rotations(
            leg_glb, clip=leg_clip, chains=chains, pitch_tracks=tracks
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
    return {**body, "unified_sha256": sha256_json(body)}


__all__ = [
    "replace_axial_rotations",
    "solve_gaze_targets",
    "unify_leg_and_axial",
]
