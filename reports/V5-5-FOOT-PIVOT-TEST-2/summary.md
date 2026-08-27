# V5.5 lower-foot pivot test 2

Candidate two moves both foot pivots one additional step downward while preserving candidate one for comparison. After user approval, this placement was promoted into the canonical V5.5 builder as profile-driven calibration; V5 remains unchanged.

## Artifacts

- Canonical promoted GLB: `../../procedural-animation-toolkit(v5.5)/validated_result/v5.5/tarbosaurus_procedural_v5_5_animation_pack.glb`
- Candidate-two ten-second walk: `render/films/walk-relaxed-inplace.mp4`
- Synchronized comparison: `render/films/test-1-left-vs-test-2-right.mp4` — candidate one is left; candidate two is right.
- Structural evidence: `pivot-adjustment.json`
- Matched-phase evidence: `evidence/`
- The reviewed candidate GLB is not duplicated under this report because the canonical regenerated artifact has the exact same SHA-256.

## Measurements

- Baseline-to-candidate-two movement: `10.4443 cm` downward.
- Candidate-one-to-candidate-two movement: `1.7407 cm` downward.
- Remaining distance above toe-root plane: `1.1605 cm`.
- Candidate-two GLB SHA-256: `4e6e85dc82e941a3fc10109ca781dd3dcbb084699dc19834bf8683c04b22fe65`.
- Candidate-two MP4 SHA-256: `59d609980c79a0d1a454d5b09cf4b57486b61ca360ba9c719f8405270973c7ca`.
- Comparison MP4 SHA-256: `0843959f856e090250abe314075c46b72df59c7b106703d0932af93055b558f4`.

## Verification

- Blender 5.2.0 LTS / Eevee-Metal import and render passed.
- Candidate film: H.264, 960x540, 24 fps, 240 frames, exactly 10 seconds.
- Comparison film: H.264, 1920x540, 24 fps, 240 frames, exactly 10 seconds.
- Existing V5.5 suite: 7 tests passed; release validator and site checker passed.
- V5 immutability passed.
- Review: P0=0, P1=0.

## Integration boundary

The accepted `0.90` gap fraction lives in `tarbosaurus-v5.5.json`; the builder measures each leg from its actual foot joint to the centroid plane of its three toe roots. The canonical regenerated GLB is byte-for-byte identical to this reviewed candidate.
