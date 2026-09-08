# Canonical support-anchor provider round-2 review — reviewer 2

Reviewed exact postfix `f36b1eeb9af059f006000106624b8ae3ea143c8f` against round-one head `7b584f21cff3197d8afcba9fbd109ee9f29e5026`. Scope stayed within the canonical provider's four-file postfix. The reviewed worktree was read-only and clean.

## Finding

### P1 — canonical row content remains outside the live binding

The postfix correctly binds source identity/scale, semantic roles, solver and locomotion dataclasses, transition metadata, selected plan metadata, performance/gaze, contact profile and ordered material IDs, axes, articulation profile, and the anchor payload. It rejects the round-one wrong-contact provider, changed solver cadence, and mutated anchor origin.

However, `_binding_inputs` deliberately excludes `plan["samples"]`, while `_validate_active_program` checks only top-level parameters for a sustained gait. No per-row canonical-law validation replaces the omitted grid bytes. Consequently, a provider built for a canonical plan also validates and is consumed with a plan whose loaded foot target and root travel were changed at the same declared time, as long as the top-level metadata is unchanged.

The executable reproduction changed the first loaded row at `t=0`: `root_forward_m 0.0 -> 0.25` and left `forward_m 0.9827017633 -> 1.4827017633`. All selected request fields remained equal, `validate_for_consumption` accepted it, and `solve_with_skin_targets(iterations=0)` consumed it. The iteration count proves binding acceptance only; it is not a quality result.

Required narrow fix: retain grid independence by validating the law at each supplied time instead of hashing a particular row list. Re-evaluate every sustained row through `sample_grounded_gait` or `sample_airborne_gait`, then apply the same deterministic row decoration and compare all gait/contact/root/phase fields. For transitions, use the canonical transition choreography at each requested time or another authoritative planner sampler. Permit only explicitly solver-owned refinement state after binding; do not accept arbitrary preexisting offsets. This preserves shifted/nested grids while rejecting fabricated rows and does not change the source event, constraints, or thresholds.

No other P0/P1 or reachable local P2 was found in the postfix. The request and material binding, defensive anchor copies, cadence rejection, opt-in enforcement, and compatibility receipt are otherwise coherent.

## Checks and evidence

- `132 passed in 34.06s`: canonical anchors, skin-refinement final-state, and motion-performance suites.
- Ruff passed on the changed provider, consumer, and test files.
- `git diff --check` passed.
- Probe script SHA-256: `66046ee7263d7362c26a46dba54a20158014ac549bacecaddd7a2024d691461b`.
- Probe JSON SHA-256: `a2f7a3de6766c8984dd9085dce4b4bd5d1ab365b07839601f0b78e74f2f13691`.
