# Eonwild Procedural Animation Toolkit V4

V4 turns the V3 anatomically constrained Tarbosaurus locomotion solver into a browser-oriented creature animation factory. It preserves the complete source skeleton, fits timing/posture from the supplied side-view reference, solves selected sole vertices against terrain, generates curved-path turning and speed changes, creates whole-body actions, bakes explicit transitions, writes all clips into one GLB, and emits a runtime manifest.

## What V4 contains

- Reference-video silhouette fitting with explicit limits.
- Rich semantic bone mapping; no 18-bone export reduction.
- Signed knee and ankle hinges inherited from V3.
- Vertex-level sole selection from skin weights.
- Terrain height and normal queries.
- Persistent contact targets and sole penetration correction.
- Straight, sloped, uneven and curved paths.
- Start, acceleration, braking and stop schedules.
- Relaxed and alert locomotion.
- Idle, alert idle, eating, bite and roar actions.
- Direct and routed action-to-locomotion transitions.
- Root-motion and in-place clip variants.
- Browser state graph, phase clock and residual terrain adapter.
- Numeric validation plus human perceptual review artifacts.

## Fast reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

python3 scripts/reference_fit.py \
  ../../inputs/tarbosaurus_reference_walk_side_v02.mp4 \
  --output /tmp/reference-fit-v4.json

python3 scripts/run_pipeline_v4.py \
  --input ../../inputs/tarbosaurus_source.glb \
  --bone-map ../../inputs/tarbosaurus_bone_map.edited.yml \
  --output-dir /tmp/tarbosaurus-v4

python3 tests/validate_generated_pack.py \
  --glb /tmp/tarbosaurus-v4/tarbosaurus_procedural_v4_animation_pack.glb \
  --report /tmp/tarbosaurus-v4/procedural-v4-report.json
```

## Important output clips

```text
PROC_WALK_RELAXED_V4_INPLACE / ROOTMOTION
PROC_WALK_UNEVEN_TERRAIN_V4_INPLACE / ROOTMOTION
PROC_WALK_UPSLOPE_V4_INPLACE / ROOTMOTION
PROC_TURN_LEFT_35_V4_INPLACE / ROOTMOTION
PROC_TURN_RIGHT_35_V4_INPLACE / ROOTMOTION
PROC_START_WALK_V4_INPLACE / ROOTMOTION
PROC_BRAKE_TO_IDLE_V4_INPLACE / ROOTMOTION
PROC_ALERT_WALK_V4_INPLACE / ROOTMOTION
PROC_IDLE_BREATH_V4
PROC_ALERT_IDLE_V4
PROC_EAT_LOOP_V4
PROC_BITE_ATTACK_V4
PROC_ROAR_V4
```

The animation pack also contains explicit state-transition clips. See `docs/ACTIONS_AND_TRANSITIONS.md` and `animation-manifest.v4.json`.

## Definition of success

A technically valid result is not automatically a believable animal. V4 separates:

1. structural validation;
2. biomechanical/contact validation;
3. motion-signal validation;
4. browser/runtime validation; and
5. perceptual review against the supplied reference.

The last gate remains human by design.


## Deep-dive documents

- `docs/IMPLEMENTATION_MATRIX.md` maps every requested V4 capability to code, output, runtime contract and validation.
- `docs/BROWSER_PERFORMANCE_AND_FIDELITY.md` defines the offline/runtime split and browser quality tiers.
- `docs/REFERENCE_FITTING.md`, `VERTEX_SOLE_AND_TERRAIN.md`, `ACTIONS_AND_TRANSITIONS.md`, and `QUALITY_GATES.md` cover the core subsystems.

## Validated profile versus ultra profile

The produced 37-clip GLB uses `examples/profiles/tarbosaurus-v4-browser-production.json`:

```text
60 Hz internal solve and export
64 selected sole witnesses per foot
8 bounded leg-solver evaluations
```

`examples/profiles/tarbosaurus-v4-ultra-offline.json` preserves a more expensive option:

```text
120 Hz internal solve / 60 Hz export
up to 192 sole witnesses per foot
20 bounded leg-solver evaluations
```

The latter is an authoring option, not a claim about how the downloadable validation GLB was generated.

## Interactive browser validation

`browser_demo/` contains a dependency-free WebGL2 viewer for the exact generated GLB. It evaluates the 75-joint skin with all three joint/weight sets and supports orbit camera controls, root-motion following, clip switching, crossfades, terrain presentation and full eat/bite/roar sequences.

```bash
cd browser_demo
python3 serve.py
```

A separate self-contained HTML in the validation package embeds both the viewer and the complete GLB.
