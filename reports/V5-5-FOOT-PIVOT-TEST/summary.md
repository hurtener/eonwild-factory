# V5.5 lower-foot pivot test

The requested quick test is ready. Both foot pivots were lowered toward the point where the three toes branch, with the same anatomical-axis adjustment on both legs. The accepted V5.5 GLB and showcase were left unchanged; this folder contains a separate candidate for evaluation.

## Candidate evidence

- Ten-second Blender walk: `render/films/walk-relaxed-inplace.mp4`
- Machine-readable adjustment evidence: `pivot-adjustment.json`
- Full-body, foot-phase, ankle-detail, loop-seam, and deformation-difference evidence: `evidence/`
- The 62.6 MB candidate GLB is not duplicated in the repository; its hash is retained below and it can be regenerated with the committed adjustment script at `--gap-fraction 0.75`.

## Result

- Blender 5.2.0 LTS, Eevee/Metal, 960x540, 24 fps, H.264.
- Film duration: exactly 10.000 seconds / 240 frames.
- GLB SHA-256: `1480847ef9bd56298ab5f934cc2ea1a48bdd3198fc21590fbd0fa0fbd9b4dad6`.
- MP4 SHA-256: `9cc8bdb66c926bf8a341a75d91b07b6bb10bbcb2e74c922c87a1b28493e581f3`.
- V5 immutable hash: `c4f4905f2974aa751a7fe0485a44d194898ead71280992c34d0129dc81362119`.
- Accepted V5.5 source GLB hash remains `4020d6d3db42231d5fb414c3d42ab0d702c5bfe08aeae8e919deefaacde7d287`.
- Existing V5.5 suite: 7 tests passed; release validator and site checker passed.
- Adversarial review: P0=0, P1=0; ready for user perceptual review.

## Release boundary

This 75% experiment remains preserved as the rejected first comparison. The user selected the subsequent 90% placement, which is the only placement promoted into the canonical V5.5 build.
