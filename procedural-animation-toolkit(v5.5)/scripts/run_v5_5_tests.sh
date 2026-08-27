#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
ENGINE="$ROOT/toolkit/v5.5"
OUT="$ROOT/validated_result/v5.5"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONDONTWRITEBYTECODE=1

"$ROOT/scripts/check_v5_immutable.sh"
PYTHONPATH="$ENGINE/scripts" "$PYTHON_BIN" -m unittest discover -s "$ENGINE/tests" -p 'test_*v5.py' -v
PYTHONPATH="$ENGINE/scripts" "$PYTHON_BIN" "$ENGINE/tests/validate_v5_5_release.py" \
  --baseline "$ROOT/validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb" \
  --generated "$OUT/tarbosaurus_procedural_v5_5_animation_pack.glb" \
  --bone-map "$ROOT/inputs/tarbosaurus_bone_map.edited.yml" \
  --manifest "$OUT/animation-manifest.v5.5.json" \
  --profile "$ENGINE/examples/profiles/tarbosaurus-v5.5.json" \
  --constrained-report "$OUT/constrained-solve-report.json" \
  --output "$OUT/v5.5-release-validation.json"
"$PYTHON_BIN" "$REPO/showcase/v5.5/check_site.py"
