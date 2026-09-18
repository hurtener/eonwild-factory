# Body v7 support-speed carrier round-one review

Reviewed `98ab0af6610267a27373d8f6f91b8ce850028394` against base `30f434ce914b6392f1438f0ff234718c82d2e985` in the external SSD worktree. Review scope was the five changed source/input/test files only. The later `f5f8bdfca91a42463e35c77e875747c51f883c1e` commit contains reports only. No source files were edited.

## Source verdict

No P0 or P1 source defect found.

The opt-in coefficient produces a step-periodic pelvis-local translation whose analytic derivative is the declared signed velocity residual. The formula has zero net displacement, preserves the constant root motor, supports both stride signs, uses the declared forward direction, and converts the world displacement through the actual root parent basis. Nonzero use requires grounded locomotion and `stance_vault_proxy`. The actual semantic root-to-pelvis hierarchy is checked. Omission and explicit zero serialize identically and solve to byte-identical motions in the focused actual-rig regression.

The v7 recipe changes only its recipe identity/version/supersession metadata and the hash-bound performance profile. The v6 performance profile changes only `pelvis_forward_velocity_modulation_fraction`; gait, animal, rig, contact, articulation, axes, stride, cadence, duty, recovery, and root ownership bindings remain unchanged. The coefficient is explicitly classified as a bounded kinematic analogy rather than a COM, force, work, mass-response, or biological result.

An independent actual-rig interface probe produced a maximum pelvis-world-matrix difference of exactly `0.0` at both the grounded start-to-steady and steady-to-stop phase-zero interfaces. This confirms pose equality; exact emitted derivative continuity remains governed by the separate current evaluator.

## Required report correction

**P1 (report-only): the later diagnostic report overstates current continuity.** `reports/V9-ADULT-SUPPORT-SPEED-V7-001/README.md` labels the package technical PASS and says cyclic continuity passes. Those immutable package receipts used the historical quadratic estimator. The current exact adjacent LINEAR/shortest-SLERP evaluator reports local linear seam mismatch `0.0032116449766123154 m/s` against the unchanged `0.001 m/s` limit in both root-motion and in-place modes. The witness is `Bone_001`; angular mismatch is `3.652031815499178 deg/s` and remains within the `10 deg/s` limit. Current exact loop status is therefore `BLOCKED`. Correct the report and attach/link the exact companion receipt without rewriting the package or changing thresholds.

Evidence: `/Volumes/m2-extended-disk/Repos/eonwild-factory/out/continuation-adult-v7-support-speed-001/host-exact-continuity-status.json`.

**P2 (report-only): test-count wording is ambiguous.** The report states 86 performance tests plus three catalog tests, then calls the focused candidate set 16 tests. The reproduced combined invocation is 89 tests; label any 16-test subset explicitly or use the reproduced total.

## Verification

- `uv run --frozen --group test pytest -q tests/test_motion_performance.py tests/test_adult_pelvis_speed_carrier_catalog.py --basetemp out/reviewer2-pytest`: **89 passed in 10.16s**.
- `python -m eonwild_motion.factory verify out/continuation-adult-v7-support-speed-001`: integrity PASS and historical technical PASS; current exact-continuity override is the BLOCKED receipt above.
- `git diff --check 30f434ce..98ab0af`: clean.
- Ruff on the changed source and new catalog test has no new reported defect; the whole selected invocation reports seven pre-existing style findings in unchanged portions of `tests/test_motion_performance.py`.
- Worktree was clean; package hashes match the retained report.

No visual, Unity, biological, physical, or production approval is granted by this review.
