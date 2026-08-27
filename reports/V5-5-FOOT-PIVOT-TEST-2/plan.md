# V5.5 lower-foot pivot test 2

## Intent

Follow the positive first foot-pivot test with one controlled additional downward step. Preserve candidate one and create a separate candidate two for direct perceptual comparison.

## Adjustment

- Move `foot_l` and `foot_r` to 90% of their original vertical gap toward the three-toe-root plane.
- This is 15 percentage points farther than candidate one: approximately `0.0174 m` additional downward travel.
- Leave approximately `0.0116 m` between each foot pivot and its toe-root plane.
- Preserve fore/aft and lateral placement, toe-root origins, undeformed mesh shape, hierarchy, animation arrays, and frozen V5 content.

## Acceptance checks

1. Candidate two is separate from candidate one and the accepted V5.5 release.
2. Both sides receive the same anatomical-axis adjustment within `1e-6 m`.
3. Toe-root rest origins and undeformed skinned vertices remain unchanged within `1e-6 m`.
4. Joint order and all 37 animation payloads remain unchanged.
5. Blender renders exactly 10 seconds / 240 frames at 960x540 and 24 fps.
6. Matched-phase comparison finds no new collapse, pinching, ground penetration, or cycle seam.
