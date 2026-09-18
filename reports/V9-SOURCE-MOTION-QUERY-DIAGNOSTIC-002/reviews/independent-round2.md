# SourceMotionQuery final-head review — reviewer 2

Reviewed clean head `270d4b2c9bdc13998cec2a3e816cfca5b4c2e362` (parent/shared source-admission integration `7e97c1bbf0c33ce9f2aa0d4c323378c2edb9974f`). Scope was the final SourceMotionQuery implementation, shared frozen-source helper use, and focused tests. No reviewed files were changed.

## Decision

No P0 or P1 remains. The postfix closes the round-1 source-law, contact provenance, event-source, and derivative-authority findings. Formal derivatives are always typed unavailable; raw h/h2/h4 values remain explicitly non-authoritative. Retained rows are canonically resampled from the supplied gait/transition at the admitted source height, and material witnesses require the exact frozen source plus the shared uniform-scale-only admission. Legacy compiler/emitter behavior is outside this non-emitting module and the adjacent payload-pin tests pass.

Three local P2 findings remain:

1. **Directional raw-probe room includes the queried event behind the requested direction.** At the canonical right liftoff `t=0.352`, the left-limit probe is unavailable and the right-limit probe is reduced to `h=1.00000015212931e-10 s`; at the canonical touchdown `t=0.8`, both explicit sides are unavailable. `_limit_time` correctly moves the anchor into the selected side, but `raw_probe` then takes the absolute distance to every boundary, including the just-crossed event behind that anchor. The local correction is to choose only boundaries strictly ahead in the derivative direction (strictly behind for a left limit, strictly ahead for a right limit), retaining absolute nearest boundaries only for centered probes.

2. **Transition contract metadata is only bound by `kind`.** A canonical start transition remains accepted after independently replacing `steady_phase_s`, `entry_speed_mps`, `root_distance_m`, or `interface_schema`. The rows still solve canonically, so this is not a pose-integrity failure, but the retained plan can carry false handoff provenance. A narrow authoritative comparator is the complete `transition_contract` from `build_transition_plan(bound_transition, bound_locomotion_gait, admitted_body_height)`, checked with the existing recursive typed comparator. This avoids a second hand-written contract law.

3. **Huge integer public numerics escape as `OverflowError`.** `initial_h_s=10**10000` in `derivative` and `raw_probe`, the same value in plan `body_height_m`, `duration_s`, or `same_foot_cycle_s`, and a refined `target_offset_m` evaluated at its retained key escape the diagnostic's `ContractError` boundary. Ordinary malformed rows and finite-invalid offsets already fail closed. This is non-emitting follow-up debt: reuse a finite-numeric conversion helper that catches `OverflowError` before `math.isfinite`/NumPy coercion.

## Verification

- `uv run --frozen pytest -q tests/test_source_motion_query.py tests/test_source_identity.py tests/test_phase_local_solved_pose.py --basetemp out/source-query-round2-reviewer2`: **26 passed in 6.32 s**.
- Ruff over the two source modules and their focused tests: **All checks passed**.
- Worktree remained clean at the reviewed head.

Evidence:

- Probe script SHA-256: `b99d67e5531f3c27b3ef47c31fc0e41f8f0134e9ebfb648500099c03f96914f0`
- Probe result SHA-256: `714f0acbee8199ad31df22c56946a61fa575cd60551c51c62aa4d03308b15bfa`
- Pytest log SHA-256: `690e1d8f528369b52037cde1eb19e02d00b089703ca169c8c1b81129539ab18b`
- Ruff log SHA-256: `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`
