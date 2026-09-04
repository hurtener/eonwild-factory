# Eonwild V9 — Growth-aware biomechanical motion specification pack

This pack turns the V9 proposal into an implementation contract for the Eonwild Factory. It is a **design, data, solver, animation, and validation specification**. It does not claim that final V9 GLB animations have already been generated or perceptually approved.

## Decision

V9 should be an authored motion-program system constrained by a reduced-order biomechanical planner:

```text
MotionIntent
  + MotionProgram (performance and phase graph)
  + BodyInstanceProfile (morphology, mass properties, growth, condition)
  + EnvironmentState (terrain, contacts, target)
        ↓
CentroidalContactPlan (whole-body COM, momentum, support, impulse, contact schedule)
        ↓
WholeBodySolve (root/pelvis, legs, feet, toes, spine, neck, head, tail, jaw)
        ↓
Bounded presentation overlays (gaze, breathing, exertion, injury, variation)
        ↓
Baked clips + runtime metadata + validation evidence
```

Physics is not the director. Authored intent decides whether the animal is cautious, explosive, tired, threatening, feeding, or committed. Dynamics makes that performance feasible, continuous, and auditable.

## Key refinements to the original proposal

1. A reusable `MotionProgram` layer sits between intent and physics. It owns performance beats, contacts, timing ranges, target windows, branches, and interruption policy.
2. Ballistic equations apply to the **whole-body center of mass**, not automatically to the pelvis/root. The root is solved from COM and changing pose.
3. Static support polygons are used only for quasi-static phases. Locomotion, starts/stops, turns, attacks, and landings use COM velocity, planned contacts, momentum, friction, and contact-wrench/impulse feasibility.
4. Normalized segment mass is retained, but absolute force, impulse, landing, and injury claims remain disabled until a reviewed mass/geometry range is pinned.
5. Passive mass and inertia describe the motion required; they do not establish the force, torque, power, positive work, negative work, impulse, or rate that the animal can produce or absorb. A separate `ActuationCapacityProfile` is therefore mandatory.
6. Joint constraints use separate hard non-interpenetration/articulation envelopes and preferred loaded-motion envelopes, with pose/load coupling and rate limits. Independent Euler min/max boxes are not the default multi-axis model.
7. Heavy optimization and baking belong in the factory. Runtime selects/interpolates compatible plans and applies bounded terrain/contact and condition layers.
8. The final pose is an ordered authority stack, not an unrestricted sum of additives.

## Pack contents

- `docs/V9_ARCHITECTURE.md` — architectural critique, equations, authority ordering, growth model, and offline/runtime split.
- `docs/V9_ANIMATION_SYSTEM.md` — how 29 semantic animation contracts share 12 reusable motion programs.
- `docs/ANIMATION_CATALOG.md` — generated human-readable expansion of all 29 contracts, including every phase and body chain.
- `docs/IMPLEMENTATION_HANDOFF.md` — phased automated-agent handoff, independent reviewer roles, evidence, and stop conditions.
- `docs/RESEARCH_NOTES.md` — evidence boundaries and primary-source DOI references.
- `schemas/` — versioned contracts for motion intent, body profiles, segment mass properties, actuation capacity, coupled joint-limit envelopes/catalogs, growth, motion regimes, contact state, motion programs, biomechanical plans, dynamic actions, animation specs, and catalogs.
- `profiles/families/` — reusable heavy-predatory-biped family and explicitly provisional actuation-capacity contracts.
- `profiles/species/tarbosaurus/` — explicitly provisional normalized body, joint-limit, and growth templates.
- `profiles/fixtures/synthetic-heavy-biped.yaml` — deterministic non-Tarbosaurus fixture proving family reuse.
- `motions/contracts/global-animation-contract.yaml` — shared anatomy, contact, tail, head/neck, breathing, event, loop, and authority rules.
- `motions/programs/*.yaml` — twelve reusable motion programs.
- `motions/tarbosaurus/catalog.yaml` — all 29 machine-readable animation contracts.
- `motions/tarbosaurus/power-attack.yaml` — separate airborne/grounded V9 benchmark with full centroidal/contact phase graph and branches.
- `validation/acceptance-gates.yaml` — release-blocking mechanical, growth, reuse, and perceptual gates.
- `validation/pinned-regressions.yaml` — immutable V8.1/V8.2 and V5.5 input contracts.
- `scripts/render_animation_catalog.py` — deterministic Markdown rendering from `catalog.yaml`.
- `scripts/validate_spec_pack.py` — fail-closed schema and internal-consistency validation.
- `validation-report.json` — current structural validation result.

## Scientific truthfulness

The Tarbosaurus mass fractions are explicitly marked `gameplay_hypothesis`. They are normalized priors for exercising contracts, not published biological measurements. `absolute_dynamics_enabled` is `false` for that template. Before absolute impulse, force, speed, landing, or injury outputs are accepted, the factory must bind reviewed individual geometry, a volumetric mass range, segment uncertainty, and calibrated positive/negative actuation capacity. The included capacity and joint-limit files deliberately preserve unresolved numerical fields instead of inventing exact Tarbosaurus capabilities or ranges.

The synthetic second fixture has exact values only because it is fictional test data. It must never be presented as a reconstructed animal.

## Repository placement

Keep historical `procedural-animation-toolkit(v*)` releases immutable. Introduce a canonical reusable engine:

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

The approved V8.1/V8.2 walk remains a pinned regression fixture. V5.5 posture findings remain valuable inputs, but its own skeleton-based balance proxies are not treated as physical COM ground truth.

## Reproduce this pack’s structural checks

```bash
python3 scripts/render_animation_catalog.py
python3 scripts/validate_spec_pack.py
```

The structural validator checks contracts, counts, phase coverage, event types, normalized mass, capacity/joint-profile resolution, growth regimes, power-attack variants/branches, program references, and pinned hashes. It deliberately does **not** claim biological correctness or visual approval of animations that have not yet been implemented.
