#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/toolkit/v8/scripts/run_v8_1_tests.sh"
