# Adult axial clock round 1 — reviewer 1

Exact implementation `483e006b1ddd20617b75e32b2e660b31e5ed0853`, parent `26ec06837cd03d59bd03d6bf948ae6e7d8cf4212`. Reviewed only the two-file axial diff. Independent focused run: `tests/test_motion_performance.py tests/test_phase_local_solved_pose.py`, **105 passed in 10.14 s**.

The new clock has the agreed leading-hemipelvis sign, zero at the canonical stance midpoints, uses canonical grounded double-support witnesses independently of finite sample rows, and applies the corresponding tail clock after centering. Default profile serialization and the heavy/renamed phase-local payload pins pass. This is code-level evidence; the body-only diagnostic package and visible-motion improvement are still pending.

Two concrete local P2 fixes are requested before the post-fix freeze. No P0/P1 finding in this review.

## P2 — bind both hip roles to the pelvis whose rotation carries them

`_support_timed_axial_clock` checks bilateral positions but does not verify that the hips descend from the semantic pelvis. I reparented both synthetic hips from pelvis to root while preserving their world rest positions. The helper still admitted the source and returned pulse +1 at the first double-support midpoint. Actual performance application then displaced **both hips by exactly 0 m forward**: its advertised leading-hip carrier did not reach either leg.

Validate distinct typed semantic hips and their ancestry beneath the bound pelvis before accepting this option. Allow supported intervening hierarchy helpers if appropriate; do not require an unnecessary universal immediate-parent layout. Add a reparented-hip negative control and a valid transformed/helper hierarchy control. This is a new-carrier binding check, not a request to redesign or re-review all legacy rig validation.

## P2 — preserve the omitted option's original tail arithmetic

The tail expression is reassociated even when the axial option is omitted: historical `-gain * amplitude * weight * sin(...)` becomes `-amplitude * weight * (gain * sin(...))`. Running old and new `apply_performance` side-by-side on 300 deterministic source poses with partial transition gain changed **181 float64 rotation arrays**, maximum quaternion component difference `2.0816681711721685e-17`. No float32 differences were observed in this particular fixture, so this is not a demonstrated visible regression or a claim that its emitted GLB differs.

The declared scope nevertheless promises an unchanged legacy arithmetic path. Retain the exact original expression in the `axial_clock is None` branch and use the new expression only when opted in. Add a deterministic omitted-option partial-gain rotation equality witness. This is a small local compatibility fix, not a new render requirement for the unchanged new-clock branch.

Reviewer 1 made no implementation edits. No recipe, threshold, amplitude, source asset, or approval status was changed.
