# Procedural Animation Skill v2

V2 turns the successful v1 proof into a reusable creature-locomotion pipeline.

## Implemented in this package

- GLB inspection and non-destructive animation append.
- Semantic YAML rig mapping with arbitrary source bone counts.
- Canonical glTF Y-up anatomical basis.
- Two-cycle large-biped superloop.
- C2-continuous foot swing trajectories.
- World-space stance contacts.
- FABRIK position solve converted back into the original thigh, shin, ankle, and foot bones.
- Foot orientation stabilization and distributed three-toe articulation.
- Support-weight pelvis translation, roll, yaw, pitch, loading compression, and passing-position rise.
- Distributed spine, chest, neck, head, arm, and hand response.
- Neutral animation pose for a bind-pose-open jaw, plus subtle breathing gape.
- Nine-segment periodic spring-damper tail response.
- 120 Hz internal solve and 60 Hz dense GLB export.
- In-place and root-motion clips.
- Structural, contact, ground-proxy, and loop diagnostics.
- Offline textured validation rendering and a self-contained HTML comparison.

## Dependencies

Core generation:

```text
Python 3.11+
numpy
scipy
PyYAML
```

Preview generation additionally uses:

```text
VTK
Pillow
ffmpeg
```

Blender is not required for the direct-GLB runner. A Blender authoring adapter can still use the same semantic/controller layers and bake Blender Actions.

## Generate a GLB

```bash
python3 scripts/run_pipeline.py \
  --input /absolute/path/tarbosaurus.glb \
  --bone-map /absolute/path/tarbosaurus.bone-map.yml \
  --profile examples/profiles/large-theropod-v2.json \
  --output-dir /absolute/path/output
```

Outputs:

```text
<asset>.procedural-v2.glb
procedural-v2-report.json
animation-manifest.v2.json
resolved-profile.json
```

The GLB contains:

```text
PROC_WALK_LARGE_V2_INPLACE
PROC_WALK_LARGE_V2_ROOTMOTION
```

## Render the validation HTML

```bash
python3 scripts/render_validation_html.py \
  --input /absolute/path/tarbosaurus.glb \
  --bone-map /absolute/path/tarbosaurus.bone-map.yml \
  --output-dir /absolute/path/output
```

The HTML embeds its videos and has no CDN dependency.

## Important boundary

V2 is a quality-capable procedural foundation, not an automatic guarantee that every untouched profile will match a studio animator’s final shot. The system is designed so profile tuning, reference comparison, and reviewers improve the motion without rewriting the pipeline.
