# Source-query target-offset fast path — reviewer 2 narrow closure

- Reviewed head: `ff85ddd59da5da8d62f769b447f8accb87800124`
- Parent: `f125e97ec857ac006ab84126f1b052232cd66693`
- Reviewed tree: `d51cc3b54a74e465a9aef3e7815aa8e53c37f743`
- Scope: the exact-type guard and its private-override regression only
- Outcome: **PASS — original P1 closed; P0=0, P1=0**

The fast path now requires `type(active_query) is SourceMotionQuery` in addition
to the two public-method identity checks. The original subclass that overrides
only `_evaluate_owned` therefore takes the compatibility fallback. Its offset
override receives no combined-offset call, and both the ordinary result and a
forced prior fallback are `AVAILABLE` with the calibrated offsets applied.

Evidence:

- Closure JSON: `audits/source-query-offset-fastpath/reviewer2_subclass_narrow_closure_ff85ddd.json`
- Four targeted ownership/fallback tests: `4 passed in 47.29s`
- `git diff --check f125e97..ff85ddd`: PASS
- Author worktree: clean at the exact reviewed head

No whole-stage re-review was performed.
