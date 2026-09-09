# Shared motion set: root release review, round 2

Reviewed release head `0330d8ae7acbf7a6300e1e991658f78544d9886c`, tree
`5f22a62f8b2512e8cc89d7fd5ecadc19825e2df4`. The complete 20-file integration
was reviewed in round 1; this release review revisited its ownership and package
verification boundaries and all three files in the combined fix from `38f14dd`.

## Remaining P1: transition program snapshot is retained but not authoritative

The grounded gait substitution is now rejected: response and canonical gait
parameters come from the packaged input. For a transition, however,
`compiler.py` only hashes `program-profile.json`. It never loads that program
or compares it with the generated `plan.transition_parameters`.

The independent witness retains the real walk-start intent, its exact program
`062bc956067bdbc96ebd2901d5e657f36adf46ae34a126cfcea2aa1f7592b480`, and
the exact steady gait. The positive case passes the production provenance
function. Separate changes to ramp cycles (2 to 3), kind (start to stop), and
anticipation (0.3 to 1.5 seconds) also pass that function. This contradicts the
locked movement request and leaves the transition half of the original
authoritative-program finding open. The witness does not claim a substituted
GLB passed full mechanical verification.

Required narrow closure: load the already packaged transition program with
`load_gait_transition`, compare canonical transition parameters with the plan,
and cover a valid start/stop plus contradictory/missing transition metadata.
This changes provenance validation, not choreography, solving, or thresholds.
Only a narrow diff and witness re-review is required after this P1 fix; no
third whole-branch review round.

Evidence: `shared-set-root-round2-transition-0330d8a/result.json`.

## Closed and retained boundaries

- Program and steady-gait snapshots are retained and independently hash-bound.
  The original grounded timing substitution no longer supplies its own expected
  response. Missing provenance is rejected before the emitted checks.
- Eight unsafe movement names reject through public selection compilation
  before creating output. Six malformed axes reject during resolution.
  Evidence: `shared-set-root-round2-transition-0330d8a/path-axis-closure.json`,
  SHA-256 `3dcbaeb4e881f4e898384b7cf1e3651f0eb16625815c982ba182f763ec545312`.
- Shared source, rig, animal, contact, articulation, frame, calibration, style,
  response and solve-policy ownership remain intact. Intents still cannot
  override these. No new species/movement dispatch or threshold relaxation.
- Legacy recipe defaults remain unchanged. Initial motion-set capabilities
  remain explicitly limited to grounded gait and grounded transitions.
- Author release-head focused suite: 134 pass. Root full mandatory suite is
  running separately on an isolated copy of this exact release head; it is not
  yet a pass. Post-fix source-law preflight retains exact V10 walk equivalence
  and fast native-sample mechanics. Actual new set export remains pending.

Outcome: P0=0, remaining P1=1, new local P2=0. Publication awaits narrow P1
closure, the independent release review, and required verification evidence.
