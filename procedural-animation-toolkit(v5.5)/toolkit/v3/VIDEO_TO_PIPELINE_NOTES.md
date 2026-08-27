# Video-to-Pipeline Notes

## Supplied Tarbosaurus side-view reference

File:

```text
Tarbosaurus#walk_side_v02.mp4
```

Measured file properties:

```text
duration: 8.041667 seconds
video rate: 24 fps
video frames: 193
resolution: 736 × 400
```

Visual observations used for V3 profile tuning:

- The opening portion includes mouth/pose transition and is not treated as pure steady locomotion.
- The later steady walk suggests roughly a two-second gait cycle.
- Ground support occupies a large portion of each cycle.
- The torso is forward-balanced but not pitched into a running/crouched attitude.
- The skull is carried near the horizon with controlled residual motion.
- The tail root remains muscular and comparatively stable while the distal tail shows delayed compliance.
- Swing legs retain anatomical knee and ankle folding while moving from rear extension to forward placement.

These are silhouette-based estimates, not marker-based motion capture. V3 records them as profile assumptions and retains human perceptual review.

## Procedural-animation tutorials supplied earlier

The tutorial videos establish useful authoring principles:

- expose meaningful procedural controls;
- derive repeated motion from compact signals;
- layer deterministic phase and secondary variation;
- sample/bake the result into standard animation.

V3 extends those principles for creature locomotion with persistent contacts, constrained anatomical solving, support-aware balance, neutral-pose layers, and inertial tail response.

## What was not inferred from the reference

The video does not provide reliable skeletal joint centers, mass distribution, foot pressure, terrain depth, or exact camera calibration. V3 therefore does not claim physically measured biomechanics. Those remain model/profile assumptions until a marker, multiview, or physics-supported reference workflow is added.
