# V8.1 relaxed-walk respin visual review plan

## Task

Independently review the final V8.1 relaxed-walk respin approval film against the supplied relaxed-walk reference and the user-provided capture criteria. The review is read-only with respect to source assets, candidate generation, engine/media files, and existing reports. It must judge normal 24 fps playback and frame-level evidence for cadence, reach, limb-chain cohesion, late-stance metatarsal/toe behavior, contact quality, posture/mass, loop seam, and framing. The result remains an approval candidate, not a release approval.

## Files to touch

- `reports/V8-1-WALK-RESPIN/visual-review/plan.md` (this plan)
- `reports/V8-1-WALK-RESPIN/visual-review/visual-review.md` (review output)

No source GLB, profile, candidate, showcase media, or canonical toolkit files will be edited.

## Acceptance checks

- Verify both MP4 paths, codecs, dimensions, duration, frame rate, and decoded frame counts with `ffprobe`.
- Extract representative full-frame and foot-region frame sheets from both videos for visual comparison.
- Inspect temporal behavior across the complete candidate film, including both cycles and the loop seam, at normal 24 fps timing where possible.
- Compare observed behavior with the supplied reference and the user capture criteria; separate directly visible evidence from limitations.
- Classify findings as P0/P1/P2 and state whether the candidate is visually acceptable for user approval.
- Preserve exact input paths, hashes, commands, and limitations in the review.

## Ownership and assumptions

- The factory repository has no shared ownership map; the parent candidate plan designates `reports/V8-1-WALK-RESPIN/**` as task-scoped output. In the eonwild constitution, reports are task-owner scope; this review writes only its own report directory.
- The user captures are treated as pose/timing references available in the conversation, not as calibrated motion-capture truth. If their original image files are not discoverable locally, that limitation will be explicit.
- Visual review cannot prove hidden mesh/animation state; machine-readable candidate diagnostics are evidence context only, not a substitute for looking at the film.
