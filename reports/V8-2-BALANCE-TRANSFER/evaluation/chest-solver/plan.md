# Candidate-A chest-balance solve plan

## Objective

Derive a deterministic, upper-body-only correction for iteration-b that lifts
the official chest-relative roll to the Candidate-A safe range without moving
pelvis, lower body, tail, or head local channels.

## Allowed writes

- `reports/V8-2-BALANCE-TRANSFER/evaluation/chest-solver/**`

No candidate GLB, generator, validator, rendering, or engine file is changed.
Temporary in-memory or `/tmp` GLB variants may be used solely to evaluate the
numerical response.

## Acceptance checks

1. Use the frozen 120-phase official evaluator convention.
2. Derive one bounded scalar solve applied only to `Bone_002` rotations.
3. Check official Candidate-A gates: chest roll/correlation/pitch/yaw, head
   caps, fixed pelvis/lower leg values, tail preservation, and seam.
4. Capture a reproducible search result and an implementation handoff.
