# Source-derived CUBICSPLINE emitter — reviewer 2 round two

Reviewed exact postfix `36f311e4cfc67cd73eb684a21f353d0c804ff5fb` against parent `67a675686475e18c28e3900e519272fbb6f65320`. Scope was the three-file verifier closure only. The worktree remained clean. Result: **one remaining P1; no P0**.

## Closed round-one findings

Both original real-package bypasses are closed. Unchanged CUBICSPLINE GLBs presented as default LINEAR reject with `package interpolation declaration differs from serialized exports`. A root-motion midpoint contact verdict changed to `FAIL` with `1 m` penetration while technical status remains PASS rejects with `technical status ignores midpoint contact failure`.

The normal-copy closure receipt is `audits/source-cubic-round2-reviewer2-probes.json`, SHA-256 `76aefde5be4fa22ed9dadd099ee2f9a38db345251e38ccf54d8a42149b73d527`.

## P1 — Verdict-only mappings erase the required midpoint contact evidence

`src/eonwild_motion/factory/compiler.py:679-690` now requires each midpoint result to be a dictionary whose `verdict` is `PASS` or `FAIL`, but it does not validate the supported result structure. Replacing both complete `evaluate_skin` results in the actual Stage 2 package with `{"verdict":"PASS"}`, refreshing `validation.json` in the manifest, and leaving technical status PASS makes `verify_package` return `integrity: PASS` and `technical_status: PASS`.

This is the unclosed half of round one's request to validate the supported per-mode verdict shape. It permits a CUBICSPLINE package to discard the newly required midpoint sample count, ground level, penetration/gap measurements, classification and authority details while retaining technical acceptance.

Require the exact supported top-level shape produced by `evaluate_skin` for each mode, with strict primitive and finite numeric validation for the scalar fields used as acceptance evidence. A low-risk closure can share a narrow validator with the existing final skinned-contact result or validate the midpoint result against the same contract. It need not redesign legacy package verification or recompute the full cycle.

Reproduction: `audits/source-cubic-round2-shape-reviewer2.json`, SHA-256 `f201b94a5f363b15ef7c1b4f3bddf0cd0e8ea5763071f285981735d29ef32054`.

## Focused checks and boundaries

The five focused files passed **87 tests in 85.02 s**. Ruff on the changed implementation and `git diff --check` pass. The retained real package remains exact at manifest SHA-256 `03c0edb00b53abe5d68094480f2558d657f076e4099c85650ac293bb901a277c`.

No other P0/P1 was found in the postfix. This review does not reopen the emitter, source law, interval bound, Blender adapter, Unity, visual, or global-continuity stages. Per the review cap, the remaining P1 needs one narrow diff-only closure rather than another full review.
