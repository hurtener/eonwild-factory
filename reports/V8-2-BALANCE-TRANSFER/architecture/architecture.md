# V8.2 balance-transfer architecture

## Decision

Build V8.2 as an overlay on the exact approved iteration-38 GLB, not as a new
walk generation pass. The first candidate may replace only spine, neck, head,
and tail rotation samples in the two relaxed-walk clips. It must preserve every
root, pelvis, leg, foot, and toe sample exactly.

Do **not** change pelvis translation or rotation in this candidate. Pelvis is
the common parent of both thighs; any pelvis delta changes planted-foot world
poses even when all leg-local channels remain byte-identical. A pelvis balance
pass is therefore a separate experimental lane that must apply pelvis motion
before leg IK, re-solve the legs, rerun the iteration-38 distal-contact solve,
and prove world-contact equivalence. It cannot claim exact lower-body channel
preservation.

This split protects the part the user has already approved: the 2.60 m stride,
near-peak metatarsal rocker, fixed distal toe witnesses, passive toe-down lag,
and coherent leg fold.

## Pinned baseline

| Item | Required identity/value |
| --- | --- |
| Source GLB | `candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb` |
| Source SHA-256 | `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e` |
| Root-motion clip | `PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION` |
| In-place clip | `PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE` |
| Samples / duration | 245 keys / 4.069565 s per clip |
| Reference stride | 2.59999997 m |
| Reference speed | 4.59999986 km/h |
| Hip height | 2.75636 m |
| Final-skinned rocker lead | .09596-.09954 cycle before rear-extension peak |
| Toe-only dwell / passive lag | .11475 cycle / 8 baked keys |

The actual iteration-38 GLB contains 67 rotation channels and four translation
channels per walk clip. The translation channels are `Bone_000` (root),
`Bone_001` (pelvis), `Bone_008` (left foot pivot), and `Bone_012` (right foot
pivot). Root and pelvis also have rotation channels. This is why a pelvis edit
is not an innocuous upper-body adjustment.

## Exact ownership map

### Frozen locomotion boundary

All listed translation and rotation tracks are immutable in candidate A.

| Function | Semantic chain | Bones |
| --- | --- | --- |
| Global displacement/heading | root | `Bone_000` |
| COM motion and common leg parent | pelvis | `Bone_001` |
| Left proximal/distal leg | thigh, shin, ankle, foot | `Bone_011`, `Bone_010`, `Bone_009`, `Bone_008` |
| Left digits | three complete toe chains | `Bone_044 -> Bone_043 -> Bone_042`; `Bone_050 -> Bone_049 -> Bone_048`; `Bone_047 -> Bone_046 -> Bone_045` |
| Right proximal/distal leg | thigh, shin, ankle, foot | `Bone_015`, `Bone_014`, `Bone_013`, `Bone_012` |
| Right digits | three complete toe chains | `Bone_053 -> Bone_052 -> Bone_051`; `Bone_059 -> Bone_058 -> Bone_057`; `Bone_056 -> Bone_055 -> Bone_054` |

The foot translations are especially protected. Iteration 38 solves a
geometry-bearing foot rocker and distal toe lock during loaded contact, then
uses a target-free spring-damper for foot translation and foot/toe rotation
after release (`generate_walk_respin_2.py:128-195` and `196-280`). Rebuilding
or smoothing these channels would erase the approved causal mechanism.

### Candidate-A write allowlist

Only rotation channels below may change, and only in the two pinned walk clips.

| Function | Bones | Notes |
| --- | --- | --- |
| Spine/chest counterrotation | `Bone_007`, `Bone_006`, `Bone_005`, `Bone_004`, `Bone_003`, `Bone_002` | Safe: this branch does not parent either thigh. `Bone_002` carries neck and arms. |
| Neck stabilization | `Bone_041`, `Bone_040`, `Bone_039`, `Bone_038`, `Bone_037` | Safe downstream branch. |
| Head stabilization | `Bone_036` | Move the skull as a unit; preserve skull, snout, and jaw local tracks. |
| Tail counterphase/wave | `Bone_024`, `Bone_023`, `Bone_022`, `Bone_021`, `Bone_020`, `Bone_019`, `Bone_018`, `Bone_017`, `Bone_016` | Safe sibling of leg branches under the pelvis. |

All arm, skull, snout, jaw, and claw local channels remain exact. Arms will
naturally inherit the changed chest world transform; skull/jaw will naturally
inherit the changed head world transform. Editing their local tracks as well
would double-apply the transfer.

