# Exact emitted tangent reproduction and bounded continuation proposal (v2)

**Source evaluator:** `52e826ccd7e05dd2e82c37e889af8cf0a977c7a0` in the clean external SSD worktree. This was read-only against existing GLBs; no render, compile, recipe, source, or threshold changed.

**Artifacts:** `exact-emitted-reproduction-52e826c-v2.json`, SHA-256 `067985a967d586ae1005afac9c40f18cf86a149ffa8c45ed6a251620f635bb91`; `reproduce-exact-emitted-52e826c.py`, SHA-256 `2d591791ed3aafa9d43c2f4bc882587e2ddbc422734753fc0ca4df599b6297ff`.

## Reproduction

The exact adjacent LINEAR translation/scale, shortest-SLERP, product-rule FK and LBS calculation reproduces the prior generic scope audit. Values below are maximum world / bound-material handoff speed differences in mm/s, root-motion then in-place.

| gait | start root | start in-place | stop root | stop in-place |
| --- | ---: | ---: | ---: | ---: |
| walk | 48.454 / 26.647 | 48.561 / 26.663 | 48.524 / 26.649 | 48.524 / 26.649 |
| reverse walk | 5.754 / 3.910 | 5.754 / 3.909 | 5.635 / 3.902 | 5.635 / 3.902 |
| run | 180.861 / 181.541 | 180.923 / 181.603 | 180.974 / 181.653 | 181.003 / 181.683 |
| sprint | 129.332 / 129.727 | 129.351 / 129.745 | 129.263 / 129.651 | 129.263 / 129.651 |

All are above the unchanged 1 mm/s limit. In-place reconstruction uses the declared per-adjacent-key motor velocity and matches the independent audit values; it is not a separate root-motion or clock problem.

The exact local cyclic metric also blocks each retained steady export: walk 2.282 mm/s and 3.178 deg/s; reverse walk 3.460 and 1.698; run 47.942 and 6.332; sprint 70.390 and 5.441. Both modes agree. These are local translation / local angular values only, not a world/skin loop claim.

Fast recovery C3 (`f53782e` package) is also locally discontinuous under the exact metric: 5.406219 mm/s at `Bone_001` and 6.683922 deg/s at `Bone_009`, identically for its root-motion and in-place GLBs. This does not alter its prior per-frame articulation/rate receipt; it adds a truthful serialized loop-representation blocker.

Adult-v6 postfix was measured from root-verified `/Volumes/m2-extended-disk/Repos/eonwild-factory/out/continuation-adult-v6-sagittal-body-001/postfix-package`: root-motion SHA-256 `4a2c3587d932a8c8bab002b9e536f1ed22a28388e928cbe18fe8845b553e7e7b` and in-place SHA-256 `2878670fbeacfd7e99014e8a75537d5711deea5ceafc96362b5fbc545a63aa0b`. Both have exact local cyclic linear mismatch 1.728740 mm/s and angular mismatch 3.410360 deg/s. It is therefore technically blocked by the unchanged 1 mm/s local linear limit; this does not alter its existing body visual or Unity status.

## Cause and feasible representation correction

A sampled analytic motion can be position-continuous while its exported LINEAR/SLERP segments are not velocity-continuous. At a join, direct playback requires

- `(p_N - p_{N-1}) / dt_N = (p_1 - p_0) / dt_0` for every relevant local translation/scale channel; and
- the two adjacent shortest-SLERP angular-velocity vectors to agree when expressed at the matched endpoint orientation.

The current solvers can supply smooth intended motion, but independent clips quantize that motion into different adjacent straight/chord segments. Equality of endpoint poses therefore cannot supply C1 playback except in the special case where those discrete segment slopes already match. Copying a boundary pose, holding frames, retiming, filtering after export, or relaxing the threshold cannot establish the missing derivative contract and is excluded.

**Bounded next stage proposal:** add a source-level pose-and-tangent interface for paired transition/steady planning. It carries each channel's already-authored endpoint value and first derivative at the declared handoff phase, including declared motor velocity. The solver remains responsible for contact choreography and its original sample clock. The emitter serializes those values with glTF CUBICSPLINE Hermite tangents, assigning the same interface tangent to the two meeting endpoints. It does not copy a pose, add a hold, alter duration, crossfade, or smooth an already-written GLB. The exact evaluator gains a CUBICSPLINE branch that reads the serialized in/out tangents directly and propagates them through FK/LBS.

For stance/contact channels, constrain the analytic endpoint tangents before export: a locked contact point receives its planned zero tangential velocity in the reconstructed world frame; release and landing use the planner's own nonzero derivative. Validate Hermite segments between native keys for floor gap, penetration, slip and articulation/rate extrema, because cubic interpolation can overshoot even where keyed contact values pass. The existing motor remains the sole in-place transport term and is included in both endpoint derivatives.

## Acceptance boundary for that single stage

1. No changed recipe durations, native sample times, boundary poses, thresholds, geometry, or post-export filters.
2. New negative tests prove LINEAR cannot claim C1 for the existing chord mismatch and that malformed, nonfinite, or nonmatching CUBICSPLINE tangents fail closed.
3. All eight generic start/stop handoffs meet the current 1 mm/s world and material limits in both modes under exact CUBICSPLINE/FK/LBS evaluation; all four steady clips meet the existing local cyclic limits.
4. Reopen final GLBs and check contact over interpolation intervals, joint rate/articulation limits, deterministic replay and source hashes. The fast and adult candidates are separately recompiled only if their own package scope is selected.
5. Native-time visual review and Unity compression/import parity remain pending after technical success.

This is a representation correction, not a claim about animal forces, COM, biological gait reconstruction, or Unity behavior already implemented.
