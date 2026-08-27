#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INVENTORY="$ROOT/PACKAGE_INVENTORY.txt"
CHECKSUMS="$ROOT/KEY_SHA256SUMS.txt"

(
  cd "$ROOT"
  shasum -a 256 \
    inputs/tarbosaurus_source.glb \
    inputs/tarbosaurus_bone_map.edited.yml \
    inputs/tarbosaurus_reference_walk_side_v02.mp4 \
    validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb \
    validated_result/v5.5/tarbosaurus_procedural_v5_5_animation_pack.glb \
    validated_result/v5.5/animation-manifest.v5.5.json \
    validated_result/v5.5/constrained-solve-report.json \
    validated_result/v5.5/procedural-v5.5-report.json \
    validated_result/v5.5/v5.5-release-validation.json \
    toolkit/v5.5/scripts/build_v5_5.py \
    toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json
) > "$CHECKSUMS"

find "$ROOT" -type f \
  ! -path '*/__pycache__/*' \
  ! -name '.DS_Store' \
  ! -path "$INVENTORY" \
  -exec stat -f '%z	%N' {} \; \
  | sed "s#	$ROOT/#	./#" \
  | sort > "$INVENTORY"
