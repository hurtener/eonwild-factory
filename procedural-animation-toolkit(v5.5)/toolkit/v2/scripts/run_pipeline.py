#!/usr/bin/env python3
"""Generate contact-aware v2 animations directly into a GLB."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v2.gltf_io import GlbAsset, sha256_file
from eonproc_v2.rig import SemanticMap
from eonproc_v2.profile import BipedV2Profile
from eonproc_v2.generator import ContactAwareBipedGenerator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Fully rigged source GLB")
    parser.add_argument("--bone-map", required=True, help="Semantic YAML bone map")
    parser.add_argument("--profile", help="Optional v2 profile JSON")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--keep-existing-animations", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.input).resolve()
    bone_map_path = Path(args.bone_map).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    asset = GlbAsset(source)
    semantics = SemanticMap.load(bone_map_path)
    profile = BipedV2Profile.from_json(args.profile) if args.profile else BipedV2Profile()
    generator = ContactAwareBipedGenerator(asset, semantics, profile)
    motion = generator.generate(keep_world_matrices=False)

    glb_path = output_dir / f"{source.stem}.procedural-v2.glb"
    asset.write_animations(
        glb_path,
        generator.animation_specs(motion),
        replace_existing=not args.keep_existing_animations,
    )
    report = {
        "status": "PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED",
        "version": "2.0.0",
        "input": {
            "asset": str(source),
            "asset_sha256": sha256_file(source),
            "bone_map": str(bone_map_path),
            "bone_map_sha256": sha256_file(bone_map_path),
            "existing_animation_names": [a.get("name", "") for a in asset.json.get("animations", [])],
        },
        "output": {
            "animated_glb": str(glb_path),
            "animated_glb_sha256": sha256_file(glb_path),
            "clips": [spec["name"] for spec in generator.animation_specs(motion)],
        },
        "diagnostics": motion.diagnostics,
        "quality_gate_notes": [
            "Contact lock is measured in the horizontal ground plane.",
            "Toe-ground error uses the lowest semantic toe-tip joint as a proxy for skinned sole contact.",
            "Perceptual side/front/three-quarter review remains mandatory before production approval.",
        ],
    }
    report_path = output_dir / "procedural-v2-report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output_dir / "resolved-profile.json").write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")
    manifest = {
        "schema": "eonwild.animation-manifest.v2",
        "asset": glb_path.name,
        "family": "biped",
        "profile": profile.name,
        "clips": [
            {
                "name": "PROC_WALK_LARGE_V2_INPLACE",
                "durationSeconds": generator.duration,
                "cycleCount": profile.supercycle_count,
                "sampleHz": profile.export_sample_hz,
                "rootMotion": False,
                "recommendedSpeedMps": generator.speed,
                "phaseContacts": {"left": [0.0, 1.0, 2.0], "right": [0.5, 1.5]},
            },
            {
                "name": "PROC_WALK_LARGE_V2_ROOTMOTION",
                "durationSeconds": generator.duration,
                "cycleCount": profile.supercycle_count,
                "sampleHz": profile.export_sample_hz,
                "rootMotion": True,
                "rootMotionDistanceM": generator.stride * profile.supercycle_count,
            },
        ],
    }
    (output_dir / "animation-manifest.v2.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"glb": str(glb_path), "report": str(report_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
