# CUBICSPLINE midpoint evidence narrow closure — reviewer 2

Reviewed exact head `7cc9886283cf5de43b246bb05c3f073f121e4531` against parent `36f311e4cfc67cd73eb684a21f353d0c804ff5fb`. Scope was limited to the prior P1: an incomplete midpoint result such as `{\"verdict\": \"PASS\"}` could satisfy package verification.

**Result: CLEAN.** The real retained stage-2 package, copied with ordinary independent files, now rejects the incomplete PASS mapping with `CUBICSPLINE midpoint contact result shape is invalid`. A complete, internally consistent midpoint result with an explicit contact failure continues to reopen as integrity `PASS`, technical `BLOCKED`, `production_approved=false`. This preserves truthful blocked evidence rather than treating every non-PASS result as corruption.

The narrow implementation validates the exact top-level evidence shape, finite aggregate scalars, per-foot count and unique labels, classification/authority, and aggregate consistency. One targeted regression passed (`1 passed, 24 deselected`, 1.41 s); Ruff and diff-check passed. No whole-branch review or repeated full suite was performed.

Machine-readable probe: `source-cubic-shape-narrow-closure-reviewer2-7cc9886.json` (SHA-256 `c3ec48c0ad9d95ae0db15124effa2bcf9b5a3d2ae4e48eeeab0c4a3b7b498f65`).
