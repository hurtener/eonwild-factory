#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
test -f "$ROOT/README.md"
test -f "$ROOT/PROCEDURAL_ANIMATION_GUIDE_V4.md"
test -f "$ROOT/scripts/run_pipeline_v4.py"
test -f "$ROOT/scripts/eonproc_v4/generator.py"
test -f "$ROOT/runtime/motion-graph-v4.ts"
python3 -m compileall -q "$ROOT/scripts"
"$ROOT/scripts/run_core_tests.sh"
echo "V4 source package verification passed"
