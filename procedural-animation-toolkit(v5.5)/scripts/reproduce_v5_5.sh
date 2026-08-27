#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$ROOT/toolkit/v5.5"
OUT="$ROOT/validated_result/v5.5"
WORK="$OUT/constrained-v4.5"
PYTHON_BIN="${PYTHON_BIN:-python3}"

mkdir -p "$OUT" "$WORK"
PYTHONPATH="$ENGINE/scripts" "$PYTHON_BIN" "$ENGINE/scripts/run_pipeline_v4.py" \
  --input "$ROOT/inputs/tarbosaurus_source.glb" \
  --bone-map "$ROOT/inputs/tarbosaurus_bone_map.edited.yml" \
  --profile "$ENGINE/examples/profiles/tarbosaurus-v5.5.json" \
  --output-dir "$WORK"
cp "$WORK/procedural-v4-report.json" "$OUT/constrained-solve-report.json"

PYTHONPATH="$ENGINE/scripts" "$PYTHON_BIN" "$ENGINE/scripts/build_v5_5.py" \
  --source-glb "$WORK/tarbosaurus_procedural_v4_animation_pack.glb" \
  --bone-map "$ROOT/inputs/tarbosaurus_bone_map.edited.yml" \
  --v4-report "$WORK/procedural-v4-report.json" \
  --output-dir "$OUT"

echo "V5.5 full constrained build complete: $OUT"
