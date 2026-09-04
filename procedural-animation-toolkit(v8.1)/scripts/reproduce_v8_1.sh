#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/reproduced_result/v8.1}"
"$ROOT/toolkit/v8/scripts/reproduce_v8_1.sh" "$ROOT/inputs/v8/tarbosaurus.glb" "$ROOT/inputs/v8/bone-map.edited.yml" "$ROOT/toolkit/v8/examples/profiles/tarbosaurus-v8.1.json" "$OUT" "$(cd "$ROOT/../procedural-animation-toolkit(v8)" && pwd)"
