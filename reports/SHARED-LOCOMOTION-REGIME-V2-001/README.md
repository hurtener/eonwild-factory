# Shared locomotion regime v2 publication checkpoint

This checkpoint publishes the first reviewed shared motion-set resolver for
grounded locomotion and grounded transitions. One versioned baseline owns the
source, rig, animal, contact, articulation, neutral calibration, body style,
locomotion response and solve policy. Portable intents select only their
program and gait timing. Packages retain the canonical resolved recipe and the
exact baseline, intent, program, gait and derived-resolution snapshots needed
to reproduce provenance without the repository.

The reviewed implementation is `58c4f763d3bb1cabd333c4e27ee7a0aabc39d3f3`
(tree `344736c0ef6d4d5cdeb585546b886b4e8b99368b`). Root and reviewer2
closed the final P1 fixes with P0=0, P1=0 and P2=0. Verification replays the
source-owned touchdown geometry from the locked source, rig, animal, contact
and articulation bytes. Generic v2 admission rejects airborne gait until its
separate recovery provider is complete. The shared body response uses the
semantic hip frame and does not invoke the grounded-only axial clock for an
airborne response state.

Release integration `c6abde3020d198657d203f45254d366d5105ca26`
(tree `0724ad419f6c74c3a9ba61c28cbc012716d12cfd`) merges that reviewed
implementation with published `68018cfe7a91abc1812e31ea0afe4065b9e80fa0`.
The retained comparison confirms that both parent deltas are byte-identical.
The merge adds the already-reviewed handoff floor calibration without changing
the v2 implementation.

## Validation boundary

The combined head passed a 195-test fixture/environment preflight plus 11
subtests, then a 96-test merged-path gate. Its complete local invocation reached
**1,122 passed plus 21 subtests and one failure** in 598.12 seconds. The sole
failure was environmental: the sparse checkout omitted the tracked
`Tarbosaurus#walk_side_v02.mp4` reference that `test_animal_instance.py` hashes.
After materializing all 25 tracked `assets/examples` files, the expected and
actual video SHA-256 matched and the entire module passed **13 tests** in 3.05
seconds. The complete invocation remains truthfully recorded as
`FAILED_FIXTURE`; it is not relabeled as a clean full-suite pass. Hosted
validation of published `f24297d` subsequently passed **1,123 tests plus 21
subtests** in 648.92 seconds, and source evidence passed. Other catalog
candidate jobs remain blocked, so this is not an all-catalog green result.

## Connected native review

The actual start, steady walk and stop sequence has completed root-motion side
and three-quarter frame review. Each 19.066667-second H.264 film contains 572
verified frames at 30 fps. Review covered all frames in twelve contact sheets,
eight exact join stills and selected full-resolution frames. Full decode passed,
59 source files remained hash-stable, and no new gross pose or silhouette jump
was found at the four joins.

All four retained connected native views have now completed frame review. This
evidence does not close human native-speed acceptance. The known proximal thigh
fold remains visible. Unity verification currently covers four Tarbosaurus
walk source samples, their actual rendered poses and full skin influences; it
does not cover continuous Animator playback or Allosaurus parity.

## Remaining boundaries

- The Allosaurus shared walk remains BLOCKED. The admitted source still has a
  right loaded-contact residual and early-swing reach failures; no limit or
  authored push-off was weakened to make it pass. Its reviewed provisional
  pedal source preparation is recorded in
  [ALLOSAURUS-PEDAL-SOURCE-PREPARATION-001](../ALLOSAURUS-PEDAL-SOURCE-PREPARATION-001/README.md);
  its engineering pivots are not anatomical approval.
- Shared airborne/sprint admission remains BLOCKED until the separately
  reviewed, source-bound whole-cycle recovery provider closes its review and is
  integrated.
- The user selected Tarbosaurus V10 as the unfinished working baseline. Body
  weight presentation and the proximal thigh skin issue remain open.
- No candidate receives biological approval, Unity parity or production
  promotion from this checkpoint.

The files beside this report retain both narrow reviews, integration identity,
the local fixture-limited test result and closure, and the two completed native
view assessments. Heavy media remains outside Git and is identified by SHA-256.
