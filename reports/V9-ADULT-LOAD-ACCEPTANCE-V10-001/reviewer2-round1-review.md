# Adult body-load acceptance diagnostic — independent R1

**Verdict: PASS — P0: 0, P1: 0.**

Reviewed frozen head `94c81e7e3bb00e2e6057fd1babb183adb70ff9e3` against parent `83aa5e5` in the isolated `eonwild-adult-load-acceptance` worktree. I made no source, catalog, recipe, or test edits.

## Scope and findings

- The carrier is opt-in and bounded. Both amplitudes are required with `support_timed_load_acceptance_carrier=true`; malformed, negative, incomplete, and over-envelope inputs fail closed. Explicit use remains grounded-only.
- The clock matches the declared grounded contact choreography. For step period `s` and duty factor `d`, `u = frac(phase/s - d)` places zero at adjacent single-support midpoints `(d+n)s` and the peak at the intervening double-support midpoint `(d+n+0.5)s`. `64u^3(1-u)^3` has zero value, first derivative, and second derivative at either seam, so its step-period repetition is C2.
- The retained analytic proof is arithmetically consistent: with body height `2.2841755838983118 m`, amplitude `.01 BH`, and a `1.23 s` midpoint-to-midpoint window, `24*A/T^2 = 0.36235186736439606 m/s^2 = 0.03694960739543025 g`. This is correctly labeled as an authored kinematic timing diagnostic, not a physical or biological simulation.
- Frame signs are correct. Pelvis translation is `-up` and converted through the pelvis parent's basis before assignment. Positive rotation about `cross(up, forward)` tips declared forward toward declared down. On the actual admitted rig, the isolated peak measured `-0.02 m` along up and `+0.35000007 degrees` about lateral for a 2 m plan.
- The trunk binding uses the existing semantic spine/chest admission, rejects collisions with root/pelvis/head/neck/tail/leg/toe roles, and verifies actual parent topology before applying the distributed world-space rotation. No species or literal bone-name branch was added.
- The v9 performance profile is byte-identical to frozen v8 (`e133819dddf19bd224ddec7419687208e01abf8f3906fa147837813710dc2dfc`) outside the three new carrier parameters and reference metadata. The v10 recipe preserves source, rig, animal, program, contact, gaze/performance inheritance, and articulation bindings; it remains unselected by baseline workflow/catalog verification.
- Default behavior remains byte-stable. The existing plan/decorated-plan digests stayed `d072715a03d517df64c43553d69311fec94b020b002bce46ce1a0215ca9e066c` and `cb07b756443ee231d12bec2a5e948a23f8a31ea8048a937966c0ed2e90e4dce3`, with all new optional fields omitted.
- Start/stop compatibility is complete at the pointwise source-query layer. The transition planner supplies a nonnegative wrapped native `locomotion_time_s` and `[0,1]` gain. I independently applied the carrier to every actual-rig transition row: start `987/987` and stop `828/828` were finite. Peak isolated responses were `0.01999997 m / 0.35000007 degrees` for start and `0.01999367 m / 0.34988997 degrees` for stop. Independent `SourceMotionQuery` probes at each endpoint and two off-grid interior times returned `AVAILABLE` with finite world matrices for both transitions.

## Verification

- `PYTHONPATH=src .venv/bin/pytest -q tests/test_motion_performance.py -k 'load_acceptance' tests/test_adult_load_acceptance_catalog.py` — **20 passed, 102 deselected**.
- `ruff check src/eonwild_motion/solve/performance.py tests/test_adult_load_acceptance_catalog.py` — **passed**. Whole-file lint for `tests/test_motion_performance.py` still reports seven pre-existing E701/E702 findings outside this diff; no new-line lint defect was found.
- `git diff --check 83aa5e5..94c81e7e3bb00e2e6057fd1babb183adb70ff9e3` — **passed**.
- Reviewed proof: `audits/body-compression-pulse-timing.json`.

## Frozen identities

- Recipe: `1f5d4dee6bdf224db2082878112c777e5d01c7605d512e0e9006198eff7244be`
- Performance profile: `362bd101e31974464dabc6765308d8a1292e163a94bbe895e7a171faacea55f1`
- `performance.py`: `fc7a49d10aeac9ff16e103514bce1b59fb26849d3310765b839d4ae90d77dde7`
- Focused performance tests: `cb7565618cd8f7b8b78d59b0205486ef2d02c356e1cd839bb59706bce424f922`
- Catalog tests: `3ad6fb021c89407247446ff50e57ab687ba8cc3d2244e0c53e8f5fdfaa2b5592`

Compiled contact, ROM, rotation-rate, loop gates, and matched-camera visual comparison remain outside this code-level R1 and were still pending with the author/root at review time.