## Existing solver ownership and conflict

`eonproc_v4/locomotion.py:320-373` computes support-weighted pelvis translation,
yaw, roll, and pitch. `_tail_dynamics_scheduled` at lines 392-444 drives the
tail from pelvis yaw/pitch, lateral support, and heading dynamics. In
`_pose_for_body` at lines 538-600, the order is:

1. root and pelvis translation/rotation;
2. spine counterrotation;
3. neck/head stabilization;
4. jaw, tail, and arm motion;
5. bilateral terrain/contact leg solve at lines 602 onward.

This order is correct for a full solve: the legs see the final pelvis pose.
It also proves that a post-bake pelvis overlay is incorrect. Since both thighs
are pelvis descendants, applying pelvis motion after iteration-38 foot/toe
channels have been fixed moves their world witnesses. Applying pelvis motion
before IK changes thigh/shin/ankle/foot local rotations and requires a fresh
distal contact correction. There is no third option that preserves both pelvis
change and byte-identical lower-body channels.

## What V5.5 contributes

V5.5 and iteration 38 use the same procedural relationships but different
envelopes. The relevant resolved values are:

| Control | V5.5 | V8.1 iteration 38 |
| --- | ---: | ---: |
| Pelvis support shift gain | .15 | .022 |
| Pelvis roll | 3.7 deg | 1.35 deg |
| Pelvis yaw | 3.2 deg | 1.55 deg |
| Spine yaw counter gain | .58 | .44 |
| Neck stabilization gain | .51 | .45 |
| Head stabilization gain | .68 | .58 |
| Tail root yaw gain | .76 | .62 |
| Tail COM gain | 1.20 | .72 |
| Tail stiffness root -> tip | 24 -> 6.5 | 20 -> 4.6 |
| Tail damping ratio | .69 | .75 |
| Tail coupling / parent follow | 10 / .34 | 8 / .28 |
| Tail lag per bone | .022 s | .028 s |

Do not copy V5.5 quaternions or its full profile. Its cadence (.45 Hz), stride
(1.9 m), stance (.70), swing, and lower-limb envelopes differ from the approved
V8.1 motion. Transfer response relationships against the frozen V8.1 phase and
pelvis signals instead.

## Candidate A: exact-freeze upper-body overlay

### Source and phase

Read the two iteration-38 clips directly. Retain their time accessors and
derive normalized gait phase from the existing 245-key timeline (two cycles).
Use the frozen root/pelvis tracks as driver signals; never regenerate the walk
schedule. Apply identical upper-body rotation arrays to root-motion and
in-place clips because their non-root channels are intended to match.

### Recommended first-pass controls

Use the V5.5-to-V8.1 gain differences, driven by the already-approved pelvis
signals:

- spine yaw counterrotation: move the effective gain from `.44` toward `.58`;
- neck yaw/roll stabilization: `.45` toward `.51`;
- head yaw/roll stabilization: `.58` toward `.68`;
- tail yaw/pitch: rerun only the tail response with frozen V8.1 pelvis/support
  drivers and the V5.5 response parameters, then blend toward it;
- retain V8.1 neutral pitch, body lean, breathing, head micro-motion, jaw, and
  arm local motion in the first candidate. These are not balance transfer.

Use a single candidate blend `alpha` (recommended initial `0.6`) rather than
jumping to the full V5.5 envelope. For a parameter `g`, use
`g_candidate = g_v8_1 + alpha * (g_v5_5 - g_v8_1)`. The tail may use a separate
`alpha_tail <= alpha` if its distal amplitude reaches the safety bound.

For each allowed bone and sample, represent the additional motion as a
world-space anatomical-axis rotation vector `delta_world`. Reconstruct local
quaternions root-to-tip:

```text
Qworld_target[b] = Exp(delta_world[b]) * Qworld_v8_1[b]
Qlocal_target[b] = inverse(Qworld_target[parent(b)]) * Qworld_target[b]
```

Use the already-updated parent target in the second equation. This prevents a
spine delta from being accidentally counted again in neck/head local tracks.
Normalize quaternion signs against the previous sample and force the final
loop sample to equal the first.

For spine and neck, distribute the total correction with the existing weights:

- spine: `[.08, .11, .14, .18, .22, .27]`;
- neck: `[.11, .15, .19, .24, .31]`.

The first-pass target deltas are therefore conceptually:

