# CUBICSPLINE B1 source interval primitive

Status: **PURE HELPER INTEGRATED; NON-ADMITTING; CURRENT MOTION UNCHANGED.**
B1 supplies conservative source-side binary64 bounds for one Hermite interval.
It does not emit CUBICSPLINE animation, alter a recipe or threshold, or remove
the factory's CUBICSPLINE technical block.

## Bounded result

The helper converts finite Hermite values and tangents to Bezier control
intervals using directed binary64 arithmetic. Componentwise control hulls bound
vector values and the global quadratic derivative. Quaternion value controls
are subdivided only to prove that at least one component remains separated from
zero on every leaf. That component separation supplies a conservative raw-norm
lower bound. The global derivative norm and the directed ratio
`2 * upper(|qdot|) / lower(|q|)` supply a conservative normalized-quaternion
angular-speed upper bound.

Arithmetic overflow, a divisor spanning zero, malformed values, and depth or
node exhaustion reject with `ContractError`. Underflow is enclosed by the
directed predecessor/successor around signed zero. Public nominal Bezier
controls are diagnostic values; the returned interval endpoints are the
authority.

The source and pipeline boundary are
[CUBICSPLINE_B1_SOURCE_PIPELINE.md](../../docs/CUBICSPLINE_B1_SOURCE_PIPELINE.md).
Original commits `d18de689a10f81e8f1a1cb0fd3cd2c8c5fa5431f` and
`50aa941b016566945455e7dccd229e35570ba44f` were integrated onto published
source `cc7b3d9e199d1679d28bbcbefb61bcea5407b129` as
`f67a75a0fd2f42eee2cfb73f34706f8cb903b920` and
`003504af55657562e95d5a560e70812913893330`.

## Two-round review

Round one found that a fixed 64-epsilon envelope did not prove a conservative
bound after repeated subdivision, and that large integer conversion leaked
`OverflowError`. The postfix replaces the heuristic with directed intervals,
uses the global derivative hull rather than rescaled leaf derivatives, and maps
conversion overflow to `ContractError`.

Both round-two reviewers found no remaining P0/P1. Exact-rational corroboration
covered thousands of vector controls and derivative hulls, hundreds of
quaternion norm/rate samples, subdivision paths through all 40 allowed levels,
and a nonzero proof requiring depth 30. The retained receipts are:

- `review-independent-round1.md`: SHA-256
  `5365e753bce431e441dec7b548e06e09354d44fbd9b05eaa3dca9be7f5cb6948`
- `review-independent-round2.md`: SHA-256
  `6943072c8f513cd1a832798dd92b27d8b211de91dbf1f3d7c00ce0af6294dabe`
- `review-root-round1.md`: SHA-256
  `7a1f4fc29294a18b9bc2331370f33232136ad4e769fa049a513b648388fc56c8`
- `review-root-round1.json`: SHA-256
  `5fa7a7f32b0a985a90c2c5a85b51567d6a35f149a695826d1b90afb4c11d64d2`
- `review-root-round2.md`: SHA-256
  `ae5bfdd288094f7e1ef8afda1b15d6360408353836b8d2608584311e40ef1b99`
- `review-root-round2.json`: SHA-256
  `41f62610861a8226999b8521074b36b0e725a1e84a33f226634034a9619ebda7`

## Integration verification

The tested code head `003504af55657562e95d5a560e70812913893330`, tree
`37e7fd457193ec67409c9e1719531582f823245a`, passed the complete mandatory
suite: 808 tests plus 21 subtests in 230.51 seconds. It ran from a full external
SSD checkout with external temporary storage, real Blender 5.2.0 LTS, and
Khronos glTF Validator 2.0.0-dev.3.10. There were no exclusions.

`host-validation.json` records the exact source, tree, command, tool, log and
JUnit identities; its SHA-256 is
`e9b0d6d5899c4cbb034f3fe9da245029f2335fccc6af7037fe212766bfce881a`.
The test log is SHA-256
`a5adf2620615df9882dffee9f78fbbd53a68191912fb0ecf4fd17b5926abca2a`;
JUnit is SHA-256
`e5b65451744b3ff417f425eb6348052bad34fa8f243178047efc72786cd9f4ab`.

B1 is not called by current generation or package admission, so no v7 package,
render or prior visual receipt is superseded. Exact float32 export binding,
continuous source pose/tangent generation, interval FK/LBS/contact/articulation
authority, and a CUBICSPLINE emitter remain future stages. Unity parity is
`NOT_RUN`, hosted CI for this publication descendant is pending, and production
approval is false.
