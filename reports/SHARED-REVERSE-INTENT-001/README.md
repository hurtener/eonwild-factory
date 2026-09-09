# Shared reverse intent checkpoint

Implementation `6b600aa5b5fedf0187835bec24282408ab047e3c` and local
reach-check correction `cbb3da714bc96f1cfdb9a6f568b1cd5943b83a0a` extend
the existing grounded resolver to signed strides and fixed touchdown placement.
They retain the common adult animal baseline. PR #2 remains draft; no new
animation receives production or visual approval from this checkpoint.

## Behavior

Reverse walk, start and stop intents use the shared baseline and the existing
reverse choreography: -0.38 body-height stride, 1-second step period, 0.68 duty
factor and fixed 0.2-body-height touchdown reach. The resolver scales the
intent through the same family hindlimb calibration as forward locomotion.
Fixed touchdown feasibility cannot be concealed by shortening the stride.
Centered placement uses the direction of travel and rejects a final resolved
target that remains outside the support reach interval. Valid reference
forward resolution retains its previous arithmetic and parameters.

Support-timed axial coordination follows the travel direction. Species and
bone-name special cases, source-identity exemptions, widened articulation
limits and contact tolerances are absent.

## Bounded reviews and tests

- Author implementation checks: 147 passed; post-fix checks: 149 passed.
- Root independent implementation checks: 138 passed in 8.29 seconds.
  Three focused near-bound/forward-preservation checks passed after the fix.
- Second reviewer: 152 focused checks passed in 8.58 seconds at the initial
  head. Steady/start/stop forward/reverse plan symmetry had zero root/foot
  mirror error with identical contact and other nonforward channels.
- Both reviewers identified the same small-stride reach edge case; the
  correction received narrow independent review and four reviewer-two checks
  passed. No P0/P1/P2 finding remains in that reviewed code delta.

These are focused implementation results, not a full-suite result at this
checkpoint. The preceding published `4c91c6b` hosted contracts passed 1,130
tests plus 21 subtests in 603.53 seconds; source evidence passed. The wider
candidate catalog remains blocked.

## Actual motion evidence and remaining failure

The retained pre-final-arithmetic steady diagnostic
`tarbosaurus-adult-reverse-shared-003/reverse-walk` is **BLOCKED**. Its root
GLB SHA-256 is
`59cee47bf4c504c225b1d27288d662599a05fc84df84ed9ae944b605a7634e9b`;
its in-place GLB is
`d0aa1aab158ec059f641912a1d0c2cfa0067aeb11e7dcf21e0af24e3c99d8ad5`.
This diagnostic is not exact-head emission evidence for the final code above.

The failing reopened CUBIC midpoint is the right swing ankle at
0.7375000119 seconds: 89.93523794 degrees against a hard 90-degree minimum
and unchanged 0.01-degree allowance. Key samples, contact, cyclic continuity,
solver feasibility and reported rate gates pass. Independent pointwise source
queries at the midpoints pass; the source minimum is approximately
89.99999951 degrees. The remaining defect is interpolation undershoot, not
permission to relax the limit or change the source pose. Adaptive source-key
refinement is under investigation.

Root inspected all 120 native rendered frames across side/front views and
enlarged recovery poses without finding a gross limb inversion or body jump.
The diagnostic uses 640-pixel, four-sample rendering, which limits fine skin
assessment. Browser native-speed playback was unavailable because its policy
check could not be verified; no workaround or native-speed acceptance is
claimed. Unity parity is not run for reverse.

The start/stop emission was interrupted before completion. Their source
preflight, final exports and actual direct joins remain required.

Detailed local evidence is retained on the external SSD in task storage:
`audits/reverse-shared-003-root-native/root-review.json`,
`audits/shared-reverse-round1-reviewer2-6b600aa/README.md` and
`audits/tarbosaurus-reverse-shared-001/source-midpoint-result.json`.
