# SourceMotionQuery narrow post-round-two closure

Reviewed only the authorized local diff `270d4b2c9bdc13998cec2a3e816cfca5b4c2e362..811571866f71614927996026ff1c43b61c64d548`. This is not a third whole-stage review.

CLOSED: one-sided raw probes compute available event room in their requested direction, while centered probes keep both directions. The regression verifies useful event-side step sizes instead of the former approximately 1e-10 s roundoff interval. The entire retained transition contract now compares against the bound planner's own `build_transition_plan(...)['transition_contract']`, closing forged phase, speed, root-distance and schema metadata. The shared source identity helper/tests are byte-identical to the independently closed jaw helper at `20b8bb2`.

Independent focused query tests: **10 passed in 1.77 s**. The implementation worker reports the query/identity/phase-local group **27 passed in 3.96 s**, scoped Ruff and diff-check clean. No pose, emitter, interpolation, threshold or derivative authority changed. No remaining P0/P1. The documented huge-integer float-conversion `OverflowError` remains P2 follow-up debt for this non-emitting diagnostic API.

SourceMotionQuery source stage is closed at `8115718`; tracked evidence packaging, combined source-query/jaw compatibility and full-suite publication remain separate work.
