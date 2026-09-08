# Phase-local solved-pose extraction — round 1 reviewer 2

Reviewed head: `e6c0b6f6daefba490305a79722ebb1644ffd1a41`

Base: `cc7b3d9e199d1679d28bbcbefb61bcea5407b129`

Scope: read-only review of the extracted `AirborneSolveContext`, `SolvedAirbornePose`, and `solve_airborne_plan_sample` seam. No arbitrary-time, interpolation, emitted tangent, or continuous skin claim was assessed.

## Findings

### P2 — the frozen context is shallow and caller mutation changes later results

`AirborneSolveContext` is declared `@dataclass(frozen=True)` and documented as read-only at `src/eonwild_motion/solve/airborne_gait.py:326-360`, but it retains ordinary mutable `roles`, `plan`, `legs`, `toes`, `hip_offsets`, and `Glb` references plus writable NumPy arrays. Construction at lines 835-847 marks only `base_w` matrices read-only. A direct probe found `up`, `forward`, `lateral`, and `origin` all `flags.writeable == True`; assigning `context.forward[:] = context.lateral` changed the translation returned for the same unchanged row. Editing the caller-owned roles/plan/source references has the same shared-state class of risk.

Normal `solve_airborne_gait` use does not mutate this state, and the supplied order-independence test passes, so this is a defensive API-contract defect rather than an observed output regression. Before a caller retains/reuses the context, snapshot mutable mappings/geometry and make all derived arrays and nested normal arrays immutable. Add a regression that attempted caller mutation rejects or cannot affect a repeated same-row solve.

### P2 — malformed direct seam inputs leak implementation exceptions

The new callable starts reading the row and optional body response directly at lines 395-407. Removing `root_forward_m` from an otherwise valid captured plan row raises raw `KeyError('root_forward_m')`; passing `body_response_sample={}` raises raw `KeyError('sagittal_node_degrees')`. The internal full-clip caller is protected because `_validate_plan_override` and `driven_body_response` run first, so accepted output is unaffected. For the direct seam, either validate/normalize its documented already-built row/body-response payload or translate malformed payloads to `ContractError`, and test both cases.

### P2 — one adjacent source-level regression and new lint fail after extraction

The meaningful focused batch produced `50 passed, 1 failed`. `tests/test_articulated_contact_partition.py:66-72` searches `inspect.getsource(solve_airborne_gait)` for two implementation strings that moved into `solve_airborne_plan_sample`; the behavior remains present, but the test now fails. Point the safeguard at the extracted seam or replace it with its behavioral FK witness. Ruff also flags the newly added unused `numpy` import at `tests/test_phase_local_solved_pose.py:9`. Ruff separately reports a pre-existing unused local alias in `_validate_plan_override`; that unchanged line is outside this finding.

## Independent checks

- Independently executed the exact base implementation from a `git archive` of `cc7b3d9` against the production-shaped source. Its root-motion and in-place SHA-256 values are respectively `b806d588964d0ad8d4ef9bcea3c567a30f1cd9b65888b6cb1ccb859080e9a417` and `fa7cb0e645b9a0d3c09bb9d07260713448b99d6bb0d2889d8870c76c2080a880`, exactly matching the new head's regression expectations.
- The transformed/renamed fixture, same-row order-independence, production payload identity, gait, articulation, and world-metatarsus checks passed except for the stale source-introspection assertion described above.
- `git diff --check` passed.
- Worktree remained clean at the reviewed exact head; no source, test, or documentation edits were made.

No P0 or P1 finding.
