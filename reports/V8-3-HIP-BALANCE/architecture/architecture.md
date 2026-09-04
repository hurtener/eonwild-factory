# V8.3 pre-IK hip-balance architecture

## Decision

V8.3 is feasible as a candidate-local pre-IK pelvis layer followed by a full
bilateral leg/contact re-solve. It must not be implemented as a post-bake
pelvis edit: `Bone_001` parents both thighs, so moving it after the approved
leg solve would move the feet and invalidate the contact proof.

The first candidate should close only a modest portion of the V5.5/V8.2 pelvis
gap. Its purpose is to prove that readable hip load transfer composes with the
approved 2.60 m walk and distal toe rocker. It is not permission to import the
full V5.5 sway.

The frozen rollback artifact is V8.2 iteration-g, SHA-256
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
V8.3 is produced under new candidate/report/showcase roots; the V8.2 release
candidate, evidence, media, and clean release worktree are read-only.

## Baseline and target envelope

The official evaluator uses GLB world basis X=lateral, Y=up, Z=fore-aft and
normalizes translation by sampled hip height.

| Pelvis metric | Frozen V8.2 | V5.5 reference | V8.3 first target |
| --- | ---: | ---: | ---: |
| Lateral translation P2P | .014857 H | .101657 H | **.030-.040 H**, nominal .035 H |
| Vertical translation P2P | .012369 H | .038808 H | **.016-.020 H**, nominal .018 H |
| Sagittal translation P2P | .004125 H | .019595 H | frozen within +/- .0002 H |
| Pelvis pitch P2P | 1.1384 deg | 2.8879 deg | frozen within +/- .15 deg |
| Pelvis yaw P2P | 3.1394 deg | 6.6281 deg | frozen within +/- .15 deg |
| Pelvis roll P2P | 2.6958 deg | 7.3621 deg | **3.5-4.1 deg**, nominal 3.8 deg |

This first target roughly doubles the currently subtle lateral translation but
still uses only about one-third of V5.5 lateral travel and about half of its
roll. It is intentionally below the earlier broad `.045-.060 H` / `4.2-5.2
deg` exploration envelope. Those larger values are a later bracket only after
the first candidate demonstrates contact and head stability.

Suggested starting profile controls, subject to outcome calibration rather
than acceptance by parameter value alone:

| Control | V8.2/V8.1 value | V5.5 | V8.3 starting value |
| --- | ---: | ---: | ---: |
| `pelvis_support_shift_gain` | .022 | .15 | **.050** |
| `pelvis_vertical_bob_hip_fraction` | .0045 | .014 | **.0070** |
| `pelvis_loading_drop_hip_fraction` | .0035 | .011 | **.0055** |
| `pelvis_roll_deg` | 1.35 | 3.7 | **1.90** |

The measured GLB envelope is authoritative. If these controls miss the target,
adjust only within the configured search bounds; do not declare success from
profile values.

## Channel ownership

### Byte-frozen to V8.2

- all mesh, material, node hierarchy/rest TRS, skin, joint order, inverse bind,
  and non-animation binary data;
- all non-walk animations;
- walk time accessors, sample count (245), duration (4.069565 s), interpolation,
  channel membership, and extras;
- `Bone_000` root translation and rotation;
- all arms, claws, skull, snout, and jaw local channels;
- V8.2 spine/chest rotations `Bone_007..Bone_002`;
- V8.2 tail rotations `Bone_024..Bone_016`.

Keeping spine/chest and tail local tracks exact preserves the accepted V8.2
motion relative to the pelvis. Tail is a sibling of the legs under the pelvis,
so no compensation is required. The larger pelvis movement will carry that
same accepted tail response through world space.

### Allowed to change in the two relaxed-walk clips only

- pelvis `Bone_001` translation and rotation;
- left thigh/shin/ankle/foot `Bone_011/010/009/008` rotations and `Bone_008`
  foot-pivot translation;
- right thigh/shin/ankle/foot `Bone_015/014/013/012` rotations and `Bone_012`
  foot-pivot translation;
- complete toe chains:
  - left `044->043->042`, `050->049->048`, `047->046->045`;
  - right `053->052->051`, `059->058->057`, `056->055->054`;
- neck/head `Bone_041..Bone_036`, solely to compensate the new pelvis/chest
  world movement and preserve the V8.2 head result.

Leg and foot local equality is intentionally replaced by world-contact
equivalence. No other changed accessor is allowed.

## Factory parameterization

