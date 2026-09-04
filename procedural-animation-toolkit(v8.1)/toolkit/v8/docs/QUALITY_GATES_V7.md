# V7 Quality Gates

## Structural

- GLB 2.0 header and chunk lengths valid.
- Source skin joint count and order preserved.
- Inverse-bind matrices preserved.
- All animation target nodes exist.
- All sample timelines are strictly increasing.
- No duplicate animation names.
- Every non-transition clip carries root and pelvis translation channels.

## Locomotion anatomy

- Zero knee branch reversals.
- Zero ankle branch reversals.
- Flexion remains inside profile limits.
- Joint velocity and acceleration remain below species gates.
- Rear stance does not exceed the compact relaxed-walk envelope.

## Contact

- Loaded sole penetration remains below the hip-normalized threshold.
- Stable loaded sole-gap quantile remains below threshold.
- Swing foot clears terrain.
- Pelvis is solved before the legs.
- Exported pelvis local translation is reconstructed from the same solved pose.

## Relaxed body motion

- Lateral and vertical pelvis ranges remain small relative to hip height.
- The body does not hover or fly sideways.
- Root-motion and in-place variants share identical local body/leg tracks.

## Turns

- Head lead ≥ 5°.
- Neck lead ≥ 3°.
- Head lead > neck lead > chest lead.
- Peak lead begins before half of final root heading.
- Tail counter-shape ≥ 2° target.
- Inside/outside step plans differ.
- Contact and anatomical gates remain green.

## Actions

- Idle jaw remains at calibrated living-neutral closure.
- Bite closes at contact and at recovery.
- Eating uses pelvis/legs/body lowering, not neck-only reach.
- Mirrored bite is mechanically mirrored and separately validated.
- Roar returns to neutral closure.

## Transitions and player

- Rotation endpoint error ≤ 1e-10 rad.
- Translation endpoint error ≤ 1e-10 m.
- Root and pelvis are included in every transition bridge.
- Authored sequence handoff adds no second crossfade.
- Player controls reflect active clip/action/playback state.
- Root-motion loops accumulate cycle displacement.

## Perceptual review

Review at side, three-quarter, front, and overhead cameras. Human approval remains required for:

- mass and timing
- head attention
- tail response
- foot roll and toe-off
- silhouette continuity
- attack commitment
- feeding readability
- transition feel
