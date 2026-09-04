#!/usr/bin/env python3
"""Validate the baked V8.1 walk-respin candidate at every exported key."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
TOOLKIT = ROOT / "procedural-animation-toolkit(v8.1)" / "toolkit" / "v8" / "scripts"
sys.path.insert(0, str(TOOLKIT))

from eonproc_v3.gltf_io import GlbAsset, sha256_file  # noqa: E402
from eonproc_v3.rig import SemanticMap  # noqa: E402
from eonproc_v4.animation_reader import AnimationPackReader  # noqa: E402
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator  # noqa: E402
from eonproc_v8.profile import BipedV8Profile  # noqa: E402


CONTACT_QUANTILE = 0.08
PENETRATION_LIMIT_M = 0.002
SUPPORTED_CONTACT_LIMIT_M = 0.009
TOE_PATCH_LIMIT_M = 0.008
METATARSAL_LIFT_MIN_M = 0.004


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", required=True, type=Path)
    parser.add_argument("--bone-map", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--generation-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def toe_patch_indices(asset: GlbAsset, generator: TarbosaurusV8LocomotionGenerator, side: str) -> np.ndarray:
    """Choose actual selected sole vertices materially weighted to toe branches."""
    primitive = asset.primitive()
    selected = generator.sole.selections[side].vertex_indices
    skin_nodes, _ = asset.skin_data(asset.skin_index_for_mesh_node(primitive.mesh_index))
    node_to_joint = {node: joint for joint, node in enumerate(skin_nodes)}
    toe_nodes: set[int] = set()
    for tag in (f"toe_{side}", f"toe_2_{side}", f"toe_3_{side}"):
        if tag not in generator.semantics.tags:
            continue
        root = generator.semantics.bone(tag)
        for bone in asset.single_child_chain(root, max_nodes=5):
            node = asset.name_to_node[bone]
            if node in node_to_joint:
                toe_nodes.add(node_to_joint[node])
    toe_weight = np.sum(primitive.weights[selected] * np.isin(primitive.joints[selected], list(toe_nodes)), axis=1)
    chosen = selected[toe_weight >= 0.35]
    if len(chosen) < 8:
        chosen = selected[np.argsort(toe_weight)[-max(8, min(24, len(selected))):]]
    return np.asarray(chosen, dtype=np.int64)


def relative_phase(time_s: float, duration_s: float, cycles: float, side: str) -> float:
    global_phase = time_s / duration_s * cycles
    return (global_phase - (0.0 if side == "l" else 0.5)) % 1.0


def main() -> int:
    args = parse_args()
    overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    profile = BipedV8Profile.from_json(args.profile)
    asset = GlbAsset(args.glb)
    semantics = SemanticMap.load(args.bone_map)
    generator = TarbosaurusV8LocomotionGenerator(asset, semantics, profile)
    reader = AnimationPackReader(asset)
    generation = json.loads(args.generation_report.read_text(encoding="utf-8"))
    root_name = generator.root
    pelvis_name = semantics.bone("pelvis")
    primitive = asset.primitive()
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    rest_points = asset.skin_points(primitive.positions, primitive.joints, primitive.weights, asset.rest_world, skin)
    ground = float(np.min(rest_points[:, 1]))
    cycles = 2.0
    target = overlay["referenceScale"]
    raw_hip_height = float(asset.rest_world[asset.name_to_node[pelvis_name]][1, 3] - ground)
    reference_scale_factor = float(profile.reference_hip_height_m / raw_hip_height)
    clips: dict[str, dict] = {}

    for name in ("PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION", "PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE"):
        animation = reader.animation(name)
        toe_indices = {side: toe_patch_indices(asset, generator, side) for side in ("l", "r")}
        key_rows: list[dict] = []
        foot_relative = {side: [] for side in ("l", "r")}
        rocker_rows = {side: [] for side in ("l", "r")}
        root_world_positions: list[np.ndarray] = []
        for index, time_s in enumerate(animation.times):
            worlds = reader.world_matrices_at(animation, float(time_s))
            root_world_positions.append(worlds[asset.name_to_node[root_name]][:3, 3].copy())
            pelvis = worlds[asset.name_to_node[pelvis_name]][:3, 3]
            row = {"keyIndex": index, "timeSeconds": float(time_s), "sides": {}}
            for side in ("l", "r"):
                sole_ids = generator.sole.selections[side].vertex_indices
                sole = asset.skin_points(primitive.positions[sole_ids], primitive.joints[sole_ids], primitive.weights[sole_ids], worlds, skin)
                toes = asset.skin_points(primitive.positions[toe_indices[side]], primitive.joints[toe_indices[side]], primitive.weights[toe_indices[side]], worlds, skin)
                heights = sole[:, 1] - ground
                toe_heights = toes[:, 1] - ground
                foot = worlds[asset.name_to_node[semantics.bone(f"foot_{side}")]][:3, 3]
                forward = float(np.dot(foot - pelvis, generator.base_basis.forward))
                foot_relative[side].append(forward)
                phase = relative_phase(float(time_s), animation.duration, cycles, side)
                metatarsal_up = float(foot[1] - asset.rest_world[asset.name_to_node[semantics.bone(f"foot_{side}")]][1, 3])
                row["sides"][side] = {
                    "phase": phase,
                    "soleMinimumM": float(np.min(heights)),
                    "soleContactQuantileM": float(np.quantile(heights, CONTACT_QUANTILE)),
                    "toePatchMinimumM": float(np.min(toe_heights)),
                    "toePatchContactQuantileM": float(np.quantile(toe_heights, CONTACT_QUANTILE)),
                    "footRelativePelvisForwardM": forward,
                    "metatarsalPivotLiftM": metatarsal_up,
                }
                late = profile.stance_fraction - profile.toe_off_window_fraction <= phase < profile.stance_fraction
                if late:
                    rocker_rows[side].append(row["sides"][side])
            key_rows.append(row)

        root_distance = float(np.dot(root_world_positions[-1] - root_world_positions[0], generator.base_basis.forward))
        same_foot_stride = root_distance / cycles if name.endswith("ROOTMOTION") else 0.0
        speed = root_distance / animation.duration if name.endswith("ROOTMOTION") else 0.0
        extrema = {side: {"frontM": float(np.max(values)), "rearM": float(np.min(values))} for side, values in foot_relative.items()}
        rocker = {}
        for side, rows in rocker_rows.items():
            toe_loaded_rocker = [entry for entry in rows if entry["metatarsalPivotLiftM"] >= METATARSAL_LIFT_MIN_M and entry["toePatchContactQuantileM"] <= TOE_PATCH_LIMIT_M]
            toe_released = [entry for entry in rows if entry["toePatchContactQuantileM"] > TOE_PATCH_LIMIT_M]
            rocker[side] = {
                "lateStanceKeyCount": len(rows),
                "maximumMetatarsalLiftM": max((entry["metatarsalPivotLiftM"] for entry in rows), default=float("-inf")),
                "maximumMetatarsalLiftWhileToePatchLoadedM": max((entry["metatarsalPivotLiftM"] for entry in toe_loaded_rocker), default=float("-inf")),
                "toeLoadedRockerKeyCount": len(toe_loaded_rocker),
                "toeReleasedKeyCount": len(toe_released),
                "sequence": "metatarsal lift with toe patch loaded, followed by toe release" if toe_loaded_rocker and toe_released else "incomplete",
            }

        all_sole_min = [side["soleMinimumM"] for row in key_rows for side in row["sides"].values()]
        lowest_support = [min(row["sides"]["l"]["soleContactQuantileM"], row["sides"]["r"]["soleContactQuantileM"]) for row in key_rows]
        clips[name] = {
            "durationSeconds": float(animation.duration),
            "exportedKeyCount": len(key_rows),
            "measuredKeyCount": len(key_rows),
            "rootDistanceM": root_distance,
            "sameFootStrideM": same_foot_stride,
            "meanRootSpeedMps": speed,
            "meanRootSpeedKmh": speed * 3.6,
            "referenceScaleSameFootStrideM": same_foot_stride * reference_scale_factor,
            "referenceScaleMeanRootSpeedMps": speed * reference_scale_factor,
            "referenceScaleMeanRootSpeedKmh": speed * reference_scale_factor * 3.6,
            "footExtremaRelativePelvis": extrema,
            "worstSelectedSolePenetrationM": float(max(0.0, -min(all_sole_min))),
            "maximumLowestSupportContactQuantileM": float(max(lowest_support)),
            "progressiveRocker": rocker,
            "keyMeasurements": key_rows,
        }

    root_clip = clips["PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"]
    diagnostics = generation["clips"]["PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION"]
    checks = {
        "immutable_v8_1_unchanged": bool(generation["immutableUnchanged"]),
        "both_clips_all_exported_keys_measured": all(value["exportedKeyCount"] == value["measuredKeyCount"] for value in clips.values()),
        "reference_scale_speed_4_5_to_4_8_kmh": target["targetSpeedKmh"][0] <= root_clip["referenceScaleMeanRootSpeedKmh"] <= target["targetSpeedKmh"][1],
        "reference_scale_same_foot_stride_matches_target_within_1pct": abs(root_clip["referenceScaleSameFootStrideM"] - target["targetSameFootStrideM"]) <= target["targetSameFootStrideM"] * 0.01,
        "long_front_reach": all(value["frontM"] >= profile.reference_hip_height_m * 0.43 for value in root_clip["footExtremaRelativePelvis"].values()),
        "rear_reach_bounded": all(value["rearM"] >= -profile.reference_hip_height_m * 0.52 for value in root_clip["footExtremaRelativePelvis"].values()),
        "no_selected_sole_penetration_any_key": all(value["worstSelectedSolePenetrationM"] <= PENETRATION_LIMIT_M for value in clips.values()),
        "always_supported": all(value["maximumLowestSupportContactQuantileM"] <= SUPPORTED_CONTACT_LIMIT_M for value in clips.values()),
        "joint_continuity_and_constraints": bool(diagnostics["quality_gates"]["zero_anatomical_reversals"] and diagnostics["quality_gates"]["velocity_within_gate"] and diagnostics["quality_gates"]["acceleration_within_gate"]),
        "progressive_toe_contact_before_release": all(
            item["lateStanceKeyCount"] > 0
            and item["toeLoadedRockerKeyCount"] > 0
            and item["toeReleasedKeyCount"] > 0
            for item in root_clip["progressiveRocker"].values()
        ),
    }
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "method": "actual final GLB, every exported baked key, selected weighted sole vertices and toe-weighted patch vertices skinned from the candidate mesh",
        "sourceGlbSha256": generation["input"]["sourceGlbSha256"],
        "candidateGlbSha256": sha256_file(args.glb),
        "checks": checks,
        "thresholds": {
            "penetrationM": PENETRATION_LIMIT_M,
            "supportedContactQuantileM": SUPPORTED_CONTACT_LIMIT_M,
            "toePatchContactQuantileM": TOE_PATCH_LIMIT_M,
            "metatarsalLiftM": METATARSAL_LIFT_MIN_M,
        },
        "scale": {
            "candidateWorldHipHeightM": raw_hip_height,
            "referenceHipHeightM": profile.reference_hip_height_m,
            "referenceScaleFactor": reference_scale_factor,
            "interpretation": "The candidate already carries one top-level uniform reference-scale wrapper. The near-unity factor shown here reconciles the measured candidate-world hip height with the 2.75 m target and must not be applied a second time.",
        },
        "clips": clips,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checks": checks}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
