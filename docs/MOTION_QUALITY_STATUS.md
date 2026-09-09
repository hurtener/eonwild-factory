# Motion quality: shared baselines, candidates and joins have separate gates

PR #2 continues the existing engine and approved references. **Quality-01 is
REJECTED**. Technical acceptance, source integrity, native visual review and
Unity parity are separate; none transfers automatically to a newer candidate.

## Current integration checkpoint

The latest [source CUBIC refinement checkpoint](../reports/SOURCE-CUBIC-REFINEMENT-001/README.md)
closes the reverse-walk between-key ankle undershoot with one source-derived
key and unchanged limits. The exact integrated release package verifies PASS
and has identical animation bytes to the independently reviewed candidate.
Both code reviews and narrow immutable-cache correction reviews are closed.
Root inspected 120 side/front frames; native-speed user and Unity acceptance
remain open. Reverse starts/stops and their actual direct joins are still
separate, unfinished acceptance requirements.

The preceding [shared reverse-intent checkpoint](../reports/SHARED-REVERSE-INTENT-001/README.md)
records signed/fixed-placement resolution through the same adult baseline and
the retained rejected diagnostic. Its historical failure is superseded only
by the later source-bound steady package above.

The shared locomotion regime v2 implementation at
`58c4f763d3bb1cabd333c4e27ee7a0aabc39d3f3` passed both bounded closure
reviews with no remaining P0/P1/P2 finding. Combined head
`c6abde3020d198657d203f45254d366d5105ca26` adds the published handoff
floor calibration with both parent deltas byte-identical. Its local complete
invocation reached **1,122 tests plus 21 subtests passed and one missing sparse
fixture**. Materializing the tracked reference media closed the entire failing
module at 13/13, but the original complete run remains `FAILED_FIXTURE`; hosted
validation at published `f24297d` subsequently passed 1,123 tests plus 21
subtests in 648.92 seconds and source evidence passed. The wider candidate
catalog still has blocked jobs. See the
[shared-regime checkpoint](../reports/SHARED-LOCOMOTION-REGIME-V2-001/README.md).

The provisional Allosaurus source has explicit joint relocations, effector
endpoints, bounded scale normalization and complete eight-influence admission.
Its first actual walk is **REJECTED**: the unchanged body-height-relative intent
places touchdown 44.993 mm beyond the provisional limb's reach. The equivalent
Tarbosaurus configuration has 154.203 mm of reach margin. This is evidence for
shared morphology-aware intent resolution, not permission to stretch bones or
increase correction limits. The first shared-v2 resolution still blocks on the
right loaded-contact residual and early-swing reach. Hand/pedal detail, hip
placement and anatomical approval remain unfinished. The reviewed provisional
weighted pedal source and its raw/admitted identity boundary are recorded in
[ALLOSAURUS-PEDAL-SOURCE-PREPARATION-001](../reports/ALLOSAURUS-PEDAL-SOURCE-PREPARATION-001/README.md);
this source preparation does not pass the gait.

The user selected V10 walk as the unfinished working baseline; shared fast walk
remains its current fast comparison, with the confirmed
proximal thigh surface intersection still open. The sprint component-selection
prototype is rejected: it moves the discontinuity earlier and still exceeds
15,000 degrees/s of solved foot pitch. No rejected sprint pose replaces either
walking baseline. The full walk-start and walk-stop exports record technical
PASS, and both actual start-to-steady and steady-to-stop handoffs pass.
All four connected native views completed frame review without a new gross join
discontinuity. Human native-speed acceptance remains pending and the known
thigh fold remains. Unity verification covers four Tarbosaurus walk source
samples, their actual rendered poses and full skin influences, but continuous
Animator/runtime and Allosaurus parity remain pending. The start handoff had exposed an
unscaled-versus-animal-scaled floor comparison in
the verifier. The reviewed fix at `1f783f8` reuses the compiler's bound animal
calibration without changing floor equality or join limits. The author's actual
start-to-steady replay and independent root replay pass both modes.
The [start/handoff report](../reports/V9-SHARED-GROUNDED-START-HANDOFF-001/README.md)
records exact identities, complete side-frame coverage and remaining concerns.
The combined source `12677c17d8b756fdc2be99fb1cce1243f5b29e87` passes 1,081 tests
plus 21 subtests in 517.84 seconds, with no exclusions. Its hosted contracts
and source-evidence checks pass.

The wider current hosted workflow still has candidate failures. At preceding `5fe4c17`,
contracts and source-evidence passed, while legacy candidate/transition and
native-review jobs still failed. No all-catalog green result, Unity parity,
biological approval or production promotion is claimed. PR #2 remains draft
and must not be merged.

