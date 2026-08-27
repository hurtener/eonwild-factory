# Eonwild Procedural Animation Toolkit V3

V3 is the anatomically constrained evolution of the Eonwild procedural animation pipeline. It preserves the complete source deformation rig and generates ordinary glTF skeletal clips directly against a semantic YAML bone map.

V1 and V2 remain separate regression baselines. V3 does not overwrite either version.

## What V3 adds

- Explicit knee and ankle hinge-direction constraints measured from the source rig's rest pose.
- Hard flexion ranges that prevent reverse bending and near-hyperextension.
- A temporally continuous, bounded three-angle sagittal leg solve for thigh, knee, and ankle.
- Independent lateral hip correction without allowing the sagittal hinge to choose the wrong branch.
- Long-support relaxed walking with a reference-informed two-second cycle.
- A more upright, horizon-facing Tarbosaurus torso, neck, and head posture.
- Softer nine-joint tail dynamics: muscular root, lower distal stiffness, per-joint lag, and mild neutral sag.
- Persistent foot contacts, C2 swing paths, toe-off, pre-contact extension, three toe branches per foot, and ground correction.
- Neutral closed-mouth locomotion layered over the model's open-mouth bind pose.
- 120 Hz internal solving and 60 Hz dense GLB animation export.
- In-place and root-motion clips, deterministic diagnostics, fixture tests, and self-contained visual review HTML.

## It does not impose an 18-bone limit

The Tarbosaurus fixture has 75 skin joints. V3 preserves all 75 and drives 55 during relaxed walking. Other bones remain available for bite, roar, alert, eat, breathing, hand, claw, facial, or corrective layers.

## Requirements

Core generation:

```text
Python 3.11+
numpy
scipy
PyYAML
```

Offline visual validation additionally uses:

```text
VTK
Pillow
ffmpeg
```

Blender is optional. The direct-GLB runner writes standard glTF animation channels; a Blender adapter can use the same semantic controllers and bake Actions later.

## Generate V3 clips

```bash
python3 scripts/run_pipeline.py \
  --input /absolute/path/tarbosaurus.glb \
  --bone-map /absolute/path/tarbosaurus.bone-map.yml \
  --profile examples/profiles/large-theropod-v3.json \
  --output-dir /absolute/path/output
```

Outputs:

```text
<asset>.procedural-v3.glb
procedural-v3-report.json
animation-manifest.v3.json
resolved-profile.json
```

The generated GLB contains:

```text
PROC_WALK_LARGE_V3_INPLACE
PROC_WALK_LARGE_V3_ROOTMOTION
```

## Validate the real rig

```bash
python3 tests/run_fixture_validation.py \
  --input /absolute/path/tarbosaurus.glb \
  --bone-map /absolute/path/tarbosaurus.bone-map.yml \
  --profile examples/profiles/large-theropod-v3.json \
  --output /absolute/path/fixture-validation.json

python3 tests/validate_baked_glb.py \
  --source /absolute/path/tarbosaurus.glb \
  --generated /absolute/path/output/tarbosaurus.procedural-v3.glb \
  --expect PROC_WALK_LARGE_V3_INPLACE \
  --expect PROC_WALK_LARGE_V3_ROOTMOTION \
  --output /absolute/path/baked-glb-validation.json
```

## Review, do not auto-approve

V3 fails automatically on missing semantic roles, invalid GLB structures, reversed knees/ankles, broken loops, and other structural defects. Style still requires side, front, three-quarter, half-speed, and frame-step review. A valid solve can still need species-specific artistic tuning.

## V2 comparison inputs

When supplying V2 preview videos to the validation renderer, trim them to one gait cycle and retime them to the V3 cycle duration. The final Tarbosaurus validation package includes already phase-matched V2 previews.
