#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V5="$ROOT/toolkit/v5"
PYTHONPATH="$V5/scripts" python3 -m unittest discover -s "$V5/tests" -p 'test_*v5.py' -v
node --check "$V5/browser_demo/v5-viewer.js"
PYTHONPATH="$V5/scripts" python3 "$V5/tests/validate_v5_release.py" \
  --source "$ROOT/validated_result/v4/tarbosaurus_procedural_v4_animation_pack.glb" \
  --generated "$ROOT/validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb" \
  --bone-map "$ROOT/inputs/tarbosaurus_bone_map.edited.yml" \
  --manifest "$ROOT/validated_result/v5/animation-manifest.v5.json" \
  --player-js "$ROOT/validated_result/v5/browser/v5-viewer.js" \
  --output "$ROOT/validated_result/v5/v5-release-validation.json"