## Current source and workstream

The 2026-09-07 continuation fetched PR #2 at
`5475b6988ad5c82b1f5a56415a075f36d0e58dc0`. Baseline CI run
34137687969 passed all 18 individual candidates, but sprint, run and walk
transition pairs failed velocity checks. Reverse-walk passed its pair checks.
Several one-shot previews also failed the FBX transport-clock admission. These
are baseline results, not acceptance of the later implementation.

The continuation corrects native preview/FBX clock transport and camera framing,
adds actual source-bound connected rendering, removes the gaze controller's
unwanted absolute-world upward correction, and adds the explicit adult animal
benchmark below. The authored sprint retains its stride, cadence, flight and
contact policy. The user has authorized evidence-bound reassessment of inherited
articulation limits; no limit change is accepted merely to make a candidate
feasible. See
[HINDLIMB_ARTICULATION_EVIDENCE.md](HINDLIMB_ARTICULATION_EVIDENCE.md) for the
current evidence and angle conventions. Raw direct-join limits remain unchanged.
Under the historical quadratic finite-difference estimator at exact local source
`7920c59dd354027b8784483bb208fd0e6229cd91`, walk, reverse-walk and run pass
both direct joins in both movement modes; sprint remains `BLOCKED` in both.
See [TRANSITION_INTEGRATION.md](TRANSITION_INTEGRATION.md) and the
[exact-source pair report](../reports/V9-NATIVE-CLOCK-PAIR-STATUS-001/README.md).
The later final evidence set independently reopened the twelve retained pair
packages and re-ran that estimator: walk, reverse-walk and run remain `PASS`,
while sprint start and stop remain `BLOCKED`. See the
[final continuation report](../reports/V9-CONTINUATION-FINAL-4AE0FE9-001/README.md).

The host has inspected every native frame of the baseline sprint and the corrected
side preview. Upward craning is corrected. The aggressive sprint's persistent
crouch, compressed neck presentation and recovery folding remain motion-quality
concerns; correcting gaze does not approve the full sprint. The host also inspected
all 74 native review frames of the adult grounded walk in side, three-quarter and
foot-close views, verified full media decode and hashes, and exercised native 1x
browser playback. Forward head posture and recovery clearance are visible; the
fairly flat foot release remains a qualitative comparison concern. This is an
inspection record, not human art-direction or biological approval.

The subsequent adult-only profile polish increases distal articulation and delayed
tail response. It passed isolated compilation and focused checks, but the user
identified that its recovery foot moves in the opposite direction to the walking
reference. The host confirmed this and withdrew its initial positive assessment:
the foot tucks upward/forward instead of hanging down beneath the flexed knee.
That recovery polish is visually rejected and is being corrected. Technical
checks did not establish reference alignment. A later downward/trailing-foot
probe was also rejected for a pinched ankle and rigid hanging foot. Coordinating
the metatarsal, pad and toes improved that fold, but full-cycle host inspection
rejected its 0.20-height-clearance version for floor-skimming recovery. The
current correction therefore requires both coherent joint motion and visible
material clearance throughout swing. The supplied `assets/examples`
videos have now been audited
directly, including every native frame and original-speed playback of five key
walking, sprint and start/stop references, plus the complete walking clip used
in the user's recovery comparison. See
[EXAMPLE_VIDEO_REVIEW.md](EXAMPLE_VIDEO_REVIEW.md) for exact coverage, source
identities, observations and the remaining candidate gaps.

## Current adult recovery candidate

`tarbosaurus-pin-552-1-adult-walk.v3` is now the current factory recovery
candidate. It supersedes v2 for future candidate CI without rewriting the v1/v2
recipes, assets, tests or receipts. The reusable solve uses a common
world-metatarsus recovery target, geometry-derived bilateral hip lane centering
and a hash-bound scalar articulation guardrail. The profile records its
comparative-anatomy basis and uncertainty; it is not measured Tarbosaurus range
of motion or biological certification.

The immutable one-cycle package passed independent package verification and all
unchanged technical gates. Reopened final skin retained 35.214 mm left and
40.603 mm right minimum full-patch clearance through the interior recovery
window. These final values are lower than the pre-refinement raw solve values
and are the applicable material evidence.

