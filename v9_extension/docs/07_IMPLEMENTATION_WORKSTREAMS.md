# Implementation workstreams and agent operating model

## 1. Operating principle

Parallelism is useful only when contracts and integration gates are explicit. The lead agent owns the plan, dependency graph, immutable baseline, release truthfulness, and final integration. Sub-agents work in isolated scopes; reviewers are independent from authors.

## 2. Phase 0 — repository and contract audit

Deliver:

- repository pin and clean-worktree proof;
- exact inventory of V5.5 and V8.2 source artifacts;
- hash verification;
- semantic rig resolution report;
- current clip/accessor/channel inventory;
- mapped V5.5 recovery matrix with no unaccounted capability;
- proposed canonical directory tree;
- test/evidence harness before motion changes.

No animation changes are accepted in Phase 0.

## 3. Phase 1 — productized V8.2 compatibility

Implement:

- strict config/schema loaders;
- immutable fixture management;
- exact V8.2 generator and verifier in canonical architecture;
- changed/unchanged channel reporting;
- fixed-camera evidence generation;
- resolved profile output;
- release manifest and inventory.

Gate: compatibility output passes the existing V8.2 contract and new package checks.

## 4. Phase 2 — V5.5 subsystem recovery

Parallel workstreams:

### Rig/contact engineer

- semantic map and hierarchy;
- sole/toe witness resolution;
- contact-state representation;
- loaded patch lock;
- terrain interface;
- optional foot-pivot diagnostic only.

### Body/secondary-motion engineer

- support-phase pelvis correction proxy;
- counter-solve legs to preserve contacts;
- V8.2 trunk/neck/head productization;
- damped tail state;
- breathing, attention, forelimb, variation overlays.

### Jaw/action engineer

- mesh-witness jaw calibration;
- action jaw staging;
- neutral idle, alert idle, grounded bite, feeding, threat call.

### Transition/runtime engineer

- endpoint/derivative/contact-state bridges;
- phase matching;
- state packets;
- queue/deadline/fallback;
- exact handoff and event dispatch.

### Release/validation engineer

- mechanical reports;
- event/spec validation;
- root/in-place equivalence;
- media generation;
- inventory/hashes.

Gate: each recovered subsystem is independently tested against V8.2 before integration.

## 5. Phase 3 — V8.3 balanced walk and P0 clip set

Implement the compatibility and balanced outputs separately. The balanced walk changes pelvis/body only through declared scopes and counter-solves loaded contacts. Generate P0 states, gait transitions, alert walk, bite, feed, call, and bridges.

Gate: no contact/root regression, all P0 fixed-camera reviews approved.

## 6. Phase 4 — V8.3 P1 terrain and turning

Implement signed-curvature turns and deterministic slope/uneven fixtures from the common gait/contact system.

Gate: no special per-frame Tarbosaurus patches and flat-terrain no-op equivalence.

## 7. Phase 5 — V9 body and centroidal model

Parallel workstreams:

- body segmentation/mass properties;
- hard/preferred joint limits;
- actuation/capacity profiles;
- contact patches/support regions;
- whole-body COM, linear momentum, angular momentum;
- growth/allometry and tier hysteresis;
- planner diagnostics and uncertainty sweeps.

Gate: approved adult walk can be measured/reproduced through the new body model without changing its accepted appearance.

## 8. Phase 6 — V9 animation waves

### V9.1 locomotion and condition

Animations 01–10, 25, 26.

### V9.2 perception, combat, and interactions

Animations 11–21 plus grounded and feasibility-gated airborne power attack.

### V9.3 posture, calls, and terminal state

Animations 22–24 and 27–29.

## 9. Agent roles

- **Lead/orchestrator:** owns scope, contracts, integration, and release truth.
- **Rig and skin engineer:** role resolution, articulation frames, witness geometry, deformation integrity.
- **Contact engineer:** contact schedules, patches, foot/toe solver, terrain adaptation.
- **Locomotion engineer:** gait programs, starts/stops, turning, root/phase relationships.
- **Centroidal dynamics engineer:** COM, momentum, impulses, dynamic feasibility.
- **Growth/allometry engineer:** morphology/capacity curves, tiers, hysteresis, sweeps.
- **Action/interactions engineer:** bites, shove, feeding, tear, drink, target contacts.
- **Presentation engineer:** breathing, gaze, throat, forelimbs, tail detail within authority.
- **GLB/runtime engineer:** baking, manifests, state packets, events, runtime sequencing.
- **Mechanical reviewer:** independent numeric/constraint/contact review.
- **Perceptual reviewer:** independent fixed-camera animation review.
- **Scientific-honesty reviewer:** verifies provenance, uncertainty, and claim boundaries.

## 10. Integration rules

- Each workstream modifies only declared files/modules.
- Each PR includes tests, reports, and before/after evidence relevant to its scope.
- No author self-approves perceptual quality.
- Generic code may not branch on `tarbosaurus` or literal bone names.
- Temporary compatibility adapters are isolated and carry removal criteria.
- A failed gate returns to the owning workstream; it is not waived by unrelated progress.

## 11. Required status updates from agents

Every implementation report states:

```text
what changed
why it changed
source contract
files and channels touched
tests run
numeric evidence
visual evidence
known limitations
provisional/scientific boundary
next dependency
```

## 12. Stop conditions

Stop and fail the release when:

- V8.2 compatibility cannot be reproduced;
- historical baselines were modified;
- a balanced pelvis change creates foot slide or root drift;
- a generic solver hard-codes the Tarbosaurus fixture;
- root-motion and in-place clips diverge;
- an action bypasses support/commitment/recovery;
- transition pose is exact but velocity/contact state pops;
- numeric PASS conflicts with visibly poor motion;
- legacy proxies are labeled as physical COM;
- unresolved capacity/joint values produce absolute biological claims;
- a second fixture needs per-frame code patches.
