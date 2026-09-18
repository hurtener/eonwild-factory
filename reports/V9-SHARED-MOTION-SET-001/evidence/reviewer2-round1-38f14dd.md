# Shared motion-set baseline — independent round 1 review

Reviewed `38f14dd4142c161f2838d80210ee3a83be836a91` (tree
`3d0a3bb3aa7f7552b7667f877ee0f4a1e076c8e0`) against published
`945b189340f9d461373a1309bd06a7a7c3bcea8d`. The implementation worktree was
clean and was not modified.

## Findings

### P1 — package-local verification does not bind the gait that drove the plan

`compile_recipe` includes the set, baseline, intent, performance style, and
neutral-pose snapshots, but omits the intent's `program_profile` and optional
`gait_profile` from the package (`compiler.py:663-668`). During verification,
`_verify_motion_set_provenance` constructs a `GroundedGait` from the generated
`plan.parameters` and derives the response from that value
(`compiler.py:840-868`). It never checks those parameters against the
intent-bound gait bytes.

`provenance_repro.py` resolves the real `walk` intent, whose locked program
profile has `step_period_s=1.23`, then supplies a plan and matching response
receipt made from the existing fast-walk gait (`step_period_s=0.8`). The
unchanged walk intent, recipe, program-profile hash, set/baseline snapshots,
runtime identities, and solve policy are retained. The verifier returns
`ACCEPT`; no program-profile snapshot exists in the evidence package. This
means package-local reconstruction proves the flat recipe binding but does not
prove that the bound program/gait input produced the plan or effective response.
For transitions, the same code trusts `plan.parameters` instead of the
separately bound steady `gait_profile`.

Close this by packaging every consumed program/gait snapshot, binding each
snapshot to the reconstructed recipe hash, loading the response gait from that
snapshot, and rejecting any mismatch between its canonical parameters and the
plan. A transition must derive response from its packaged steady gait profile,
not from mutable generated evidence.

### P2 — motion names can escape the requested selection output

Motion entry names are required only to be nonempty strings
(`motion_set.py:67-75`) and are then appended directly to the output path
(`compiler.py:725-727`). `repro.py` uses the public selection compiler with an
otherwise valid set whose motion name is `../escaped-package`; the captured
package destination resolves outside `requested/`.

Require a portable single path component before selection (no absolute path,
slash, backslash, dot segment, or platform separator). This is a local
fail-closed fix and should be covered through the public compile-set path.

### P2 — baseline coordinate axes admit JSON strings

The baseline validator delegates directly to `frame_axes`
(`motion_set.py:90-92`), whose NumPy conversion coerces numeric strings.
`repro.py` shows `["0","0","1"]` is accepted unchanged as the baseline forward
axis. The new shared-baseline schema is described as strict and these values
control geometry admission and emitted runtime axes, so it should require a
three-element JSON numeric sequence with booleans and strings rejected before
normalization.

## Checks

- 104 focused motion-set, gait-response, connected-schedule, and emitted-handoff
  tests passed in 2.77 seconds.
- Two legacy deterministic compile/reopen cases passed in 3.22 seconds.
- All four catalog intents resolve to baseline snapshot
  `0c92fc7c3a42ad28d4712a7bb33b4e8d0c27f4715547e05a4d268a0d844d429a`;
  start and stop both bind steady gait
  `271ccb833a8913d3dc6bd8281e798e54b9c7bebad2080136245cb7b5e5afa725`.
- Author evidence records 132 focused tests passing in 258.69 seconds and Ruff
  passing.

No other P0/P1 or realistic local P2 was found in the reviewed scope. The
strict style/calibration/solve-policy split, unsupported-program and LINEAR
rejection, effective transition response from a grounded gait object, shared
baseline handoff comparison, connected-schedule identity comparison, and
legacy recipe path behave as intended in the focused checks. The P1 above
prevents treating package-local response reconstruction as complete until the
consumed gait snapshots are added.
