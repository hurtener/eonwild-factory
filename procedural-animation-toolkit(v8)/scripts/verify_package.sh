#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
sha256sum -c SHA256SUMS.txt
python3 - <<'PY'
import json
from pathlib import Path
root=Path('.')
manifest=json.loads((root/'PACKAGE_MANIFEST.json').read_text())
missing=[p for p in manifest['requiredEntrypoints'] if not (root/p).exists()]
if missing: raise SystemExit(f'Missing required entrypoints: {missing}')
print(f"Package entrypoints verified: {len(manifest['requiredEntrypoints'])}")
PY
