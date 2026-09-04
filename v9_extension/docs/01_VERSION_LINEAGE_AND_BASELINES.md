# Version lineage and baseline authority

## 1. Why this document exists

Several historical versions solve different parts of the problem. A new implementer must know which version is authoritative for which behavior; otherwise “combining” them will silently reintroduce old defects.

## 2. V5.5 — broad constrained animation factory

V5.5 is the broad historical system. It contains 37 clips: 21 base/action/locomotion clips and 16 authored transitions. Its useful contributions include:

- semantic rig mapping and a 75-joint Tarbosaurus fixture;
- vertex sole/contact and terrain machinery inherited from V4;
- signed anatomical leg constraints;
- pelvis translations and a stronger body/posture pass;
- a principal support leg and less extreme rear stance;
- hip-led recovery with delayed distal response;
- leg-driven bite delivery;
- pelvis/knee feeding descent and tail counterbalance;
- mesh-witness jaw calibration;
- protected quaternion-space polish;
- endpoint-exact and phase-matched transitions;
- runtime sequencing, source-phase scheduling, root offsets, and exact authored handoffs;
- animation manifests, reports, and release tests.

Its validated generated SHA recorded by the release report is:

```text
4e6e85dc82e941a3fc10109ca781dd3dcbb084699dc19834bf8683c04b22fe65
```

Important boundary: V5.5’s balance measurements are skeleton-based visual proxies. They are not physical center-of-mass or biological validation.

## 3. V8.1 — approved walk source

V8.1 iteration 38 is referenced by SHA:

```text
1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e
```

It is the approved walk source underlying the later V8.2 transfer. The current lean V8.2 package references this source rather than duplicating it.

## 4. V8.2 — approved balance-transfer walk

V8.2 is deliberately narrow and high-discipline. It starts from a pinned iteration-B base:

```text
bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2
```

and reproduces the approved output:

```text
a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5
```

For the two relaxed-walk clips, V8.2 changes only the declared chest, five neck, and head rotation nodes. It applies a bounded world-relative chest-roll response, reconstructs the neck chain to preserve the intended head behavior, enforces local-delta limits, preserves the GLB JSON and all other binary accessors, and verifies an exact release inventory.

### V8.2 is authoritative for

- the approved relaxed-walk perception;
- root, pelvis, legs, feet, toe, and tail tracks in that approved artifact;
- allowed-node and unchanged-channel discipline;
- exact reproducibility and package verification philosophy.

### V8.2 does not contain

- a reusable whole-body engine;
- a physical COM model;
- the full V5.5 clip/action set;
- growth-aware regimes;
- momentum/impulse planning;
- a generalized data contract for all 29 animations.

## 5. V8.3 — the immediate consolidation target

At review pin `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3`, no inspected `procedural-animation-toolkit(v8.3)` package exists. In this handoff, V8.3 is a target definition:

```text
V8.3 =
  approved V8.2 walk authority
  + selected V5.5 body/contact/action/transition/runtime capabilities
  + modular reusable configuration
  + strict release/evidence contracts
```

V8.3 should prove that the project can combine quality without combining historical defects.

### V8.3 has two walk products

1. **Compatibility walk:** exact V8.2 reproduction, used as a permanent regression.
2. **Balanced V8.3 walk:** a separately reviewed variant that adds bounded pelvis/whole-body support-phase corrections. Any pelvis change must counter-solve the loaded leg/foot/toe chain so world contacts and root displacement remain valid.

This separation prevents a “better balance” experiment from destroying the only approved walk.

## 6. V9 — the biomechanical motion compiler

V9 replaces legacy support-phase balance proxies with a measured reduced-order body model:

- segment mass fractions and local COM;
- approximate inertia;
- whole-body COM and momentum;
- foot/toe/body contact patches;
- static and dynamic balance criteria;
- actuation/capacity contracts;
- growth-aware motion regimes;
- takeoff, ballistic COM, landing, braking, and failure planning;
- a reusable whole-body pose/contact solver;
- detailed semantic animation specs and bounded presentation layers.

V9 should be built on an approved V8.3 foundation, not while the factory layout and baseline migration are still unstable.

## 7. Authority table

| Question | Authority |
|---|---|
| What should the approved relaxed walk look like? | V8.2 artifact and review media |
| Which broad animation capabilities existed historically? | V5.5 manifest, source modules, and reports |
| Is V5.5 support balance physical COM? | No; its own report says it is a visual proxy |
| How should V8.3 be packaged? | This handoff’s V8.3 architecture and recovery matrix |
| How should the 29 animations behave? | `docs/animations/ALL_29_ANIMATIONS.md` and `motions/tarbosaurus/catalog.yaml` |
| How should true COM/momentum/growth be implemented? | V9 architecture, schemas, profiles, and power-attack spec |
| What decides final animation taste? | Independent perceptual review against approved evidence |

## 8. Versioning rules

- Historical release directories are immutable.
- New releases are additive and semantically versioned.
- Every artifact pins source/config/tool hashes.
- A migration may preserve intent without preserving old samples.
- No version label implies scientific certainty.
- Numeric PASS and binary reproducibility do not replace visual approval.
