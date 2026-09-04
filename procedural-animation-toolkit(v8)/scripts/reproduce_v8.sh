#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/reproduced_result/v8}"
cd "$ROOT/toolkit/v8"
./scripts/reproduce_v8.sh \
  "$ROOT/inputs/v8/tarbosaurus.glb" \
  "$ROOT/inputs/v8/bone-map.edited.yml" \
  "$ROOT/inputs/v8/tarbosaurus-attack-eat-reference.mp4" \
  "$OUT"
