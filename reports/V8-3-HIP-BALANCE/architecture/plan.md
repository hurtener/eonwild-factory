# V8.3 hip-balance architecture plan

## Task

Plan the first pelvis-driven balance candidate after the frozen V8.2
Candidate-A release. V8.3 will introduce a bounded pelvis lateral/vertical/roll
layer **before** leg IK, re-solve both legs against the approved world contact
schedule, reapply the exact approved rocker/toe-lock/passive-release mechanism,
and preserve the V8.2 upper-body result wherever hierarchy permits.

This stage is architecture-only. It writes only this report directory. No
engine, candidate GLB, profile, validator, media, accepted snapshot, or release
worktree file is modified.

## Frozen references

- V8.2 Candidate-A iteration-g GLB:
  `candidates/v8.2-balance-transfer/generated/iteration-g-official-chest-solver/tarbosaurus_v8_2_balance_transfer.glb`
  - SHA-256:
    `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`
- V8.2 technical and visual reviews:
  `reports/V8-2-BALANCE-TRANSFER/reviews/technical-iteration-g.md` and
  `reports/V8-2-BALANCE-TRANSFER/reviews/visual-iteration-g.md`
- V8.2 machine evidence:
  `reports/V8-2-BALANCE-TRANSFER/implementation/iteration-g-official-chest-solver/`
- V8.1 iteration-38 canonical contact source:
  `procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/`
- V5.5 behavior reference:
  `procedural-animation-toolkit(v5.5)/validated_result/v5.5/` and
  `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

V5.5 supplies target behavior and scale only. Its gait clips and local leg
rotations are not retargeting inputs.

## Files written

- `reports/V8-3-HIP-BALANCE/architecture/plan.md`
- `reports/V8-3-HIP-BALANCE/architecture/architecture.md`

The clean release worktree at
`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-2-release` is explicitly
out of scope and remains untouched.

## Planned analysis

1. Pin the exact V8.2 release artifact and its accepted gait/balance metrics.
2. Separate channels that remain byte-frozen from channels that must change
   when pelvis motion is introduced before IK.
3. Define a candidate-local pelvis balance layer using support/load signals,
   not copied V5.5 animation curves.
4. Fix the solve order: root/contact schedule, pelvis balance, bilateral IK,
   approved distal contact mechanics, V8.2 upper-body preservation, export.
5. Define a deliberately conservative first envelope and hard mechanical,
   visual, provenance, and rollback gates.
6. Provide an exact implementation handoff without authorizing engine edits or
   release promotion.

## Acceptance checks for this report

- Quantitative V8.2, V5.5, and first-candidate pelvis targets are explicit.
- Root/stride/timing freezes and world-contact equivalence are distinguished
  from local-channel equality.
- The full pre-IK and post-IK ordering is unambiguous.
- The approved rocker, witness lock, toe dwell, passive lag, and seam gates are
  retained without threshold weakening.
- V8.2 spine/chest/tail preservation and head compensation ownership are
  explicit.
- Rendering evidence includes both contact-readable and lateral-balance views.
- Failure leaves the V8.2 release artifact and pointer unchanged.

## Assumptions

- V8.3 is an isolated candidate, not a replacement for V8.2 until separately
  approved.
- Local leg, foot, toe, pelvis, and neck/head channels may change only where
  required to preserve world-space mechanics after the pelvis change.
- “Exact approved contact” means the same contact targets, event phases,
  rocker/toe-lock/passive mechanism, and quantitative final-skinned gates; it
  cannot mean byte-identical lower-body quaternions after changing their common
  parent.
- The first candidate changes lateral shift, vertical load response, and roll.
  Pelvis yaw, pitch, sagittal sway, cadence, and stride remain frozen.

