# Eonwild Factory — V8.3 consolidation and V9 biomechanics complete handoff

**Audience:** a lead engineer, automated coding agent, technical animator, or reviewer who has not read the prior discussion.

**Repository:** `hurtener/eonwild-factory`  
**Review pin used by this handoff:** `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3`  
**Status:** implementation handoff and specification. It does not claim that V8.3 or V9 animation artifacts have already been generated or visually approved.

## The mission in one paragraph

Build a reusable procedural animation factory for Eonwild’s heavy predatory bipeds. First consolidate a trustworthy **V8.3** from the approved V8.2 Tarbosaurus walk, the useful whole-body/contact/action capabilities of V5.5, and a new modular configuration/release system. Then use that foundation for **V9**, where authored animation intent is made physically coherent by segment mass properties, whole-body COM, support/contact planning, momentum, impulse, growth-aware capacity, and a whole-body pose/contact solver. The final system must produce the 29 specified Tarbosaurus animations without turning physics into the director or hard-coding Tarbosaurus into generic code.

## Read this pack in this order

1. `README_FIRST.md` — this file.
2. `docs/00_PRODUCT_AND_MOTION_CONTEXT.md` — what Eonwild is and why movement is the product.
3. `docs/01_VERSION_LINEAGE_AND_BASELINES.md` — what V5.5, V8.2, V8.3, and V9 mean.
4. `docs/02_V5_5_TO_V8_3_RECOVERY_PLAN.md` — exact capabilities to restore, rebuild, defer, or reject.
5. `docs/03_V8_3_TARGET_ARCHITECTURE_AND_RELEASE.md` — the immediate implementation target and release gates.
6. `docs/03A_V8_3_CLIP_RECOVERY_CATALOG.md` — exact mapping of all 21 base/action clips and 16 bridges.
7. `docs/04_GLOBAL_ANIMATION_CONTRACT.md` — rules applying to every animation.
8. `docs/animations/` — the detailed 29-animation catalog, split into four readable documents; `ALL_29_ANIMATIONS.md` is the canonical combined version.
9. `docs/05_V9_BIOMECHANICAL_ENGINE.md` — the stronger engine architecture.
10. `docs/06_RUNTIME_METADATA_AND_SPEC_FORMAT.md` — event vocabulary, phase/windows, runtime state, and machine-readable contract.
11. `docs/07_IMPLEMENTATION_WORKSTREAMS.md` and `docs/08_VALIDATION_AND_EVIDENCE.md` — execution and acceptance.
12. `docs/09_GOAL_PROMPT.md` — copy-paste kickoff prompt for an orchestrating agent.

## Non-negotiable interpretation

### V8.3 is not “copy V5.5 over V8.2”

V8.2 is the later approved relaxed-walk baseline. V5.5 contributes reusable capabilities, body-performance intentions, action mechanics, transition/runtime contracts, and validation ideas. Its old relaxed-walk samples, skeleton-based balance proxies, monolithic profile shape, and fixture-specific rig mutations do not overwrite V8.2.

### V9 is not full ragdoll or muscle simulation

V9 is an authored motion-program compiler:

```text
MotionIntent
+ MotionProgram
+ BodyInstanceProfile
+ Environment / target / contacts
        ↓
CentroidalContactPlan
        ↓
WholeBodySolve
        ↓
Bounded presentation overlays
        ↓
Baked clips + runtime metadata + evidence
```

Authored intent decides whether a bite is cautious or explosive, which leg launches, target height, contact timing, and what the animal does after contact. Dynamics determines whether the plan is feasible and how support, COM, momentum, landing, and recovery make it coherent.

### The 29 animations are semantic contracts

They are not 29 unrelated scripts and not 290 condition-specific clips. They share reusable programs plus procedural condition layers. The combined detailed catalog contains more than six thousand lines of phase-by-phase body, support, event, growth, and validation requirements.

## Immediate definition of success

A successful V8.3 release provides:

- an exact V8.2 compatibility reproduction;
- a separately reviewed V8.3 balanced variant whose pelvis/body changes do not regress contacts;
- modular versioned configs and strict loaders;
- semantic rig resolution with no generic `Bone_###` or species-name branching;
- the semantically recovered V5.5 21-clip base/action set and 16 authored bridges, staged by priority;
- one world-space plan yielding root-motion and in-place views;
- standardized events and animation metadata;
- deterministic manifests, hashes, numeric reports, and fixed-camera perceptual evidence;
- no claim that legacy support-phase balance is physical COM.

A successful V9 then proves:

- segment mass fractions and COM reconstruction;
- contact patches and support/dynamic feasibility;
- growth-aware motion regimes without snapping;
- grounded and, when feasible, airborne power-attack planning;
- all 29 animations through reusable programs;
- a second digitigrade-biped fixture without per-frame species patches.

## Machine-readable companions

- `matrices/v5_5_to_v8_3_recovery.yaml` — detailed recovery ledger.
- `matrices/v8_3_clip_recovery.yaml` — all 21 base/action clips and 16 bridges.
- `motions/tarbosaurus/catalog.yaml` — 29 animation contracts.
- `motions/tarbosaurus/power-attack.yaml` — dynamic attack benchmark.
- `profiles/`, `schemas/`, and `validation/` — V9 contracts and gates.
- `config/v8_3-package-layout.example.yaml` — proposed V8.3 modules and release products.

## Sources and authority

The canonical game-design files are copied under `references/game-design/`. Repository baselines remain in their original historical directories and should be read at the pinned commit. Facts or mechanics not supported by those materials are labeled as engineering recommendation, provisional hypothesis, or open decision.
