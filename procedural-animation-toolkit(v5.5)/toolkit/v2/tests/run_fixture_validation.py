#!/usr/bin/env python3
"""Run the full v2 generator against a real GLB + semantic map and assert gates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eonproc_v2.gltf_io import GlbAsset
from eonproc_v2.generator import ContactAwareBipedGenerator
from eonproc_v2.profile import BipedV2Profile
from eonproc_v2.rig import SemanticMap


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV2Profile.from_json(args.profile) if args.profile else BipedV2Profile()
    generator = ContactAwareBipedGenerator(asset, semantics, profile)
    motion = generator.generate(keep_world_matrices=False)
    diagnostics = motion.diagnostics

    failures: list[str] = []
    if diagnostics["internal_sample_count"] < 2 * diagnostics["export_sample_count"] - 1:
        failures.append("internal solve does not preserve the configured dense sampling ratio")
    if diagnostics["rotation_endpoint_max_abs_diff"] != 0.0:
        failures.append("rotation loop is not exactly closed")
    if diagnostics["tail_endpoint_yaw_max_abs_diff"] > 1e-10:
        failures.append("tail yaw loop is not exactly closed")
    if diagnostics["tail_endpoint_pitch_max_abs_diff"] > 1e-10:
        failures.append("tail pitch loop is not exactly closed")
    for side in ("l", "r"):
        if diagnostics["normalized_contact_error"][side] > 0.01:
            failures.append(f"{side} loaded horizontal contact error exceeds 1% hip height")
    expected_distance = generator.stride * profile.supercycle_count
    if abs(diagnostics["root_motion_distance_m"] - expected_distance) > 1e-6:
        failures.append("root-motion distance does not equal stride × supercycle count")
    if len(generator.driven_bones) < 40:
        failures.append("unexpectedly small driven-bone set")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "input": str(Path(args.input).resolve()),
        "boneMap": str(Path(args.bone_map).resolve()),
        "profile": profile.name,
        "failures": failures,
        "diagnostics": diagnostics,
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
