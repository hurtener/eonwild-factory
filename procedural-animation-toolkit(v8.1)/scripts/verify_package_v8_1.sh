#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
shasum -a 256 -c SHA256SUMS_V8_1.txt
python3 - <<'PY'
import json
from pathlib import Path
p=json.loads(Path('PACKAGE_MANIFEST_V8_1.json').read_text())
assert p['schema']=='eonwild.package-manifest.v8.1'
assert p['fileCount']==len(p['files'])
print(f"verified {p['fileCount']} V8.1 package files")
PY
