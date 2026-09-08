# CUBICSPLINE emitted-tangent Stage A — reviewer 2

- Reviewed head: `b87c591954c5c5f313d22cad334471f825b62b0d`
- Base: `52e826ccd7e05dd2e82c37e889af8cf0a977c7a0`
- Scope: shared emitted TRS reader, normalized Hermite quaternion tangent,
  contact/FK/LBS/handoff/local-loop consumers, and pre-interval fail-closed
  technical authority.
- Result: **one P1, one local P2; no P0**.

## P1 — translation-only CUBICSPLINE can retain technical rate authority

`factory/quality.py:180-186` skips every non-rotation channel before checking
interpolation. It therefore rejects a CUBICSPLINE rotation, but accepts a GLB
whose translations are CUBICSPLINE and rotations are LINEAR. This contradicts
the explicit Stage A boundary in `docs/CUBICSPLINE_EMITTED_TANGENT_STAGE_A.md`
that no CUBICSPLINE package may receive technical PASS before interval-rate and
contact authority exists.

The reproduction builds a translation CUBICSPLINE with equal 10 m/s endpoint
tangents and zero endpoint values, plus a constant LINEAR rotation. The cubic
translation reaches 1.875 m at 0.5 seconds. `emitted_rotation_rates` returns
PASS at 0 degrees/second and `emitted_cyclic_continuity` returns PASS at zero
endpoint mismatch. The compiler's technical conjunction has no other general
CUBICSPLINE interval-rate gate.

Receipt:
`out/cubicspline-stage-a-review-b87c591/translation-only-cubic-rate-authority-repro.json`,
SHA-256 `7d7ca91fc90738641f31b31171884ee033b620a2aa075ad1f188eceb084cb5f3`.

Narrow closure: before Stage B supplies governed interval extrema, scan all
emitted TRS tracks at the compiler-owned rate boundary and reject if any track
uses CUBICSPLINE. Add a mixed translation-CUBICSPLINE/rotation-LINEAR regression
that cannot return rate PASS or complete technical PASS.

## P2 — shared reader accepts invalid animation accessor component types

`glb/animation.py:121-128` validates decoded numeric shape and finiteness but
does not enforce the glTF animation accessor representation. A CUBICSPLINE
sampler whose input accessor is changed from FLOAT to unsigned INT is accepted;
the same bytes are parsed as times `[0, 1073741824]`. A strict emitted reader
should require FLOAT SCALAR inputs and FLOAT outputs with the correct path type,
and reject invalid `normalized` declarations.

Receipt:
`out/cubicspline-stage-a-review-b87c591/invalid-animation-accessor-type-repro.json`,
SHA-256 `2d92d6d0ee90e179993a4f43970c8d047ea7c8703f33b7a79fa072c854458c73`.

This is local P2 because the factory emitter produces FLOAT accessors and the
pinned Khronos validator catches malformed external files in the complete
toolchain. It still weakens standalone reader strictness and is inexpensive to
close through accessor metadata checks.

## Positive evidence

The CUBICSPLINE triplet layout, interval scaling, normalized quaternion
derivative projection, world/FK/LBS product rule, mixed contact sampling,
duplicate/zero/nonfinite rejection, LINEAR byte preservation, and exact-loop
witness path are internally consistent in the reviewed fixtures. The focused
exact-tangent, handoff, adversarial-contact and quality gate ran **81 tests
PASS** in 1.53 seconds. `git diff --check 52e826c..b87c591` passes. The worker
checkout was not modified by this review.
