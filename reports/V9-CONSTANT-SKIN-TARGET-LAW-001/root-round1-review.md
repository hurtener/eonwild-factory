# Constant skin-target law: root round 1

Reviewed head: `07514b8` in the canonical-constant-skin-target-law worktree, based on the closed provider `f847630`. Scope: the new law module and its two tests. No recipe or emitter activates it.

Decision: **CHANGES REQUIRED — two P1 issues.** Wait for the independent first review before a consolidated postfix.

## P1: bind and preserve the actual evaluation state

`build` validates the independently supplied request and provider, but never proves that its separately supplied `SourceMotionQuery` is that request. Root constructed a valid query with pelvis yaw 3 degrees and supplied a provider/request bound to 2 degrees. Construction succeeded and `value(.2)` returned `AVAILABLE`. The actual query source, roles, gait/transition, decorated plan, frame, contact and articulation context must be admitted against the same request. Prefer a single authoritative query/request binding over parallel unconnected argument lists.

Returned `corrections_m` arrays are the law's owned arrays. Root enabled writes on a returned left correction and added 10 mm vertically. A later evaluation used the changed value without any binding or integrity rejection. Return detached data and preserve a checked immutable internal calibration; do not rely on an exposed NumPy writeable flag as ownership isolation.

## P1: enforce the promised pointwise geometry checks

`_observe_at` always returns `AVAILABLE`. It computes residual and clearance observations, but does not reject a loaded residual beyond 0.2 mm, failed clearance, or infeasible IK/articulation. In the executable returned-array probe, the later result was still `AVAILABLE` with a loaded residual of `0.010006475526659746 m`, gap `0.01010647552665615 m`, and `clearance_ok=true`. Positive clearance alone does not establish loaded contact.

After both constants are applied, check all loaded feet together at both calibration events and every requested time; check unloaded clearance and the existing pointwise target-residual, extension and articulation criteria. A failed value must be explicitly unavailable/rejected, with the observed reason retained. Missing derivative or branch-stability authority should remain separate from a checked pointwise pose value and must not be relabeled as proven continuity.

## Verification and evidence limits

Root inspected the complete new module and tests and executed both API probes above against the frozen code. The author reported 11 focused tests (nine provider tests plus two new law tests). The new tests do not exercise the promised mismatched query, returned-state corruption, failed loaded contact, clearance failure or incompatible/cross-influence geometry boundaries.

The initial full-cycle JSONs contain unqualified source observations: they do not retain source/recipe/code/input hashes or a reproducer, and the adult file contains only aggregate values. They cannot yet substantiate exact recipe-level coverage. The test helper also replaces the loaded walk performance with `Performance` defaults; the exact full-cycle inputs need to be clarified. Preserve the observations as provisional, and bind the corrected full-cycle run to the actual recipes, all performance/articulation/gaze inputs, source and code.

The closed provider, default runtime, thresholds, existing movies and prior review stages are not reopened by this review.
