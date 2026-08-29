# V9 evidence ingest remediation commands and checks

This record covers the rights-gated removal of the ten productized duplicate
MP4s. It does not authorize use of the external source. All commands were
run from:

`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`

## Identity and source inventory

```sh
git rev-parse HEAD
find /Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence \
  -maxdepth 1 -type f -name '*.mp4' -print0 | xargs -0 -n1 basename | LC_ALL=C sort
```

Observed target HEAD before ingest:

```text
85de1f2ceaa75427f74090a47d2b6a1ca3c6022a
```

Observed source inventory before and after remediation:

```text
SOURCE_RECHECK=PASS count=10 regular_mp4s
```

The source root is `/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence`.
The productized removal root is
`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/assets/examples/tarbosaurus/v9_evidence`.

## Source stability and hashes

The source was enumerated, hashed, and stat'ed before ffprobe; the same names,
sizes, integer modification times, and SHA-256 values were checked after
ffprobe and immediately before the historical copy. The source was rehashed
after removal of the productized duplicates.

```sh
shasum -a 256 \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/BITE MISS + RECOVERY — front three-quarter.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/BODY SHOVE → SMALL STUMBLE → RECOVERY.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/FEEDING + TEAR:PULL — fixed side.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/GROUNDED COMMITTED BITE — fixed side.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/LISTEN REACTION — front three-quarter.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/RUN START-RUN-RUN STOP.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/running-sustained-left.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/sprint-left.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/walking-back-gauge.mp4' \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/walking-front-gauge.mp4'
```

Result: `SOURCE_STABILITY=PASS count=10`. Exact hashes, byte sizes, ffprobe
facts, and mappings are retained in `audit.json`.

## Historical copy and rights remediation

The ten source files were historically copied with `cp -p` and set to mode
`0644`; no media processing or re-encoding occurred. Before removal, a
source-to-stored check passed for all ten files:

```text
HASH_SOURCE_EQUALS_STORED=PASS count=10 mode=0644
```

After the rights disposition was changed to external receipt only, the
productized duplicates were removed by an explicit list of the ten paths from
`plan.md`. No wildcard or source-root deletion was used. The post-removal
check was:

```sh
find assets/examples/tarbosaurus/v9_evidence -maxdepth 1 \
  -type f -name '*.mp4' -print
```

Result:

```text
PRODUCTIZED_DUPLICATE_COUNT=0
SOURCE_FILES_PRESERVED=PASS count=10
```

The external source files remain in place. `stored_path` is now `null` for
all rows; there is no productized media path to use or commit.

## Technical probe

```sh
ffprobe -v error -of json -show_streams -show_format \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/<file>.mp4'
```

Tool: `ffprobe version 9.0.1`.

All ten primary streams were H.264, `24/1`, with dimensions `1280x704` for
the bite-miss clip and `736x400` for the other nine. Frame counts were `193`
or `145`; durations were `8.041667` or `6.041667` seconds. All ten had AAC
audio. Nine had an attached-picture MJPEG stream at index 2; it is auxiliary
container metadata, not a second motion stream.

The requested 60 fps timing gate is not met. No retiming or frame synthesis
was performed; 24 fps evidence is insufficient for sub-frame native-speed
validation.

## Manifest and report validation

```sh
python3 - <<'PY'
import json
from hashlib import sha256
from pathlib import Path

source = Path('/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence')
manifest = json.loads(Path('reports/V9-EVIDENCE-INGEST-001/audit.json').read_text())
rows = manifest['files']
assert manifest['status'] == 'BLOCKED_PENDING_RIGHTS_CONFIRMATION'
assert len(rows) == 10
assert manifest['scope']['file_count_stored'] == 0
assert manifest['scope']['productized_duplicates_removed'] is True
for row in rows:
    src = Path(row['source_path'])
    assert src.parent == source and src.is_file()
    assert row['sha256'] == sha256(src.read_bytes()).hexdigest()
    assert row['byte_size'] == src.stat().st_size
    assert row['stored_path'] is None and row['stored_path_absolute'] is None
    assert row['copied'] is False and row['committed'] is False
    assert row['usable_as_motion_input'] is False
    assert row['rights_status'] == 'unresolved'
    assert row['rights_confirmation'] is None
    assert row['fps_rational'] == '24/1'
print('MANIFEST_SOURCE_HASHES=PASS count=10')
print('RIGHTS_BLOCK=PASS stored=0 usable_as_motion_input=false')
PY

python3 -m json.tool reports/V9-EVIDENCE-INGEST-001/audit.json >/dev/null
python3 -m json.tool reports/V9-EXTENSION-001/reference-coverage.json >/dev/null
python3 -m json.tool reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json >/dev/null
test ! -e reports/V9-EVIDENCE-INGEST-001/narrow-gauge-contract.json
```

Results:

```text
JSON_PARSE=PASS audit coverage canonical-contract
DUPLICATE_NARROW_GAUGE_CONTRACT=ABSENT canonical_contract=present
```

The canonical narrow-gauge contract under
`reports/V9-GAIT-FOOT-AUDIT-001/` was not modified.

## Whitespace, diff, and scope checks

```sh
python3 - <<'PY'
from pathlib import Path
paths = [
    Path('reports/V9-EVIDENCE-INGEST-001'),
    Path('reports/V9-EXTENSION-001/reference-coverage.md'),
    Path('reports/V9-EXTENSION-001/reference-coverage.json'),
]
bad = []
for root in paths:
    files = [root] if root.is_file() else [p for p in root.rglob('*') if p.is_file()]
    for path in files:
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            if line.endswith((' ', '\t')):
                bad.append(f'{path}:{line_no}')
assert not bad, bad
print('REPORT_TRAILING_WHITESPACE=PASS')
PY
git diff --check -- reports/V9-EVIDENCE-INGEST-001 reports/V9-EXTENSION-001/reference-coverage.md reports/V9-EXTENSION-001/reference-coverage.json
```

The final status is intentionally uncommitted. Existing unrelated worktree
changes are not included in this report's scope.
