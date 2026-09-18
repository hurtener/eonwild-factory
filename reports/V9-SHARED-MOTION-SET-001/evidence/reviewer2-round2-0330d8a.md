# Shared motion-set release — independent round 2 review

Reviewed exact head `0330d8ae7acbf7a6300e1e991658f78544d9886c`,
tree `5f22a62f8b2512e8cc89d7fd5ecadc19825e2df4`, against parent
`38f14dd4142c161f2838d80210ee3a83be836a91`. The source worktree was clean
and unchanged.

## Finding

### P1 — the transition program snapshot is retained but does not govern transition choreography

The fix packages and hash-checks `program-profile.json`, but the transition
branch only loads `gait-profile.json` as a `GroundedGait`
(`compiler.py:846-862`). It never loads the bound transition program or
compares it with `plan.transition_parameters`.

The independent `transition_program_repro.py` resolves the actual
`walk-start` intent and retains its exact packaged program profile, hash
`062bc956067bdbc96ebd2901d5e657f36adf46ae34a126cfcea2aa1f7592b480`.
That profile declares `anticipation_seconds=0.3`. The repro constructs the
plan from an otherwise valid transition with `anticipation_seconds=1.5`,
keeps the bound program bytes unchanged, and supplies the correctly bound
steady gait and response. `_verify_motion_set_provenance` returns `ACCEPT`.

This leaves an end-to-end drift path for transition kind, ramp, hold,
placement, sampling, and handoff declarations even though the package appears
to carry the authoritative program snapshot. Close it locally by loading
`program_bytes` with `load_gait_transition` for transition recipes and
requiring `plan.transition_parameters == gait_parameters(transition)`. Add
one negative regression through package provenance verification.

## Closed round-1 findings

- The walk/fast gait substitution is rejected because the actual consumed
  program or gait snapshot is now packaged, hash-checked, parsed, and compared
  with `plan.parameters`.
- Unsafe motion names are rejected as safe catalog components before the output
  directory is created, and resolved destinations are confined under it.
- Shared-baseline axes now require three finite JSON numeric values; booleans
  and numeric strings reject before normalization.

## Checks and limits

- Independent focused run: 44 motion-set and gait-response tests passed in
  1.35 seconds, including the three round-1 regression families.
- Author affected gate: 134 tests passed in 275.17 seconds; Ruff and diff checks
  passed. Receipt SHA-256:
  `f9b28b5d6e593526153b60d5431ce8a10d66e1ef8d6727fc739a819bd8cd6d24`.
- A separate real walk compile was stopped during expensive midpoint skin
  evaluation after the transition authority P1 had been independently
  reproduced. It produced no package and is classified as interrupted, not a
  pass or failure. Root owns the complete mandatory suite and release package
  verification.

Result: P0=0, P1=1, local P2=0. No further full review is warranted after the
narrow transition-program closure.