The host inspected all 444 frames across six native 30 fps films, twelve
exact-time side and three-quarter stills, complete contact sheets, and complete
original-speed browser playback of all six views. The revised recovery retains the intended trailing-to-forward progression, avoids the
rejected compressed ankle, keeps the thigh coordinated, and shows no leg
crossing or abrupt lateral sway. This
accepts v3 as the revised factory candidate only. User art-direction approval,
biological validation, Unity parity and production promotion remain pending.
The complete review page is
`out/continuation-adult-v3-world-recovery-001`; the tracked structured receipt
and summary are in
[reports/V9-ADULT-RECOVERY-V3-HOST-001](../reports/V9-ADULT-RECOVERY-V3-HOST-001/README.md).

The v6 body-response diagnostic is
`tarbosaurus-pin-552-1-adult-walk.v6`. It preserves v3's leg, contact and
articulation inputs and v5's support-directed lateral response, then adds a
modest support-timed pelvis pitch with opposing distributed trunk, neck and
tail response. The host inspected all 370 rendered frames across five
native-time views and completed all five paired v5/v6 native-speed playbacks.
Coordination improves without losing recovery clearance or gaze, but constant
forward travel and body effort remain too even for the requested several-ton
presentation. Its status is **WHOLE_BODY_POLISH_REQUIRED**. This is authored
kinematic response, not a center-of-mass, force, inertia or mass simulation.
User art-direction approval, biological validation, Unity parity and production
approval are absent. See
[reports/V9-ADULT-SAGITTAL-RESPONSE-V6-001](../reports/V9-ADULT-SAGITTAL-RESPONSE-V6-001/README.md).
The v5 Candidate B report remains a historical diagnostic.

The v7 body-response review candidate retains v6 and adds a periodic
support-timed pelvis-forward speed carrier with zero net travel. The host
inspected all 370 rendered frames across five native-time views and completed
all five paired v6/v7 native-speed playbacks. The motion shows a modest
travel-rhythm improvement and preserves the recovered leg behavior, but the
body response remains too subtle for the requested several-ton presentation.
Its status is **WHOLE_BODY_POLISH_REQUIRED**. The current exact local-loop gate
is `BLOCKED` at `3.2116449766123154 mm/s` against the unchanged `1 mm/s`
limit. This remains authored kinematics without force, COM, inertia or mass
simulation. See
[reports/V9-ADULT-SUPPORT-SPEED-V7-001](../reports/V9-ADULT-SUPPORT-SPEED-V7-001/README.md).

The latest combined review candidate is
`tarbosaurus-pin-552-1-adult-walk.v9`. V8 preserves the recovered, skin-aligned
bind geometry; v9 keeps its gait, legs, contacts, articulation, root travel and
configured amplitudes while enabling the reviewed support-timed axial clock and
neutral-jaw calibration. The host inspected all 370 rendered frames across five
byte-identical camera locks and found the bilateral recovery and support-timed
chest carriage visible, with no gross mesh rupture or adjacent-frame body jump.
Native-speed playback remains `PENDING_MAC_UI_LOCK`, so perceived weight is not
accepted. The exact emitted LINEAR translation loop remains `BLOCKED` at
`3.23101227406632 mm/s` against the unchanged `1 mm/s` limit. This is authored
body timing; mass physics, measured force, Unity parity and production approval
remain unavailable. See
[reports/V9-ADULT-AXIAL-JAW-V9-001](../reports/V9-ADULT-AXIAL-JAW-V9-001/README.md).

The exact integrated source `5304b1967ad350737cf7e9ee6555a5f4de9e9bff`
passed 658 tests plus 21 subtests in 225.75 seconds. The new adult v3 catalog
binding test then passed at exact source
`7809ada9743818e860e096ffb38ddba3488a7d9b` in 0.26 seconds.

Adult fast-walk recovery v3 is the current bounded fast-cadence diagnostic. It
preserves the 1.6-second cycle, stride, duty, clearance, world-metatarsus target
and articulation guardrails while replacing the onset/return recovery envelope
with an opt-in rate-limited C2 carrier. The host inspected all 192 frames across
four native views and completed four native-speed playbacks. The distal
recovery improves without the earlier pinched ankle, floor skim or lateral
crossing. Its older body profile remains level and even, so the status is
**WHOLE_BODY_POLISH_REQUIRED**; it is not the adult benchmark and has no
biological, Unity or production approval. See
[reports/V9-ADULT-FAST-WALK-RECOVERY-V3-001](../reports/V9-ADULT-FAST-WALK-RECOVERY-V3-001/README.md).

The pre-evaluator combined source
`30f434ce914b6392f1438f0ff234718c82d2e985` passed 749 tests plus 21
subtests in 502.90 seconds with the pinned real Blender and Khronos tools.
Both new recipes are retained alongside adult v3, body diagnostic v5 and generic
fast-walk v2 in candidate/native CI matrices.

