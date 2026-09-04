# V8.2 balance-transfer evaluation plan

## Objective

Evaluate the user's impression that the approved V5.5 walk has more natural whole-body balance than the approved V8.1 walk-respin-2 iteration 38, while V8.1 has the stronger lower-leg/foot solution. Define a narrow, measurable V8.2 balance overlay that preserves V8.1 foot/contact behavior.

## Immutable comparison inputs

- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/tarbosaurus_procedural_v5_5_animation_pack.glb`
- `reports/V5-5-BALANCE-001/render-candidate-5/films/walk-relaxed-inplace.mp4`
- `candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb`
- `showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4`

## Scope and ownership

Only this report directory is written. The factory checkout has no local `config/ownership.yml`; no engine, GLB, video, profile, candidate, or showcase file may be modified. All coordinate comparisons will be normalized by the animated hip height and will state basis/semantic limitations explicitly.

## Method

1. Identify corresponding relaxed in-place walk clips and mapped anatomical channels in both GLBs.
2. Resample each loop to 120 normalized phase samples; remove static pose offsets; normalize translations by median hip height.
3. Measure pelvis translation and rotation, trunk/chest and neck/head counter-motion, tail base/mid/tip counterphase, support/COM proxy, loop seam, and lower-limb articulation envelopes.
4. Inspect normal-speed media and phase-matched contact sheets.
5. Produce a bounded V8.2 transfer target that alters only balance-envelope channels and explicitly retains V8.1 leg/foot/contact behavior.

## Acceptance checks

- Both exact GLB hashes and both video facts are recorded.
- Metrics distinguish absolute basis/pose offset from cycle-local movement.
- Every proposed V8.2 envelope is expressed in hip-height-normalized translation or degrees and has a protected V8.1 channel boundary.
- The report states whether the user's impression is supported, mixed, or rejected.
