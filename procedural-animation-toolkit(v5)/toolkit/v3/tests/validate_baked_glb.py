#!/usr/bin/env python3
"""Compare a baked procedural GLB with its source and validate animation structure."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from eonproc_v3.gltf_io import GlbAsset, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--expect", action="append", default=[])
    args = parser.parse_args()

    source = GlbAsset(args.source)
    generated = GlbAsset(args.generated)
    source_joints, source_ibm = source.skin_data(0)
    generated_joints, generated_ibm = generated.skin_data(0)
    names = [animation.get("name", "") for animation in generated.json.get("animations", [])]
    failures: list[str] = []
    if source_joints != generated_joints:
        failures.append("skin joint order changed")
    if not np.array_equal(source_ibm, generated_ibm):
        failures.append("inverse-bind matrices changed")
    if len(source.nodes) != len(generated.nodes):
        failures.append("node count changed")
    if len(source.json.get("meshes", [])) != len(generated.json.get("meshes", [])):
        failures.append("mesh count changed")
    for expected in args.expect:
        if expected not in names:
            failures.append(f"missing expected animation: {expected}")
    for animation in generated.json.get("animations", []):
        times_by_sampler: list[np.ndarray] = []
        for sampler in animation.get("samplers", []):
            times = generated.accessor(sampler["input"]).reshape(-1)
            if len(times) < 2 or not np.all(np.diff(times) > 0):
                failures.append(f"non-monotonic or empty times in {animation.get('name', '')}")
            times_by_sampler.append(times)
        for channel in animation.get("channels", []):
            target = channel.get("target", {})
            node = target.get("node")
            if not isinstance(node, int) or node < 0 or node >= len(generated.nodes):
                failures.append(f"invalid target node in {animation.get('name', '')}")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "sourceSha256": sha256_file(args.source),
        "generatedSha256": sha256_file(args.generated),
        "sourceNodeCount": len(source.nodes),
        "skinJointCount": len(source_joints),
        "animationNames": names,
        "animationCount": len(names),
        "failures": failures,
    }
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
