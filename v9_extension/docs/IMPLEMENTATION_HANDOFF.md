# Implementation handoff for an automated agent

## Mission

Implement a reusable growth-aware biomechanical motion engine that preserves the approved adult walk, computes auditable COM/support/momentum plans, and produces Tarbosaurus motion from data rather than species-name branches.

## Workspace

```text
branch: codex/v9-biomechanics
worktree: eonwild-factory-v9-biomechanics
review pin: aca1eab3f6e9f6970cf8a8281f4440a74f8551d3
```

Historical `procedural-animation-toolkit(v*)` release directories are immutable inputs.

## Target layout

```text
src/eonmotion/
  body/
  contacts/
  centroidal/
  programs/
  planning/
  solve/
  bake/
  gltf/
  validation/
profiles/
motions/
schemas/
fixtures/
tests/
artifacts/v9/
```

## A — Contracts and loaders

1. Implement strict versioned loaders for this pack’s schemas.
2. Require units, coordinate-system declaration, unknown-field policy, provenance, and uncertainty.
3. Resolve semantic roles through the existing bone map; generic code may not reference literal Tarbosaurus bone names.
4. Resolve every `joint_limit_profile`, `joint_limit_catalog`, and `actuation_capacity_profile` reference fail-closed.
5. Emit a resolved profile containing all derived dimensions, segment properties, joint limits, capacities, and evidence status.

**Gate:** malformed, non-positive, non-normalized, unitless, or unprovenanced physical data fails closed.

## B — Body segmentation and mass properties

1. Partition the rest-pose skinned mesh using semantic bones and weights.
2. Repair/voxelize regions or fit configured geometric proxies.
3. Estimate volume, local COM, principal inertia, and uncertainty samples.
4. Render segment regions, local COMs, total COM, proxies, and principal axes.
5. Keep provisional values visibly provisional.

**Gate:** fractions sum to one; resolved inertia is symmetric positive definite; output is deterministic; uncertainty sampling is seeded.

## B2 — Joint and actuation-capacity resolution

1. Build articulation frames from semantic parent/child roles and the pinned rest pose.
2. Keep hard articulation/non-interpenetration boundaries separate from preferred loaded-motion envelopes.
3. Use hinge, swing-twist, sampled-orientation-surface, or custom parameterization per articulation; do not default to independent Euler boxes.
4. Resolve positive force/torque, power, work, and impulse separately from negative braking/landing absorption.
5. Apply growth, fatigue, injury, pain-confidence, posture, contact-duration, and rate modifiers without changing structural mass tier.
6. Preserve unresolved values as unresolved; no solver may silently substitute an authoritative biological number.

**Gate:** every referenced articulation resolves; preferred poses remain inside hard bounds; pose/rate/acceleration checks pass; absolute capability export stays disabled until both mass geometry and actuation capacities are reviewed.

## C — Contacts

1. Derive foot/toe witness geometry from skinned vertices and semantic toe chains.
2. Represent patches, not ankle points.
3. Use contact states: approaching, contact, loading, loaded, unloading, toe-off.
4. Bind substrate/friction assumptions to environment fixtures.
5. Preserve approved foot trajectories until replacement passes equivalence review.

**Gate:** no loaded-foot skate, arbitrary yaw, marker mismatch, or terrain penetration.

## D — Centroidal planner

1. Reconstruct segment transforms, COM, linear momentum, and angular momentum every sample.
2. Implement static support margin for slow/stationary phases.
3. Implement extrapolated-COM and contact-wrench/impulse checks for dynamics.
4. Generate bounded pelvis/chest/neck/tail compensation requests.
5. Schedule a corrective step when compensation authority is insufficient.

**Gate:** whole-body COM—not pelvis—is authoritative.

## E — Growth

1. Resolve the motion tier primarily from resolved structural mass/weight with hysteresis; resolve continuous traits from age, dimensions, proportions, inertia, strength, condition, and growth profile.
2. Generate juvenile, subadult, adult, and heavy-adult fixtures.
3. Separate morphology from temporary fatigue/injury.
4. Implement hysteresis and phase-preserving regime changes.
5. Validate monotonic, explainable trends without assuming every curve is linear.

**Gate:** no scaled-adult juvenile and no phase/contact/velocity snap.

## F — Locomotion

Implement:

1. stationary support;
2. approved relaxed walk reproduction;
3. fast walk;
4. run;
5. sprint;
6. starts/stops;
7. wounded idle and stumble.

Bake root-motion and in-place views from one authoritative world-space plan, not two independent solves.

**Gate:** approved adult walk remains reproducible within pinned mechanical and perceptual tolerances.

## G — Power attack

1. Grounded lunge first.
2. Select launch leg from current support phase.
3. Solve COM shift/preload and takeoff impulse.
4. Solve ballistic COM and root-from-COM path.
5. Budget angular momentum and bite timing.
6. Plan lead contact, catch contact, braking, and continuation.
7. Add hit, miss, target-yields, target-resists, and landing-failure branches.
8. Reject infeasible air attacks to grounded fallback.

**Gate:** exact velocity continuity; no root reset; capability varies explainably with mass, inertia, strength, fatigue, injury, target, and terrain.

## H — Remaining programs

Implement attention, bite variants, shove, feeding/tear/swallow/drink, lie/rest/rise, calls, and collapse from `catalog.yaml`.

## I — Validation evidence

Required per release:

```text
resolved-profile.json
motion-plan.json
animation-manifest.json
mechanical-validation.json
contact-report.json
joint-limit-report.json
capacity-feasibility-report.json
growth-sweep.json
fixed-camera-side.mp4
fixed-camera-3q.mp4
com-support-debug.mp4
release inventory + SHA256
```

Test schema/provenance, determinism, mass/inertia, COM/momentum, contact/support, footskate, penetration, joint limits, angular rates, takeoff/flight/landing, transitions, growth/hysteresis, second-profile reuse, and perceptual regression.

## Sub-agents

- Body/mass-properties engineer.
- Contact/foot-solver engineer.
- Centroidal dynamics engineer.
- Growth/allometry engineer.
- Motion-program/spec engineer.
- GLB/bake/runtime-metadata engineer.
- Numeric validation reviewer.
- Perceptual animation reviewer.
- Scientific provenance reviewer.

Reviewers must be independent of authors.

## Stop conditions

Fail the release when contacts regress; whole-body COM is not measured; a hand-shaped flight root lacks COM proof; passive mass is mistaken for active capacity; unresolved joint/capacity values drive absolute claims; tier changes snap; generic code branches on Tarbosaurus; the second fixture needs per-frame patches; or numeric PASS conflicts with visibly poor motion.
