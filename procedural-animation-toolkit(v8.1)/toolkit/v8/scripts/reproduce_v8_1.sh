#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="${1:?source GLB required}"
MAP="${2:?bone map required}"
PROFILE="${3:?canonical V8.1 profile required}"
OUT="${4:?fresh output directory required}"
V8_ROOT="${5:-}"
if [[ -e "$OUT" ]] && [[ -n "$(find "$OUT" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "Refusing non-empty output directory: $OUT" >&2; exit 2
fi
mkdir -p "$OUT"
export PYTHONPATH="$ROOT/scripts"
UV="${UV:-$(command -v uv)}"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
run(){ "$UV" run --python "$PYTHON_BIN" --with numpy --with scipy --with pyyaml -- "$@"; }
run python "$ROOT/scripts/run_pipeline_v8.py" --input "$SOURCE" --bone-map "$MAP" --profile "$PROFILE" --output-dir "$OUT"
run python "$ROOT/tests/validate_baked_ground_v8_1.py" --glb "$OUT/tarbosaurus_procedural_v8_1_animation_pack.glb" --bone-map "$MAP" --profile "$PROFILE" --output "$OUT/v8.1-baked-ground-validation.json"
run python "$ROOT/tests/validate_v8_1_release.py" --source "$SOURCE" --glb "$OUT/tarbosaurus_procedural_v8_1_animation_pack.glb" --bone-map "$MAP" --report "$OUT/procedural-v8.1-report.json" --manifest "$OUT/animation-manifest.v8.1.json" --profile "$PROFILE" --pivots "$OUT/foot-pivot-calibration-v8.1.json" --baked-ground "$OUT/v8.1-baked-ground-validation.json" --output "$OUT/v8.1-release-validation.json"
run python "$ROOT/tests/validate_jaw_centering_v8_1.py" --source "$SOURCE" --bone-map "$MAP" --profile "$PROFILE" --output "$OUT/jaw-centering-v8.1.json"
run python "$ROOT/scripts/build_v8_1_browser_html.py" --output-dir "$OUT" --glb "$OUT/tarbosaurus_procedural_v8_1_animation_pack.glb" --manifest "$OUT/animation-manifest.v8.1.json"
run python "$ROOT/tests/validate_browser_contract_v8_1.py" --html "$OUT/OPEN_ME_tarbosaurus_v8_1_3d_browser.html" --glb "$OUT/tarbosaurus_procedural_v8_1_animation_pack.glb" --manifest "$OUT/animation-manifest.v8.1.json" --viewer-js "$ROOT/browser_demo/v8.1-viewer.js" --output "$OUT/v8.1-browser-contract-validation.json"
if [[ -n "$V8_ROOT" ]]; then
  run python "$ROOT/tests/validate_walk_preservation_v8_1.py" --v8-glb "$V8_ROOT/validated_result/v8/tarbosaurus_procedural_v8_animation_pack.glb" --v8-report "$V8_ROOT/validated_result/v8/procedural-v8-report.json" --v8-1-glb "$OUT/tarbosaurus_procedural_v8_1_animation_pack.glb" --v8-1-report "$OUT/procedural-v8.1-report.json" --bone-map "$MAP" --output "$OUT/v8-to-v8.1-walk-preservation.json"
fi
