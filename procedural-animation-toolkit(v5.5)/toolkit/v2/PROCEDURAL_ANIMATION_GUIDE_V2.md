# Eonwild Procedural Animation Guide — V2

## Goal

Create reusable, expressive animal animation from fully rigged GLB assets while preserving every useful deformation joint. Family controllers provide shared mechanics; creature profiles provide size, timing, posture, and species character.

The target is not “more sine waves.” The target is movement in which each visible response has a cause:

```text
planned contact
  → supporting leg accepts load
  → pelvis moves over support
  → torso counteracts pelvis
  → neck/head retain controlled residual motion
  → tail reacts to body momentum
  → feet roll and toes release the ground
```

## V2 architecture

```text
GLB + semantic YAML map
        ↓
rig validation and anatomical basis
        ↓
family profile resolved to actual hip height
        ↓
contact schedule and foot target planner
        ↓
120 Hz support/balance/tail evaluation
        ↓
per-frame full-rig pose composition
        ↓
leg IK + foot orientation + toe-ground correction
        ↓
60 Hz dense quaternion sampling
        ↓
in-place GLB + root-motion GLB clips
        ↓
metrics + side/front/three-quarter perceptual review
```

## 1. Keep bind pose and neutral pose separate

A bind pose exists to skin the mesh. It is not automatically the creature’s living neutral posture.

For the test Tarbosaurus, the mandible is open in the bind pose so teeth and tongue can be modeled. V2 applies a locomotion-neutral jaw closure before adding any action layer. Roar, bite, eat, pant, and threat states then override or add to that neutral controller.

The jaw chain is discovered from hierarchy:

```text
Bone_074 → Bone_073 → Bone_072 → Bone_071 → Bone_070
```

This prevents semantic numbering mistakes from breaking the actual chain.

## 2. Plan feet before rotating legs

For each foot, v2 calculates:

- current gait phase;
- stance or swing state;
- load fraction;
- current and next contact positions;
- C2-continuous swing interpolation;
- swing height and slight lateral arc;
- contact, flat-foot, toe-off, and pre-contact orientation;
- distributed toe articulation.

The swing position uses minimum-jerk interpolation:

```text
s(t) = 10t³ − 15t⁴ + 6t⁵
```

The lift uses a bump with zero value, velocity, and acceleration at both boundaries:

```text
h(t) = 64t³(1−t)³
```

That removes the snap created by binary phase gates.

## 3. Solve the original leg hierarchy

V2 does not create a replacement 18-bone skeleton. It uses the mapped source chain:

```text
thigh → shin → ankle → foot → three articulated toe chains
```

A short FABRIK solve creates target joint positions while preserving segment lengths. The result is converted back into rotations on the original deformation bones. Foot world orientation is stabilized separately, so leg IK cannot accidentally rotate the entire foot into the ground.

## 4. Balance from support, not decoration

Each stance leg has a smooth load value. The weighted support position drives:

- lateral pelvis translation;
- pelvis roll toward support;
- loading compression after contact;
- passing-position rise;
- fore-aft pelvis sway;
- pelvis yaw from alternating strides.

The pelvis begins moving toward the future support before the other foot fully unloads. This anticipation is essential to avoid a late, reactive sway.

## 5. Distribute torso compensation

Spine, chest, neck, and head are not rigid counter-rotators. V2 distributes motion with increasing distal weights and intentionally leaves residual movement.

The result should feel controlled but massive:

- pelvis generates force;
- torso reduces excessive rotation;
- neck absorbs some remaining movement;
- head stabilizes incompletely;
- breathing runs over a slower two-cycle superloop.

## 6. Make the tail dynamic

The v1 tail was a phase wave. V2 calculates a periodic spring-damper response from:

- support-side error;
- pelvis yaw;
- pelvis yaw velocity;
- pelvis pitch and vertical loading.

Proximal segments are stiffer and faster. Distal segments are softer and more delayed. The simulation is warmed through repeated supercycles and only the settled periodic result is baked.

## 7. Use a superloop

A one-cycle loop forces every secondary motion to repeat once per stride. V2 uses two gait cycles so breathing, slight asymmetry, jaw micro-motion, and head drift can vary while the complete clip still closes.

## 8. Sample densely, validate intelligently

V2 evaluates at 120 Hz and exports at 60 Hz. Dense sampling does not replace good mechanics, but it preserves the solved motion reliably across glTF players.

Validation distinguishes:

- horizontal contact lock;
- intentional vertical foot-root rise during toe-off;
- toe-tip ground proxy error;
- loop rotation closure;
- tail periodic closure;
- root-motion distance;
- mapping and skin preservation.

## 9. Extend by layers, not copied clips

New actions should reuse the same stack:

```text
neutral pose
+ locomotion/contact layer
+ balance layer
+ attention layer
+ jaw/action layer
+ secondary/inertial layer
```

A bite attack can temporarily replace head/jaw targets while the legs continue supporting the body. Alert locomotion can change neck/head attention without rebuilding the gait. Eating can constrain the head toward a feeding target while feet and pelvis keep balance.

## Definition of done

A production candidate is not approved merely because the GLB exports. It must pass metrics and a fixed camera review:

- side view for foot arcs and stride;
- front view for support transfer and knee tracking;
- three-quarter view for total silhouette, tail, jaw, and torso mass;
- runtime test with translation speed matched to gait speed;
- terrain test after runtime foot targets are connected to raycasts.
