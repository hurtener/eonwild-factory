#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/scripts"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
uv run --python "$PYTHON_BIN" --with numpy --with scipy --with pyyaml -- python -m unittest -v "$ROOT/tests/test_v8_1_contract.py"
node --check "$ROOT/browser_demo/v8.1-viewer.js"
