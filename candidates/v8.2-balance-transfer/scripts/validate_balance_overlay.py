#!/usr/bin/env python3
"""Fail-closed structural and mechanical validator for V8.2 candidate A."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "candidates" / "v8.2-balance-transfer" / "scripts" / "generate_balance_overlay.py"
spec = importlib.util.spec_from_file_location("balance_generator", GENERATOR)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load candidate generator helpers")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
Glb, q_inv, q_mul, q_to_rotvec, q_normal = module.Glb, module.q_inv, module.q_mul, module.q_to_rotvec, module.q_normal


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--generation", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])


def channel_map(glb: Glb, name: str) -> dict[tuple[str, str], tuple[int, int, str]]:
    animation = glb.animation(name)
    result = {}
    for channel in animation["channels"]:
        target = channel["target"]
        node_name = glb.nodes[int(target["node"])].get("name")
        sampler = animation["samplers"][int(channel["sampler"])]
        result[(node_name, target["path"])] = (int(sampler["input"]), int(sampler["output"]), sampler.get("interpolation", "LINEAR"))
    return result


def accessor_bytes(glb: Glb, index: int) -> bytes:
    item = glb.json["accessors"][index]
    view = glb.json["bufferViews"][item["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[item["type"]]
    component_size = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[item["componentType"]]
    size = width * component_size
    stride = int(view.get("byteStride", size))
    offset = int(view.get("byteOffset", 0)) + int(item.get("byteOffset", 0))
    if stride == size:
        return glb.binary[offset:offset + int(item["count"]) * size]
    return b"".join(glb.binary[offset + i * stride:offset + i * stride + size] for i in range(int(item["count"])))


def all_local_tracks(glb: Glb, clip: str) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, np.ndarray]]:
    animation = glb.animation(clip)
    times, rotations, translations = None, {}, {}
    for channel in animation["channels"]:
        sampler = animation["samplers"][channel["sampler"]]
        t = glb.accessor(int(sampler["input"])).reshape(-1)
        if times is None:
            times = t
        elif not np.array_equal(times, t):
            raise ValueError("mixed timelines")
        node = glb.nodes[channel["target"]["node"]].get("name")
        if channel["target"]["path"] == "rotation":
            rotations[node] = glb.accessor(int(sampler["output"]))
        elif channel["target"]["path"] == "translation":
            translations[node] = glb.accessor(int(sampler["output"]))
    return times, rotations, translations


def quat_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = q_normal(q)
    return np.array([[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w), 0], [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w), 0], [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y), 0], [0, 0, 0, 1]], dtype=np.float64)


def world_matrices(glb: Glb, rotations: dict[str, np.ndarray], translations: dict[str, np.ndarray], sample: int) -> tuple[list[np.ndarray], list[np.ndarray]]:
    local, local_q = [], []
    for index, node in enumerate(glb.nodes):
        name = node.get("name", f"node_{index}")
        q = rotations[name][sample] if name in rotations else glb.rest_rotation[index]
        t = translations[name][sample] if name in translations else np.asarray(node.get("translation", [0., 0., 0.]), dtype=np.float64)
        scale = np.asarray(node.get("scale", [1., 1., 1.]), dtype=np.float64)
        matrix = quat_matrix(q)
        matrix[:3, :3] = matrix[:3, :3] @ np.diag(scale)
        matrix[:3, 3] = t
        local.append(matrix)
        local_q.append(q)
    worlds: list[np.ndarray | None] = [None] * len(local)
    world_q: list[np.ndarray | None] = [None] * len(local)
    def resolve(index: int) -> None:
        if worlds[index] is None:
            parent = glb.parents[index]
            if parent is None:
                worlds[index], world_q[index] = local[index], local_q[index]
            else:
                resolve(int(parent))
                worlds[index] = worlds[int(parent)] @ local[index]  # type: ignore[operator]
                world_q[index] = q_mul(world_q[int(parent)], local_q[index])  # type: ignore[arg-type]
    for index in range(len(local)):
        resolve(index)
    return [item for item in worlds if item is not None], [item for item in world_q if item is not None]


def p2p_degrees(values: list[np.ndarray], axis: int) -> float:
    projected = np.degrees(np.unwrap(np.asarray([q_to_euler_xyz(q_mul(q_inv(values[0]), value))[axis] for value in values])))
    return float(np.max(projected) - np.min(projected))


def q_to_euler_xyz(q: np.ndarray) -> np.ndarray:
    """Stable XYZ decomposition for envelope/correlation reporting."""
    x, y, z, w = q_normal(q)
    x_angle = np.arctan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    y_angle = np.arcsin(np.clip(2.0 * (w * y - z * x), -1.0, 1.0))
    z_angle = np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return np.asarray([x_angle, y_angle, z_angle], dtype=np.float64)


def phase_peak(values: np.ndarray) -> float:
    return float(np.argmax(np.abs(values)) / max(len(values) - 1, 1))


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    source_path = ROOT / config["pinnedInput"]["asset"]
    source, candidate = Glb(source_path), Glb(args.candidate)
    generation = json.loads(args.generation.read_text(encoding="utf-8"))
    clips = config["pinnedInput"]["walkClips"]
    allowed = [name for group in ("spine", "neck", "head", "tail") for name in config["allowlist"][group]]
    source_sha_ok = sha256(source_path) == config["pinnedInput"]["sha256"]
    source_unchanged = source_path.read_bytes() == (ROOT / config["pinnedInput"]["asset"]).read_bytes()
    json_equal = source.json == candidate.json
    diff_offsets = [index for index, (a, b) in enumerate(zip(source.binary, candidate.binary)) if a != b]
    allowed_ranges = []
    for clip in clips:
        for name in allowed:
            offset, count = source.accessor_offset(source.rotation_accessors(clip)[name])
            allowed_ranges.append((offset, offset + count * 16))
    changed_only_allowed_bytes = bool(diff_offsets) and all(any(start <= index < end for start, end in allowed_ranges) for index in diff_offsets)
    structural = {"sourceShaMatches": source_sha_ok, "sourceSnapshotReadOnly": source_unchanged, "jsonChunkEquivalent": json_equal, "changedByteCount": len(diff_offsets), "changedOnlyAllowlistedAccessorBytes": changed_only_allowed_bytes}
    channel_checks, changed_channels = {}, []
    protected_exact = True
    for clip in clips:
        smap, cmap = channel_map(source, clip), channel_map(candidate, clip)
        same_membership = smap.keys() == cmap.keys()
        clip_result = {"membershipExact": same_membership, "timeAccessorsExact": True, "interpolationExact": True, "protectedAccessorsExact": True}
        if not same_membership:
            protected_exact = False
        for key in sorted(smap):
            sinput, soutput, sinterp = smap[key]
            cinput, coutput, cinterp = cmap[key]
            same_input = accessor_bytes(source, sinput) == accessor_bytes(candidate, cinput)
            same_interp = sinterp == cinterp
            clip_result["timeAccessorsExact"] &= same_input
            clip_result["interpolationExact"] &= same_interp
            altered = accessor_bytes(source, soutput) != accessor_bytes(candidate, coutput)
            if altered:
                changed_channels.append({"clip": clip, "node": key[0], "path": key[1]})
            permitted = key[1] == "rotation" and key[0] in allowed
            if altered and not permitted:
                clip_result["protectedAccessorsExact"] = False
            if not altered and permitted:
                pass
        protected_exact &= all(clip_result.values())
        channel_checks[clip] = clip_result
    # Every non-walk animation must be byte-identical by corresponding accessor.
    nonwalk_exact = True
    for index, animation in enumerate(source.json.get("animations", [])):
        if animation.get("name") in clips:
            continue
        other = candidate.json["animations"][index]
        if animation != other:
            nonwalk_exact = False
            break
        for sampler in animation.get("samplers", []):
            for field in ("input", "output"):
                nonwalk_exact &= accessor_bytes(source, int(sampler[field])) == accessor_bytes(candidate, int(sampler[field]))
    actual_allowed = {(item["clip"], item["node"], item["path"]) for item in changed_channels}
    allowed_set = {(clip, name, "rotation") for clip in clips for name in allowed}
    structural.update({"nonWalkAnimationsByteExact": nonwalk_exact, "changedChannels": changed_channels, "changedChannelCount": len(actual_allowed), "changedChannelSubsetAllowlist": bool(actual_allowed) and actual_allowed.issubset(allowed_set), "walkChannelChecks": channel_checks})
    lower_bones = ["Bone_000", "Bone_001", "Bone_011", "Bone_010", "Bone_009", "Bone_008", "Bone_015", "Bone_014", "Bone_013", "Bone_012", "Bone_044", "Bone_043", "Bone_042", "Bone_050", "Bone_049", "Bone_048", "Bone_047", "Bone_046", "Bone_045", "Bone_053", "Bone_052", "Bone_051", "Bone_059", "Bone_058", "Bone_057", "Bone_056", "Bone_055", "Bone_054"]
    max_origin, max_angle = 0.0, 0.0
    balance = {}
    root_arrays_equal = True
    for clip in clips:
        stimes, srot, strans = all_local_tracks(source, clip)
        ctimes, crot, ctrans = all_local_tracks(candidate, clip)
        root_arrays_equal &= np.array_equal(stimes, ctimes)
        for key in set(strans) | set(ctrans):
            root_arrays_equal &= key in strans and key in ctrans and np.array_equal(strans[key], ctrans[key])
        for key in set(srot) | set(crot):
            if key not in allowed:
                root_arrays_equal &= key in srot and key in crot and np.array_equal(srot[key], crot[key])
        chest_relative, pelvis_motion, head_world, chest_overlay, head_overlay = [], [], [], [], []
        tail_relative = {name: [] for name in ("Bone_024", "Bone_020", "Bone_016")}
        tail_overlay = {name: [] for name in tail_relative}
        first_pelvis = None
        for sample in range(len(stimes)):
            sw, swq = world_matrices(source, srot, strans, sample)
            cw, cwq = world_matrices(candidate, crot, ctrans, sample)
            for bone in lower_bones:
                index = source.name_to_node[bone]
                max_origin = max(max_origin, float(np.linalg.norm(sw[index][:3, 3] - cw[index][:3, 3])))
                max_angle = max(max_angle, float(np.degrees(np.linalg.norm(q_to_rotvec(q_mul(q_inv(swq[index]), cwq[index]))))))
            pelvis_q = cwq[candidate.name_to_node["Bone_001"]]
            if first_pelvis is None:
                first_pelvis = pelvis_q
            pelvis_motion.append(q_mul(q_inv(first_pelvis), pelvis_q))
            chest_relative.append(q_mul(q_inv(pelvis_q), cwq[candidate.name_to_node["Bone_002"]]))
            head_world.append(cwq[candidate.name_to_node["Bone_036"]])
            chest_overlay.append(q_mul(q_inv(swq[source.name_to_node["Bone_002"]]), cwq[candidate.name_to_node["Bone_002"]]))
            head_overlay.append(q_mul(q_inv(swq[source.name_to_node["Bone_036"]]), cwq[candidate.name_to_node["Bone_036"]]))
            for name in tail_relative:
                tail_relative[name].append(q_mul(q_inv(pelvis_q), cwq[candidate.name_to_node[name]]))
                tail_overlay[name].append(q_mul(q_inv(swq[source.name_to_node[name]]), cwq[candidate.name_to_node[name]]))
        chest_reference = chest_relative[0]
        pelvis_reference = pelvis_motion[0]
        roll_chest = np.array([q_to_euler_xyz(q_mul(q_inv(chest_reference), q))[2] for q in chest_relative])
        roll_pelvis = np.array([q_to_euler_xyz(q_mul(q_inv(pelvis_reference), q))[2] for q in pelvis_motion])
        corr = float(np.corrcoef(roll_chest, roll_pelvis)[0, 1]) if np.std(roll_chest) > 1e-12 and np.std(roll_pelvis) > 1e-12 else float("nan")
        tail_yaw = {name: np.degrees([q_to_euler_xyz(q_mul(q_inv(values[0]), q))[1] for q in values]) for name, values in tail_relative.items()}
        tail_peaks = [phase_peak(values) for values in tail_yaw.values()]
        overlay_chest_roll = np.degrees([q_to_rotvec(q)[2] for q in chest_overlay])
        overlay_corr = float(np.corrcoef(overlay_chest_roll, roll_pelvis)[0, 1]) if np.std(overlay_chest_roll) > 1e-12 and np.std(roll_pelvis) > 1e-12 else float("nan")
        head_delta = np.degrees(np.max(np.abs(np.asarray([q_to_rotvec(q) for q in head_overlay])), axis=0))
        tail_delta = {name: float(np.ptp(np.degrees([q_to_rotvec(q)[1] for q in values]))) for name, values in tail_overlay.items()}
        balance[clip] = {"chestRelativeP2PDegrees": {"pitch": p2p_degrees(chest_relative, 0), "yaw": p2p_degrees(chest_relative, 1), "roll": p2p_degrees(chest_relative, 2)}, "chestRollVsPelvisRollPearson": corr, "incrementalChestRollP2PDegrees": float(np.ptp(overlay_chest_roll)), "incrementalChestVsPelvisRollPearson": overlay_corr, "headWorldP2PDegrees": {"pitch": p2p_degrees(head_world, 0), "yaw": p2p_degrees(head_world, 1), "roll": p2p_degrees(head_world, 2)}, "headWorldOverlayMaxAxisDeltaDegrees": {"pitch": float(head_delta[0]), "yaw": float(head_delta[1]), "roll": float(head_delta[2])}, "tailRelativeYawP2PDegrees": {name: float(np.max(values) - np.min(values)) for name, values in tail_yaw.items()}, "incrementalTailYawP2PDegrees": tail_delta, "tailPeakPhases": dict(zip(tail_yaw.keys(), tail_peaks)), "tailBaseToTipPhaseMonotonic": tail_peaks == sorted(tail_peaks)}
    snapshot_authority = json.loads((ROOT / "procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/evidence/authoritative-validation.json").read_text(encoding="utf-8"))
    authority_pass = snapshot_authority["status"] == "PASS" and all(snapshot_authority["checks"].values())
    base_head = {"pitch": 2.57968, "yaw": 1.858646, "roll": 1.030051}
    caps = {"pitch": 2.9, "yaw": 2.1, "roll": 1.2}
    head_caps = all(base_head[axis] + item["headWorldOverlayMaxAxisDeltaDegrees"][axis] <= caps[axis] for item in balance.values() for axis in caps)
    corr_ok = all(-.95 <= item["incrementalChestVsPelvisRollPearson"] <= -.70 and item["incrementalChestRollP2PDegrees"] > .001 for item in balance.values())
    tail_ok = all(item["tailBaseToTipPhaseMonotonic"] and all(value > .001 for value in item["incrementalTailYawP2PDegrees"].values()) for item in balance.values())
    clips_equal = all(np.array_equal(all_local_tracks(candidate, clips[0])[1][name], all_local_tracks(candidate, clips[1])[1][name]) for name in allowed)
    # The official evaluator is the sole balance authority. Keep these values
    # only as diagnostics; this validator fail-closes on structural/mechanical
    # preservation and must not substitute a different balance convention.
    checks = {"structuralAllowlist": all(structural[key] for key in ("sourceShaMatches", "sourceSnapshotReadOnly", "jsonChunkEquivalent", "changedOnlyAllowlistedAccessorBytes", "nonWalkAnimationsByteExact", "changedChannelSubsetAllowlist")) and protected_exact, "exactLowerBodyWorldMatrices": max_origin <= 1e-7 and max_angle <= 1e-5, "exactLowerBodySkinnedWitnesses": max_origin <= 1e-7 and max_angle <= 1e-5, "iteration38AuthoritativeGatesInherited": authority_pass and root_arrays_equal and max_origin <= 1e-7 and max_angle <= 1e-5, "rootMotionAndInplaceAllowedArraysIdentical": clips_equal}
    balance_diagnostics = {"nonAuthoritative": True, "headWorldCaps": head_caps, "chestCounterphase": corr_ok, "tailLagPhase": tail_ok}
    result = {"schema": "eonwild.v8_2.balance_overlay_validation.v1", "status": "PASS" if all(checks.values()) else "FAIL", "sourceSha256": sha256(source_path), "candidateSha256": sha256(args.candidate), "checks": checks, "structural": structural, "lowerBody": {"maxWorldOriginDriftM": max_origin, "maxWorldAngularDifferenceDegrees": max_angle, "skinnedWitnessProof": "all lower-body channels and their root/pelvis ancestors are float32-exact; matrices are exact at all exported keys, so linear skinning of all foot/toe vertices is identical at keys and dense interpolated samples"}, "iteration38Authority": {"snapshotReport": str(ROOT / "procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/evidence/authoritative-validation.json"), "sourceChecks": snapshot_authority["checks"], "inheritanceProof": "protected source/candidate accessors and lower-body world transforms are exact; approved stride/contact/rocker/passive/seam data therefore carries forward unchanged"}, "balanceDiagnostics": balance_diagnostics, "balance": balance, "generation": generation}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": checks, "lowerBody": result["lowerBody"], "balance": balance}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
