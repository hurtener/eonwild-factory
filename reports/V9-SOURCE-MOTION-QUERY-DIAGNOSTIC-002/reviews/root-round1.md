# SourceMotionQuery review round 1 — reviewer 1

Reviewed exact freeze `c02a17769d86841d9c9dddb66b4e0ed8e9365deb` (implementation `6d3f8e32b839a6e0b20a5f2ede73bf0ea2b81767`). Scope is this diagnostic diff only; no reopening of prior phase-local or bind-admission stages.

Decision: changes required. Independent focused run: `tests/test_source_motion_query.py tests/test_phase_local_solved_pose.py`, **13 passed in 3.13 s**. Existing heavy and renamed payload pins pass. The additional source-law probes below nevertheless expose missing contracts.

## P1 — bind retained rows and source sampler to the same program

`SourceMotionQuery.__init__` accepts the supplied plan, gait, height, and optional transition independently. Exact keys use retained rows; adjacent floating-point times use a fresh sampler at the context's geometric height. A grounded fixture built with the actual 1.6 m context height has a key/nextafter FK difference of only `3.262667913617179e-13`. Changing only one retained `root_forward_m` by 0.25 m is still accepted, and both evaluations return `AVAILABLE` despite a **0.24999999999999994 m root jump** between that key and its immediate next representable time. A transition plan accepted without its transition object similarly produced a **0.28038595338509686 m maximum node-position jump**. Even the new `_grounded_query` test helper uses a 2.0 m plan with a 1.6 m source context, hiding this mismatch behind independent status assertions.

Bind program kind, locomotion and transition parameters, frame/height, and all source-owned row decorations before claiming off-grid availability. Re-evaluate canonical rows at retained times and reject incompatible rows or explicitly restrict such plans to exact-key diagnostics. A refined correction must remain exact-key-only. Do not silently regenerate or overwrite authored rows. Test mismatched height/gait/transition, changed source-owned row fields, missing or extra transition, and compatible exact-key/near-key continuity using the correct fixture height.

## P1 — unavailable optimizer branches cannot prove a converged branch

`_branch_signature` uses contact plus the literal `UNAVAILABLE_FROM_EXISTING_ROW_SOLVER`; all unavailable optimizer witnesses therefore compare equal. At t=0.123 the actual evaluator returns `DIAGNOSTIC_CONVERGED` while both feet report unavailable optimizer tie margins and active toe-reach correction identities. The planned diagnostic contract requires branch-stable evidence and residual/envelope compliance before providing derivative availability. Neither equality of unknown fields nor finite-difference agreement establishes those conditions.

Either expose the concrete solver branch and feasibility witnesses without changing pose arithmetic, or return typed unavailable for derivative authority when the required witnesses cannot be established. An explicitly separate raw numerical-probe receipt can remain useful, but must not masquerade as branch-validated derivatives. Test a true pitch/constraint/active-toe branch change and a residual or hard-envelope violation.

## P2 — event boundaries and requested derivative side are grid dependent

The constructor detects contact changes by taking the next output row's timestamp. For step=0.8 s and duty=0.72, actual right liftoff is t=0.352 s, but the retained boundary is t=0.36923076923076925 s. `_is_boundary(0.352)` is false; both explicit left/right derivative requests then reset direction to centered and return a branch-change refusal. This is conservative but does not implement the promised one-sided event seam. Boundaries should come from the bound choreography's events, independently of output sample rate. Honor an explicit derivative side at any valid query; do not silently replace it with centered differencing. If the existing sampler cannot supply a reliable event-side limit, label that capability unavailable. Test both sides of lift and touchdown, shifted grids, and start/stop handoffs.

## P2 — convergence receipt lacks an error budget

The current check only requires the maximum mixed-unit h/h2/h4 difference to decrease (plus 1e-8), and returns only the finest estimate. It does not establish an accuracy budget, finite derived rates, roundoff/error estimate, or residual/slack margin. A decreasing large error is not convergence to a useful tolerance. Record per-unit errors and explicit acceptance tolerances, or report raw probes without derivative-availability authority. Avoid blending metres/second and radians/second into one unlabelled threshold.

No implementation changes were made by reviewer 1. The first exploratory use of `geometry_height` on a synthetic, non-admitted fixture failed with missing `eonwildGeometry`; the corrected probe used the already constructed context's 1.6 m height. This was a probe setup error, not a product test failure.
