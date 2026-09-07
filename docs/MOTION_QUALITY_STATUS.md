# V9 motion quality: execution restored, motion review still pending

PR #2 continues the existing engine and approved references. **Quality-01 is
REJECTED**. Technical acceptance, source integrity, native visual review and
Unity parity are separate; none transfers automatically to a newer candidate.

## Executable verification, not an infrastructure blocker

GitHub Actions execution has been restored by the owner. The assistant's local
container and image access remained unavailable; no local recovery directory
was overwritten or declared completely recovered. The earlier partial recovery
receipts remain historical evidence, not proof that all missing parts exist.

The nine legacy integration errors have been traced to **two float32 rounding
values on Linux**. The preserved animation reproduces byte-for-byte on macOS
arm64, including inside Blender. The approved output hash is unchanged:

`b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`

Mandatory full-suite CI now uses that verified legacy toolchain, real Blender
5.2.0 and the real Khronos glTF validator 2.0.0-dev.3.10. Linux independently
compiles and verifies the current V9 candidates. This is an explicit legacy
reproduction boundary, not a claim of universal bitwise floating-point parity.
No test exclusion or approved-hash update was used.

The verified intermediate full-suite run **34074280191**, source
`63cccb285b2fba481568b9241e3c8464d04eaa27`, passed **356 tests and 21 subtests**.
All tests, including real render, promotion, corruption and exact double-build
integration, ran. This intermediate evidence does not replace the final PR-head
check. Read the latest workflow results for the final source status.

## Motion fixes in this continuation

- Separate the ankle/metatarsal from the load-bearing pad frame. Metatarsal
  articulation no longer forces nearly straight toes through unstable IK.
  The pad and all calibrated digits remain in their support frame, with C2
  release and explicit swing flex. No limb translation or scaling is added.
- Declare the pad's own recovery trajectory instead of treating a 55-degree
  metatarsal push-off as a downward pad rotation immediately after lift.
- Center forward walking support around distance traveled DURING stance.
  The old fixed-reach planner remains the default compatibility path; the
  newer program explicitly opts into centered placement. Starts/stops share
  the same placement authority.
- Calibrate forward attention from admitted head-to-upper-rostrum geometry.
  The previous generic axis concealed a roughly 25-degree downward snout.
  This is geometric presentation calibration, not a reconstructed optic axis.
- Plan bounded common pelvis accommodation before supported mouth/leg solving.
  Feeding now loads its braced posture without stretching the trailing leg or
  moving its foot anchor. Feeding v2 admits a feasible initial brace first.
- Bite-miss v2 uses a forward-target posture and controlled closure rather than
  feeding posture and an abrupt jaw snap. Existing rate limits are unchanged.

These are shared, semantic programs and input data, not imports of historical
builders. The approved GLBs, legacy capsules and reference hashes are unchanged.
All exact staging helpers and diagnostic-only workflows are excluded from the
active PR tree. Read-only diagnostic commands do not publish or repair motion.

## Measured intermediate candidates

These measurements describe the indicated actual outputs, not ungenerated
final-head promises. Subsequent changes must regenerate and revalidate them.

| Candidate | Actual technical result | Evidence run |
|---|---|---|
| walk.v3, before independent pad recovery | PASS; 2.165 m root-relative foot stroke, 1.289 m/s travel, 0.634 m foot-root gauge; ankle interior range about 62/68 degrees | 34075285131 |
| reverse-walk.v4, before independent pad recovery | PASS; 1.462 m stroke, -1.004 m/s travel, 0.634 m foot-root gauge | 34075285131 |
| feeding.v2 | PASS; fixed foot contact, oral anchoring and unchanged joint/rate limits | 34074559443 |
| bite-miss.v2 | PASS; peak 195.49 degrees/s against the unchanged 360 limit; actual side/three-quarter videos rendered | 34072825372 / 34073556706 |
| idle.v1 / alert.v1 / call.v1 | PASS on the inspected earlier catalog source | 34071484802 |
| run / sprint / transition catalog | Remaining motion feasibility or acceptance work; do not promote | Latest per-recipe CI |

Large articulation numbers do not by themselves establish natural movement.
The current walking performance must be compared visually against V9 before
replacing an approved take. Native-time review is required, not optional.

## Preserved V9 walking comparison

```
build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb
SHA-256 b54e3740ea451927b3b812c1be3f4ca6146cc369ad1313be7f08edd5ca741cd3
Clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION
```

The inherited clip name does not change the identity of this V9 artifact.
Read-only native measurements (run 34073669963) establish a 2.073/2.088 m
root-relative foot stroke and 1.281 m/s mean travel. Its foot-ROOT gauge is
about 0.876 m; do not confuse a directory's numeric sweep setting with this
measured geometry quantity. No reference is retimed, repaired or copied into
a factory generation recipe.

## Reproduction and review

```sh
uv run python -m pytest tests -q --tb=short
uv run python tools/verify_catalog.py --recipes walk.v3 reverse-walk.v4 \
  --output out/walking-candidates
uv run python tools/review_compiled_candidate.py \
  --package out/walking-candidates/walk.v3 --output out/walk-review \
  --views side front rear three-quarter --fps 30 --compare-v9-walk
```

The review command compiles nothing. It renders the same immutable package,
verifies it before and after, shares reference-first camera locks per view,
and records each clip's own native timeline. Separate candidate jobs retain
real failures without allowing a slow transition to hide the whole catalog.

## Still required before ready/merge

Pass the complete final-source suite and all requested current recipe gates.
Finish run/sprint reach and transition handoff, inspect real multi-view motion,
and bind decisions to exact output hashes. No random noise, lowered floor,
dropped seam witness, changed approved hash or looser acceptance bar can
substitute for those requirements.

**PR: draft. Visual approval: PENDING. Unity validation: NOT_RUN.
Production promotion: NOT_GRANTED.**
