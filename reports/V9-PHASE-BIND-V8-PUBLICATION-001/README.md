# Phase-local seam plus V8 bind-pose publication

Status: **LOCALLY VERIFIED CANDIDATE INTEGRATION; NOT A MOTION APPROVAL.** This
publication combines the non-emitting phase-local airborne row seam with the
already-reviewed V8 bind-pose admission work. It adds no CUBICSPLINE emitter,
new acceptance mode, gait tuning, threshold change, visual decision, Unity
result, or production promotion.

## Frozen integration

Publication base: `424644e1b3ac184a03c64fc661786a1e2ab1a68b`.

The phase-local seam is retained from the preserved branch heads
`e6c0b6f6daefba490305a79722ebb1644ffd1a41` and
`79bc9f9cab6e3aebbae9e1aeb6e90324de4371e5`, first publication head
`b3b0b4201bb14e66dfa379de2e4b76353ded0526`. It evaluates one existing,
already-planned airborne row into local TRS and existing witnesses before
serialization; it is not arbitrary-time planning or source-tangent authority.

The bind-pose work is applied from exactly these preserved commits:
`0a6ca91`, `7d3945b`, `16aab62`, `1b5a13e`, `2d6b5e6`, `ef1c305`,
`4fc8c9c`, and `74ba50c` (reviewed source head `4fc8c9c`). It strictly
recovers neutral skin-aligned geometry from inverse-bind data, binds the adult
V8 recipe, and validates malformed accessor inputs fail closed. Its two full
reviews and narrow P1 closures remain in
`reports/V9-ADULT-BIND-POSE-V8-001/`.

The phase seam's four verbatim review receipts remain in
`reports/V9-PHASE-LOCAL-SOLVED-POSE-001/`. Its residual P2 is explicit:
`ArticulationProfile.support` and `.swing` are caller-owned mutable maps and
must be snapshotted before a future retained external source-motion query. It
does not affect immediate full-clip generation.

## V8 rebuild and existing films

The V8 recipe was freshly compiled from this combined source into the new
external-SSD path `out/phase-bind-v8-regenerate-788e213`. The regenerated
root-motion GLB is byte-identical to the immutable package at
`d0ca24b7738517804f525c7261d5dcbc0790b94479915ba1251250cd76433d37`; the
in-place GLB is byte-identical at
`b9f8f18f2508132bf3a78c900d6f4c8addc380f4d65c0c81751fd5a3016a3579`.
All payload files other than source-provenance `inputs.lock.json` and its
manifest entry are also byte-identical. The original manifest is
`a8b5b1d82b98d6e3579e4aec2e2ac15eec3f0baa9c0cb42ea4ff734dc15b88d3`; the
rebuild manifest is different only because it records the current source
hashes for `factory/source.py`, `glb/cubic_bounds.py`, and
`solve/airborne_gait.py`.

The existing V8 review films therefore remain valid evidence for the same
emitted GLBs; no rerender was needed. This does not change their status:
technical **BLOCKED** by the unchanged exact local linear loop limit, visual
**PENDING**, Unity **NOT_RUN**, and production approval false. Static evidence
alone does not establish walking deformation. The recorded 370-frame review
found bilateral geometry improved and still required whole-body polish and jaw
calibration; native-speed playback remains pending. No COM, force, biological,
or mass-response claim is made.

## Combined local validation

At exact code head `f267c9671f4eedadc91888b21685b0f74eb0e08d`, the mandatory
suite passed **844 tests plus 21 subtests** in **218.63 s**, using real Blender
5.2.0 LTS and checksum- plus smoke-verified Khronos glTF Validator
2.0.0-dev.3.10. The JUnit has 844 testcase elements and zero failures, errors,
or skips. Receipt hashes and the two setup-only attempts are in
`validation.json`; no test was run in either setup-only attempt.

The first setup-only attempt exited 126 because the checked-in Khronos helper
lacks an executable bit when called directly. The second ran the helper through
`bash`, passed its archive checksum and smoke, then stopped before pytest when
a manual post-smoke validator probe named a fixture the helper had removed.
The final retry reused the verified validator and completed the suite. These
are preserved command/environment outcomes, not test failures.

Hosted CI for base `424644e` is not green. A compact read-only receipt records
two completed jobs only: adult V7 is blocked at its governed exact local
linear-loop limit, and a V6 native review rendered successfully but exited 2
because its candidate remains technically blocked. The wider workflow was not
complete, so no claim about its remaining jobs is made.

There is no push, merge, automatic approval, native playback approval, Unity
parity result, or source-motion/CUBICSPLINE admission in this publication.
