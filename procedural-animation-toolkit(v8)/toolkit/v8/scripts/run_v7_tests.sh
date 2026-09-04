#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/scripts"
python3 -m unittest discover -s "$ROOT/tests" -p 'test_v7_core.py' -v
python3 -m unittest discover -s "$ROOT/tests" -p 'test_browser_contract_v7.py' -v
node --check "$ROOT/browser_demo/v7-viewer.js"
