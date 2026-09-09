# Canonical support-anchor provider round-1 review — reviewer 2

Reviewed head `7b584f21cff3197d8afcba9fbd109ee9f29e5026` against parent `b31bcf655d72883d98e899e70f86213d3cec9730`. Scope was the six changed provider/compiler/skin/performance/test files only. The worktree was read-only and clean.

## Findings

### P1 — a provider is not bound to the solve request that consumes it

`solve_with_skin_targets` checks only `isinstance(provider, CanonicalSupportAnchorProvider)` and then copies its origins. It does not prove that the provider was built from the current source and uniform scale, semantic rig, solver gait, locomotion/transition law, decorated plan, contact region order, coordinate frame, or articulation profile. `gait_family_sha256` hashes only selected locomotion-gait parameters and is emitted as a receipt; the consumer never compares it.

The executable probe built a second provider from the same source/gait but with sole and toe contact regions exchanged, then passed it to a solve using the original contact profile. The current source keeps equal total counts, so shape checks cannot catch the mismatch. Both sides retain the same family digest; the consumer accepts the object and copies its origins. Ordered origins differ from the correctly bound provider by as much as `1.0462262098 m` left and `0.7905283979 m` right. `iterations=0` is used solely to prove the binding acceptance, not to claim contact quality.

The builder also accepts an independently changed `solver_gait.step_period_s` while the active plan and `locomotion_gait` remain unchanged. That mutation happens not to move this grounded touchdown anchor, but demonstrates that the solver member of the requested binding is unchecked. The public constructor can likewise create an arbitrary same-class provider without having called `build`.

Required fix: create one canonical binding record/digest covering every value that can affect anchor construction and material correspondence, and make the consumer recompute/compare it from its live arguments before reading an anchor. At minimum that includes admitted source identity plus uniform scale/current geometry, semantic roles, complete solver and locomotion/transition parameters with deliberate sampling exclusions, decorated performance/gaze inputs, contact profile and ordered per-region vertex identities, normalized axes, body height, and articulation profile. Construction must be private/tokenized or validate the same record. The consumer should verify side, count, ordered vertex-ID digest, finite origin shape, and lowest-index range. This is a binding fix; it does not change the event law, thresholds, or emitter.

### Sampling-family check

I did not reproduce a second current-asset failure from excluded sampling clocks. For `run.v4`, rebuilding at 24/60/120/240 Hz, including corresponding boundary/handoff rates, retained byte-equal left/right anchor arrays and one family digest. The response-driven chest/neck/head/tail nodes have zero weight on the current selected foot patches. This does not replace the missing live-request binding: a generic admitted rig may retain nonzero response-node weight below the foot-region threshold, so the postfix should either bind sampling-dependent inputs or explicitly prove that the selected material patch is independent of those nodes before omitting clocks.

No other P0/P1 finding was reproduced in the bounded scope. The canonical event construction itself is independent of the active output rows, start/steady/stop tests share the same exact touchdown references, and the stock provider's sole-then-toe ordering matches the exact-frame consumer ordering.

## Checks and evidence

- `130 passed in 10.24s`: `test_canonical_support_anchors.py`, `test_skin_refinement_final_state.py`, and `test_motion_performance.py`.
- The six provider tests alone passed in `2.55s`.
- `git diff --check` passed.
- Ruff reported only the existing semicolon statements at `skin_rig.py:46`, outside the changed lines.
- Reviewer probe: `canonical-anchor-round1-reviewer2-7b584f2.py`, SHA-256 `fa8bc745075ff179f1887cdf2e1f27f0148e444e5fc2fc3d0d1e16e712b854bf`.
- Reviewer JSON: `canonical-anchor-round1-reviewer2-7b584f2.json`, SHA-256 `d7d5f141e5d2dde7d6c3060ec489091db275c4fa45e0e51294dbbb1ab7d350f3`.
- Independently reproduced root probe JSON: `root-canonical-anchor-round1-probe.json`, SHA-256 `85fb2fcca8867816f3957b1382d74702557e159240d331135443b22597e39dce`.