Implement a candidate-local `PelvisBalanceLayer`, preferably as a subclass or
composition around the pinned V8.1 `V4BodyPlan`. Do not edit the accepted V8.1
or V8.2 package during candidate development.

At every internal 120 Hz solve sample, derive only from the existing schedule:

```text
support = (left.target * left.load + right.target * right.load)
          / max(left.load + right.load, epsilon)
s = clamp(dot(support - path.position, lateral) / (foot_span / 2), -1, 1)
b = -cos(4 pi phase)
d = cyclic_gaussian(phase, center=.055, width=.055, period=.5)
```

Use zero-mean, exactly periodic signals:

```text
pelvis_lateral = support_shift_gain * support_lateral
pelvis_vertical = H * (vertical_bob_fraction * b
                       - loading_drop_fraction * d)
pelvis_roll = radians(roll_degrees) * s
```

Retain the frozen V8.2/V8.1 terrain-follow term, forward sway, pelvis yaw,
pelvis pitch, root path, and foot target schedule. On flat ground, the new
layer therefore owns only lateral translation, vertical load response, and
roll.

### Determinism and symmetry

- Inputs are the pinned schedule/profile and support loads; V5.5 animation
  samples are never read by the generator.
- Left/right support must satisfy half-cycle antisymmetry for lateral/roll
  within float tolerance; vertical response must repeat each half-cycle.
- Subtract cycle mean from added lateral and roll signals. Do not shift neutral
  stance or add a root offset.
- Run the same internal 120 Hz solve and 60 Hz export used by iteration 38.
- Search/calibration variables, order, bounds, step sizes, tie-breaking, and
  selected result must be serialized in the generation report.

Recommended first search box:

```text
support_shift_gain: [.040, .060]
vertical_bob_H:     [.0060, .0080]
loading_drop_H:     [.0045, .0065]
pelvis_roll_deg:    [1.70, 2.05]
```

Select the smallest geodesic/local-channel departure from V8.2 among candidates
that meet the outcome envelope and every mechanical gate. Never optimize a
weighted score that can trade a contact failure for a balance improvement.

## Required solve order

The order is part of the contract:

1. **Pin inputs.** Verify the V8.2 release SHA, V8.1 approved snapshot
   manifest, resolved iteration-38 profile, and the contact generator/
   validator script hashes before work begins.
2. **Reuse the frozen locomotion schedule.** Copy exact times, phases, root
   distances, foot world targets, loads, stance/swing flags, terrain, contact
   anchors, and event landmarks. Root displacement remains identical.
3. **Apply `PelvisBalanceLayer`.** Modify the body plan before pose construction
   or IK. The final pelvis translation/rotation is visible to both hip joints.
4. **Solve both legs.** Run the existing terrain-aware thigh/shin/ankle/foot IK
   against the unchanged world foot targets, including selected-sole vertical
   correction and all joint limits.
5. **Reapply the approved distal mechanism.** Run the exact pinned
   iteration-38 `respin_2_phase_dynamics` after the base leg solve:
   - loaded contact window `.40 <= phase < .78`;
   - rocker start `.645` left / `.647` right;
   - visible rise end `.720`;
   - release `.78`, passive target-free interval through `.85`;
   - receiving preparation `.85`, flatten `.88`;
   - the same three distal skinned witness groups, metatarsal target, bounds,
     spring `K=14`, damping `C=7`, and no active passive target.
6. **Restore the V8.2 upper-body reference.** Copy the frozen V8.2
   spine/chest and tail local arrays exactly. Keep arms/jaw/etc. exact.
7. **Stabilize neck/head.** Compute the world delta introduced at the chest by
   the changed pelvis. Cancel it progressively through `Bone_041..037` using
   the proven cumulative fractions `[.11,.26,.45,.69,1.0]`, then reconstruct
   `Bone_036` so its target world rotation matches V8.2 where bounds allow.
8. **Export once.** Enforce quaternion continuity and exact loop endpoints;
   root-motion and in-place clips share every non-root channel.
9. **Validate final GLB.** All metrics are recomputed from exported float32
   channels and final skinned vertices. In-memory solver data is diagnostic
   only.

Pinned current script identities for provenance:

- `generate_walk_respin_2.py` SHA-256
  `9de1aa0260b6b941ce11f51e857e1914e66440d8d7b2c98bd122212b0bd146a3`;
- `validate_walk_respin_2.py` SHA-256
  `b28d5fdcd8c8951c1bc960b22f6f7e33f8843f1f4d126cddcc08413b23fbc395`;
