# Narrow mechanics P1 re-review — 4ae0fe92ec3ffd49dfeca14085756cc7cbe7d852

This is a diff-only re-review of the grounded support/swing coverage fix, from
`3219d65d66f4408e1eaf05d4eccec39409b474e1` to
`4ae0fe92ec3ffd49dfeca14085756cc7cbe7d852`. It is not another full review.

## Result: CLEAN — P0: 0, P1: 0

`build_grounded_plan()` now derives its samples exactly as before and then
requires support and swing witnesses for each leg. The original reproduction
trigger, `GroundedGait(step_period_s=0.06, duty_factor=0.999, cycles=1,
sample_hz=24)`, now raises `ContractError` naming `left:swing, right:swing`
before a candidate can be emitted.

Grounded transitions apply the same coverage gate after their existing
boundary construction. The final reopened-articulation gate independently
checks both `grounded_gait` and `gait_transition` plans with a grounded
locomotion program; an omitted phase now yields `FAIL` and
`missing_phase_samples`. Supported actions remain exempt, as their own
support contract owns their phase semantics.

The direct narrow probe confirmed support and swing witnesses for each leg in
the current walk v3, reverse-walk v4, fast-walk v2, adult-walk v3, and a
grounded start/stop transition. The current head is clean. No current plan
rows or clocks are altered by the added checks; the change only rejects an
otherwise unsampled invalid configuration.

The previous exact-head suite is accurately recorded as **661 tests plus 21
subtests**, not 682 separate tests. The root reviewer owns the post-fix full
suite; this narrow re-review did not duplicate it.
