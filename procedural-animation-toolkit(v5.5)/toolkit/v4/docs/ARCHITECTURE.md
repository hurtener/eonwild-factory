# V4 Architecture

## Modules

```text
reference_fit.py  -> image-space cadence/posture evidence
profile.py        -> explicit species and quality parameters
path.py           -> straight and arc root trajectories
terrain.py        -> height/normal surfaces
sole.py           -> weighted vertex contact patches and measurements
locomotion.py     -> contact, body, leg, terrain and tail solve
actions.py        -> idle, alert, eat, bite and roar layers
transitions.py    -> pose and phase-matched bridges
clip.py           -> normalized animation containers
generator.py      -> complete pack orchestration and manifest
gltf_io.py        -> preserved direct GLB read/write
runtime/*         -> browser phase/state/terrain integration
```

## Data flow

```text
GLB + semantic YAML + V4 profile + optional reference video
                       |
                       v
             validated anatomical model
                       |
          +------------+-------------+
          |                          |
   locomotion schedules         action controls
          |                          |
  path + terrain + contacts      planted action base
          |                          |
 signed leg solve + sole test    whole-body layers
          +------------+-------------+
                       |
                 AnimationClip
                       |
          transitions + state manifest
                       |
                 multi-clip GLB
                       |
       browser phase clock + motion graph
```

## Authoring versus runtime

Offline generation performs the expensive work: constrained IK, selected-vertex skinning, contact correction, tail dynamics and action synthesis. Runtime should select clips, synchronize phase, translate the actor, and apply only low-authority terrain residuals. Re-solving the full creature every browser frame is unnecessary and would make results nondeterministic across devices.

## Invariants

- The source deformation skeleton is authoritative.
- Semantic tags are an adapter, not an export skeleton.
- Bind pose and living-neutral pose are distinct.
- Joint feasibility outranks target accuracy.
- Loaded foot contacts are evaluated in world space.
- Root distance, gait phase and clip playback remain coupled.
- Actions declare priority and return state.
- Generated clips are reproducible from recorded inputs and profile hashes.
