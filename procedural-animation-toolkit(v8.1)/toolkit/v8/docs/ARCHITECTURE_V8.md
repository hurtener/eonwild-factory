# Eonwild Procedural Animation V8 Architecture

## Purpose

V8 preserves the V7 contact-locked locomotion foundation and raises three areas to a production-directed standard:

1. reference-staged heavy-theropod power attacks;
2. expressive, grounded feeding;
3. pronounced gaze-led mass reorientation during turns.

The architecture remains bone-count agnostic. The Tarbosaurus fixture retains all 75 skin joints and the semantic adapter maps behavior roles onto the complete deformation hierarchy.

## Solve order

```text
runtime/path target
    ↓
root trajectory and terrain frame
    ↓
final pelvis translation + orientation
    ↓
left and right anatomical leg IK
    ↓
weighted sole-vertex correction
    ↓
spine / chest response
    ↓
neck curvature / head attention / jaw
    ↓
tail counter-shape and residual settling
    ↓
exact sampled tracks
    ↓
GLB + manifest + event markers + validators
```

The pelvis transform used by the legs is the transform written to the GLB. V8 forbids a later balance or presentation transform that would invalidate planted feet.

## Authoring layers

### Lower-body authority

The pelvis, thigh, shin, ankle, foot, and three toe branches per side form the contact-critical layer. Every action supplies:

- pelvis translation before IK;
- complementary support loads;
- explicit foot targets;
- foot lift windows;
- target-relative foot pitch;
- signed knee and ankle branch preferences.

### Expressive upper body

The non-contact branches are evaluated after the feet are solved:

- six torso segments distribute pitch, yaw, and roll;
- five neck segments create curvature rather than a rigid neck turn;
- the skull carries target focus, overshoot, contact response, and recovery;
- the five-joint mandible chain receives calibrated closure plus behavior-specific gape;
- nine tail joints oppose, transmit, and settle angular momentum;
- arms and hands receive bracing/inertial tension.

### Event-aware runtime contract

The manifest exposes semantic moments instead of only clip duration:

- target lock;
- hindlimb release;
- first catch step;
- bite contact;
- tear release;
- recovery start;
- feeding gape/contact/pull/swallow;
- turn attention lead / mass commit / settle;
- foot contacts;
- transition commit.

Damage, sound, particles, camera impulse, prey reactions, and AI decisions should bind to these events rather than arbitrary normalized times.

## V8 action philosophy

A detailed creature action is not a large head rotation pasted over an idle pose. It is a sequence of support decisions:

```text
attention
→ support choice
→ body preload
→ force transmission
→ contact
→ resistance
→ recoil / recovery
```

The attack and feeding controllers therefore share the same leg and sole system used by locomotion.

## Reference use

The supplied video contains camera cuts, zoom, and perspective changes. V8 separates:

- **observed evidence**: visible order, timing, support changes, gape timing, and silhouette response;
- **design inference**: gameplay-compatible root displacement, contact phase, target alignment, and loop closure.

The source is not represented as calibrated motion capture.
