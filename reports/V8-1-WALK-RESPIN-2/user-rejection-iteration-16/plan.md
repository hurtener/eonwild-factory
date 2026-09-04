# Iteration-16 user-rejection diagnostic plan

## Task

Perform a bounded, read-only frame/world-space diagnostic of the rejected iteration-16 walk candidate against the five supplied user captures. Identify the startup/release phases, quantify the planted-toe witness failure and vertical reset, and define a fail-closed acceptance contract for iteration 17. This report does not approve the candidate and does not modify engine or media files.

## Files allowed to change

- `reports/V8-1-WALK-RESPIN-2/user-rejection-iteration-16/plan.md`
- `reports/V8-1-WALK-RESPIN-2/user-rejection-iteration-16/diagnostic-addendum.md`

## Evidence and checks

- Exact iteration-16 MP4 and GLB hashes, dimensions, frame rate, and duration.
- Fixed 24-fps startup/release frame review and fixed-render lower-body pixel witness.
- 60-Hz GLB world-matrix measurement of terminal toe mesh, foot/metatarsal pivot, and terminal toe pitch.
- Comparison with all five user captures; capture-to-frame matches are explicitly approximate because the screenshots carry no source timestamps.
- `git diff --check`, trailing-whitespace scan, and report-file SHA-256 checks.

## Assumptions and limitations

- No exhaustive camera calibration is attempted. World measurements use the GLB's generator axes: F (forward), L (lateral), and U (up); screen pixels are fixed 960x540 render coordinates only.
- The terminal toe mesh is selected from terminal-toe weighted vertices, so visual occlusion/branch overlap can make a screenshot witness less identifiable than the world-space measurement.
- The candidate's hip-height normalization is `H = 2.756361830 m`.