- V8.2 `generate_balance_overlay.py` SHA-256
  `8dd8907cfad2e45453ef08a364b701e59d61094a2587000caa6fb4f82961bca2`;
- V8.2 `apply_official_chest_solver.py` SHA-256
  `7ec18b39d6316f6eceffa8ccf2b811c4f287acf6e6d44afff59e6cc2fb17e92d`.

If any pinned hash changes, stop and review the new implementation rather than
silently accepting drift.

## Hard gates

### Exact freezes

The validator must prove:

1. source V8.2 SHA is exact and the source remains unchanged after the run;
2. only the explicit V8.3 allowlist differs in the two walk clips;
3. all frozen structural data, non-walk clips, time arrays, root arrays, upper
   spine/chest/tail arrays, and unrelated local tracks are byte-identical;
4. root-motion horizontal distance, 2.59999997 m reference stride, 4.59999986
   km/h speed, cadence, duration, and phase landmarks are exact within float32
   round-trip (`1e-6 m`, `1e-6 m/s`, `1e-7 s`);
5. root-motion and in-place non-root arrays are identical.

### Pelvis balance gates

- lateral, vertical, sagittal, pitch, yaw, and roll envelopes meet the first
  target table;
- added lateral/roll cycle means are <= `.0001 H` / `.01 deg`;
- lateral translation and roll correlate with the weighted loaded-side support
  signal at `abs(Pearson) >= .85`, with the documented sign;
- no single exported pelvis translation step exceeds `.0025 H`, and no roll
  step exceeds `.35 deg`;
- pelvis correction velocity and acceleration are reported and contain no
  isolated one-key extremum or half-cycle asymmetry above 5%.

### Leg and final-skinned contact equivalence

Local leg arrays may differ, but all of the following are mandatory:

- the exact original foot world target/stance/release schedule is used;
- maximum final IK foot-target error <= `.00035 H` (about `.96 mm` at the
  approved 2.756 m hip height);
- dense loaded distal-witness absolute motion remains X <= `.005 H` and Y/Z <=
  `.003 H`;
- every dense distal witness remains within `2 mm` Euclidean distance of the
  phase-matched V8.2 trajectory and each candidate worst axis is no more than
  `.5 mm` worse than the V8.2 worst axis;
- selected-sole penetration and stable-contact quantile are no more than `.5
  mm` worse than V8.2 and also pass the existing absolute gates;
- final-skinned rocker onset-to-rear-extension lead remains `.04-.10` cycle
  and differs from V8.2 by <= one 60 Hz key / `.0082` cycle;
- release follows the peak by >= `.02` cycle; loaded keys remain 15/16 +/- 1;
  toe-only dwell differs from `.11475` by <= one key;
- passive toe-down remains at least 8 left / 7 right consecutive baked keys,
  with `activeTarget: null`, monotonically decreasing spring energy/speed, and
  the same `.78-.85` passive interval;
- zero metatarsal reversals above 1 mm; maximum adjacent dense-witness movement
  <= `1.0 mm` (V8.2 authority: `.789 mm`);
- no anatomical reversal; knee/ankle limits, continuity, 390 deg/s velocity,
  and 9000 deg/s2 acceleration gates pass.

As secondary deformation bounds, compare local tracks to V8.2 at every baked
key and require candidate deltas no greater than 3 deg thigh, 3 deg shin, 4 deg
ankle, 4 deg foot, and 3 deg per toe root, unless an independently reviewed
anatomical reason justifies a tighter/alternate bound. Foot-pivot translation
delta must remain <= 15 mm. These bounds do not replace skinned contact proof.

### Preserve the V8.2 balance result

- spine/chest and tail local arrays are byte-identical to V8.2;
- chest-relative-to-pelvis remains inside the V8.2 Candidate-A gates: pitch
  within `.20 deg` of `4.081645`, yaw >= `2.647963`, and roll `5.4-6.25 deg`;
- chest-roll/pelvis-roll correlation remains in `[-.95,-.70]`;
- tail relative yaw remains within `.25 deg` of V8.2 base/mid/tip
  `5.587140/18.718186/22.991999`, with identical phase ordering;
- head world pitch/yaw/roll stay <= `2.9/2.1/1.2 deg` and differ from V8.2 by
  no more than `.10 deg` P2P;
- neck local delta from V8.2 <= `.75 deg` per bone, head local delta <= `1.0
  deg`, and head-world difference from V8.2 <= `.05 deg` at every baked key;
- seam is zero translation and <= `.00001 deg` rotation.

