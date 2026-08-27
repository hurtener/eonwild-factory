# V3 Learning Labs

## Lab 1 — Reproduce and remove the wrong IK branch

1. Temporarily allow knee/ankle angles to cross zero.
2. Frame-step rear-to-front swing.
3. Record the first signed-angle reversal.
4. Restore source-derived hinge signs and non-zero minimum flexion.
5. Verify zero reversals across the full 120 Hz superloop.

Lesson: unconstrained IK may reach a target through an anatomically impossible branch.

## Lab 2 — Flexion margin versus reach

1. Sweep knee minimum flexion from 5° to 25°.
2. Sweep ankle minimum flexion from 5° to 22°.
3. Plot target error and joint acceleration.
4. Keep the largest safe margin that does not visibly degrade placement.
5. Prefer small target miss over hyperextension.

Lesson: anatomical validity outranks exact Cartesian reach.

## Lab 3 — Temporal continuity

1. Set `leg_continuity_weight` to zero.
2. Record knee/ankle velocity and acceleration.
3. Increase continuity gradually.
4. Compare contact error and frame-step smoothness.
5. Keep foot target curves C2; do not use filtering to hide discontinuous planning.

Lesson: smooth target planning and solver continuity solve different problems.

## Lab 4 — Relaxed versus running-like posture

1. Hold leg timing fixed.
2. Render V2 posture, V3 relaxed posture, and an over-upright candidate.
3. Compare the skull to the horizon and chest-to-pelvis line.
4. Distribute corrections across pelvis, spine, neck, and head.
5. Reject a single-joint “fix.”

Lesson: species silhouette is a distributed pose.

## Lab 5 — Tail root and tip

1. Render tail dynamics disabled.
2. Use uniform high stiffness.
3. Use V3 root-to-tip stiffness and lag.
4. Compare support transfer and tip settling.
5. Reject both plank-rigid and weightless-whip behavior.

Lesson: a heavy tail needs a muscular base and delayed distal compliance.

## Lab 6 — Neutral mouth

1. Render the bind pose.
2. Sweep jaw closure safely.
3. choose neutral locomotion closure.
4. add sub-degree breathing gape.
5. reserve large gape for actions.

Lesson: bind pose is not the living neutral pose.

## Lab 7 — V4 handoff

After V3 passes, add one capability at a time:

1. vertex-weighted sole collision;
2. terrain height and normal adaptation;
3. turning;
4. acceleration and braking;
5. alert, eat, bite, and roar layers;
6. reference-fitted species profiles.

Lesson: preserve the validated anatomical kernel while extending targets and state layers.
