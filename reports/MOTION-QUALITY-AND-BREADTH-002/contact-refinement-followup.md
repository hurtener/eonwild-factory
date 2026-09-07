# Contact refinement follow-up

Source reviewed: `21f3213d54b4eb5ebb1ab1e20506049e0b4ba4c1` on PR #2.
Status: implementation and regression witnesses added; execution and visual
acceptance are still blocked. Quality-01 is still rejected.

## Actual solver defect corrected

`solve_with_skin_targets` computed swing-floor corrections, but its stopping
condition measured only loaded-foot error. A planted foot satisfying the
0.2 mm refinement tolerance could therefore stop the loop before the required
swing correction was sent to the next constrained limb solve.

The stopping condition now covers BOTH loaded material-target error and
unloaded-foot clearance shortfall, measured on the current serialized output.
A swing-only problem requests another solve. At the iteration limit, the
returned GLBs, offsets and receipt describe the last solve actually measured,
not the correction which would have been attempted next. The receipt reports
separate convergence components and iteration residuals.

The existing 0.1 mm target gap, 0.2 mm refinement tolerance, seven correction
iterations, 0.85 update gain and 6%-of-body-height correction envelope remain.
The independent contact-authority limits, material anchors and fixed floor
have not been changed. This correction does not make the planner a force or
muscle simulator, and cannot establish natural-looking motion by itself.

## Final-sample audit corrected

Before this change, cyclic contact computed a seam distance and then omitted
the duplicate terminal sample when expanding three cycles. A NaN in that
actual endpoint can make the seam comparison false instead of rejecting it;
subsequent phase evaluation then never sees that sample. Different patch
counts can also enter NumPy broadcasting instead of failing correspondence.

All original patch coordinates and timestamps are now checked for finite
values, stable per-region counts, ordered timing and boolean contact state
BEFORE de-duplication. Valid root-unwrapped seam evaluation is retained. A
real contact-state/position seam failure is still rejected, not removed.

Final skin evaluation also checks sample times against the plan, not just
sample count. Refinement rejects an up-axis/floor-axis disagreement rather
than applying a scalar floor level along a different axis. A missing loaded
phase remains failure; absent stance-gap evidence is represented as null,
not negative infinity or fabricated zero drift.

## Regression witnesses

`tests/test_skin_refinement_final_state.py` covers swing-only correction,
hover correction without moving the floor, iteration exhaustion, exact
returned-solve identity, input immutability, invalid iteration/axis/contact
inputs, timeline mismatch, valid seam-crossing support, corrupted actual
terminal vertices/timestamps and broadcasting-shaped patches.

The mocked emitter tests isolate the refinement controller; they are NOT
proof of real-species transfer or visual animation quality. The existing
real-asset/contact tests and catalog verification remain mandatory.

```sh
uv run python -m pytest tests/test_skin_refinement_final_state.py \
  tests/test_motion_contact_adversarial.py tests/test_motion_performance.py -q
uv run python -m pytest tests -q --tb=short
```

## Verification boundary

Both local execution attempts failed before running a shell command; Python
also failed initialization. `/mnt/data/eonwild-factory` could not be inspected
and was not modified. The existing PR check was retried once (run 34050061968,
contracts job 101580973880) and again returned `steps: null`; dependent jobs
were skipped. Source changes are committed through the authorized GitHub API.
This record does not claim that the added tests executed or passed.

No gait recipes, approved GLBs, immutable legacy assets or historical approval
records change in this follow-up. No new animation render was produced.
The remaining stroke/ankle/stance, tail, gaze, transitions and feeding quality
requirements in `docs/MOTION_QUALITY_STATUS.md` still apply.

**PR remains draft. Visual review: PENDING. Unity validation: NOT_RUN.**
