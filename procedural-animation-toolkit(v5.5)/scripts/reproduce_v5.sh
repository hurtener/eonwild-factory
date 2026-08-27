#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V5="$ROOT/toolkit/v5"
OUT="$ROOT/validated_result/v5"
mkdir -p "$OUT" "$OUT/browser"
PYTHONPATH="$V5/scripts" python3 "$V5/scripts/upgrade_v4_pack_to_v5.py" \
  --source-glb "$ROOT/validated_result/v4/tarbosaurus_procedural_v4_animation_pack.glb" \
  --bone-map "$ROOT/inputs/tarbosaurus_bone_map.edited.yml" \
  --v4-report "$ROOT/validated_result/v4/procedural-v4-report.json" \
  --output-dir "$OUT"
cp "$V5/browser_demo/index.html" "$OUT/browser/index.html"
cp "$V5/browser_demo/v5-viewer.js" "$OUT/browser/v5-viewer.js"
cp "$OUT/tarbosaurus_procedural_v5_animation_pack.glb" "$OUT/browser/"
cp "$OUT/animation-manifest.v5.json" "$OUT/browser/"
python3 "$ROOT/scripts/build_v5_browser_html.py"
PYTHONPATH="$V5/scripts" python3 "$V5/tests/validate_v5_release.py" \
  --source "$ROOT/validated_result/v4/tarbosaurus_procedural_v4_animation_pack.glb" \
  --generated "$OUT/tarbosaurus_procedural_v5_animation_pack.glb" \
  --bone-map "$ROOT/inputs/tarbosaurus_bone_map.edited.yml" \
  --manifest "$OUT/animation-manifest.v5.json" \
  --player-js "$OUT/browser/v5-viewer.js" \
  --output "$OUT/v5-release-validation.json"
echo "V5 core build complete: $OUT"
