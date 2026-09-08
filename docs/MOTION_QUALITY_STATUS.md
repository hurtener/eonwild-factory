# V9 motion quality: candidates and direct joins are separate gates

PR #2 continues the existing engine and approved references. **Quality-01 is
REJECTED**. Technical acceptance, source integrity, native visual review and
Unity parity are separate; none transfers automatically to a newer candidate.

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
current evidence and angle conventions. Raw direct-join limits remain unchanged
and the sprint joins remain unresolved. At exact local source
`7920c59dd354027b8784483bb208fd0e6229cd91`, walk, reverse-walk and run pass
both direct joins in both movement modes; sprint remains `BLOCKED` in both.
See [TRANSITION_INTEGRATION.md](TRANSITION_INTEGRATION.md) and the
[exact-source pair report](../reports/V9-NATIVE-CLOCK-PAIR-STATUS-001/README.md).

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

The exact integrated source `5304b1967ad350737cf7e9ee6555a5f4de9e9bff`
passed 658 tests plus 21 subtests in 225.75 seconds. The new adult v3 catalog
binding test then passed at exact source
`7809ada9743818e860e096ffb38ddba3488a7d9b` in 0.26 seconds.

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
The complete local suite passed at exact integrated source
`5304b1967ad350737cf7e9ee6555a5f4de9e9bff`: 658 tests plus 21 subtests passed
in 225.75 seconds with the real pinned tools and a clean tracked checkout. The
host receipt is
`out/continuation-full-suite-5304b19/host-validation.json`. The additional adult
v3 catalog binding test passed at exact source
`7809ada9743818e860e096ffb38ddba3488a7d9b` in 0.26 seconds. Remote CI has not
run for this source.

## Verification and immutable legacy boundary

Mandatory full-suite CI runs all tests, including real rendering, exact duplicate
builds, promotion rejection and corruption. Its canonical toolchain is macOS
arm64, Blender 5.2.0 and the genuine Khronos glTF validator 2.0.0-dev.3.10.
The preserved release reproduces byte-for-byte there. Linux differs by two
float32 rounding values; the approved output hash is unchanged:

`b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`

Current V9 candidates independently compile and verify on Linux. The new pair
jobs compile each bound start, steady and stop and check both native serialized
joins in root-motion and in-place reconstructed-world modes. No tolerance is
relaxed, failing witness discarded, or Unity result inferred from this work.

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

The remaining direct-join source gate is sprint start and stop in both movement
modes. Retain user art-direction approval separately; adult v3 has been accepted
only as the current factory recovery candidate. Then validate the intended Unity
consumer, root authority, phase handoff, event delivery, import/compression and
target-device performance.

**PR: draft. Visual approval: PENDING. Unity validation: NOT_RUN.
Production promotion: NOT_GRANTED.**
