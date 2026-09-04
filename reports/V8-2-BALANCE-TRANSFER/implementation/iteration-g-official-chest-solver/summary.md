# V8.2 Candidate-A iteration-g — official chest-balance solve

## Result

PASS. This candidate starts from the quarantined diagnostic iteration-b GLB
and applies the independently reviewed, bounded official-basis chest solve at
`gain=0.3984375`. It is not an edit of the V8.1 approved snapshot.

## Inputs and output

- Frozen V8.1 source SHA-256: `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`
- Iteration-b input SHA-256: `bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2`
- Candidate GLB: `candidates/v8.2-balance-transfer/generated/iteration-g-official-chest-solver/tarbosaurus_v8_2_balance_transfer.glb`
- Candidate SHA-256: `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`

Only `Bone_002`, `Bone_041..037`, and `Bone_036` rotation accessors changed,
in both RESPIN walk clips. The chest target is `Exp(Log(Rchest Rp^-1) +
[0,0,-0.3984375*pelvisRollZ]) * Rp`; the neck chain deterministically cancels
the resulting chest world delta to preserve iteration-b head world motion.
Tail accessors remain iteration-b-identical.

## Gates

The official evaluator was run explicitly with
`--gate-mode candidate-a-upper-only --enforce-gate`.

- Official Candidate-A gate: PASS.
- Chest pitch/yaw/roll P2P: `4.081645 / 2.647963 / 5.617933` degrees.
- Head world pitch/yaw/roll P2P: `2.580076 / 1.528822 / 0.966137` degrees.
- Tail yaw base/mid/tip: `5.587140 / 18.718186 / 22.991999` degrees.
- Structural/mechanical gate: PASS; lower-body world origin drift `0 m`,
  angular difference `1.50e-15 degrees`; iteration-38 contact/stride/rocker/
  passive/seam authority is inherited exactly.
- Frozen baseline reproduction: PASS, max error `7.27e-7` (tolerance `2e-5`).

See `official-balance.json`, `structural-mechanical.json`, and
`generation.json` in this directory for machine-readable evidence.

## Review media

- Candidate side video: `showcase/v8.2-balance-transfer/iteration-g/side/walk-relaxed-v8-1-respin-side.mp4`
  — 960x540, 24 fps, 240 frames, 10.000 seconds, SHA-256
  `a29a14dcbcab3b6963c03966755e274419acb43704f26a71da2b055f0eaa8bac`.
- Synchronized comparison: `showcase/v8.2-balance-transfer/iteration-g/comparison/v8-1-approved-vs-v8-2-balance-transfer-side-by-side.mp4`
  — 1920x540, 24 fps, 240 frames, 10.000 seconds, SHA-256
  `76910cd426c11d00e66a5bba98ba05a9a9f555638142fff48587825a4d2be5d2`.

No temporary render frames remain. No commit or push was performed.

## Narrow visual-review evidence

Following visual-review P1, this evidence-only follow-up leaves both GLBs and
the existing side media byte-for-byte unchanged. It adds a synchronized fixed
front-three-quarter comparison with approved V8.1 on the left and V8.2 on the
right. The V8.1 sampled bounds are locked verbatim for the V8.2 render, with
the same neutral floor and key/fill/rim values.

- Approved three-quarter MP4: `showcase/v8.2-balance-transfer/iteration-g/threeq/v8-1-approved/walk-relaxed-threeq.mp4`
  — SHA-256 `ec5092958858b56523a7f6e53ae6cbf18cb27fe40f4448db0a15dc1773046682`.
- Candidate three-quarter MP4: `showcase/v8.2-balance-transfer/iteration-g/threeq/v8-2-candidate/walk-relaxed-threeq.mp4`
  — SHA-256 `5fdeed0aaf15c9852d1a4a537989b709b2875cf48947255c05108e41d6462cf7`.
- Side-by-side comparison: `showcase/v8.2-balance-transfer/iteration-g/threeq/comparison/v8-1-approved-vs-v8-2-threeq-side-by-side.mp4`
  — 1920x540, 24 fps, 240 frames, 10.000 seconds, SHA-256
  `5e11692890b18166cea169c61894c0cb3824a69fea79c932ebfffbba00045d10`.

The V8.1 source asset remains SHA-256
`1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`;
the V8.2 candidate remains SHA-256
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
