# Source-query target-offset fast path — round 1 reviewer 2

- Reviewed head: `f125e97ec857ac006ab84126f1b052232cd66693`
- Parent: `6e3080196182688cad49a4b441753e27064824fc`
- Reviewed tree: `e87ede6b466f827482a4f66ff6fb2df19276ff75`
- Scope: the four-file parent diff only; no emitter, provider, recipe, or prior-stage review
- Outcome: **P1=1, P0=0, P2=0**

## P1 — the fast-path ownership check admits subclass overrides of its private evaluator

`CanonicalConstantSkinTargetLaw._observe_at` checks only the bound `evaluate`
and `evaluate_with_target_offsets` public method functions before trusting the
single-solve result (`constant_skin_targets.py:431-441`). Both public methods
dispatch through the newly introduced overridable `_evaluate_owned` seam
(`source_motion_query.py:711-715, 750-760`). A subclass can therefore inherit
both checked public functions, override `_evaluate_owned`, and still enter the
fast path instead of the documented compatibility fallback.

The retained reproducer subclasses `SourceMotionQuery` and changes only
`_evaluate_owned` to discard non-null target offsets. At `time_s=0.2`, the
ownership check admits the subclass and the fast path returns `UNAVAILABLE`
with both loaded residuals above tolerance. Forcing the prior two-observation
fallback on the same law returns `AVAILABLE` and applies the two calibrated
offsets (`left y=-0.012855410625621094 m`, `right y=-0.013645160572923313 m`).
This is a reachable semantic regression for the subclass compatibility that
the patch explicitly promises to preserve, rather than a performance-only
difference.

Evidence:

- Reproducer: `audits/source-query-offset-fastpath/reviewer2_subclass_repro.py`
- Result: `audits/source-query-offset-fastpath/reviewer2_subclass_repro.json`
- Result SHA-256: `1b51ad7f953d7d1b08eefd2b76197ca7feb235e7ab85b00bd7a08d2bcf98ed3e`

The smallest closure is to admit the optimized path only for an exact
`SourceMotionQuery` instance, leaving every subclass on the compatibility
fallback. Checking only the new private function would still leave other
subclass-controlled internal dispatch involved in the one-solve result.
Add this exact private-override case as the regression test.

## Checks

- Ten focused new/adjacent tests passed in `25.91s`: owned offset application
  and detachment, malformed offsets, refined `UNAVAILABLE`, fast/prior parity,
  one-solve count, public subclass override, and instance override.
- `git diff --check 6e308019..f125e97` passed.
- The author's receipt records all 40 focused tests passing in `104.10s`, Ruff
  passing, and the actual adult eight-sample benchmark with exact zero deltas
  and solve count reduction from 32 to 8.
- Reviewer Ruff execution was unavailable because neither the worker nor the
  primary borrowed environment contains a Ruff executable; no contrary lint
  result was observed.
- Author worktree remained clean and was not edited.
