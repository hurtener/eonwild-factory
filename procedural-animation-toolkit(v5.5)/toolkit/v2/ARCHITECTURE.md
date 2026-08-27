# V2 Architecture

## Package map

```text
scripts/
  run_pipeline.py                 Direct GLB bake entrypoint
  render_validation_html.py       Offline textured review renderer
  eonproc_v2/
    gltf_io.py                    GLB parsing, skinning, animation writing
    rig.py                        semantic map, basis, mutable pose operations
    curves.py                     minimum-jerk and loop-safe curves
    profile.py                    typed biped profile
    generator.py                  contact, balance, tail, jaw, IK, sampling
examples/
  profiles/large-theropod-v2.json
  work-orders/tarbosaurus-v2.json
  tarbosaurus.bone-map.yml
tests/
  test_core.py
runtime/
  phase-clock.ts
  contact-events.ts
```

## Contracts

### Semantic map

The family kernel never relies on source bone names. It asks for semantic roles such as `thigh_l`, `spine_04`, or `tail_07`. The map may point several semantic aliases to one source bone, but validation reports the unique source count.

### Profile

The profile is written at a reference hip height and scaled to the actual creature. Angular values remain independent unless a species profile overrides them; linear stride, foot lift, pelvis displacement, and tolerances scale with measured hip height.

### Generated motion

The generator returns:

- internal sample times;
- export sample times;
- continuous quaternion tracks;
- root translation;
- per-frame contact/body plans;
- diagnostics;
- optional world matrices for preview rendering.

### GLB boundary

The exported GLB contains ordinary sampled skeletal animation. It does not require Python, Blender drivers, or geometry-node evaluation at runtime.

## Family extension points

The reusable shell is:

```text
I/O → semantics → profile → target planner → pose layers → constraints → bake → validate
```

A quadruped replaces the biped contact schedule and limb solver orchestration. A swimmer replaces ground contacts with body-wave and fin targets. A flyer replaces foot stance with wingbeat, aerodynamic body attitude, takeoff, and landing states. The GLB writer and validation harness remain shared.
