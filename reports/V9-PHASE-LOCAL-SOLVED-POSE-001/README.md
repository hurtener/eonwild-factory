# Phase-local solved-pose seam

Status: **INTEGRATED AND LOCALLY VERIFIED; NOT AN ARBITRARY-TIME OR EMISSION
AUTHORITY.** This is a bounded extraction of the existing airborne plan-row
solve. It does not change an animation recipe, profile, sample clock,
serialization, threshold, candidate package, visual decision, Unity state, or
production approval.

## Integrated source

Publication base: `424644e1b3ac184a03c64fc661786a1e2ab1a68b`.

The preserved implementation heads were:

- `e6c0b6f6daefba490305a79722ebb1644ffd1a41`: initial extraction from
  `cc7b3d9e199d1679d28bbcbefb61bcea5407b129`.
- `79bc9f9cab6e3aebbae9e1aeb6e90324de4371e5`: bounded immutable-context
  postfix.

They are integrated on this publication branch as `69a328968a30ea33a645dba666695cbc392759c5`
and `5da9b609da9725caccf243e66666179f9621307e`. The original seam branch is
preserved separately.

## API and boundary

`solve_airborne_plan_sample(AirborneSolveContext, row,
body_response_sample=...)` evaluates one already-planned sample into local TRS
and the existing skeletal foot/contact/articulation witnesses. The existing
`solve_airborne_gait` loop still selects body-response samples in its existing
order, calls the row solver, applies quaternion sign continuity, serializes
once, and reopens the generated GLBs through the existing checks.

The retained context snapshots source topology, roles, plan and geometry arrays
into detached read-only values. Direct malformed row/body-response payloads
fail as `ContractError`. This stage does **not** expose arbitrary-time planning,
source tangents, CUBICSPLINE emission, float32 interval authority, FK/LBS
between-key contact extrema, continuous skin refinement, a new acceptance flag,
or a visual/Unity approval.

## Exact preservation and review

The test suite pins the real heavy-biped complete payloads to root-motion
`b806d588964d0ad8d4ef9bcea3c567a30f1cd9b65888b6cb1ccb859080e9a417` and
in-place `fa7cb0e645b9a0d3c09bb9d07260713448b99d6bb0d2889d8870c76c2080a880`.
It separately pins a renamed, frame-transformed fixture and checks row-order
independence, caller mutation isolation, nested write rejection and rejected-row
safety.

Two bounded independent review rounds are preserved verbatim here. The final
round reports no P0/P1. Round-one P2 findings for shallow context, direct input
exceptions, and the moved source-level safeguard were closed by the postfix.

## Residual P2 debt

`ArticulationProfile` remains a caller-owned shallow-frozen object in this
bounded seam. Its support/swing maps can be mutated after context capture, so a
future retained `SourceMotionQuery` or arbitrary-time stage must snapshot its
engineering guardrails before exposing repeated external queries. Immediate
full-clip generation is unaffected. This P2 is recorded under the review cap;
it is not silently treated as resolved.

## Local full-suite evidence

At exact code head `5da9b609da9725caccf243e66666179f9621307e`, the complete
mandatory `tests` directory passed **813 tests plus 21 subtests** in **302.67 s**.
The JUnit has 834 testcase elements, 0 failures, 0 errors and 0 skipped. The
run used the pinned uv environment, real Blender 5.2.0 LTS and a checksum- and
smoke-verified Khronos glTF Validator 2.0.0-dev.3.10. No exclusions were used.
The external-SSD receipt paths and hashes are in `host-validation.json`.

Two setup-only attempts are preserved in that receipt. The first stopped before
pytest because this desktop shell lacked a bare `python` executable for the CI
setup helper. The second successfully installed and smoke-tested Khronos, then
stopped before pytest because a manual stdout invocation supplied an extra path.
The successful retry reused that verified binary and completed the unchanged
full suite. These are environment/command setup outcomes, not test results.

Hosted CI at base `424644e` was observed as not green while jobs were still
running. This report does not attribute a cause and does not treat the local
suite as hosted CI success.

There is no new native render for this byte-preserving seam. Existing visual
and Unity decisions remain unchanged and pending where previously pending.
