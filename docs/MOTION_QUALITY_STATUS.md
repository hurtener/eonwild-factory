# V9 motion quality: candidates and direct joins are separate gates

PR #2 continues the existing engine and approved references. **Quality-01 is
REJECTED**. Technical acceptance, source integrity, native visual review and
Unity parity are separate; none transfers automatically to a newer candidate.

## Current source and workstream

The recovered branch at `544b93e859f56339f2b804b81aac57b820924cd5` already
contained sprint v4 and fast-walk v2. Their actual candidate and multi-view jobs
passed in run 34093117077. Do not confuse the earlier written handoff with that
newer repository state. These are mechanical results, not visual approvals.

This pass adds prospective support placement, explicit loaded-phase interfaces,
continuous driven-lag evaluation, cross-document package metadata checks and
permanent start/steady/stop pair verification. Read the precise behavior and
remaining direct-join failures in [TRANSITION_INTEGRATION.md](TRANSITION_INTEGRATION.md).
The active start/stop selectors are v3. Sustained stride/cadence/flight settings,
contact floors, acceptance limits and approved assets remain unchanged.

## Evidence-bound adult benchmark

`tarbosaurus-pin-552-1-adult-walk.v1` is the first explicit animal-instance
benchmark. It binds the adult PIN 552-1 estimates of 2816.3 kg body mass and
2.415 m summed femur, tibia and central-metatarsal length to a separately
versioned evidence document. The admitted neutral geometry is uniformly scaled
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

Dececchi et al. supplement S4 also provides taxon-level femur/tibia/central-
metatarsal lengths, but that row has no specimen identifier and sums to 2.420 m
rather than the PIN 552-1 Table 1 value. It is retained only as comparison:
the neutral rig's relative segment proportions differ, so anatomical fit remains
`UNVERIFIED`. Uniform scaling does not conceal that mismatch or authorize
per-bone resizing.

Local execution and image access now work. Mounted old work was preserved
before source recovery. A GitHub source-evidence artifact and per-file Git blob
checks supplied current source when local Git network/DNS failed. This is not
proof that every historical partial-recovery fragment has been recovered.

Local preliminary generation with the revised engine passed individual
sprint-start v3, sprint-stop v3 and run-start v3 mechanical gates. Their actual
direct joins are still BLOCKED by velocity mismatch. Final CI on the exact
committed source must establish the full catalog results. A green individual
clip must not be reported as a green connected locomotion sequence.

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

Pass all current individual candidates AND both direct joins for all four gait
pairs. Inspect native-time multi-view motion and retain human art-direction
approval separately. Then validate the intended Unity consumer, root authority,
phase handoff, event delivery, import/compression and target-device performance.

**PR: draft. Visual approval: PENDING. Unity validation: NOT_RUN.
Production promotion: NOT_GRANTED.**
