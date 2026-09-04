#!/usr/bin/env python3
"""Generate the complete Tarbosaurus V4 animation pack."""
from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap
from eonproc_v4.profile import BipedV4Profile
from eonproc_v4.generator import TarbosaurusV4Generator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV4Profile.from_json(args.profile) if args.profile else BipedV4Profile()
    generator = TarbosaurusV4Generator(asset, semantics, profile)
    generator.generate_all()
    outputs = generator.write(args.output_dir, args.input, args.bone_map)
    print(json.dumps({name: str(path) for name, path in outputs.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
