#!/usr/bin/env python3
"""Validate V4 semantic mapping and vertex-level sole extraction on the real Tarbosaurus fixture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from eonproc_v3.gltf_io import GlbAsset, sha256_file
from eonproc_v3.rig import SemanticMap
from eonproc_v4.locomotion import TerrainAwareLocomotionGenerator
from eonproc_v4.profile import BipedV4Profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--bone-map", required=True)
    parser.add_argument("--profile", help="Optional V4 profile JSON")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    asset = GlbAsset(args.input)
    semantics = SemanticMap.load(args.bone_map)
    profile = BipedV4Profile.from_json(args.profile) if args.profile else BipedV4Profile()
    generator = TerrainAwareLocomotionGenerator(asset, semantics, profile)
    primitive = asset.primitive()
    mapped = list(semantics.tags.values())
    missing = sorted(set(mapped) - set(asset.name_to_node))
    selections = generator.sole.selections
    overlap = np.intersect1d(selections["l"].vertex_indices, selections["r"].vertex_indices)
    output = {
        "status": "PASS" if not missing and len(overlap) == 0 else "FAIL",
        "input": {"sha256": sha256_file(args.input), "nodeCount": len(asset.nodes)},
        "boneMap": {
            "sha256": sha256_file(args.bone_map),
            "tagCount": len(semantics.tags),
            "uniqueBoneCount": len(set(mapped)),
            "missingBones": missing,
        },
        "skin": {"jointCount": len(asset.skin_data()[0]), "primitiveVertexCount": len(primitive.positions)},
        "sole": {
            side: {
                "selectedVertexCount": int(len(selection.vertex_indices)),
                "candidateVertexCount": selection.total_candidate_vertices,
                "allIndicesInPrimitive": bool(np.all(selection.vertex_indices < len(primitive.positions))),
                "uniqueIndices": bool(len(np.unique(selection.vertex_indices)) == len(selection.vertex_indices)),
                "restMinHeight": selection.rest_min_height,
                "restContactQuantile": selection.rest_contact_quantile,
                "influencingBones": list(selection.influencing_bones),
            }
            for side, selection in selections.items()
        },
        "leftRightSelectionOverlap": int(len(overlap)),
        "anatomicalConstraints": {
            "leftExpectedKneeSign": float(generator.leg_geometry["l"]["knee_signed_sign"]),
            "rightExpectedKneeSign": float(generator.leg_geometry["r"]["knee_signed_sign"]),
            "leftExpectedAnkleSign": float(generator.leg_geometry["l"]["ankle_signed_sign"]),
            "rightExpectedAnkleSign": float(generator.leg_geometry["r"]["ankle_signed_sign"]),
        },
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
