# Eonwild Procedural Animation Skill V7

## Purpose

V7 is the production-oriented heavy-biped animation factory used to generate the Tarbosaurus validation pack. It is a rebuild of locomotion around one non-negotiable invariant:

```text
root path
→ pelvis movement
→ full leg IK
→ vertex-level sole correction
→ export those exact local transforms
```

No post-solve balance translation may be added after foot contacts have been validated. This rule exists because the V6 regression exported a pelvis track that did not match the pelvis used by the leg solver, causing visible hovering, penetration, and side-to-side flight in the browser.

V7 also upgrades turning from a root-yaw clip into a mass-reorientation behavior:

```text
gaze/head anticipates path
→ neck distributes the lead
→ chest begins turning
→ inside/outside steps diverge
→ pelvis commits
→ tail counter-shapes and settles
```

## Inputs

Required:

- A skinned GLB with a complete deformation hierarchy.
- A semantic YAML bone map.
- A V7 profile or the included Tarbosaurus defaults.

Optional but strongly recommended:

- A side-view locomotion reference.
- Behavior references for feeding, attack, display, and recovery.
- A ground or height-field sampler for terrain-aware clips.

The workflow does not impose an 18-bone limit. It preserves the source skin and drives as many mapped bones as the behavior needs.

## End-to-end workflow

### 1. Inspect and map the rig

Resolve semantic roles rather than hard-coding species-specific node names:

- root and pelvis
- thigh, shin, ankle, foot, toe branches
- distributed spine and chest
- distributed neck and head
- jaw hierarchy
- arms, wrists, hands, claws
- complete tail chain

Verify hierarchy, rest transforms, local axis signs, and inverse-bind matrices.

### 2. Fit reference timing separately from joint motion

Single-view video can support:

- cadence
- stance/swing timing
- torso carriage
- head carriage
- approximate stride rhythm
- qualitative leg sequencing

It cannot establish calibrated world scale, force, or exact 3D joint trajectories. V7 records this distinction in the reference-fit report.

### 3. Build immutable foot contacts

For each side, calculate contact points in a persistent path frame. During stance, the contact point does not move with the body. During swing, the target follows a minimum-jerk trajectory from the old contact to the next contact.

Use the complete chain:

```text
thigh → shin → ankle → foot → toe branches
```

The signed knee and ankle bend directions are derived from the real rest hierarchy and enforced at every internal sample.

### 4. Solve body motion before the legs

The V7 body plan computes:

- root path position and heading
- terrain height and surface normal
- small support-driven pelvis translation
- pelvis roll, yaw, and pitch
- speed and acceleration response
- alert posture
- turn commitment

Only after these values are known are both legs solved to their world-space targets.

### 5. Validate with mesh vertices

The semantic foot joint is not the sole. V7 selects actual weighted sole vertices from the mesh, re-skins them, measures their signed distance to terrain, corrects the foot target, and re-solves the leg.

Measure:

- maximum loaded penetration
- loaded contact-quantile error
- target error
- correction magnitude
- swing clearance
- anatomical reversals

### 6. Add upper-body and tail motion without invalidating contacts

Spine, neck, head, jaw, arms, and tail are sibling branches beneath the already-solved pelvis. They may be shaped after the leg solve as long as they do not translate or rotate the root/pelvis again.

### 7. Export at 60 Hz from a 120 Hz internal solve

The internal solve catches joint discontinuities and contact errors. The exported 60 Hz tracks remain suitable for browser animation while preserving exact transition endpoints and loop boundaries.

### 8. Validate the baked GLB and browser runtime

A procedural result is not accepted because the Python generator passed. Reparse the final GLB and verify:

- animation count and names
- skin-joint order
- inverse-bind matrices
- channel targets
- increasing sample times
- root and pelvis translation channels
- exact transition endpoints
- runtime queue/handoff behavior
- root-motion loop accumulation

## Turn authoring rules

### The head does not rotate the animal by itself

Head lead is a visual and inertial anticipation layer. The actual path remains controlled by the root trajectory and foot placement. A good large-theropod turn has a sequence rather than one simultaneous rotation.

### Left turn

- eyes/head lead left
- neck follows with distributed curvature
- chest begins left rotation
- left foot becomes the inside step
- right foot takes the longer outside arc
- pelvis commits later
- body leans modestly into the turn
- tail initially counter-shapes right, then settles

Right turns mirror this logic.

### Turn quality gates

- head lead is visibly greater than neck lead
- neck lead is greater than chest lead
- lead begins before half the final heading has been reached
- inside/outside contact geometry differs
- no knee or ankle branch reversal
- loaded sole vertices remain within terrain gates
- tail has an opposite counter-shape
- beginning and end are transition-safe

## Action generation

V7 includes:

- living-neutral idle
- alert idle
- relaxed/alert locomotion
- terrain and slope locomotion
- left/right turns
- start and brake
- whole-body eating
- left- and right-lead power bites
- roar
- exact action/locomotion transitions

Actions use the same order as locomotion: body/pelvis intent first, contact/leg solution second, expressive upper-body branches last.

## Anti-regression rules

Never:

- add pelvis translation after the leg solve
- smooth foot-contact or leg tracks without rechecking contacts
- loop root motion by sampling time modulo duration without accumulating cycle displacement
- apply an extra runtime crossfade after an authored transition
- substitute a root-yaw-only turn for a full-body turn
- infer exact biomechanics from an uncalibrated single-view reference
- delete source bones to satisfy an arbitrary export count

## Primary commands

```bash
python3 scripts/reference_fit.py inputs/tarbosaurus_walk.mp4 \
  --output work/reference-fit.json

python3 scripts/run_pipeline_v7.py \
  --input inputs/tarbosaurus.glb \
  --bone-map inputs/bone-map.yml \
  --output-dir validated_result/v7

python3 -m unittest discover -s tests -p 'test_v7*.py' -v

python3 tests/validate_v7_release.py \
  --glb validated_result/v7/tarbosaurus_procedural_v7_animation_pack.glb \
  --report validated_result/v7/procedural-v7-report.json \
  --manifest validated_result/v7/animation-manifest.v7.json \
  --output validated_result/v7/v7-release-validation.json
```

## Acceptance philosophy

Automated gates establish that the animation is reproducible, anatomically bounded, contact-aware, structurally valid, and browser-playable. Perceptual review still decides whether the motion feels like a living animal. Numeric success is necessary, not sufficient.
