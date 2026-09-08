# CUBICSPLINE Stage A post-fix review — 534ff53

Reviewed `534ff53eb6cf7133864e713fb33968828d944774` against its parent `b87c591954c5c5f313d22cad334471f825b62b0d`. Scope was the three-file consolidated fix diff: the shared TRS sampler, fail-closed CUBICSPLINE rate authority, and exact-tangent regressions. No source files were edited.

## Finding

**P1 — the LINEAR quaternion sampler still disagrees with its exact derivative on ordinary short intervals.**

`src/eonwild_motion/glb/animation.py::_shortest_slerp` switches to normalized linear interpolation when the quaternion dot product exceeds `0.9995`. The same track's `_linear_rotation_derivative` correctly reports the constant shortest-SLERP derivative. For a 0.06-radian rotation over 1/120 second, a sample immediately after the first key yields `7.198920080991454 rad/s`, while true SLERP and the derivative helper both yield `7.2 rad/s`. At a point one metre from the rotating joint this is `1.079919008546426 mm/s`, exceeding the governed `1 mm/s` linear threshold. This is a real consumer/validator disagreement, not only floating noise.

The new regression samples `t=1` in `[0,2]`, exactly the midpoint. Normalized lerp and SLERP coincide at the midpoint for unit endpoints, so that assertion does not exercise the faulty branch away from the midpoint.

Reproduction evidence: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/audits/root-cubic-short-slerp-534ff53.json`. Independent numeric reproduction matched the recorded values.

Required bounded fix: implement numerically stable shortest-path SLERP for all finite angular separations, with its small-angle limit handled analytically rather than substituting NLERP. Add a genuine quarter-time, short-angle sample regression and compare its finite-difference endpoint derivative to `_linear_rotation_derivative`. Do not lower the epsilon or gate.

## Other consolidated fixes

No additional P0/P1 defect was found in the reviewed diff. The patch correctly rejects negative/out-of-range accessor indices, requires FLOAT unnormalized SCALAR/VEC metadata, restores antipodal shortest-path behavior for non-small LINEAR rotations, and makes technical rate authority reject any CUBICSPLINE TRS channel until interval-extrema validation exists. The translation-only and scale-only CUBICSPLINE bypasses from round one are closed.

## Verification

- `tests/test_exact_emitted_tangent.py`: **20 passed in 1.78s**.
- Ruff on the two changed source files and exact-tangent test: **PASS**.
- `git diff --check b87c591..534ff53`: **PASS**.
- Independent 0.06-radian/1/120-second probe reproduced sampler `7.198920080991454`, exact/helper `7.2`, and one-metre discrepancy `1.079919008546426 mm/s`.

Verdict: **P1 OPEN**. One narrow fix and exceptional diff-only re-pin is sufficient; no third full Stage A review is warranted.
