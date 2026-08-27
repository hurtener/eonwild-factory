# Procedural Animation Guide V4

## Goal

Generate reusable, species-tunable large-theropod animations that remain anatomically valid, terrain-aware and phase-consistent in a browser. The source rig may contain any useful number of deformation bones. V4 drives semantic functions over that original hierarchy rather than compressing it into a small humanoid proxy.

## Core equation

```text
final local pose =
    calibrated living-neutral pose
  + path/root frame
  + terrain-adapted pelvis support
  + contact-planned constrained legs
  + vertex-sole correction
  + torso/neck/head inertia
  + momentum-coupled tail response
  + attention and breathing
  + action layer
  + transition/inertialization layer
```

## Pipeline

### 1. Inspect and map the actual rig

The YAML semantic map identifies functional roles such as pelvis, thigh, shin, ankle, foot, toes, spine, neck, head, jaw and tail. V4 validates that every mapped source bone exists. The complete skin joint order and inverse-bind matrices remain unchanged.

### 2. Establish a living-neutral pose

The source Tarbosaurus has an open-mouth modeling/bind pose. V4 applies a locomotion-neutral jaw closure without modifying inverse binds. Breathing adds a sub-degree gape. Bite, roar and eating layers override this neutral closure.

### 3. Fit timing and posture conservatively

The reference fitter measures translation-normalized silhouette recurrence, torso angle statistics and cadence from the supplied side-view video. It is not markerless motion capture. Measurements become bounded profile suggestions, never unconstrained joint trajectories.

### 4. Plan root path and gait phase

Locomotion is sampled against a `MotionPath` and a phase schedule. The same phase drives contacts, support loads, leg preferences, body balance and tail forcing. Root distance is integrated from speed, allowing steady walk, acceleration, braking and curved turns to share one solver.

### 5. Create persistent contacts

Each foot has contact and next-contact targets. During stance, the target remains fixed in world space. During swing, a minimum-jerk trajectory blends between contacts with clearance and lateral shaping. This eliminates the impossible rear-to-front hinge flip that V3 was built to prevent and reduces foot drift.

### 6. Solve signed anatomical hinges

The thigh-shin and shin-ankle chains are solved only on their measured anatomical bend branch. Preference and continuity terms discourage abrupt solutions. The solver is allowed to miss an unreachable target by a small amount rather than reverse a knee or ankle.

### 7. Correct against real sole vertices

V4 selects a deterministic patch of mesh vertices influenced by each foot/ankle/toe subtree. After the leg solve, those vertices are skinned in the current pose and tested against terrain. A bounded correction moves the foot target along the terrain normal until loaded penetration and sole-gap metrics satisfy configured gates.

### 8. Adapt to terrain

Terrain supplies height and surface normal at root, foothold and selected-vertex positions. Feet align toward local normals within pitch/roll limits. Pelvis height, roll and pitch respond at lower authority so the torso does not glue itself to every small surface change.

### 9. Build whole-body response

Pelvis translation and rotation derive from support loading and path acceleration. Spine, neck and head compensation are distributed across their chains. The tail responds to support, yaw, yaw velocity, acceleration and turning, with a muscular root and more compliant distal joints.

### 10. Generate actions and transitions

Idle, alert, feeding, bite and roar are whole-body actions. They keep the feet anatomically solved and the neutral jaw contract intact. Transitions use minimum-jerk quaternion/translation blending, phase matching for moving loops, and explicit bridge clips for urgent browser actions.

### 11. Bake and validate

The direct GLB writer appends animation accessors/channels while preserving mesh, materials, textures, skins and inverse binds. Validation checks clip names, channel targets, sample times, hinge signs, contact error, penetration, joint derivatives, loop closure and transition endpoints.

## Extension model

V4 is a family kernel plus species profile. To add another large theropod, retain the architecture and replace:

- semantic map;
- scale and stride profile;
- neutral posture;
- hinge limits;
- tail mass/compliance distribution;
- action amplitudes and timing;
- visual reference constraints.

Do not fork the GLB writer, runtime state graph or validation harness unless the family itself changes.