The exact emitted-tangent evaluator is integrated at source
`61c7ffc99ac2c5166345c5b690328c55bce2aefd`, which passed 758 tests plus
21 subtests in 211.81 seconds with the same real tools. It measures actual glTF
LINEAR/SLERP endpoint slopes. Generic joins and local steady loops, adult v6
and fast recovery v3 are blocked where those measurements exceed unchanged
limits. See
[V9-EXACT-EMITTED-TANGENT-001](../reports/V9-EXACT-EMITTED-TANGENT-001/README.md).

The current combined code and CI head
`3b1f55602ba2d8d177c42ec15ccb02d401f92b7d` adds the strict shared
CUBICSPLINE-capable TRS reader and selects adult v7 alongside its historical
body diagnostics. The complete mandatory suite passed 788 tests plus 21
subtests in 237.65 seconds with real Blender 5.2.0 and Khronos glTF Validator
2.0.0-dev.3.10. Stage A is consumer-side validation only: no CUBICSPLINE
emitter or interval-rate authority is included, and current motion remains
blocked under the exact gates. See
[V9-CUBICSPLINE-CONSUMER-STAGE-A-001](../reports/V9-CUBICSPLINE-CONSUMER-STAGE-A-001/README.md).

The published checkpoint underlying this integration is
`83aa5e5391848493c902af0c6bd4ecab6228afe6`. Its local real-tool suite and
hosted macOS arm64 CI each passed 928 tests plus 21 subtests; the CI source tree
is identical to the published tree. This head includes the opt-in canonical
support-anchor provider and SourceMotionQuery admission, but does not activate
a tangent emitter or change any motion threshold. Exact emitted evaluation
still blocks the generic direct joins and local loops, including adult V9 at
`3.23101227406632 mm/s`. Bounded walk v3 start/steady/stop measurements are
consistent with a shared continuous source trajectory at both tested
interfaces; no finite jump is resolved. They are numerical evidence for a
future all-key source-derived tangent experiment, not formal derivatives or a
current C1 pass. See
[V9-CURRENT-CONTINUITY-83AA5E5-001](../reports/V9-CURRENT-CONTINUITY-83AA5E5-001/README.md),
[V9-CANONICAL-SUPPORT-ANCHOR-PROVIDER-001](../reports/V9-CANONICAL-SUPPORT-ANCHOR-PROVIDER-001/README.md),
and
[V9-SOURCE-MOTION-QUERY-V9-INTEGRATION-001](../reports/V9-SOURCE-MOTION-QUERY-V9-INTEGRATION-001/README.md).

Two diagnostics are closed through two independent review rounds after that
published checkpoint. The canonical constant skin-target law provides
source-bound pointwise values for opt-in callers, and the adult V9
support-resultant diagnostic records sensitivity to explicit engineering
mass/COM/load alternatives. Both remain non-emitting: no recipe, emitter,
default motion, threshold or accepted asset activates them. The current exact
LINEAR continuity failures remain authoritative, and neither diagnostic grants
C1, mass-physics, biological, visual, Unity or production approval. See
[V9-CLOSED-DIAGNOSTICS-83AA5E5-001](../reports/V9-CLOSED-DIAGNOSTICS-83AA5E5-001/README.md).

The unselected adult V10 load-acceptance diagnostic adds a bounded authored
double-support compression and trunk response on top of V9. Its implementation
passed two independent code reviews and its reopened package preserves contact,
articulation, extension and rotation-rate checks, but exact LINEAR loop velocity
remains `BLOCKED` at `3.965012792580725 mm/s`. Root inspected all 148 front/side
frames and exercised both paired comparisons at 1x without finding a P0/P1
regression; the response remains restrained and perceptual weight acceptance is
open. It changes no selected recipe or default and grants no mass-physics,
biological, Unity or production approval. See
[V9-ADULT-LOAD-ACCEPTANCE-V10-001](../reports/V9-ADULT-LOAD-ACCEPTANCE-V10-001/README.md).

## Evidence-bound adult benchmark