If exact spine/tail copying plus head compensation cannot meet these gates,
the pelvis target must be reduced. Do not reopen the accepted V8.2 chest or
tail solver in the same candidate.

The official evaluator expresses relative rotations in world-basis rotation
vectors (`R_child_world * R_pelvis_world.T`). Changing pelvis orientation can
slightly rotate those reported components even when the local spine/tail arrays
are byte-identical. The byte freeze is therefore the primary preservation
proof; the metric bands detect harmful world-basis coupling without demanding
mathematically impossible component identity.

## Evidence package

Mechanical PASS precedes rendering. After PASS, produce:

1. a 10-second, 960x540, 24 fps, 240-frame candidate side view using the
   V8.2 locked framing/lighting, for stride, limb, foot, and ground contact;
2. a synchronized 1920x540 V8.2-left/V8.3-right side comparison;
3. a synchronized fixed front-three-quarter comparison with the same global
   full-body bounds, floor, lighting, and phase, for hip lateral load transfer;
4. a fixed rear or front orthographic diagnostic view with a subtle floor grid
   and pelvis center marker, kept separate from editorial media;
5. phase-matched full-body and foot crops at contact, mid-stance, rocker onset,
   rear-extension peak, release, passive lag, and swing pass for both sides;
6. plots of pelvis XYZ/roll, support signal, foot target error, and the three
   distal witness coordinates over two cycles.

No camera may track pelvis lateral movement, auto-reframe each asset
independently, or use different bounds: those choices would hide or exaggerate
the change. Review normal-speed playback first; slow motion is diagnostic only.

Visual acceptance requires that the support-side hip settles toward the loaded
foot without wobble, the opposing leg remains cohesive, the head stays quiet,
the tail remains a counterweight rather than a whip, and the approved rocker/
toe dwell remains readable in both side and three-quarter views.

## Candidate layout and implementation handoff

Proposed new roots:

- `candidates/v8.3-hip-balance/config/hip-balance.json`
- `candidates/v8.3-hip-balance/scripts/generate_hip_balance.py`
- `candidates/v8.3-hip-balance/scripts/validate_hip_balance.py`
- `candidates/v8.3-hip-balance/scripts/render_hip_balance_blender.py`
- `candidates/v8.3-hip-balance/generated/<iteration>/`
- `showcase/v8.3-hip-balance/<iteration>/`
- `reports/V8-3-HIP-BALANCE/implementation/`

`generate_hip_balance.py` should load/check the pinned source libraries,
construct the frozen schedule, apply the candidate-local body-plan layer,
invoke existing IK, run the pinned distal mechanism, transplant exact V8.2
spine/tail/unrelated arrays, solve neck/head compensation, and export. The
validator must independently decode the final GLB; it may reuse witness math
but must not trust generation diagnostics as acceptance evidence.

Run one narrow parameter bracket at a time. The orchestrator should keep the
V8.2 artifact as the visible control and authorize media only after a complete
mechanical pass.

## Rollback and promotion boundary

- V8.2 iteration-g remains the release/default pointer throughout V8.3 work.
- Every failed V8.3 iteration is quarantined under its own directory with raw
  failure evidence; it is never copied over V8.2 or presented as a release.
- No engine or accepted-snapshot change is part of candidate iteration.
- If the first target cannot pass without weakening a V8.2 contact/head gate,
  reduce pelvis amplitude or stop. Do not change thresholds.
- Promotion requires reproducible generation, full mechanical PASS, independent
  technical review, independent side and three-quarter visual review, and user
  approval.
- Only after approval should a separate integration task port the pelvis layer
  into the canonical engine, create a new immutable snapshot, update pointers,
  and commit/sign the coherent release. Rollback remains the pinned V8.2 SHA.

## Known risks

- More lateral pelvis travel may exhaust hip abduction or force foot-pivot
  translation to hide an unreachable IK target. Local bounds plus final-skinned
  proof prevent this.
- More vertical bob can alter visible rocker timing even when event constants
  are unchanged. The final-skinned onset gate remains authoritative.
- Pelvis roll can couple into measured pitch/yaw and head motion. Outcome gates
  are measured in the official world-basis rotation-vector convention; Euler
  controls alone are not evidence.
- Exact V8.2 upper local tracks preserve relative motion, but the new pelvis
  changes their world motion. The neck/head compensation and three-quarter
  review are mandatory.
- V8.2 release evidence identified content-addressed/Git-addressing debt. V8.3
  must continue to identify inputs by artifact SHA and must not infer release
  identity from the current dirty checkout HEAD.
