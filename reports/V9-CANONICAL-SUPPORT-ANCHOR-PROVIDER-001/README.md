# V9 canonical support-anchor provider 001

This record freezes the reviewed, opt-in canonical support-anchor provider at `f847630b901d86b4aeb895fe50fd9523b13d79e6`, integrated with the local byte-range review server in code union `806e3398c0f41a3c9c0a9dd2707887c284267611` (tree `679f0c0367ab75bee406a4df2b28e29cb99ed6b8`). The merge was conflict-free. Provider source files match the reviewed provider commit, and server source files match reviewed server commit `343ff071c90747377cd9f8a6bdee4c0c482626c8`.

The provider evaluates stable material anchors from the source-bound sustained gait at canonical touchdown events. Its binding covers the current frozen source and uniform scale, semantic roles, solver and transition data, performance and gaze data, contact definitions and ordered material identities, axes, articulation, and the supplied plan rows. The consumer recomputes that binding. The mode remains optional: existing recipes do not activate it, a missing provider fails closed when requested, caller-authored `target_offset_m` is rejected, and supplied rows are validated against `SourceMotionQuery`.

Review proceeded through two independent rounds and one exceptional narrow P1 closure:

- Round 1 at `7b584f21cff3197d8afcba9fbd109ee9f29e5026`: both reviewers found that the provider was not bound to the consuming source/material request.
- Round 2 at `f36b1eeb9af059f006000106624b8ae3ea143c8f`: the root reviewer closed the round-1 binding issue; reviewer 2 then found that modified plan-row content could still be accepted under unchanged metadata.
- Narrow closure at `f847630b901d86b4aeb895fe50fd9523b13d79e6`: both reviewers independently found the exact P1 fix clean. The provider reuses `SourceMotionQuery` authority, rejects caller offsets, and binds the supplied row content to the source law.

The exact integrated union passed the mandatory real-tool suite: **928 pytest cases plus 21 subtests**, with zero failures, errors, or skips, in 408.98 seconds. JUnit records 949 total tests. The run used Python 3.12.10, pytest 9.1.1, Blender 5.2.0 LTS, and the Khronos validator 2.0.0-dev.3.10. `final-suite-receipt.json` pins the command, executable paths, result, and external log/JUnit hashes.

This stage does not activate a recipe and does not establish an arbitrary-time skin correction law, exact emitted continuity, physical dynamics, biological validity, native playback, Unity parity, or production approval. Existing V9 film and source inputs were unchanged, so no rerender was performed.

## Evidence

- `root-round1-review.md` — SHA-256 `1e595711d846d1ce57916146dd30c00b48ee3dd0650513a5d76b69752a0bda57`
- `reviewer2-round1-review.md` — SHA-256 `2f48d8c40d73ebc9082227ae736ea7b566ccb19ce094073c34c0b54a58cac36d`
- `root-round2-review.md` — SHA-256 `49c814aa202fbc51f516b1e299e4a717f93b43576cfdaf04defb10d4b48b1a09`
- `reviewer2-round2-review.md` — SHA-256 `1e1d702d1294678186f4a97a1d141224ea6c9dff2d038f09543a001df58cc6a1`
- `root-narrow-closure.md` — SHA-256 `65b0c18c288b26cf14a3be84947710f8bc31dcff79c1fe19688542ce3d048060`
- `reviewer2-narrow-closure.md` — SHA-256 `7896166e4f5427885814d7db5960277b89e7264b73a764d59ae2bca7ddc72efc`
- `final-suite-receipt.json` — SHA-256 `32996520d2047cab1c3728d731e321bc624e8cc9c4851332e04e708ef201f984`
- External pytest log — SHA-256 `cb0e41cd81262b38e7a2d9a7cb13f5c02ad35782e64075e255d410aabea2ed62`
- External JUnit XML — SHA-256 `5628439e0414387c1c254a1f94db60bd3a35e830f12f8371abb96beeac49414d`
