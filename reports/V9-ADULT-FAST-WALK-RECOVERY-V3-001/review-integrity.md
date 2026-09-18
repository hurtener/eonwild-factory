# Fast-walk recovery independent review

- Reviewed head: `0955fc867fcf70383613d67f984baf4a92c4d6e0`
- Feature commit: `f53782e060d38554879cbd25a65d0d62c72d44f4`
- Base: `3726cb7fe4e620745f83d1e5ea7499561a1191ae`
- Scope: six-file feature delta plus the lint-only test fix in `0955fc8`
- Result: **CLEAN — no P0/P1 findings**

The new `metatarsal_recovery_carrier` is opt-in, accepts only the exact
`rate_limited_c2` selector, and requires the existing paired world target and
release controls. Null omission produces the exact legacy plan and omits the
new serialized parameter. False, numeric, empty, collection, misspelled, and
whitespace-suffixed selectors reject with `ContractError`.

The carrier preserves the existing peak/release envelope. Independent endpoint
checks returned exactly `0, 1, 0` at phase `0, .42, .90`; the implementation's
integrated quintic ramps meet the constant-slope middle in value, first
derivative, and second derivative. Grounded transitions consume the same
steady sample output rather than reconstructing a second carrier.

The v3 recipe binds the intended program profile hash exactly. All other source,
rig, animal, contact, performance, and articulation hashes resolve. Version 3
and `supersedes` v2 are consistent. No thresholds or final validation gates
changed.

Validation:

- `15 passed`:
  `tests/test_world_metatarsus_recovery.py`,
  `tests/test_adult_fast_walk_recovery_catalog.py`, and
  `tests/test_grounded_recovery_direction.py`.
- Focused malformed/omission probe: PASS.
- `git diff --check 3726cb7..0955fc8`: PASS.
- Commit `0955fc8` changes only the test-local lambda into a named function;
  production behavior is identical to feature head `f53782e`.

The checkout's four untracked v1/v2 historical profile/recipe files predate and
are outside the reviewed commit delta. They were preserved untouched.
