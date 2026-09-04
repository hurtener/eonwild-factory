#!/usr/bin/env python3
"""Generate the complete Eonwild Tarbosaurus V8 animation pack."""
from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap, AnatomicalBasis
from eonproc_v5.jaw import JawClosureModel
from eonproc_v8.profile import BipedV8Profile
from eonproc_v8.generator import TarbosaurusV8Generator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--skip-jaw-calibration", action="store_true")
    args = parser.parse_args()

    asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV8Profile.from_json(args.profile) if args.profile else BipedV8Profile()
    jaw_meta = None
    if not args.skip_jaw_calibration:
        basis = AnatomicalBasis.gltf_y_up(asset, semantics)
        ground = float(asset.primitive().positions[:, 1].min())
        pelvis_y = float(asset.rest_world[asset.name_to_node[semantics.bone("pelvis")]][1, 3])
        model = JawClosureModel(asset, semantics, basis, pelvis_y - ground)
        calibration = model.calibrate(target_minimum_gap_m=(pelvis_y - ground) * 0.0015)
        profile = replace(profile, neutral_jaw_close_deg=float(calibration.close_degrees))
        jaw_meta = calibration.to_dict()

    generator = TarbosaurusV8Generator(asset, semantics, profile)
    generator.generate_all()
    outputs = generator.write(args.output_dir, args.input, args.bone_map)
    if jaw_meta is not None:
        jaw_path = Path(args.output_dir) / "jaw-calibration-v8.json"
        jaw_path.write_text(json.dumps(jaw_meta, indent=2), encoding="utf-8")
        outputs["jaw"] = jaw_path
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
