# V3 Architecture

## Package map

```text
scripts/
  run_pipeline.py                  direct GLB generation entrypoint
  render_validation_html.py        offline validation renderer
  eonproc_v3/
    gltf_io.py                     GLB parsing, accessors, skinning, animation writing
    rig.py                         semantic map, anatomical basis, mutable pose operations
    curves.py                      minimum-jerk, C2 bump, cyclic functions
    profile.py                     typed V3 biped profile and validation
    generator.py                   contacts, constrained legs, balance, jaw, tail, sampling
tests/
  test_core.py                     deterministic math/profile tests
  run_fixture_validation.py        real-rig anatomical and motion gates
  validate_baked_glb.py            source/generated structural comparison
runtime/
  phase-clock.ts                   distance-driven phase helper
  contact-events.ts                contact marker helpers
examples/
  profiles/large-theropod-v3.json
  work-orders/tarbosaurus-v3.json
  tarbosaurus.bone-map.yml
```

## Stage contracts

### Input contract

- Valid GLB 2.0.
- One selected skinned mesh/skin.
- Semantic YAML mapping all required family roles.
- Profile expressed at a reference hip height.

### Rig-analysis contract

The loader derives:

- glTF Y-up anatomical basis;
- source hierarchy and rest world transforms;
- thigh, shin, ankle, and foot segment lengths;
- signed rest knee and ankle bend directions;
- toe chains and ground-proxy heights;
- jaw and tail chains.

### Planner contract

For any global phase, the planner emits immutable `FootPlan` and `BodyPlan` values. Targets are in world space and remain persistent while loaded.

### Constrained-solver contract

The leg solver may reduce target accuracy to preserve anatomy. It must never cross the signed hinge direction. Hard joint bounds take precedence over perfect Cartesian reach.

### Pose-composition contract

Layers are composed in causal order:

```text
root translation
→ pelvis support pose
→ spine/neck/head posture
→ neutral jaw
→ tail dynamics
→ arms/secondary motion
→ left and right constrained leg solve
→ foot orientation and toes
```

### Generated-motion contract

The generator returns:

- internal and export times;
- continuous quaternion tracks;
- root translation;
- contact/body plans;
- diagnostics;
- optional world matrices used by the exact same offline renderer.

### GLB contract

The writer appends or replaces standard glTF animation channels while preserving:

- node count;
- skin joint order;
- inverse-bind matrices;
- mesh primitives;
- textures/materials;
- unmapped and undriven source joints.

## Extensibility

V3 separates family mechanics from creature tuning. A second large theropod usually needs a profile, not a rewritten solver. A quadruped needs a different contact scheduler and limb orchestration but can reuse GLB I/O, semantic maps, pose operations, curves, baking, reports, and validation.

## V4 boundary

The architecture already has extension points for:

- vertex-weighted sole collision;
- terrain height and normal targets;
- turn curvature;
- acceleration and braking state;
- action layers for alert, eat, bite, and roar;
- reference-derived species profile fitting.

Those are intentionally outside V3 so the anatomical relaxed-walk kernel remains testable in isolation.