```text
delta_spine_yaw_total = -(g_spine_candidate - .44) * pelvis_yaw
delta_neck_yaw_total  = +(g_neck_candidate  - .45) * pelvis_yaw
delta_neck_roll_total = +(g_neck_candidate  - .45) * pelvis_roll
delta_head_yaw        = -(g_head_candidate  - .58) * pelvis_yaw
delta_head_roll       = -(g_head_candidate  - .58) * pelvis_roll
```

There is no first-pass spine-roll delta: both engines use the same hard-coded
`.52 * pelvis_roll` relationship. There is no first-pass head-pitch delta:
both use the same `.42 * pelvis_pitch` relationship. Add neither merely for
visual activity.

For the tail, use the existing periodic spring-damper formulation from
`_tail_dynamics_scheduled`, but feed it the frozen iteration-38 pelvis yaw,
pitch, vertical translation signal, root heading velocity, and a support signal
derived from the frozen contact schedule. Evaluate both V8.1 and candidate
parameter sets, then apply only their difference to the existing tail rotations.
Warm up over the existing 28 supercycles and force exact loop closure. This
preserves iteration-38 timing while transferring V5.5-like counterphase and
wave propagation.

### Candidate-A amplitude safety bounds

Bounds are deltas from iteration 38, per local bone, after quaternion-log
conversion:

- each spine bone: <= 1.0 deg; accumulated chest world delta <= 1.6 deg;
- each neck bone: <= .75 deg; accumulated neck world delta <= 1.25 deg;
- head: <= 1.0 deg yaw/roll and <= .25 deg unintended pitch;
- tail root: <= 1.0 deg; each distal tail bone <= 1.5 deg; tail-tip accumulated
  world delta <= 3.0 deg;
- no translation channel may be added or changed.

These are initial engineering bounds, not claims of optimal animation. A bound
hit should reduce `alpha`, not silently clip isolated frames and create a kink.

## Candidate B: pelvis balance experiment

Only attempt this after candidate A has a clean mechanical pass and visual
comparison. Candidate B is a separate output and report, never an overwrite.

### Required solve order

1. Start from the same frozen root trajectory, phase, foot target schedule,
   stance/release landmarks, and 2.60 m stride.
2. Introduce a small pelvis lateral shift/roll before leg IK. Do not start with
   the full V5.5 `.15` support gain or 3.7-degree roll. A sensible first bracket
   is support gain `.03-.05` and pelvis roll `1.6-1.9 deg`, retaining the V8.1
   yaw/pitch unless a separate test justifies them.
3. Re-solve thigh/shin/ankle/foot against the original world contact targets.
4. Reapply the iteration-38 loaded rocker/toe-witness solve and passive
   post-release mechanism in the same phase windows.
5. Generate upper-body/tail response from the new pelvis signal.
6. Validate final skinned geometry, not foot origins or channel proxies.

An exact algebraic compensation through thigh local transforms is possible in
principle, but it is the same inverse-kinematics problem with worse constraint
handling. Reusing the leg solver is safer and auditable.

### Candidate-B claim boundary

Candidate B may claim **world-contact equivalence**, never “unchanged legs.”
Its lower-body local quaternions are expected to differ because they compensate
for the new pelvis. Root motion, contact targets, gait landmarks, and final
skinned contact must remain equivalent.

## Validator additions

### Structural and channel allowlist

For candidate A, compare decoded float32 accessor arrays, not only JSON shape:

1. Source SHA equals the pinned iteration-38 SHA.
2. Node hierarchy, node rest TRS, mesh primitives, materials, skins, joint
   order, inverse bind matrices, vertex positions/normals/UVs/joints/weights,
   and all non-animation binary regions are unchanged.
3. Animation count and all non-walk animations are byte-identical.
4. Both walk time accessors, interpolation modes, duration, sample count, clip
   extras, and channel membership are unchanged.
5. Exact-array equality for every translation channel: `Bone_000`, `Bone_001`,
   `Bone_008`, `Bone_012`.
6. Exact-array equality for root/pelvis and every bilateral leg/foot/toe
   rotation listed in the frozen ownership map.
7. Exact-array equality for all arm, skull, snout, jaw, and claw local tracks.
8. The changed-channel set is a non-empty subset of the 21 allowed rotations
   (6 spine + 5 neck + 1 head + 9 tail), with no other difference.

### Mechanical invariants

Candidate A should meet both exact and independently recomputed checks:

- root distance, reference stride, and speed equal iteration 38 within float32
  round-trip tolerance (`1e-6 m`, `1e-6 m/s`);
