# V8.1 relaxed-walk respin — approval candidate

## Result

Iteration 15 is the all-pass isolated V8.1 relaxed-walk candidate. It preserves accepted V8.1 rig/posture/pivots and makes no change to the source GLB, canonical profile, validated result, or existing `showcase/v8.1` material.

The sole delivery film is [walk-relaxed-v8-1-respin-side.mp4](../../showcase/v8.1-walk-respin/iteration-3/walk-relaxed-v8-1-respin-side.mp4): fixed side view, in-place, 960x540 H.264/yuv420p, 24 fps, 240 frames, and exactly 10.000 seconds. Iteration 3 changes only the presentation: a lighter neutral floor and raised existing key/fill/rim lighting make the toe/contact shadow readable. No GLB, motion, profile, camera envelope, or render duration changed. No other animation film, still, montage, or gallery is delivered. The interrupted pre-lock PNG sequence in `showcase/v8.1-walk-respin/iteration-1/` is explicitly non-delivery work.

## Measured final GLB

The candidate has a single scene-root scale wrapper, `RESPIN_REFERENCE_SCALE_ROOT`, at `12.0 / 5.974026 = 2.0086956434`; this is not vertex/bone baking and must not be applied twice.

| Measure | Result |
| --- | --- |
| Candidate world hip height | 2.75636 m |
| Reference-calibrated same-foot stride | 2.75000 m |
| Reference-calibrated mean speed | 1.27875 m/s; 4.60350 km/h |
| Root-motion distance / duration | 5.51272 m / 4.30108 s |
| Selected-sole worst penetration | 0.00000 m across every baked key |
| Greatest lowest-support contact quantile | 0.00619 m |
| Left/right toe-loaded metatarsal lift | 0.00926 m / 0.00589 m |
| Late stance | toe-loaded metatarsal rise, then toe release on both sides |

Both clips have 259 measured/exported keys. The final validation passes immutable proof, key coverage, 4.5–4.8 km/h speed, stride, longer bounded reach, no penetration, support, joint continuity, and bilateral toe-contact/release order.

The candidate-local constrained toe-contact solve uses bisection against actual weighted distal toe vertices only during late stance. It changes toe roots, never the metatarsal/foot node; its maximum solved correction is 3.104 degrees and it eases to zero for release.

## Provenance

- Source GLB SHA-256: `fbb42c2edad4eadebbcf808d32028d7c73b3fbfd6172610eddd5df84990a65c7`
- Canonical profile SHA-256: `f128bd39cca62a674855ffbcce2e88226cec3b17048bf9a830bd158238240143`
- Candidate GLB SHA-256: `96bf5c37402bd784b23785173fbb9a45cd8cbbed33ea2fd0675bdfd11c48a5a1`
- Approval MP4 SHA-256 (iteration 3): `4a654cad0878dcb710090b44d7647644215b0c3b9a696566c1638ecf347145dc`

Machine-readable evidence: `candidates/v8.1-walk-respin/generated/iteration-15/generation-report.json`, `candidates/v8.1-walk-respin/generated/iteration-15/walk-respin-validation.json`, and `showcase/v8.1-walk-respin/iteration-3/render-run.json`. `ffprobe` verified H.264, yuv420p, 960x540, 24/1 fps, 10.000000 seconds, and 240 decoded frames. The final candidate GLB hash still matches the validated value, and the accepted V8.1 package manifest verified all 285 non-cache files with zero mismatches.

This remains a visual approval candidate; the supplied captures are pose/timing references rather than calibrated motion capture. No commit or push was made.
