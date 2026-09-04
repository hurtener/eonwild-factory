# Plan — V8.1 walk-respin reference analysis

## Restatement

Perform a read-only, frame-reviewed comparison of the supplied Tarbosaurus walk references, the four user captures, and the current V8.1 walk output. Reconcile the walk with the user-specified 12 m adult length, 2.75 m hip height, and 4.5–4.8 km/h target. Hand off bounded V8.1 correction parameters for a walk-only MP4 respin; do not roll back to V5.5 and do not edit engine or media files.

## Files intended to touch

- `reports/V8-1-WALK-RESPIN/reference-analysis/plan.md`
- `reports/V8-1-WALK-RESPIN/reference-analysis/reference-analysis.md`
- `reports/V8-1-WALK-RESPIN/reference-analysis/metrics.json`
- `reports/V8-1-WALK-RESPIN/reference-analysis/commands.log`

No engine, source asset, generated media, or other workstream file is in scope. `reports/**` is owned by the task owner under `config/ownership.yml`; this task owns only the requested report directory.

## Acceptance checks

- Native-rate source metadata and SHA-256 provenance recorded.
- Relaxed reference reviewed frame-by-frame through extracted native-rate frames/contact sheets; four user PNGs reviewed as qualitative still evidence.
- Current V8.1 and V5.5 walk profile/output values recorded without changing them.
- Candidate parameters are bounded, implementable, and satisfy `stride_length_m * cycle_hz = 1.25–1.333333 m/s` at reference scale.
- JSON parses; report diff passes `git diff --check`.
- Final report explicitly separates measured observations, estimates/inferences, tuned recommendations, and uncertainties.

## Unresolved assumptions

- The 4.5–4.8 km/h adult Tarbosaurus range is treated as the user-specified tuning envelope, not independently validated in this analysis.
- `stride_length_m` follows the generator contract: same-foot advance over one gait cycle; alternating contacts are approximately half a cycle apart.
- User captures are static, uncalibrated illustrations; their apparent pixel reach cannot override the speed/cadence constraint.

## Iteration-2 addendum scope

The new bounded pass addresses the rejection of the iteration-3 editorial walk while
remaining an 8.1 adjustment, not a V5.5 rollback. Inspect the iteration-3 side MP4,
the relaxed source video, and the four supplied captures; then hand off exact phase
ordering for an early rocker, 15–20 loaded micro-samples, a passive unloaded toe lag,
and a later receiving toe/ankle arm. The target center is a 2.60 m same-foot stride
at approximately 4.60 km/h (`0.4914529915 Hz`), with no engine or media edits.

Additional file intended to touch:

- `reports/V8-1-WALK-RESPIN/reference-analysis/iteration-2-addendum.md`
- `reports/V8-1-WALK-RESPIN/reference-analysis/iteration-2-addendum.json`

Additional acceptance checks:

- Rocker onset precedes measured maximum rear extension by at least `0.06` cycle.
- Each side exposes `15–20` loaded rocker samples (center `18`) before toe release.
- A `0.05–0.08` cycle passive/free-weight interval follows release; active receiving
  toe/ankle control begins only after it.
- Stride, cadence, speed, toe-patch retention, rocker lift, and no-penetration gates
  are all measurable from the walk-only candidate output.
