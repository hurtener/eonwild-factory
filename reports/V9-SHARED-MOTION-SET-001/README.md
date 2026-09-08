# V9 shared animal motion set

## Publication boundary

This report records the shared motion-set implementation generated at
`62e4b60a399672fc68f9817aeabc6bff8c300912` (tree
`bf814e4536ece37d963f35cdc8693f3feba4b09c`) and its verifier-only JSON
representation closure at final source head
`1cc88b0b1669764421da1ef11cd48aa6ca9bbd08` (tree
`a33800102d942652841d4863477f2e8d8f8866a7`). It adds a reusable configuration
and verification path; it does not select a new emitted clip or change legacy
recipe output by default.

The adult V10 walk remains the user-selected working baseline. Its frozen source
and source-law fingerprints are recorded in
`evidence/published-v10-source-reference-945b189.json`. Existing historical
packages, approved references, and the SSD review gallery remain unchanged.

The first actual fast-walk package resolved through this shared baseline is at
`ARC/out/adult-fast-shared-baseline-cubic-001/fast-walk`. Generation at
`62e4b60` completed its recorded emitted gates, but the command returned exit 1
because tuple/list representation differences caused a false-negative provenance
comparison; `evidence/fast-initial-verification-failure-62e4b60.json` preserves
that event. The verifier-only `1cc88b0` closure reopens the unchanged package as
integrity **PASS** and technical **PASS**. The source-bound renderer produced 48 decoded native-time frames in each of
the true-front and side views, with all 156 tracks evaluated by the exact CUBIC
adapter. Root inspected all 96 fast frames and eight phase comparisons per view
against V10. The result is **READY_FOR_USER_REVIEW**: no obvious new rupture,
floor penetration, upward-facing head, or unilateral tail protrusion appeared,
but the front tail remains occluded and native interactive playback was not
performed. Visual approval remains **PENDING**, Unity parity **NOT_RUN**, and
production approval false. See `evidence/fast-final-result.json`,
`evidence/fast-render-validation.json`, and the root frame assessment.

## One baseline, four intents

The motion set
`catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json` binds one
baseline snapshot, then resolves four named intents:

| Entry | Program | Intent-owned input |
| --- | --- | --- |
| `walk` | `grounded_gait` | adult walk gait program |
| `fast-walk` | `grounded_gait` | adult fast-walk gait program |
| `walk-start` | `gait_transition` | start program plus bound steady walk gait |
| `walk-stop` | `gait_transition` | stop program plus bound steady walk gait |

The shared baseline owns the source asset, semantic rig, animal instance,
contact profile, articulation limits, coordinate frame, neutral-pose
calibration, performance style, gait-response policy, and solve policy. Intent
files cannot silently override those fields. Calibration, authored style, and
solver policy remain typed and separate. The initial admitted program set is
only `grounded_gait` and `gait_transition`; unsupported capabilities and
representations reject before solving.

The reference-gait response is authored kinematics derived from the bound steady
gait. It is not measured dynamics, biological force, mass, or center-of-mass
evidence.

## Provenance and compatibility

Every selected package retains package-local snapshots of the resolved set,
baseline, intent, performance style, neutral calibration, program profile, and
transition steady-gait profile when applicable. Those snapshots carry hash
bindings to the admitted geometry, rig, animal, contact, articulation, and other
source dependencies; the dependency bytes themselves are not all embedded.
Package-local verification therefore checks the resolved configuration and
rejects drift in authoritative gait or transition parameters, but does not
promise standalone source recompilation without the hash-addressed dependencies.
Movement names are confined to safe output components, malformed
axes reject, connected schedules and handoffs require the same shared baseline,
and legacy recipe compilation stays on its existing path.

