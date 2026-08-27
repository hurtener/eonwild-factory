#!/usr/bin/env python3
"""Create a V5.5 GLB experiment with lower foot pivots on both hind legs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import AnatomicalBasis, SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader
from eonproc_v5_5.pivots import lower_foot_pivots


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--bone-map", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--gap-fraction", type=float, default=0.75)
    return parser.parse_args()


def main() -> None:
    cfg = parse_args()
    if not 0.0 < cfg.gap_fraction < 1.0:
        raise ValueError("--gap-fraction must be strictly between 0 and 1")
    asset = GlbAsset(cfg.input)
    semantics = SemanticMap.load(cfg.bone_map)
    basis = AnatomicalBasis.gltf_y_up(asset, semantics)
    before_reader = AnimationPackReader(asset)
    source_clip_contract = {
        name: {
            "times": animation.times.copy(),
            "rotations": {bone: values.copy() for bone, values in animation.rotations.items()},
            "translations": {bone: values.copy() for bone, values in animation.translations.items()},
        }
        for name, animation in before_reader.animations.items()
    }

    pivot_result = lower_foot_pivots(asset, semantics, basis, cfg.gap_fraction)
    asset.write(cfg.output)

    rebuilt = GlbAsset(cfg.output)
    after_reader = AnimationPackReader(rebuilt)
    animation_payload_exact = set(before_reader.animations) == set(after_reader.animations)
    if animation_payload_exact:
        for name, expected in source_clip_contract.items():
            actual = after_reader.animation(name)
            animation_payload_exact &= np.array_equal(expected["times"], actual.times)
            animation_payload_exact &= expected["rotations"].keys() == actual.rotations.keys()
            animation_payload_exact &= expected["translations"].keys() == actual.translations.keys()
            animation_payload_exact &= all(np.array_equal(values, actual.rotations[bone]) for bone, values in expected["rotations"].items())
            animation_payload_exact &= all(np.array_equal(values, actual.translations[bone]) for bone, values in expected["translations"].items())
            if not animation_payload_exact:
                break

    result = {
        "schema": "eonwild.v5.5-foot-pivot-test.v1",
        "status": "PASS" if animation_payload_exact else "FAIL",
        "source": str(cfg.input.resolve()),
        "sourceSha256": sha256(cfg.input),
        "output": str(cfg.output.resolve()),
        "outputSha256": sha256(cfg.output),
        **pivot_result,
        "jointOrderPreserved": asset.skin_data()[0] == rebuilt.skin_data()[0],
        "clipCount": len(after_reader.animations),
        "animationPayloadExact": bool(animation_payload_exact),
        "measurementBoundary": "Rig-space pivot experiment; not a biological or weight-paint validation.",
    }
    cfg.report.parent.mkdir(parents=True, exist_ok=True)
    cfg.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
