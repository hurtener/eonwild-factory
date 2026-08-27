#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
test -f "$ROOT/validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb"
test -f "$ROOT/validated_result/v5/OPEN_ME_tarbosaurus_v5_3d_browser.html"
test -f "$ROOT/validated_result/v5/OPEN_ME_tarbosaurus_v5_validation.html"
test -f "$ROOT/validated_result/v5/v5-release-validation.json"
python3 - <<'PY' "$ROOT"
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);v=json.loads((r/'validated_result/v5/v5-release-validation.json').read_text())
assert v['status']=='PASS';assert v['clipCount']==37;assert v['skinJointCount']==75;assert v['transitionCount']==16
print('Package verification PASS')
PY