The published V10 reference capture at `945b189` binds source
`2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`,
recipe `1f5d4dee6bdf224db2082878112c777e5d01c7605d512e0e9006198eff7244be`,
and 297 native plan rows. The generator-head `62e4b60` preflight independently
matches all 14 declared source probes, all 297 plan rows, and the effective
performance values to that capture. Its fast-walk native-grid source law checks
193 samples and passes the declared geometry, contact, articulation, and rate
bounds. This is **NON-EMITTING** preflight evidence; it is not a CUBICSPLINE
interval result, visual review, Unity transfer, or production approval. See
`evidence/final-source-preflight-62e4b60.json`, SHA-256
`e0b40a4ac511a5f72ef4bea99cd6b9d74fd8d043cf0d31787614905a2b4c738c`.

## Review closure

Round 1 at `38f14dd` found one P1: package-local verification trusted generated
gait parameters rather than the bound program/gait snapshot. It also found
local P2 issues in output-name confinement and strict axis typing. The combined
fix at `0330d8a` closed those cases.

Round 2 found the remaining transition half of the same provenance P1: the
retained transition program did not govern `plan.transition_parameters`.
Exceptional narrow head `62e4b60` loads that program with the production loader
and requires equality with its canonical transition mapping. Root and reviewer
2 independently closed the actual start/stop positive cases and the altered
kind, ramp-cycle, anticipation, and missing-parameter negatives.

The first real fast package then exposed a verifier false negative: persisted
JSON arrays were compared against reassembled Python tuples even though the
values were equal. Final verifier head `1cc88b0` canonicalizes the expected
performance through the existing JSON encoder before exact comparison.
Root independently verified the focused persisted-plan cases. Join and
reviewer 2 independently ran the public verifier on the preserved real fast
package; both received integrity and technical `PASS`. Final review status is
P0=0, P1=0.

## Validation accounting

- Complete mandatory suite on complete implementation checkpoint `0330d8a`:
  **1,045 tests plus 21 subtests passed**, no exclusions, using the real
  toolchain. Result receipt:
  `evidence/full-suite-0330d8a.json`; test log SHA-256
  `ce6703fa4f2b8d2b15115e7727e2921ff4115902d988ad9211133d1bdcd25aee`;
  JUnit SHA-256
  `4998d4361a54d324e1f452858356e21915586389180d04a22579263d4c017848`.
- Final `62e4b60` narrow author gate: **29 passed**.
- Final root motion-set/gait-response gate: **46 passed**.
- Final independent exact transition regression: **2 passed in 1.75 s**.
- Verifier-only `1cc88b0` author gate: **29 passed**; root persisted-plan gate:
  **3 passed**; reviewer-2 focused gate: **1 passed in 1.10 s**.

The complete suite was not repeated after the narrow `62e4b60` and `1cc88b0`
verifier changes; that difference is stated rather than folding focused results
into the full-suite claim. The earlier reviewer-2 real export attempt at `0330d8a` was
interrupted
and produced no package; it remains `NOT_COMPLETED`.

## Transition preflight boundary

The actual start and stop configuration bindings resolve, but their retained
`62e4b60` source-law preflight is **BLOCKED** because sampled swing-clearance
requirements are unavailable at listed times. The receipt is explicitly
**NON-EMITTING**: no transition GLB, serialized interpolation, connected film,
visual result, or join acceptance follows from it. See
`evidence/transition-source-preflight-62e4b60.json`.

## Current limits

This stage does not establish that every movement is ready, grant visual or production approval to the
fast-walk output, alter the published V10 movie, validate Unity consumption, or
claim physical/biological correctness.

The point-in-time `945b189` CI triage records contracts and source-evidence
success. Its sampled legacy LINEAR walk, fast-walk, and sprint candidates were
technically **BLOCKED** by their distinct exact cyclic-linear results; the walk
pair timed out after its packages reopened but before a join result; the sampled
native job rendered successfully and then returned exit 2 for technical
BLOCKED. See `evidence/ci-triage-945b189.md` and its exact JSON receipt. These
historical states are context and are not reclassified by this configuration
work.
