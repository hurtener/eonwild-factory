# V2 Learning Labs

Each lab changes one causal layer and produces a measurable comparison.

## Lab 1 — Neutral jaw calibration

1. Render jaw closure sweeps at 5° intervals.
2. Choose the largest closure without visible tooth or tongue collision.
3. Set `neutral_jaw_close_deg`.
4. Add less than 1° breathing gape.
5. Verify the loop and inspect side/front views.

Expected lesson: bind pose and animation-neutral pose are different contracts.

## Lab 2 — Foot trajectory shape

1. Keep stride and cadence fixed.
2. Compare a sine lift with `64t³(1−t)³`.
3. Frame-step toe-off and pre-contact.
4. Plot foot velocity and acceleration.
5. Keep the C2 curve unless a species reference clearly requires sharper timing.

Expected lesson: more samples do not repair discontinuous target motion.

## Lab 3 — Contact lock

1. Disable the FABRIK correction and render v1-like FK.
2. Enable foot targets but no pelvis balance.
3. Enable full v2.
4. Measure loaded horizontal contact error.
5. Inspect the ground grid at half speed.

Expected lesson: target planning and support transfer solve different problems.

## Lab 4 — Weight transfer

1. Set `pelvis_support_shift_gain` to zero.
2. Render front view.
3. Increase gradually while monitoring knee tracking.
4. Add pelvis roll only after lateral translation is convincing.
5. Reduce torso counter-rotation until some mass remains visible.

Expected lesson: support anticipation should occur before the opposite foot unloads.

## Lab 5 — Tail dynamics

1. Replace dynamic tail values with zero.
2. Re-enable support and yaw drive only.
3. Add velocity response.
4. Compare root/tip stiffness.
5. Review acceleration and stopping once those clips exist.

Expected lesson: a tail should react to momentum, not simply repeat the gait phase.

## Lab 6 — Sampling

1. Evaluate at 120 Hz.
2. Export at 30, 60, and 120 Hz.
3. Compare foot contact and tail tip at half speed.
4. Record GLB size differences.
5. Keep 60 Hz as default until a tolerance-bounded key reducer is added.

Expected lesson: dense export is cheap relative to a textured creature GLB, but only after the motion itself is correct.

## Lab 7 — Species profile

1. Duplicate `large-theropod-v2.json`.
2. Change only one parameter group at a time: cadence/stride, loading, torso, tail, then attention.
3. Render fixed cameras.
4. Save metric and perceptual notes.
5. Promote the profile only after two reviewers agree.
