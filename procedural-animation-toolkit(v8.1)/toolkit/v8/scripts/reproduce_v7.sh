#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT="${1:-$ROOT/inputs/tarbosaurus.glb}"
MAP="${2:-$ROOT/inputs/bone-map.yml}"
OUT="${3:-$ROOT/validated_result/v7}"
export PYTHONPATH="$ROOT/scripts"
mkdir -p "$OUT"
python3 "$ROOT/scripts/run_pipeline_v7.py" --input "$INPUT" --bone-map "$MAP" --output-dir "$OUT"
python3 "$ROOT/tests/validate_fixture_v7.py" --input "$INPUT" --bone-map "$MAP" --profile "$OUT/resolved-profile-v7.json" --output "$OUT/v7-fixture-validation.json"
python3 "$ROOT/tests/validate_v7_release.py" --glb "$OUT/tarbosaurus_procedural_v7_animation_pack.glb" --report "$OUT/procedural-v7-report.json" --manifest "$OUT/animation-manifest.v7.json" --output "$OUT/v7-release-validation.json"
python3 "$ROOT/tests/validate_baked_ground_v7.py" --source "$INPUT" --glb "$OUT/tarbosaurus_procedural_v7_animation_pack.glb" --bone-map "$MAP" --output "$OUT/baked-ground-regression-v7.json"
python3 "$ROOT/scripts/analyze_turn_v7.py" --glb "$OUT/tarbosaurus_procedural_v7_animation_pack.glb" --bone-map "$MAP" --output "$OUT/turn-kinematics-v7.json"
python3 "$ROOT/scripts/build_v7_browser_html.py" --output-dir "$OUT" --glb "$OUT/tarbosaurus_procedural_v7_animation_pack.glb" --manifest "$OUT/animation-manifest.v7.json"
