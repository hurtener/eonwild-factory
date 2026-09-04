# V8.2 candidate A — balance-transfer implementation plan

## Scope

Create a new, reproducible **candidate A** from the immutable approved V8.1
iteration-38 walk snapshot.  This is an upper-body/tail rotation overlay only
for `PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION` and
`PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE`.

The architecture is authoritative over the older comparative evaluation's
pelvis envelope: `Bone_001` is frozen in candidate A because it parents both
legs and a post-bake pelvis change would invalidate the approved skinned
contact.  Pelvis balance remains candidate B work and is not part of this
implementation.

## Pinned input and ownership

- Frozen pointer: `procedural-animation-toolkit(v8.1)/approved_snapshots/APPROVED_WALK_BASE.json`.
- Frozen source GLB: `approved_snapshots/v8.1-walk-iteration-38/asset/tarbosaurus_procedural_v8_1_walk_iteration_38.glb`.
- Required source SHA-256: `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`.
- Implementation owner: `/root/v8_1_walk_respin`.
- Allowed write roots, authorized by the parent task: `candidates/v8.2-balance-transfer/**`, `showcase/v8.2-balance-transfer/**`, and `reports/V8-2-BALANCE-TRANSFER/implementation/**`.
- Read-only roots: the whole V8.1 snapshot, accepted V8.1 package,
  V8.1 iteration-38 candidate, V5.5 package, and all historical candidate
  artifacts.

## Intended files

- `candidates/v8.2-balance-transfer/config/balance-overlay.json` — pinned
  input, allowlist, gains, bounds, and phase/dynamics settings.
- `candidates/v8.2-balance-transfer/scripts/generate_balance_overlay.py` —
  hierarchy-aware local-rotation reconstruction and in-place accessor-only GLB
  export.
- `candidates/v8.2-balance-transfer/scripts/validate_balance_overlay.py` —
  structural, channel, world-transform/skinning, iteration-38 mechanics, and
  balance-effect gates.
- `candidates/v8.2-balance-transfer/scripts/render_balance_overlay_blender.py`
  and `render_balance_comparison_blender.py` — isolated approval media only.
- `candidates/v8.2-balance-transfer/generated/iteration-a/**` — candidate GLB,
  source/candidate hashes, raw validator reports, and reproduction command log.
- `showcase/v8.2-balance-transfer/iteration-a/**` — exactly one candidate side
  MP4, one synchronized comparison MP4, and their metadata after mechanical
  pass.
- `reports/V8-2-BALANCE-TRANSFER/implementation/{summary.md,commands.log,metrics.json,artifacts.json}`
  — evidence and handoff.

## Rotation allowlist

Only the rotation accessor arrays for these nodes may differ, and only in the
two pinned walk clips:

- spine: `Bone_007` through `Bone_002`;
- neck: `Bone_041` through `Bone_037`;
- head: `Bone_036`;
- tail: `Bone_024` through `Bone_016`.

All translations, root/pelvis rotations, lower-leg/foot/toe rotations,
arm/skull/snout/jaw/claw rotations, time accessors, interpolation, channel
membership, non-walk animations, node/skin/mesh data, and binary data outside
those allowed accessor ranges must remain byte-identical.

## Acceptance checks

1. Verify the frozen source SHA before generation and verify the snapshot is
   unchanged after generation/rendering.
2. Decode float32 accessors and prove the changed-channel set is non-empty and
   a subset of the 21 allowed rotation channels in exactly the two walk clips.
3. Prove byte equality for all protected accessors and non-animation binary
   data; preserve all walk time arrays, clip duration/sample count,
   interpolation, extras, and channel membership.
4. Recompute lower-body world matrices at all 245 keys and require origins
   within `1e-7 m` and angular difference within `1e-5 deg`; recompute skinned
   distal foot witnesses at keys and dense samples within `1e-6 m` per axis.
5. Re-run the authoritative iteration-38 stride, speed, rocker, toe dwell,
   passive lag, toe-down, ground/support, continuity, and seam gates against
   the candidate data without replacing the frozen report as evidence.
6. Require hierarchy-aware balance response: chest counter-correlation,
   head world-space caps, smooth base-to-tip tail lag without phase reversal,
   near-zero cycle mean delta, bounds compliance, and identical allowed arrays
   between root-motion and in-place clips.
7. Render only after the validator verdict is full PASS: one 960×540, 24 fps,
   exact 10-second V8.2 side view and one synchronized V8.1-vs-V8.2
   side-by-side comparison.  Verify their stream facts and hashes.

## Assumptions / stop conditions

- The approved snapshot is the sole V8.1 input; V5.5 contributes response
  gains, never animation samples.
- Candidate A adds no pelvis transformation despite the comparison paper's
  broader V8.2 objective; this follows the architecture's exact-freeze rule.
- Tail response is periodic, phase-driven, and base-to-tip smoothed; no
  arbitrary isolated per-frame keys may be used.
- Stop without rendering if any protected data changes, if a lower-body or
  skinned contact equality check regresses, if the head cap/balance gate fails,
  or if meeting a target requires altering the frozen locomotion boundary.

## Iteration C correction

`iteration-b` is retained as a diagnostic-only artifact: the independent
official evaluator verified its tail/head improvement but found its chest roll
to be `4.572°`, below the frozen `4.674°` baseline.  Iteration C preserves the
same tail/head response and reverses only the signed incremental spine-roll
term.  The sole balance authority is now
`evaluation/tools/evaluate_balance.py`; the candidate-local validator is
limited to structural, protected-channel, world-matrix/skinned-contact, and
iteration-38 mechanics inheritance checks.
