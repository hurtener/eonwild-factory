#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/validated_result/v5.5"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export PYTHONDONTWRITEBYTECODE=1

"$ROOT/scripts/check_v5_immutable.sh"
test -f "$OUT/tarbosaurus_procedural_v5_5_animation_pack.glb"
test -f "$OUT/animation-manifest.v5.5.json"
test -f "$OUT/procedural-v5.5-report.json"
test -f "$OUT/constrained-solve-report.json"
test -f "$OUT/v5.5-release-validation.json"

"$PYTHON_BIN" - "$OUT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
validation = json.loads((out / "v5.5-release-validation.json").read_text())
glb = out / "tarbosaurus_procedural_v5_5_animation_pack.glb"
digest = hashlib.sha256(glb.read_bytes()).hexdigest()
assert validation["status"] == "PASS"
assert validation["constrainedQualityGatesPass"] is True
assert validation["clipCount"] == 37
assert validation["skinJointCount"] == 75
assert validation["transitionCount"] == 16
assert digest == validation["generatedSha256"], (digest, validation["generatedSha256"])
print("V5.5 package verification PASS")
PY

PYTHON_BIN="$PYTHON_BIN" "$ROOT/scripts/run_v5_5_tests.sh"
