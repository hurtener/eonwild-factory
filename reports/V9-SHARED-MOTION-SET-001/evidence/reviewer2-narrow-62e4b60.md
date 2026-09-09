# Shared motion-set transition authority — reviewer 2 narrow closure

Reviewed exact head `62e4b60a399672fc68f9817aeabc6bff8c300912` (tree `bf814e4536ece37d963f35cdc8693f3feba4b09c`) against parent `0330d8ae7acbf7a6300e1e991658f78544d9886c`.

## Result

**PASS — P0: 0, P1: 0.**

The narrow change closes the remaining transition-program provenance finding. The verifier now parses the packaged transition program profile with the production loader and requires the plan's `transition_parameters` to equal its canonical `gait_parameters` mapping. An unchanged program hash can therefore no longer authorize altered or missing transition behavior in the plan.

The focused regression uses the real `tarbosaurus-pin-552-1-adult-walk-start.v1` and `tarbosaurus-pin-552-1-adult-walk-stop.v1` packages. Both unchanged plans verify. Altering `kind`, `ramp_cycles`, or `anticipation_seconds`, or removing `transition_parameters`, rejects. This directly closes the earlier actual walk-start witness in which `anticipation_seconds` changed from `0.3` to `1.5` while verification accepted.

Independent focused command:

```text
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_motion_set.py::test_transition_plan_is_bound_to_packaged_program_snapshot
```

Result: `2 passed in 1.75s`. The captured log SHA-256 is `95c10eec5341a7e00b9aa4717292459334fef7532764b627ca8311f0eb362c72`.

Scope remained narrow: no whole-branch review, full suite, or real export was rerun. Root owns the final mandatory suite and Join owns the final-head actual fast export.

The earlier reviewer-2 export attempt on `0330d8a` was interrupted during CUBICSPLINE midpoint skin evaluation. It remains classified `NOT_COMPLETED`, not pass or failure. Its empty `actual-walk` directory was removed; no emitted bytes were retained.
