#!/usr/bin/env python3
"""Strict structural validator for the baked V4 animation-pack GLB."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v3.gltf_io import GlbAsset, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = GlbAsset(args.source)
    generated = GlbAsset(args.generated)
    source_joints, source_ibm = source.skin_data()
    generated_joints, generated_ibm = generated.skin_data()
    errors: list[str] = []
    if source_joints != generated_joints:
        errors.append("skin joint order changed")
    if not np.allclose(source_ibm, generated_ibm, atol=0.0, rtol=0.0):
        errors.append("inverse bind matrices changed")
    animations = generated.json.get("animations", [])
    names = [animation.get("name", "") for animation in animations]
    if len(names) != len(set(names)):
        errors.append("duplicate animation names")
    clip_results = []
    for animation in animations:
        clip_errors: list[str] = []
        samplers = animation.get("samplers", [])
        channels = animation.get("channels", [])
        for sampler in samplers:
            times = generated.accessor(int(sampler["input"])).reshape(-1)
            outputs = generated.accessor(int(sampler["output"]))
            if len(times) < 2 or not np.all(np.diff(times) > 0.0):
                clip_errors.append("non-increasing or short input times")
            if len(outputs) != len(times):
                clip_errors.append("input/output sample count mismatch")
            if not np.all(np.isfinite(outputs)):
                clip_errors.append("non-finite animation output")
        for channel in channels:
            target = channel.get("target", {})
            node = target.get("node")
            if not isinstance(node, int) or node < 0 or node >= len(generated.nodes):
                clip_errors.append("invalid channel target node")
            if target.get("path") not in {"rotation", "translation", "scale", "weights"}:
                clip_errors.append("invalid channel target path")
        if clip_errors:
            errors.extend(f"{animation.get('name')}: {value}" for value in sorted(set(clip_errors)))
        clip_results.append({
            "name": animation.get("name"),
            "channelCount": len(channels),
            "samplerCount": len(samplers),
            "errors": sorted(set(clip_errors)),
            "extras": animation.get("extras", {}),
        })
    required = {
        "PROC_WALK_RELAXED_V4_INPLACE", "PROC_WALK_UNEVEN_TERRAIN_V4_ROOTMOTION",
        "PROC_TURN_LEFT_35_V4_ROOTMOTION", "PROC_START_WALK_V4_ROOTMOTION",
        "PROC_BRAKE_TO_IDLE_V4_ROOTMOTION", "PROC_ALERT_WALK_V4_INPLACE",
        "PROC_EAT_LOOP_V4", "PROC_BITE_ATTACK_V4", "PROC_ROAR_V4",
        "PROC_IDLE_TO_WALK_V4", "PROC_WALK_TO_BITE_READY_V4",
    }
    missing_required = sorted(required - set(names))
    if missing_required:
        errors.append(f"missing required clips: {missing_required}")
    report = {
        "status": "PASS" if not errors else "FAIL",
        "sourceSha256": sha256_file(args.source),
        "generatedSha256": sha256_file(args.generated),
        "sourceNodeCount": len(source.nodes),
        "generatedNodeCount": len(generated.nodes),
        "skinJointCount": len(generated_joints),
        "skinJointOrderPreserved": source_joints == generated_joints,
        "inverseBindMatricesPreservedExactly": bool(np.array_equal(source_ibm, generated_ibm)),
        "animationCount": len(animations),
        "animationNames": names,
        "missingRequiredClips": missing_required,
        "clips": clip_results,
        "errors": errors,
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