- lower-body joint world matrices equal iteration 38 at all 245 keys, with
  maximum origin drift <= `1e-7 m` and angular difference <= `1e-5 deg`;
- final-skinned distal witness trajectories equal iteration 38 within
  `1e-6 m` per axis at exported keys and dense 240 Hz samples;
- retain iteration-38 absolute witness gates: X <= `.005H`, Y/Z <= `.003H`;
- preserve final-skinned rocker onset-to-peak lead `.04-.10` cycle, passive
  release lead >= `.02`, toe-only dwell, 7+ consecutive passive toe-down keys,
  and zero >1 mm metatarsal reversals;
- both clip seams: first/last allowed-bone quaternions equal, no sign flip,
  and adjacent angular velocity/acceleration remain below existing 390 deg/s
  and 9000 deg/s^2 limits.

Exact lower-body world matrices are the strongest proof in candidate A. The
skinned checks remain useful defense against exporter/channel-selection errors.

Candidate B replaces exact lower-body equality with these equivalence gates:

- root arrays and 2.60 m stride remain exact;
- stance distal witnesses remain within the existing X/Y/Z limits and within
  `2 mm` Euclidean drift of iteration 38;
- contact, visible rocker onset, rear-extension peak, release, passive lag, and
  receiving-preparation landmarks differ by no more than one 60 Hz key or
  `.0082` cycle, whichever is stricter;
- selected-sole penetration and support are no worse than iteration 38 by more
  than `.5 mm` at any exported key;
- knee/ankle anatomical sign, velocity, acceleration, and continuity gates all
  pass with no new reversal.

### Balance-effect checks

The overlay must demonstrate coherent balance, not simply more motion:

- chest yaw is negatively correlated with pelvis yaw over the loop;
- neck/head stabilization reduces pelvis-induced world yaw/roll at the head,
  without locking the head or increasing high-frequency angular acceleration;
- tail-root yaw is counter-correlated with pelvis yaw/support transfer;
- tail peak phase progresses monotonically base-to-tip, with no adjacent-bone
  phase reversal and no isolated amplitude spike;
- mean cycle-local delta for each allowed axis is approximately zero
  (`abs(mean) <= .05 deg`) so the overlay does not alter neutral posture;
- root-motion and in-place clips have identical allowed-bone rotation arrays.

## Evidence and review sequence

For each candidate, produce a 10-second side view and three-quarter view at
the same camera, floor, lighting, cadence, and playback rate as iteration 38.
Also produce phase-matched V8.1/V8.2 contact sheets for support transfer, toe
rocker, release, and swing pass. Review full-body motion at native cadence;
cropped feet are corroboration, not the sole visual proof.

Candidate A advances only if channel immutability and all mechanics pass.
Candidate B advances only if its separate world-equivalence report passes.
Never accept a visually improved torso by weakening the approved foot/contact
gates.

## Implementation map

Recommended isolated files for the implementation owner (names are proposed,
not created by this analysis):

- `candidates/v8.2-balance-transfer/scripts/generate_balance_overlay.py`:
  load iteration 38, assert SHA, compute allowed rotation deltas, reconstruct
  local channels hierarchy-first, and export a new candidate GLB;
- `candidates/v8.2-balance-transfer/scripts/validate_balance_overlay.py`:
  accessor allowlist, exact lower-body matrices/channels, skinned witness
  equivalence, balance metrics, and seam checks;
- `candidates/v8.2-balance-transfer/config/balance-overlay.json`:
  explicit blend, bounds, allowlist, and pinned input SHA;
- `candidates/v8.2-balance-transfer/generated/<iteration>/...`:
  candidate-only outputs and raw validation reports;
- `showcase/v8.2-balance-transfer/<iteration>/...`:
  isolated review media.

Reuse `AnimationPackReader` for decoded tracks and the existing GLB writer from
the V8.1 candidate pipeline. Reuse the final-skinned witness logic from
`validate_walk_respin_2.py`. Do not mutate or import-time monkey-patch the
accepted V8.1 package; treat it as an immutable solver/format library only.

## Stop conditions

Stop the candidate if any unallowlisted channel changes, the source SHA is not
the pinned iteration-38 asset, a lower-body matrix differs in candidate A, a
contact/mechanical gate regresses, or the only way to obtain pelvis motion is
to weaken iteration-38 acceptance thresholds. A pelvis candidate that passes
only visually remains experimental.
