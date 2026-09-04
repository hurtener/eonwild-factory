#!/usr/bin/env python3
"""Generate only the isolated V8.1 relaxed-walk respin candidate.

The accepted V8.1 package is deliberately imported read-only.  This runner
merges a candidate-owned overlay onto its canonical profile, applies the same
accepted 90% lower-foot-pivot calibration in memory, and writes only the two
walk tracks needed for review.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation


ROOT = Path(__file__).resolve().parents[3]
TOOLKIT = ROOT / "procedural-animation-toolkit(v8.1)" / "toolkit" / "v8" / "scripts"
sys.path.insert(0, str(TOOLKIT))

from eonproc_v3.gltf_io import GlbAsset, matrix_from_trs, sha256_file  # noqa: E402
from eonproc_v3.rig import AnatomicalBasis, SemanticMap  # noqa: E402
from eonproc_v4.locomotion import constant_schedule  # noqa: E402
from eonproc_v4.terrain import FlatTerrain  # noqa: E402
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator  # noqa: E402
from eonproc_v8.pivots import lower_foot_pivots  # noqa: E402
from eonproc_v8.profile import BipedV8Profile  # noqa: E402


def sha256_tree(path: Path) -> str:
    """Digest content + relative paths without relying on Git tracking."""
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if not item.is_file() or item.name == ".DS_Store":
            continue
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(item).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--bone-map", required=True, type=Path)
    parser.add_argument("--canonical-profile", required=True, type=Path)
    parser.add_argument("--overlay", required=True, type=Path)
    parser.add_argument("--immutable-toolkit", required=True, type=Path)
    parser.add_argument("--immutable-showcase", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def add_reference_scale_wrapper(asset: GlbAsset, reference_length_m: float, accepted_raw_length_m: float) -> dict[str, float | int | str]:
    """Attach one scene-root scale node after the raw-unit solve is complete."""
    primitive = asset.primitive()
    if primitive.joints is None or primitive.weights is None:
        raise ValueError("Reference scale wrapper requires a skinned mesh")
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    points = asset.skin_points(primitive.positions, primitive.joints, primitive.weights, asset.rest_world, skin)
    spans = np.ptp(points, axis=0)
    length_axis = int(np.argmax(spans))
    measured_raw_length = float(spans[length_axis])
    if measured_raw_length <= 0.0 or accepted_raw_length_m <= 0.0:
        raise ValueError("Cannot derive reference scale from a degenerate mesh")
    # Use the accepted full-body bound (Blender/evaluated mesh) as the scale
    # authority, while retaining the direct GLB measurement for audit.
    factor = float(reference_length_m / accepted_raw_length_m)
    scenes = asset.json.get("scenes", [])
    scene_index = int(asset.json.get("scene", 0))
    if not scenes or scene_index >= len(scenes):
        raise ValueError("Candidate source must declare a default glTF scene")
    children = list(scenes[scene_index].get("nodes", []))
    if not children:
        raise ValueError("Candidate source scene has no root nodes")
    wrapper_index = len(asset.nodes)
    wrapper = {
        "name": "RESPIN_REFERENCE_SCALE_ROOT",
        "scale": [factor, factor, factor],
        "children": children,
        "extras": {
            "candidateOnly": True,
            "purpose": "12m_reference_scale_wrapper",
            "acceptedRawBodyLengthM": accepted_raw_length_m,
            "directGlbMeshLengthM": measured_raw_length,
            "referenceLengthM": reference_length_m,
            "uniformScaleFactor": factor,
        },
    }
    # ``asset.nodes`` aliases ``asset.json["nodes"]``; append exactly once.
    asset.json["nodes"].append(wrapper)
    scenes[scene_index]["nodes"] = [wrapper_index]
    return {
        "wrapperNode": wrapper["name"],
        "wrapperNodeIndex": wrapper_index,
        "acceptedRawBodyLengthM": accepted_raw_length_m,
        "directGlbMeshLengthM": measured_raw_length,
        "referenceLengthM": reference_length_m,
        "uniformScaleFactor": factor,
    }


def apply_distal_toe_ground_lock(
    clips: tuple,
    generator: TarbosaurusV8LocomotionGenerator,
    asset: GlbAsset,
    profile: BipedV8Profile,
    config: dict,
) -> dict[str, object]:
    """Solve a bounded distal-toe contact target after the accepted rocker."""
    if not config.get("enabled", False):
        return {"enabled": False}
    degrees = float(config["counterArticulationDegrees"])
    if abs(degrees - profile.toe_push_deg) > 1e-9:
        raise ValueError("Candidate toe ground-lock magnitude must equal locked toe_push_deg")
    primitive = asset.primitive()
    skin = asset.skin_index_for_mesh_node(primitive.mesh_index)
    ground = float(np.min(asset.skin_points(primitive.positions, primitive.joints, primitive.weights, asset.rest_world, skin)[:, 1]))
    skin_nodes, _ = asset.skin_data(skin)
    node_to_joint = {node: joint for joint, node in enumerate(skin_nodes)}

    def patch_indices(side: str) -> np.ndarray:
        selected = generator.sole.selections[side].vertex_indices
        joints: set[int] = set()
        for chain in generator.toe_chains[side]:
            for bone in chain:
                node = asset.name_to_node[bone]
                if node in node_to_joint:
                    joints.add(node_to_joint[node])
        weights = np.sum(primitive.weights[selected] * np.isin(primitive.joints[selected], list(joints)), axis=1)
        chosen = selected[weights >= 0.35]
        return np.asarray(chosen if len(chosen) >= 8 else selected[np.argsort(weights)[-24:]], dtype=np.int64)

    def toe_minimum(clip, sample: int, ids: np.ndarray) -> float:
        local = []
        for node, rest_rotation, rest_translation, rest_scale in zip(asset.nodes, asset.rest_rotation, asset.rest_translation, asset.rest_scale):
            name = node.get("name", "")
            rotation = Rotation.from_quat(clip.rotations[name][sample]) if name in clip.rotations else rest_rotation
            translation = clip.translations[name][sample] if name in clip.translations else rest_translation
            local.append(matrix_from_trs(np.asarray(translation), rotation, rest_scale))
        worlds = asset.world_matrices(local)
        points = asset.skin_points(primitive.positions[ids], primitive.joints[ids], primitive.weights[ids], worlds, skin)
        return float(np.min(points[:, 1]))

    changed: dict[str, int] = {}
    peak_angles: dict[str, float] = {}
    for clip in clips:
        changed_keys = 0
        peak_angle = 0.0
        for index, time_s in enumerate(clip.times):
            global_phase = (float(time_s) / clip.duration) * 2.0
            for side, phase_offset in (("l", 0.0), ("r", 0.5)):
                phase = (global_phase - phase_offset) % 1.0
                # The correction begins only once the rear rocker is visible,
                # then eases to zero in the final release interval.
                hold_start = profile.stance_fraction - 0.12
                release_start = profile.stance_fraction - 0.055
                if not (hold_start <= phase < profile.stance_fraction):
                    continue
                ids = patch_indices(side)
                roots = [chain[0] for chain in generator.toe_chains[side] if chain]
                base = {bone: clip.rotations[bone][index].copy() for bone in roots}
                baseline = toe_minimum(clip, index, ids)
                release = 0.0 if phase <= release_start else (phase - release_start) / (profile.stance_fraction - release_start)
                target_height = (ground + 0.0012) * (1.0 - release) + baseline * release

                def set_angle(angle: float) -> float:
                    for bone in roots:
                        node = asset.name_to_node[bone]
                        local_axis = asset.rest_world_rotation[node].inv().apply(generator.base_basis.lateral)
                        clip.rotations[bone][index] = (Rotation.from_quat(base[bone]) * Rotation.from_rotvec(local_axis * np.deg2rad(angle))).as_quat()
                    return toe_minimum(clip, index, ids)

                # Bisection uses actual skinned vertices; it is fail-closed if
                # the bounded 8-degree root articulation cannot meet contact.
                low, high = 0.0, 8.0
                if set_angle(high) > target_height:
                    set_angle(0.0)
                    continue
                for _ in range(12):
                    middle = (low + high) * 0.5
                    if set_angle(middle) > target_height:
                        low = middle
                    else:
                        high = middle
                final_height = set_angle(high)
                if final_height < ground - 1e-6:
                    raise RuntimeError(f"Toe contact solve penetrated ground at {clip.name}:{side}:{index}")
                peak_angle = max(peak_angle, high)
                changed_keys += 1
        clip.normalize()
        changed[clip.name] = changed_keys
        peak_angles[clip.name] = peak_angle
    return {
        "enabled": True,
        "lockedToePushDegrees": profile.toe_push_deg,
        "counterArticulationDegrees": degrees,
        "affectedKeys": changed,
        "maximumSolvedToeRootDegrees": peak_angles,
        "groundTargetM": ground + 0.0012,
        "policy": "candidate-only distal toe ground-lock; metatarsal/foot node untouched",
    }


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise RuntimeError(f"Refusing non-empty output directory: {args.output_dir}")
    overlay = json.loads(args.overlay.read_text(encoding="utf-8"))
    overrides = overlay.get("profileOverrides")
    if not isinstance(overrides, dict) or not overrides:
        raise ValueError("Overlay must contain non-empty profileOverrides")
    if overlay.get("status") != "LOCKED_AFTER_REFERENCE_REVIEW":
        raise ValueError("Overlay is not locked after reference review")

    immutable_before = {
        "toolkitTreeSha256": sha256_tree(args.immutable_toolkit),
        "showcaseTreeSha256": sha256_tree(args.immutable_showcase),
        "sourceGlbSha256": sha256_file(args.source),
        "canonicalProfileSha256": sha256_file(args.canonical_profile),
    }
    profile = replace(BipedV8Profile.from_json(args.canonical_profile), **overrides)
    asset = GlbAsset(args.source)
    semantics = SemanticMap.load(args.bone_map)
    basis = AnatomicalBasis.gltf_y_up(asset, semantics)
    pivot = lower_foot_pivots(asset, semantics, basis, profile.foot_pivot_gap_fraction)
    generator = TarbosaurusV8LocomotionGenerator(asset, semantics, profile)
    schedule = constant_schedule(
        "PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION",
        generator,
        cycles=2.0,
        terrain=FlatTerrain(generator.mesh_ground),
        cycle_hz=profile.cycle_hz,
        stride_scale=1.0,
        loop=True,
        tags=("walk", "relaxed", "respin", "contact_locked", "toe_progressive_lift"),
    )
    result = generator.generate_schedule(schedule, keep_world_matrices=False)
    if result.in_place_clip is None:
        raise RuntimeError("Relaxed walk did not generate an in-place companion clip")
    clips = (result.clip, result.in_place_clip)
    reference_scale = add_reference_scale_wrapper(
        asset,
        reference_length_m=float(overlay["referenceScale"]["bodyLengthM"]),
        accepted_raw_length_m=float(overlay["referenceScale"]["acceptedRawBodyLengthM"]),
    )
    toe_ground_lock = apply_distal_toe_ground_lock(
        clips, generator, asset, profile, dict(overlay.get("toeGroundLock", {})),
    )

    output = args.output_dir
    output.mkdir(parents=True)
    glb = output / "tarbosaurus_procedural_v8_1_walk_respin.glb"
    asset.write_animations(glb, [clip.gltf_spec() for clip in clips], replace_existing=True)
    resolved_profile = output / "resolved-profile-v8.1-walk-respin.json"
    resolved_profile.write_text(json.dumps(asdict(profile), indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema": "eonwild.animation-manifest.v8.1-walk-respin",
        "candidateOnly": True,
        "clips": [{
            "name": clip.name,
            "durationSeconds": clip.duration,
            "loop": bool(clip.extras.get("loop", False)),
            "rootMotion": bool(clip.extras.get("rootMotion", False)),
            "tags": clip.extras.get("tags", []),
        } for clip in clips],
    }
    (output / "animation-manifest.v8.1-walk-respin.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    generated = {
        "status": "CANDIDATE_READY_FOR_VALIDATION",
        "candidateOnly": True,
        "input": {
            "sourceGlb": str(args.source.resolve()),
            "sourceGlbSha256": immutable_before["sourceGlbSha256"],
            "canonicalProfileSha256": immutable_before["canonicalProfileSha256"],
            "overlaySha256": sha256_file(args.overlay),
        },
        "immutableBefore": immutable_before,
        "profile": asdict(profile),
        "footPivotCalibration": pivot,
        "toeGroundLock": toe_ground_lock,
        "referenceScaleWrapper": reference_scale,
        "clips": {clip.name: clip.diagnostics for clip in clips},
        "output": {"glb": str(glb.resolve()), "glbSha256": sha256_file(glb)},
        "immutableAfter": {
            "toolkitTreeSha256": sha256_tree(args.immutable_toolkit),
            "showcaseTreeSha256": sha256_tree(args.immutable_showcase),
            "sourceGlbSha256": sha256_file(args.source),
            "canonicalProfileSha256": sha256_file(args.canonical_profile),
        },
    }
    generated["immutableUnchanged"] = generated["immutableBefore"] == generated["immutableAfter"]
    if not generated["immutableUnchanged"]:
        raise RuntimeError("Immutable V8.1 boundary changed during candidate generation")
    (output / "generation-report.json").write_text(json.dumps(generated, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(generated, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
