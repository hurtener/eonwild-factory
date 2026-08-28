# V8.3 technical P1 closure re-review

## Verdict

- Exact commit: `ba302d7cdb715a7c1161fb7d8cc8cede3e43f6d2`
- Diff base: `c2701d09420630de8634c1a55c6c1c503a7b8f5f`
- Scope: technical P1 from `technical-final.md` only
- P0: **0**
- P1: **1**
- P2: **0**
- Recommendation: **FAIL; the normative evaluator remains conditionally bypassable**

The new evaluator substantially improves the prior acceptance seam: authentic
V8.3 validation invokes it, the committed evidence schemas validate, candidate
and baseline identity are checked, sweep winner/selected artifact are
cross-checked, selected metrics are compared across documents and thresholds,
layer semantic ownership is checked, and the final-skinned witness envelope is
validated. The controlled corrupt-value cases requested in the fix plan reject.

One fail-open dispatch condition still prevents P1 closure.

## P1-1: deleting a normative top-level key bypasses normative validation and returns PASS

`contact_inheritance_facts` invokes `evaluate_normative_evidence` only when
`artifactSha256`, `selectedScale`, `metrics`, and `evidence` are all present. If
any one is absent, it deliberately sets `normative = None` and continues through
the legacy boolean-selector path
(`src/eonwild_motion/pipeline/validate.py:41-58`). The subsequent selector path
needs only `checks.*` and `counts.undeclaredChanges`, then constructs a PASS
result (`src/eonwild_motion/pipeline/validate.py:59-83`).

This bypass defeats the new normative schema's required-field contract
(`schemas/motion/normative-evaluation.v1.schema.json:3-19`). Independent
controlled negatives copied the authentic machine report, removed exactly one
top-level key, rebound the copy as the resolved contact-evidence path, and
called `contact_inheritance_facts`:

| Removed key | Result |
|---|---|
| `artifactSha256` | **PASS**, `normativeEvaluation = None` |
| `selectedScale` | **PASS**, `normativeEvaluation = None` |
| `metrics` | **PASS**, `normativeEvaluation = None` |
| `evidence` | **PASS**, `normativeEvaluation = None` |

The committed negative test removes one nested metric while retaining the
top-level `metrics` key, so it does not exercise this bypass
(`tests/test_integration.py:167-191`). This is materially the same absent-metric
case required by the original P1 closure: a malformed V8.3 normative document
can still be accepted without schema, artifact, scale, threshold, sweep,
winner, or witness validation.

Required closure: decide whether normative evaluation is mandatory from the
resolved profile/motion contract (for example, its declared V8.3 validators or
proof type), not by detecting optional evidence keys. When mandatory, always
invoke `evaluate_normative_evidence`; let its schema reject any missing field.
Retain the legacy path only for profiles whose contract explicitly declares the
legacy evidence format. Add one negative per removed top-level required key.

## Passing focused evidence

### Authentic path and requested corrupt-value cases

The authentic command passed from a clean detached checkout:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m eonwild_motion.cli validate \
  --profile working \
  --artifact assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb \
  --work-root /tmp/eonwild-v83-auth-validate.*

status=PASS
candidate=b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03
winner=0.5
thresholdSha256=217f74ce04e7c2f7149c293110427094e95383ad434d72be6718fa3c950e5caf
finalSkinnedDenseSamples=977
media=PASS
```

The two committed focused tests passed: **2 tests, PASS** in 38.823 seconds.
Independent mutations produced the following results:

| Corruption | Result |
|---|---|
| machine status `FAIL` | rejected by normative schema |
| artifact SHA zeroed | rejected by candidate identity |
| selected scale `999` | rejected by cross-document scale |
| all metrics `null` | rejected as missing/nonnumeric metric structure |
| stride `NaN` | rejected as non-finite |
| threshold reference changed to sweep | rejected by threshold schema |
| sweep reference removed | rejected by normative schema |
| threshold baseline SHA zeroed | rejected by baseline identity |
| selected sweep status contradicted | rejected by hard-gate/status consistency |
| sweep winner changed to `0.625` | rejected by selected-scale consistency |
| witness Euclidean regression set to `0.5 m` | rejected by witness threshold |

The evaluator also confines referenced paths to the repository, validates the
four new schemas, validates semantic delta manifests against declared layer
writes, and emits current hashes for thresholds, sweep, layer metrics, witness,
candidate, and media/review bindings
(`src/eonwild_motion/pipeline/normative_evidence.py:152-282`).

### Narrow invariance and identity

- No catalog, motion, profile, channel-state, layer implementation, approved
  GLB, or V8.2 release path changed in `c2701d0..ba302d7`.
- V8.3 remains SHA-256
  `b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`.
- Stable V8.2 remains SHA-256
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
- The exact commit is the direct child of `c2701d0` and carries a valid SSH
  signature for `117486687+hurtener@users.noreply.github.com`, fingerprint
  `SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`; author and committer are
  `Santiago Benvenuto <117486687+hurtener@users.noreply.github.com>`.
- `git diff --check c2701d0..ba302d7` passed.

The diff also contains the separately reviewed visual-evidence correction;
that media/page scope was not reopened here. No code, catalog, profile, asset,
evidence, or media file was changed by this reviewer. Per instruction, this
report is not committed.