`tarbosaurus-pin-552-1-adult-walk.v1` is the first explicit animal-instance
benchmark. It binds the adult PIN 552-1 estimates of 2816.3 kg body mass and
2.415 m summed femur, tibia and central-metatarsal length to a separately
versioned evidence document. Mass provenance is [Snively et al. (2019)](https://doi.org/10.7717/peerj.6432), Tables 2–3; the limb and estimated hip-height basis is [Dececchi et al. (2020)](https://doi.org/10.1371/journal.pone.0223698), Table 1. The admitted neutral geometry is uniformly scaled
from the mean of its independently measured left/right semantic hindlimb chains;
the compiler remeasures the bound rig and full bind-pose skin before accepting
that calibration. Existing engineering recipes and approved assets are not
superseded or rewritten.

The benchmark deliberately uses the grounded walk. Sprint v4 remains an
engineering stress track whose flight and rebound have not been biologically
validated for this animal. Each animal package reports mass weight, root-motion
and pelvis kinematics, two clearly labeled Froude normalizers, and a translational
inertial-load proxy. The published 1.932 m hip height is recorded as the study's
`0.8 * hindlimb length` posture proxy, separate from the emitted semantic pelvis
height. Pelvis acceleration is not whole-body center-of-mass acceleration;
force-aware solving, contact-force distribution, segment inertia and tissue
stress remain `NOT_IMPLEMENTED` or `NOT_EVALUATED`.

[Dececchi et al. (2020)](https://doi.org/10.1371/journal.pone.0223698), supplement S4, also provides taxon-level femur/tibia/central-
metatarsal lengths, but that row has no specimen identifier and sums to 2.420 m
rather than the PIN 552-1 Table 1 value. It is retained only as comparison:
the neutral rig's relative segment proportions differ, so anatomical fit remains
`UNVERIFIED`. Uniform scaling does not conceal that mismatch or authorize
per-bone resizing.

See [ANIMAL_CONFIGURATION.md](ANIMAL_CONFIGURATION.md) for the reusable instance
contract, generation command and the distinction between recorded mass and
mass-dependent solving.

The current host uses the pinned macOS arm64 toolchain. Source tests,
individual candidates, direct joins and native-media review are recorded separately.
A passing individual clip never grants connected locomotion or biological approval.
The historical adult-v3 results above remain part of that candidate's evidence.
The complete final local suite passed at exact integrated source
`4ae0fe92ec3ffd49dfeca14085756cc7cbe7d852`: 683 tests plus 21 subtests in
212.65 seconds with the real pinned tools and a clean tracked checkout. Both
final-round P1 reproductions are rejected, their narrow re-reviews are clean,
and all 14 retained packages verify without gaining approval claims. The
tracked receipt and reviewer reports are in
[V9-CONTINUATION-FINAL-4AE0FE9-001](../reports/V9-CONTINUATION-FINAL-4AE0FE9-001/README.md).
Hosted CI for the ensuing published documentation head is pending.

## Verification and immutable legacy boundary

Mandatory full-suite CI runs all tests, including real rendering, exact duplicate
builds, promotion rejection and corruption. Its canonical toolchain is macOS
arm64, Blender 5.2.0 and the genuine Khronos glTF validator 2.0.0-dev.3.10.
The preserved release reproduces byte-for-byte there. Linux differs by two
float32 rounding values; the approved output hash is unchanged:

`b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`

Current V9 candidates independently compile and verify on Linux. The pair jobs
compile each bound start, steady and stop and apply the historical quadratic
finite-difference estimator to both root-motion and in-place reconstructed-world
modes. Independent exact LINEAR/SLERP tangent evaluation now shows that the
generic gait joins and local steady loops remain outside the governed velocity
limits. No tolerance is relaxed, failing witness discarded, or Unity result
inferred from this work.

## Preserved V9 walking comparison

```
build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb
SHA-256 b54e3740ea451927b3b812c1be3f4ca6146cc369ad1313be7f08edd5ca741cd3
Clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION
```

The inherited clip name does not change the identity of this V9 artifact.
Approved Run010, Sprint006, Feeding003 and walking references remain unchanged.
Read-only comparison is not permission to inherit a prior animation as a
factory generation dependency. No historical builders are imported by new work.

## Still required before ready/merge

The exact exported-tangent source gate remains blocked for generic gait joins
and local steady loops. The corrected evaluator is integrated; a future
motion-representation change must pass the unchanged limits. Retain user
art-direction approval separately; adult v3
has been accepted only as the current factory recovery candidate, while adult
v7 and fast recovery v3 still require whole-body polish. Then validate the
intended Unity consumer, root authority, phase handoff, event delivery,
import/compression and target-device performance.
Hosted contracts and source evidence pass at `f24297d`; the wider candidate
catalog is not green, and draft PR #2 must not merge yet.

**PR: draft. Human native-speed approval: PENDING. Unity four-sample
Tarbosaurus walk verification: PASS; continuous Animator/runtime and Allosaurus
parity: PENDING.
Production promotion: NOT_GRANTED.**
