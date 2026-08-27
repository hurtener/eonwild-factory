# Changelog

## 3.0.0 — anatomical constraints and relaxed Tarbosaurus walk

- Preserved V1 and V2 as separate baselines.
- Replaced the unconstrained leg branch with a signed-hinge, bounded sagittal solve.
- Added source-derived knee and ankle bend direction.
- Added hard knee/ankle flexion ranges and minimum-flex guards.
- Added previous-sample continuity regularization and bounded/backtracked solver steps.
- Added per-sample diagnostics for signed angle, flexion range, velocity, acceleration, and flip count.
- Added a hard fixture gate requiring zero knee and zero ankle anatomical reversals.
- Retuned the Tarbosaurus walk to a relaxed approximately 2.0-second cycle with 72% stance.
- Raised the V2 running-like torso/neck attitude into a horizon-facing relaxed walk.
- Softened the nine-segment tail using lower distal stiffness, per-bone lag, larger distal allowance, and mild neutral sag.
- Kept the neutral closed-mouth locomotion layer and breathing micro-gape.
- Kept 120 Hz internal evaluation, 60 Hz export, in-place/root-motion clips, and exact loop closure.
- Added analysis notes for the supplied `Tarbosaurus#walk_side_v02.mp4` reference.

## 2.0.0 — contact-aware body and tail architecture

- Added world-space contact planning, articulated leg targeting, support-weight balance, neutral jaw, dynamic tail, dense sampling, direct GLB bake, and V1/V2 visual comparison.

## 1.x — phase/FK proof

- Proved that semantic mapping can drive the complete rich Tarbosaurus rig and bake valid GLB animation.
