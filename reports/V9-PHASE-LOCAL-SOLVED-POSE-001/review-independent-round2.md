# Phase-local solved-pose extraction — round 2 reviewer 2

Reviewed head: `79bc9f9cab6e3aebbae9e1aeb6e90324de4371e5`

Parent: `e6c0b6f6daefba490305a79722ebb1644ffd1a41`

Base: `cc7b3d9e199d1679d28bbcbefb61bcea5407b129`

Scope: final narrow review of the immutable retained context, direct plan-row/body-response validation, stale adjacent regression repair, and legacy output identity. No arbitrary-time, interpolation, tangent, interval, or skin-continuity claim was reviewed.

## Finding

### P2 — optional articulation profile remains a mutable caller alias

The postfix replaces the retained mutable `Glb` with immutable topology, recursively freezes roles/plan/leg maps and arrays, and freezes the `AirborneSolveContext` shell. However, `AirborneSolveContext.articulation_profile` at `src/eonwild_motion/solve/airborne_gait.py:425` still receives the caller's original `ArticulationProfile` instance at lines 931-943. That dataclass is shallow-frozen: its `support`, `swing`, `angle_conventions`, and `evidence` fields are ordinary dictionaries.

Reproduction using the transformed fixture with the versioned articulation profile:

1. Capture the context during `solve_airborne_gait(..., articulation_profile=profile)`.
2. Confirm `context.articulation_profile is profile` and `type(profile.support) is dict`.
3. Solve a retained row once, then call `profile.support.clear()` from the caller.
4. Re-solving the unchanged row raises raw `KeyError('hip_sagittal_degrees')`.

This affects only contexts constructed with the optional articulation profile and requires a caller to mutate a validated input after context construction. Normal full-clip generation is unchanged, so this is P2 defensive debt rather than a P0/P1 release defect. A future local fix can snapshot the profile into an equivalent instance whose nested mappings/evidence are recursively immutable, with a retained-row regression. Under the repository's round-two cap, this P2 does not reopen implementation.

## Closure evidence

- Context geometry is now an immutable minimal topology snapshot; caller mutations to the original `Glb`, roles, and plan do not affect retained evaluation.
- Writes to nested frozen roles/plan/topology mappings and the forward/anatomical-normal arrays reject. Repeating the same row returns the same result.
- Missing `root_forward_m`, absent body-response degrees, nonfinite body-response degrees, and malformed target-offset conversion raise `ContractError` at the direct seam.
- The stale articulation source-introspection test now targets `solve_airborne_plan_sample` and passes.
- Focused independent batch: `53 passed` across phase-local, airborne gait, world-metatarsus, and articulated-contact tests.
- Independent base execution from an archived `cc7b3d9` source tree previously produced root-motion `b806d588964d0ad8d4ef9bcea3c567a30f1cd9b65888b6cb1ccb859080e9a417` and in-place `fa7cb0e645b9a0d3c09bb9d07260713448b99d6bb0d2889d8870c76c2080a880`; the post-fix regression still passes those exact hashes.
- `git diff --check` passes. Ruff has no new-head finding in the changed lines; it still reports two pre-existing unused imports outside this postfix (`_rebuild` in the solver and `replace` in the adjacent test).
- Worktree remained clean at the reviewed exact head. No files were edited.

No P0 or P1 finding.
