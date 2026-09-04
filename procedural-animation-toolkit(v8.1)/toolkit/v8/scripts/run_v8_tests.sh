#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/scripts"
python3 -m unittest -v "$ROOT/tests/test_v8_core.py" "$ROOT/tests/test_browser_contract_v8.py"
node --check "$ROOT/browser_demo/v8-viewer.js"
