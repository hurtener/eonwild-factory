# Reference-Fitted Tarbosaurus Timing and Posture

V4 treats the supplied side-view clip as evidence, not as ground-truth motion capture. The source is a 193-frame, 24 FPS render without camera calibration, markers, force plates, or a known scale, so the fitter extracts repeatable silhouette and timing information while leaving uncertain biomechanical values profile-driven.

## Automated analysis

`reference_fit.py` performs the following deterministic sequence:

1. Decode every video frame with OpenCV.
2. Estimate the cyan/gray background from border pixels.
3. Segment the dinosaur by color-distance and saturation/value differences.
4. Retain the largest coherent foreground component.
5. Normalize the silhouette to reduce screen translation and framing bias.
6. Build lower-body occupancy features for gait recurrence.
7. Compare candidate lags over the stable walking window.
8. Estimate the most repeatable full-cycle interval.
9. Track bounding-box, centroid, vertical and silhouette descriptors for posture review.
10. Write the complete fit report and a contact sheet rather than returning only a cadence number.

## Current fixture result

For `Tarbosaurus#walk_side_v02.mp4`:

```text
resolution:             736 × 400
frame rate:             24 FPS
frame count:            193
video duration:         8.0417 seconds
stable-walk start:      approximately 2.25 seconds
selected cycle lag:     54 frames
selected cycle:         2.25 seconds
selected cadence:       0.4444 Hz
production profile:     0.45 Hz / 2.2222-second cycle
```

The profile rounds the fitted cadence slightly so loop durations, state timings, and browser motion scheduling remain practical while staying within the reference uncertainty.

## What is fitted

- relaxed cadence and broad duty factor;
- stride rhythm and swing/stance timing;
- a high-support, unhurried gait character;
- torso carried closer to level than a running posture;
- skull carried near the horizon;
- progressively compliant distal tail response;
- mostly closed neutral jaw during ordinary locomotion.

## What is not claimed

The reference does not provide calibrated:

- absolute speed;
- true body scale;
- center of mass;
- ground-reaction forces;
- three-dimensional joint trajectories;
- hidden-side foot contacts;
- muscle or soft-tissue deformation.

Those remain constrained procedural estimates and must be reviewed against paleobiological references, additional views, and gameplay cameras.

## Determinism

The analysis output includes candidate lag scores, confidence, stable-window selection, posture statistics, and source metadata. Any later profile retuning should keep the original report so a reviewer can distinguish evidence-derived timing from artistic choices.
