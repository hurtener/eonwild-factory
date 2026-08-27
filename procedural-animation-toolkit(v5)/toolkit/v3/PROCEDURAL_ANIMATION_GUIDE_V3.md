# Eonwild Procedural Animation Guide — V3

## Purpose

Generate expressive creature animation from rich, fully rigged GLB assets while keeping the source skeleton intact. Shared family mechanics provide locomotion; creature profiles provide cadence, stance, posture, mass response, and species character.

V3 is built around causality:

```text
contact plan
  → constrained supporting leg
  → pelvis moves over support
  → torso and head compensate
  → tail responds with delayed counteraction
  → feet and toes load, extend, release, and recover
```

## Pipeline

```text
GLB + semantic YAML map
        ↓
rig validation + anatomical basis
        ↓
rest-pose hinge direction and segment measurement
        ↓
size-resolved family/species profile
        ↓
foot contact and swing planning
        ↓
120 Hz constrained leg + balance + tail evaluation
        ↓
neutral pose and secondary-motion layers
        ↓
60 Hz quaternion/translation sampling
        ↓
in-place and root-motion glTF clips
        ↓
numeric validation + fixed-camera perceptual review
```

## 1. Semantic mapping is the stable interface

The family solver uses roles such as `thigh_l`, `shin_l`, `ankle_l`, `spine_04`, and `tail_08`; it never assumes source names such as `Bone_011`. The model may have 30, 50, 75, or more joints.

The map identifies roles. The actual GLB hierarchy remains the authority for:

- parent/child order;
- rest transforms;
- segment lengths;
- local axis orientation;
- skin joint order;
- inverse-bind matrices.

## 2. Derive anatomical bend direction from the source rig

At load time, V3 measures the signed turn at the rest knee and ankle in the creature's sagittal plane. That sign becomes an invariant.

For every 120 Hz sample:

```text
expected_sign × signed_joint_angle > 0
```

The solver also clamps flexion magnitudes:

```text
knee_min_flex ≤ knee_flex ≤ knee_max_flex
ankle_min_flex ≤ ankle_flex ≤ ankle_max_flex
```

This removes the alternate inverse-kinematics branch that caused a brief backward knee/ankle fold when a swing leg moved from behind the body to the next contact.

## 3. Constrained leg solve

The sagittal solve has three variables:

```text
hip sagittal angle
knee flexion magnitude
ankle flexion magnitude
```

It uses a damped Jacobian iteration with:

- hard joint bounds;
- a reference-pose preference;
- a previous-sample continuity preference;
- bounded angular steps;
- Cartesian-error backtracking;
- a fixed hinge sign for knee and ankle.

Lateral placement is handled separately by bounded hip abduction. Separating lateral correction from the sagittal hinge prevents a 3D target from making the leg choose the wrong flexion branch.

The original hierarchy is driven directly:

```text
thigh → shin → ankle → foot → three toe chains
```

No proxy skeleton replaces the source rig.

## 4. Foot and contact planning

Each foot plan contains:

- gait phase;
- stance or swing state;
- load fraction;
- persistent contact position;
- target position;
- foot pitch;
- toe angle;
- contact, loading, midstance, extension, toe-off, swing, and pre-contact timing.

Forward swing uses minimum-jerk interpolation:

```text
s(t) = 10t³ − 15t⁴ + 6t⁵
```

Swing lift uses a C2 bump:

```text
h(t) = 64t³(1−t)³
```

Both have zero velocity and acceleration at their boundaries. More exported frames then preserve smooth motion rather than merely oversampling discontinuities.

## 5. Relaxed large-theropod posture

The V3 Tarbosaurus profile is informed by the supplied side-view reference:

- approximately two seconds per steady gait cycle;
- long stance duty factor;
- torso carried more level than the V2 forward-running silhouette;
- skull held near the horizon;
- modest pelvis compression and roll;
- small residual head motion rather than perfect stabilization.

Posture is distributed across pelvis, six torso joints, five neck joints, and head. Do not rotate only the root or chest; that produces a rigid plank or breaks the silhouette.

## 6. Support-aware body balance

Smooth foot load values define the weighted support point. It drives:

- lateral pelvis translation toward the loaded foot;
- pelvis roll;
- post-contact loading drop;
- passing-position rise;
- fore-aft sway;
- pelvis yaw/pitch;
- distributed torso counteraction;
- neck/head stabilization with retained mass.

The profile intentionally uses partial compensation. Perfect cancellation looks mechanical; no cancellation makes the animal collapse visually over each step.

## 7. Softer tail without making it weightless

The nine-joint tail is a periodically settled spring-damper chain.

V3 uses:

- high proximal stiffness for a muscular root;
- lower distal stiffness;
- moderate damping;
- parent coupling;
- explicit per-bone response lag;
- increasing dynamic allowance toward the tip;
- a small distributed neutral sag.

Tail input comes from support error, pelvis yaw, pelvis velocity, pelvis pitch, and loading—not a decorative sine wave. The final sample is forced to the first only after the periodic simulation itself has settled.

## 8. Bind pose versus neutral animation pose

The uploaded Tarbosaurus uses an open mandible bind pose. V3 keeps bind matrices untouched, then applies a locomotion-neutral closure through the real hierarchy:

```text
Bone_074 → Bone_073 → Bone_072 → Bone_071 → Bone_070
```

A sub-degree breathing gape prevents a frozen mouth. Bite, roar, eat, pant, and threat layers can override the neutral jaw later.

## 9. Sampling and GLB output

V3 evaluates at 120 Hz and exports at 60 Hz. The default Tarbosaurus walk is a two-cycle four-second superloop so slow breathing, tail dynamics, and small asymmetry can vary across one step while the complete clip closes exactly.

The output remains ordinary glTF animation:

- quaternion rotation tracks;
- root translation track;
- monotonic sample times;
- no Python or Blender runtime dependency.

## 10. Approval sequence

Tune in this order:

1. anatomical limits and signed hinge direction;
2. cadence, stride, stance fraction, and contact lead;
3. foot path and clearance;
4. pelvis support shift and vertical loading;
5. torso, neck, and head posture;
6. tail stiffness, damping, lag, and sag;
7. mouth neutral pose and secondary motion;
8. terrain, turning, acceleration, braking, and actions.

Changing all layers together makes defects impossible to localize.
