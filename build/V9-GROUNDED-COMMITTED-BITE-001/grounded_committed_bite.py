#!/usr/bin/env python3
"""Build the task-local, semantic, grounded committed-bite candidate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any


TASK = "V9-GROUNDED-COMMITTED-BITE-001"
REPOSITORY = Path(__file__).resolve().parents[2]
SEED = REPOSITORY / "build/V9-ALERT-IDLE-OVERLAY-001/alert_idle_overlay.py"
sys.path.insert(0, str(REPOSITORY))

from src.eonwild_motion.glb import Glb  # noqa: E402
from src.eonwild_motion.layers.leg_contact_resolve_v3 import (  # noqa: E402
    _clip_state,
    _pose,
    _world_matrices,
    _world_position,
)


def _seed() -> Any:
    spec = importlib.util.spec_from_file_location("v9_alert_idle_seed", SEED)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load alert-idle GLB helper seed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S = _seed()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def smooth(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * u * (10.0 + u * (-15.0 + 6.0 * u))


def body_signal(t: float) -> float:
    if t <= 3.0:
        return 0.55 * smooth(t / 3.0)
    if t <= 3.7:
        return 0.55 + 0.45 * smooth((t - 3.0) / 0.7)
    if t <= 5.8:
        return 1.0
    return 1.0 - smooth((t - 5.8) / 2.2)


def jaw_signal(t: float) -> float:
    if t <= 2.8:
        return 0.0
    if t <= 3.7:
        return smooth((t - 2.8) / 0.9)
    if t <= 4.4:
        return 1.0 - 0.82 * smooth((t - 3.7) / 0.7)
    if t <= 5.8:
        return 0.18
    return 0.18 * (1.0 - smooth((t - 5.8) / 2.2))


def qrotate(q: tuple[float, ...], v: tuple[float, float, float]) -> tuple[float, float, float]:
    p = (v[0], v[1], v[2], 0.0)
    qi = (-q[0], -q[1], -q[2], q[3])
    r = S.qmul(S.qmul(q, p), qi)
    return (r[0], r[1], r[2])


def unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.sqrt(sum(x * x for x in v))
    if n <= 1e-9:
        raise ValueError("degenerate semantic body basis")
    return tuple(x / n for x in v)


def binding_roles(binding: dict[str, Any]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for row in binding["roles"]:
        out.setdefault(row["semantic"], []).append(int(row["node_index"]))
    return out


def target_angles(profile: dict[str, Any]) -> tuple[float, float]:
    target = profile["target"]["normalized_position"]
    metrics = profile["body_metrics"]
    forward_m = float(target[0]) * float(metrics["body_length_m"])
    down_m = float(target[1]) * float(metrics["body_height_m"])
    lateral_m = float(target[2]) * float(metrics["body_width_m"])
    if forward_m <= 0.0:
        raise ValueError("committed Bite target must be forward of the semantic root")
    return math.degrees(math.atan2(down_m, forward_m)), math.degrees(math.atan2(lateral_m, forward_m))


def distance(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def solve_aim(
    *, source_raw: bytes, clip: str, sample: int, role_map: dict[str, list[int]],
    axes: dict[str, list[float]], masks: dict[str, Any], target: tuple[float, ...], strength: float,
) -> tuple[dict[str, tuple[float, float]], float, float]:
    glb = Glb.from_bytes(source_raw)
    tracks, _ = _clip_state(glb, clip)
    translations, rotations, scales = _pose(glb, tracks, sample)
    proxy = role_map["jaw_lower"][0]
    initial = distance(_world_position(_world_matrices(glb, translations, rotations, scales)[proxy]), target)
    angles: dict[str, tuple[float, float]] = {}
    for semantic in ("pelvis", "spine", "chest", "neck", "head"):
        mask = masks[semantic]
        pitch_cap = abs(float(mask["pitch_degrees"]))
        yaw_cap = abs(float(mask.get("yaw_degrees", 0.0)))
        best = (0.0, 0.0)
        best_distance = distance(_world_position(_world_matrices(glb, translations, rotations, scales)[proxy]), target)
        baseline = list(rotations)
        for pitch in (-(pitch_cap), -0.5 * pitch_cap, 0.0, 0.5 * pitch_cap, pitch_cap):
            for yaw in (-(yaw_cap), 0.0, yaw_cap):
                trial = list(baseline)
                for node, weight in zip(role_map[semantic], mask["chain_weights"]):
                    overlay = S.qnormalize(S.qmul(S.qaxis(axes["pitch"], math.radians(pitch * strength * weight)), S.qaxis(axes["yaw"], math.radians(yaw * strength * weight))))
                    trial[node] = S.qnormalize(S.qmul(tuple(trial[node]), overlay))
                candidate_distance = distance(_world_position(_world_matrices(glb, translations, trial, scales)[proxy]), target)
                if candidate_distance < best_distance:
                    best_distance, best = candidate_distance, (pitch, yaw)
        angles[semantic] = best
        for node, weight in zip(role_map[semantic], mask["chain_weights"]):
            overlay = S.qnormalize(S.qmul(S.qaxis(axes["pitch"], math.radians(best[0] * strength * weight)), S.qaxis(axes["yaw"], math.radians(best[1] * strength * weight))))
            rotations[node] = S.qnormalize(S.qmul(tuple(rotations[node]), overlay))
    final = distance(_world_position(_world_matrices(glb, translations, rotations, scales)[proxy]), target)
    if final >= initial:
        raise ValueError("bounded semantic aim did not reduce mouth-proxy target distance")
    return angles, initial, final


def channel_accessors(document: dict[str, Any], animation: dict[str, Any]) -> dict[tuple[int, str], tuple[int, int]]:
    out: dict[tuple[int, str], tuple[int, int]] = {}
    for channel in animation["channels"]:
        node = int(channel["target"]["node"])
        path = channel["target"]["path"]
        sampler = animation["samplers"][int(channel["sampler"])]
        out[(node, path)] = (int(sampler["input"]), int(sampler["output"]))
    return out


def build_legacy_rejected(profile_path: Path, output: Path, receipt_path: Path) -> dict[str, Any]:
    profile_raw = profile_path.read_bytes()
    profile = json.loads(profile_raw)
    if profile["schema"] != "eonwild.motion.v9.experimental-grounded-committed-bite.v1":
        raise ValueError("unexpected profile schema")
    source_path = REPOSITORY / profile["source"]["path"]
    semantic_path = REPOSITORY / profile["semantic_rig"]["path"]
    binding_path = REPOSITORY / profile["semantic_binding"]["path"]
    source_raw, semantic_raw, binding_raw = source_path.read_bytes(), semantic_path.read_bytes(), binding_path.read_bytes()
    if sha(source_raw) != profile["source"]["sha256"]:
        raise ValueError("source hash mismatch")
    if sha(binding_raw) != profile["semantic_binding"]["sha256"]:
        raise ValueError("semantic binding hash mismatch")
    if sha(semantic_raw) != profile["semantic_rig"]["sha256"]:
        raise ValueError("semantic rig hash mismatch")
    semantic_rig = json.loads(semantic_raw)
    binding = json.loads(binding_raw)
    roles = binding_roles(binding)
    allowed = {"pelvis", "spine", "chest", "neck", "head", "jaw_lower", "tail"}

    document, binary = S.parse_glb(source_raw)
    node_names = {node.get("name"): index for index, node in enumerate(document["nodes"]) if node.get("name")}
    def semantic_indices(value: Any) -> list[int]:
        names = [value] if isinstance(value, str) else value
        if not isinstance(names, list) or not all(name in node_names for name in names):
            raise ValueError("semantic rig references unavailable source nodes")
        return [node_names[name] for name in names]
    rig_roles = semantic_rig["roles"]
    jaw_node = roles["jaw_lower"][0]
    if document["nodes"][jaw_node].get("name") != next(row["node_display_id"] for row in binding["roles"] if row["semantic"] == "jaw_lower"):
        raise ValueError("jaw semantic binding identity mismatch")
    role_map = {key: semantic_indices(rig_roles[key]) for key in ("pelvis", "spine", "chest", "neck", "head", "tail")}
    role_map["jaw_lower"] = [jaw_node]
    protected_semantics = {"root", "left_contact_chain", "right_contact_chain", "left_toe_chains", "right_toe_chains"}
    protected_nodes = set(semantic_indices(rig_roles["root"]))
    for side in ("left", "right"):
        leg = rig_roles["legs"][side]
        protected_nodes.update(semantic_indices(leg["contactChain"]))
        for toe_chain in leg["toeChains"]:
            protected_nodes.update(semantic_indices(toe_chain))
    animation = S.animation_by_name(document, profile["source"]["clip"])
    channels = channel_accessors(document, animation)
    before = bytes(binary)
    duration = float(profile["timing"]["duration_seconds"])
    input_accessors = {pair[0] for pair in channels.values()}
    for accessor in input_accessors:
        times = S.read_accessor(document, binary, accessor)
        source_duration = times[-1][0]
        retimed = [(duration * row[0] / source_duration,) for row in times]
        S.write_accessor(document, binary, accessor, retimed)
        document["accessors"][accessor]["min"] = [0.0]
        document["accessors"][accessor]["max"] = [duration]

    source_glb = Glb.from_bytes(source_raw)
    source_tracks, _ = _clip_state(source_glb, profile["source"]["clip"])
    translations0, rotations0, scales0 = _pose(source_glb, source_tracks, 0)
    worlds0 = _world_matrices(source_glb, translations0, rotations0, scales0)
    head_position = _world_position(worlds0[role_map["head"][-1]])
    pelvis_position = _world_position(worlds0[role_map["pelvis"][0]])
    tail_position = _world_position(worlds0[role_map["tail"][0]])
    rear_reference = tuple((pelvis_position[i] + tail_position[i]) * 0.5 for i in range(3))
    forward_raw = tuple(head_position[i] - rear_reference[i] for i in range(3))
    forward = unit((forward_raw[0], 0.0, forward_raw[2]))
    up = (0.0, 1.0, 0.0)
    lateral = unit((forward[2], 0.0, -forward[0]))
    target_n = profile["target"]["normalized_position"]
    metrics = profile["body_metrics"]
    target_offset = tuple(
        forward[i] * target_n[0] * metrics["body_length_m"]
        + up[i] * target_n[1] * metrics["body_height_m"]
        + lateral[i] * target_n[2] * metrics["body_width_m"]
        for i in range(3)
    )
    mouth_origin = _world_position(worlds0[role_map["jaw_lower"][0]])
    target_position = tuple(mouth_origin[i] + target_offset[i] for i in range(3))
    strength = float(profile["parameter"]["default"])
    target_pitch_degrees, target_yaw_degrees = target_angles(profile)
    aim_sample = round(3.7 / duration * (int(profile["source"]["sample_count"]) - 1))
    aim_angles, aim_initial_distance, aim_final_distance = solve_aim(
        source_raw=source_raw, clip=profile["source"]["clip"], sample=aim_sample,
        role_map=role_map, axes=profile["axes_local_xyz"], masks=profile["authority_masks"],
        target=target_position, strength=strength,
    )
    changed: list[dict[str, Any]] = []
    max_norm_error = 0.0
    max_delta = 0.0
    max_rate = 0.0
    for semantic, nodes in role_map.items():
        if semantic not in allowed:
            raise AssertionError("authority escaped semantic allowlist")
        mask = profile["authority_masks"][semantic]
        weights = mask["chain_weights"]
        if len(weights) != len(nodes):
            if len(nodes) == 1:
                weights = [weights[-1]]
            else:
                weights = [weights[min(i, len(weights) - 1)] for i in range(len(nodes))]
        for node, weight in zip(nodes, weights):
            if node in protected_nodes:
                raise ValueError("protected support node overlaps bite authority")
            if (node, "rotation") not in channels:
                raise ValueError(f"semantic {semantic} lacks a rotation channel")
            input_accessor, output_accessor = channels[(node, "rotation")]
            source_rows = S.read_accessor(document, before, output_accessor)
            times = S.read_accessor(document, binary, input_accessor)
            rows = []
            prior_overlay: tuple[float, ...] | None = None
            prior_time: float | None = None
            for time_row, source_q in zip(times, source_rows):
                t = time_row[0]
                signal = jaw_signal(t) if semantic == "jaw_lower" else body_signal(t)
                configured_pitch = float(mask.get("open_degrees", mask.get("pitch_degrees", 0.0)))
                if semantic in aim_angles:
                    degrees = aim_angles[semantic][0]
                else:
                    degrees = configured_pitch
                pitch = math.radians(degrees * strength * float(weight) * signal)
                configured_yaw = abs(float(mask.get("yaw_degrees", 0.0)))
                derived_yaw = aim_angles[semantic][1] if semantic in aim_angles else math.copysign(min(abs(target_yaw_degrees), configured_yaw), target_yaw_degrees)
                yaw = math.radians(derived_yaw * strength * float(weight) * signal)
                overlay = S.qnormalize(S.qmul(S.qaxis(profile["axes_local_xyz"]["pitch"], pitch), S.qaxis(profile["axes_local_xyz"]["yaw"], yaw)))
                if prior_overlay is not None and prior_time is not None:
                    dot = min(1.0, abs(sum(prior_overlay[i] * overlay[i] for i in range(4))))
                    max_rate = max(max_rate, math.degrees(2.0 * math.acos(dot)) / (t - prior_time))
                prior_overlay, prior_time = overlay, t
                value = S.qnormalize(S.qmul(tuple(source_q), overlay))
                max_norm_error = max(max_norm_error, abs(math.sqrt(sum(x*x for x in value)) - 1.0))
                max_delta = max(max_delta, abs(math.degrees(pitch)), abs(math.degrees(yaw)))
                rows.append(value)
            rows[0] = tuple(source_rows[0])
            rows[-1] = tuple(source_rows[-1])
            S.write_accessor(document, binary, output_accessor, rows)
            changed.append({"semantic": semantic, "node_index": node, "output_accessor": output_accessor})

    rate_limit = float(profile["limits"]["max_action_angular_rate_degrees_per_second"])
    if max_rate > rate_limit + 1.0e-6:
        raise ValueError(f"emitted action angular rate {max_rate:.6f} exceeds {rate_limit:.6f} deg/s")
    minimum_aim_reduction = float(profile["limits"]["minimum_mouth_proxy_aim_reduction_m"])
    if aim_initial_distance - aim_final_distance < minimum_aim_reduction:
        raise ValueError(f"bounded semantic aim reduction {aim_initial_distance - aim_final_distance:.6f}m did not meet {minimum_aim_reduction:.6f}m")

    protected_outputs = sorted({channels[key][1] for key in channels if key[0] in protected_nodes})
    for accessor in protected_outputs:
        old = S.read_accessor(document, before, accessor)
        new = S.read_accessor(document, binary, accessor)
        if old != new:
            raise ValueError(f"protected output accessor {accessor} changed")
    animation["name"] = "grounded_committed_bite"
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = S.encode_glb(document, binary)
    emitted_glb = Glb.from_bytes(encoded)
    emitted_tracks, _ = _clip_state(emitted_glb, "grounded_committed_bite")
    emitted_translations, emitted_rotations, emitted_scales = _pose(emitted_glb, emitted_tracks, aim_sample)
    emitted_proxy_position = _world_position(
        _world_matrices(emitted_glb, emitted_translations, emitted_rotations, emitted_scales)[role_map["jaw_lower"][0]]
    )
    source_translations, source_rotations, source_scales = _pose(source_glb, source_tracks, aim_sample)
    source_proxy_position = _world_position(
        _world_matrices(source_glb, source_translations, source_rotations, source_scales)[role_map["jaw_lower"][0]]
    )
    reopened_source_distance = distance(source_proxy_position, target_position)
    reopened_emitted_distance = distance(emitted_proxy_position, target_position)
    reopened_reduction = reopened_source_distance - reopened_emitted_distance
    if reopened_reduction < minimum_aim_reduction:
        raise ValueError(f"reopened emitted mouth-proxy reduction {reopened_reduction:.6f}m did not meet {minimum_aim_reduction:.6f}m")
    output.write_bytes(encoded)
    candidate_label = str(output.relative_to(REPOSITORY)) if output.is_relative_to(REPOSITORY) else str(output)
    receipt = {
        "schema": "eonwild.motion.v9.grounded-committed-bite-receipt.v1", "task": TASK,
        "status": "STRUCTURAL_PASS_PREVIEW_CANDIDATE", "candidate": candidate_label, "candidate_sha256": sha(encoded),
        "profile_sha256": sha(profile_raw), "duration_seconds": duration,
        "body_basis": {"derivation": "frame-zero semantic head minus pelvis/tail rear reference", "forward_world": forward, "up_world": up, "lateral_world": lateral},
        "target": {"normalized_forward_down_lateral": target_n, "mouth_proxy_origin_m": mouth_origin,
                   "world_offset_m": target_offset, "world_position_m": target_position,
                   "preview_prop_radius_m": float(profile["target"]["contact_radius_normalized"]) * float(metrics["body_width_m"]),
                   "lateral_normalized": target_n[2],
                   "derived_reach_pitch_degrees": target_pitch_degrees, "derived_reach_yaw_degrees": target_yaw_degrees},
        "bounded_aim": {"sample": aim_sample, "angles_degrees_by_semantic": aim_angles,
                        "solver_trial_initial_mouth_proxy_distance_m": aim_initial_distance,
                        "solver_trial_final_mouth_proxy_distance_m": aim_final_distance,
                        "reopened_source_mouth_proxy_distance_m": reopened_source_distance,
                        "reopened_emitted_mouth_proxy_distance_m": reopened_emitted_distance,
                        "distance_reduction_m": reopened_reduction,
                        "minimum_required_reduction_m": minimum_aim_reduction},
        "phase_windows_seconds": profile["timing"]["phase_windows_seconds"],
        "authority_semantics": sorted(allowed), "changed_rotation_channels": changed,
        "protected_semantics": sorted(protected_semantics), "protected_output_accessors": protected_outputs,
        "protected_output_accessors_exact": True, "timeline_only_retimed": True,
        "endpoint_overlay_zero": True, "max_overlay_rotation_degrees": max_delta,
        "max_quaternion_norm_error": max_norm_error,
        "max_emitted_action_angular_rate_degrees_per_second": max_rate,
        "angular_rate_limit_degrees_per_second": rate_limit,
        "jaw": {"open_peak_degrees": 24.0 * strength, "closed_hold_fraction": 0.18,
                "authored_close_and_hold_proxy_window_seconds": [3.7, 5.8], "contact_geometry": "NOT_EVALUATED"},
        "gates": {
            "authority_isolation": "PASS",
            "protected_root_leg_foot_toe_output_exact": "PASS",
            "protected_support_output_channel_delta": 0.0,
            "support_world_drift": "NOT_EVALUATED_NO_SKINNED_SOLE_WITNESS",
            "emitted_endpoint_overlay_zero": "PASS",
            "emitted_action_angular_rate": "PASS",
            "target_contact_distance": "NOT_EVALUATED_NO_SKINNED_JAW_WITNESS",
            "visual_acceptance": "NOT_CLAIMED",
        },
        "claims": profile["claims"],
    }
    receipt = json.loads(json.dumps(receipt))
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def build(profile_path: Path, output: Path, receipt_path: Path) -> dict[str, Any]:
    sys.path.insert(0, str(Path(__file__).parent))
    from attack_solver import build_attack
    return build_attack(profile_path, output, receipt_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=Path(__file__).with_name("profile.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "attack-r5/grounded-committed-bite.glb")
    parser.add_argument("--receipt", type=Path, default=Path(__file__).parent / "attack-r5/receipt.json")
    args = parser.parse_args()
    print(json.dumps(build(args.profile.resolve(), args.output.resolve(), args.receipt.resolve()), indent=2))


if __name__ == "__main__":
    main()
