#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/scripts"
python3 -m unittest discover -s "$ROOT/tests" -p 'test_*.py' -v
if command -v tsc >/dev/null 2>&1; then
  tsc --noEmit --target ES2020 --moduleResolution node --module ES2020 --strict \
    "$ROOT/runtime/types.ts" "$ROOT/runtime/phase-clock.ts" \
    "$ROOT/runtime/terrain-contact-adapter.ts" "$ROOT/runtime/action-controller.ts" \
    "$ROOT/runtime/motion-graph-v4.ts" "$ROOT/runtime/babylon-v4-adapter.ts" \
    "$ROOT/runtime/event-dispatcher.ts"
fi
