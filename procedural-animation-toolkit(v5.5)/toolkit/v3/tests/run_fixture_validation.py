#!/usr/bin/env python3
"""Run V3 against a real GLB + semantic map and assert anatomical/quality gates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.generator import AnatomicallyConstrainedBipedGenerator
from eonproc_v3.profile import BipedV3Profile
from eonproc_v3.rig import SemanticMap


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV3Profile.from_json(args.profile) if args.profile else BipedV3Profile()
    generator = AnatomicallyConstrainedBipedGenerator(asset, semantics, profile)
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
    if any(diagnostics["anatomical_flip_count"].values()):
        failures.append("knee or ankle crossed its anatomical hinge direction")
    for side in ("l", "r"):
        if diagnostics["normalized_contact_error"][side] > 0.01:
            failures.append(f"{side} loaded horizontal contact error exceeds 1% hip height")
        if diagnostics["solver_success_rate"][side] < 0.999:
            failures.append(f"{side} constrained leg solver did not converge on every sample")
        knee = diagnostics["joint_constraints"][side]["knee"]
        ankle = diagnostics["joint_constraints"][side]["ankle"]
        if knee["flex_min_deg"] < max(5.0, profile.knee_min_flex_deg - 5.0):
            failures.append(f"{side} knee approaches hyperextension")
        if ankle["flex_min_deg"] < max(5.0, profile.ankle_min_flex_deg - 5.0):
            failures.append(f"{side} ankle approaches reverse flexion")
    expected_distance = generator.stride * profile.supercycle_count
    if abs(diagnostics["root_motion_distance_m"] - expected_distance) > 1e-6:
        failures.append("root-motion distance does not equal stride × supercycle count")
    if diagnostics["max_joint_velocity_deg_s"] > profile.max_joint_velocity_deg_s:
        failures.append(
            f"joint velocity {diagnostics['max_joint_velocity_deg_s']:.2f} exceeds "
            f"profile ceiling {profile.max_joint_velocity_deg_s:.2f} deg/s"
        )
    if diagnostics["max_joint_acceleration_deg_s2"] > profile.max_joint_acceleration_deg_s2:
        failures.append(
            f"joint acceleration {diagnostics['max_joint_acceleration_deg_s2']:.2f} exceeds "
            f"profile ceiling {profile.max_joint_acceleration_deg_s2:.2f} deg/s^2"
        )
    if len(generator.driven_bones) < 50:
        failures.append("unexpectedly small driven-bone set")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "version": "3.0.0",
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
