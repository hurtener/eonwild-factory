# Blender source-CUBICSPLINE playback adapter: reviewer-two round one

Reviewed exact `4823fa8cc3813fa07a06e670f7b344e8321908ec` against parent `170617beda89b1836aabebd983b7891549e03d65`. The source worktree was clean. Scope was the seven-file adapter and render integration delta; the closed source emitter and constant-law implementation were not reopened.

## Findings

No P0 or P1 finding.

No local P2 finding. The adapter uses the same importer-owned node conversions as Blender's `BlenderNodeAnim.do_channel`: glTF basis conversion, virtual-node base-to-final conversion, object-parented-to-bone translation offset, and edit-bone inverse conversion for pose-bone translation/rotation. Scale remains the converted final scale, matching the importer. Unanimated paths retain the imported rest state.

The source-time clock is finite and bounded against the decoded float timeline with the existing 2 microsecond endpoint allowance, then clamped only within that allowance. Every candidate and connected-sequence sample calls `scene.frame_set` before applying exact local TRS and updating the view layer. Both ordinary and terminal/connected join render paths use the adapter. The legacy single-frame and walk-review renderers reject cubic input rather than silently use Blender AUTO handles. CUBIC FBX export rejects before output creation; genuine LINEAR packages keep the stock import and existing FBX path.

The importer monkeypatch is restored in a `finally` block, captures exactly one importer state, and fails if animated nodes are absent from that state. Package callers hash-bind inputs and retain post-run immutability checks.

## Verification

Executed:

```
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_blender_native_playback.py \
  tests/test_review_connected_sequence.py \
  tests/test_review_candidate_stills.py
```

Result: **10 passed in 0.52 s**.

Reviewed retained native parity receipt `audits/blender-cubic-playback-001/native-playback-result-4823fa8.json` (SHA-256 `be6228f54ff02843cfccd9eb61e1276ca4712becfbb2f1f419215244a65ac11e`). It records 18 source-time samples per mode over 59,169 same-index vertices: root-motion maximum `5.710670488105736e-6 m`; in-place maximum `4.1902453752514266e-6 m`; both pass the retained 0.5 mm threshold.

This receipt applies the adapter directly without a render call. Independent frame-set then apply and actual Cycles render/post-render mesh checks are being run by root and remain the appropriate live confirmation that Blender render evaluation does not restore discarded AUTO-handle motion. That live check is an evidence boundary, not a code finding in this review.

## Post-review live-evidence update

Root's task-owned Cycles reproduction closed the explicit evidence boundary
above and exposed one concrete **P1**. All 18 `frame_set` then `apply` skin
samples stayed within 4.4 micrometres before rendering, but Blender's render
evaluation restored the approximate imported curves: the post-render pose
reached 1.566769 mm error in-place and 2.291010 mm in root-motion. The adapter
must reapply exact source-time TRS at Blender's render-evaluation boundary, and
must remove that handler in a `finally` path, before the render receipt can
claim exact native playback. The separate standard wrapper FBX default also
needs to omit or explicitly disable FBX for CUBICSPLINE native review rather
than aborting the requested review.

Updated disposition: **changes requested for one P1 render-evaluation overwrite
and its wrapper integration**. No other P0/P1 or local P2 finding.
