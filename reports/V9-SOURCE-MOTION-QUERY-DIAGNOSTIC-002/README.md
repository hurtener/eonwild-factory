# SourceMotionQuery diagnostic closure

Status: **SOURCE-ONLY DIAGNOSTIC; NOT EMISSION, TANGENT, OR APPROVAL AUTHORITY.**

This receipt closes the bounded `SourceMotionQuery` stage at code head
`811571866f71614927996026ff1c43b61c64d548`. It preserves the initial source
query receipt at `V9-SOURCE-MOTION-QUERY-DIAGNOSTIC-001`; this version records
the reviewed source-law, source-identity, contact-event, and diagnostic
closures. It does not emit animation, create CUBICSPLINE tangents, retime a
plan, change a profile, threshold, recipe, contact target, or generated payload.
It does not grant technical, visual, Unity, or production approval.

## Source boundary

`SourceMotionQuery` reconstructs a phase-local solve from admitted source data
and the bound grounded, airborne, or transition law. Exact plan keys reproduce
the retained row; unrefined off-grid queries evaluate the same source law.
A refined `target_offset_m` plan remains exact-key-only and returns
`CONTINUOUS_SKIN_TARGET_UNAVAILABLE` off grid. Formal derivatives remain
`BRANCH_OR_CONVERGENCE_UNAVAILABLE`, because the retained row solver does not
supply optimizer branch, tie-margin, active toe-correction, or feasibility-slack
witnesses. `raw_probe` reports h/h2/h4 observations under
`RAW_NUMERICAL_PROBE_ONLY`; those values carry no convergence or acceptance
claim.

The final narrow closure selects one-sided raw-probe room only in the requested
direction at canonical contact events. It also compares the complete retained
transition contract against the bound planner's
`build_transition_plan(...)["transition_contract"]`, rather than accepting a
matching kind alone. Material witnesses require the frozen raw source and a
current snapshot that differs only by the declared common uniform active-root
scale; cached node state is checked against the reparsed source.

## Review and reproducibility

Four complete bounded reviews are retained verbatim in `reviews/`, followed by
the root's authorized narrow diff-only closure. The round-one and round-two
independent reproducer scripts and their JSON results are retained in
`reproducers/`; their source hashes are in `receipt.json`. Review coverage found
and closed the source-law row/profile/height mismatches, grid-derived contact
events, stale contact-profile source admission, false formal derivative
availability, malformed inputs, the directional probe-room issue, and forged
transition-contract metadata. The narrow closure found no remaining P0/P1.

At the final code head, the implementation worker ran
`tests/test_source_motion_query.py`, `tests/test_source_identity.py`, and
`tests/test_phase_local_solved_pose.py`: **27 passed in 3.96 s**. Scoped Ruff
and `git diff --check` passed. The root narrow reviewer independently ran the
query test module: **10 passed in 1.77 s**. This is focused validation only;
no full suite, native media review, Unity parity, or production approval was
run for this diagnostic closure.

## Remaining P2 debt

Public numeric conversion can still leak `OverflowError` for huge integers such
as `10**10000` before the diagnostic API converts them to its typed
`ContractError`. This non-emitting input-boundary defect is explicitly deferred
as P2 follow-up debt. It does not change the closed source-law or authority
boundary. SourceQuery/jaw integration is separate: an eventual combined context
must retain the authoritative original raw source alongside any detached
admitted state, rather than canonical-reencoding it and changing the raw hash.
