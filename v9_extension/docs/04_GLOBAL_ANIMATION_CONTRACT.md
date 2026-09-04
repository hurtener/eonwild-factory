# Global Tarbosaurus animation contract

Status: **release-blocking specification**. These rules apply to every Tarbosaurus animation and to every derived runtime variant.

## 1. Anatomical identity

The animal must read as a heavy, horizontally balanced predatory biped. The pelvis is the central locomotor mass; the head and neck are visibly significant; the tail is a muscular counterbalance; the hindlimbs produce and absorb locomotor force; the forelimbs stay flexed and close to the body.

Motion propagates through chains:

```text
pelvis → spine → thorax → neck base → middle neck → upper neck → skull
pelvis → tail base → tail middle → tail distal
pelvis/support → thigh → lower leg → ankle/metatarsal → foot/toes
```

Do not animate bones as unrelated decorative oscillators.

## 2. Weight and action grammar

Every substantial action contains:

```text
anticipation
→ support/weight shift
→ force production
→ movement or contact
→ momentum continuation
→ force absorption
→ recovery
```

For each animation, the spec must identify:

- where the initial load is carried;
- which contact is retained or released;
- what body region leads force production;
- when commitment begins;
- what external contact is expected;
- how momentum continues after contact;
- which structures absorb or redirect it;
- when the state is safely interruptible again.

A direct pose blend is not a substitute for these mechanics.

## 3. Coordinate and root-motion contract

- Declare coordinate system, units, forward/up/lateral axes, root node, pelvis node, and ground convention.
- Root motion represents actual world displacement and heading.
- Root velocity must correspond to stride/contact geometry.
- An in-place clip is a derived view of the same world plan, not a separately authored solve.
- Transitions preserve root position, velocity, orientation, and support state unless a declared physical event changes them.
- During airborne motion, the ballistic trajectory belongs to whole-body COM; the root is reconstructed from COM and pose.

## 4. Foot and toe contact contract

Use contact states:

```text
APPROACHING
CONTACT
LOADING
LOADED
UNLOADING
TOE_OFF
AIRBORNE
```

When a foot is loaded:

- its resolved contact patch remains planted in world space;
- loaded yaw is bounded by substrate and anatomy;
- ankle/metatarsal and knee flexion respond to load;
- pelvis position and orientation respond to that support;
- the opposite limb moves relative to the planted support;
- toes may deform or redistribute pressure but may not visibly skate;
- any pelvis/body correction counter-solves the loaded chain.

Required locomotion events:

```text
L_FOOT_CONTACT
L_FOOT_LOAD
L_FOOT_FULL_LOAD
L_FOOT_UNLOAD
L_TOE_OFF
R_FOOT_CONTACT
R_FOOT_LOAD
R_FOOT_FULL_LOAD
R_FOOT_UNLOAD
R_TOE_OFF
```

Events must correlate with measured witness geometry, not only authored frame labels.

## 5. Pelvis and support

The pelvis is not a static root decoration. It may translate and rotate to:

- move over the active support;
- accept vertical load;
- prepare unloading;
- generate propulsion;
- brake or absorb landing;
- support head lowering;
- recover from asymmetry or failure.

Pelvis motion must remain causally related to contacts, intended movement, terrain, or external interaction. Arbitrary sway is rejected.

## 6. Spine and thorax

The torso is neither rigid nor snake-like. It distributes small counter-rotation, force transmission, breathing, and inertial response across the spine. Large movement should not occur in one isolated chest joint.

Thorax authority is lower than pelvis/primary-limb authority and higher than presentation overlays. It may stabilize the head and balance the body, but it may not hide impossible contacts.

## 7. Head and neck

The head is not a camera gimbal.

- Small attention can begin with eyes/skull and propagate into the upper neck.
- Larger orientation uses the full cervical chain and eventually thorax/pelvis or a foot adjustment.
- Bite delivery propagates from support and torso through the cervical chain.
- Head stabilization may reduce—but not erase—body acceleration.
- Targeting authority is phase-limited, especially after commitment.
- Downward interactions distribute lowering across pelvis, thorax, neck base, middle neck, and skull.

Required jaw/head events where applicable:

```text
HEAD_TARGET_WINDOW
TARGET_LOCK
JAW_OPEN
JAW_MAX_GAPE
JAW_CONTACT
JAW_CLOSE
```

## 8. Tail

The tail:

- follows pelvis rotation with phase lag;
- opposes rapid turning or pitching where appropriate;
- changes posture during acceleration, braking, landing, or head lowering;
- has a stiff muscular proximal region and more compliant distal response;
- carries state and angular velocity across transitions;
- damps rather than oscillates indefinitely;
- does not wag continuously;
- does not create net angular momentum in flight.

Larger tail excursions are reserved for real events such as stumble, fall, hard turn, collision, or failed recovery.

## 9. Forelimbs

Default forelimb behavior:

- flexed and close to the torso;
- low amplitude;
- subtle shoulder response to thorax motion;
- minor independent inertia and asymmetry;
- never synchronized like human running arms;
- never used as hidden balance poles unless a specific contact event is authored and anatomically justified.

## 10. Jaw, throat, and mouth

- Neutral mouth pose comes from fixture-specific mesh-witness calibration.
- Locomotion and idle use only breathing/exertion-scale opening.
- Jaw begins opening before the skull reaches a bite target.
- Maximum gape occurs before contact.
- Closure and contact timing are explicit.
- A miss preserves the committed skull/neck trajectory and produces overextension/recovery.
- Calls are generated through inhalation, throat/chest resonance, jaw staging, and release—not a detached open-mouth pose.

## 11. Breathing and exertion

No clip completely freezes chest, throat, abdomen, or neck base unless a deliberate brief processing/freeze phase calls for it.

Breathing is layered through:

- ribcage expansion;
- abdomen/flank response;
- throat and cervical-base response;
- slight jaw or nostril behavior where appropriate;
- exertion-conditioned rate and amplitude.

Breathing must not create uniform torso bob, foot-pressure discontinuity, or visible loop pumping.

## 12. Loop contract

A loop is safe only when the seam matches:

```text
pose
translation
orientation
linear velocity
angular velocity
approximate acceleration
contact states
event cursor
breathing state
tail state
overlay state
```

The final frame should lead naturally into the first. Exact pose equality with derivative discontinuity is insufficient.

## 13. Transition and interruption contract

Events have three types:

- **Point:** one occurrence, such as `JAW_CLOSE`.
- **Window:** active range, such as `NON_INTERRUPTIBLE` or `HEAD_TARGET_WINDOW`.
- **Condition:** runtime result, such as `CONTACT_MISSED`, `TEAR_RELEASE`, or `SUPPORT_FAILED`.

Global action events:

```text
ANTICIPATION_START
COMMIT_START
CONTACT_BEGIN
CONTACT_PEAK
CONTACT_END
RECOVERY_START
RECOVERY_END
LOOP_SAFE
INTERRUPTIBLE
PARTIALLY_INTERRUPTIBLE
NON_INTERRUPTIBLE
```

A non-interruptible action cannot be cancelled by an arbitrary animation request. Emergency interruption requires an explicit collision, stumble, fall, death, or other failure transition.

## 14. Ordered procedural authority

Final pose is not an unrestricted additive sum. Apply layers in order:

```text
1. MotionProgram performance and phase
2. support/centroidal/contact plan
3. root, pelvis, and primary limbs
4. foot/toe/terrain contacts
5. spine, neck, and tail inertial compensation
6. target/water/carcass/jaw contacts
7. injury, fatigue, and exertion within remaining capacity
8. gaze, breathing, throat, and biological variation
9. final joint-limit, collision, contact, and continuity projection
```

Each layer declares bone mask, positional/angular authority, COM authority, contact authority, phase restrictions, and suppression rules.

## 15. Growth and condition

Every animation must describe juvenile, subadult, adult, and heavy-adult behavior. Growth is not playback speed alone. It changes cadence, stride, inertia, support transfer, turning, launch/braking horizon, tail frequency, recovery, and capability.

Temporary fatigue, injury, hunger, or pain modifies capacity and expression inside the structural tier. It does not make an adult switch to a juvenile animation family.

## 16. Scientific and presentation boundary

- Animation engineering values are not automatically biological measurements.
- Uncertain resting postures, calls, and attack performances are labeled as gameplay reconstruction.
- No generic Hollywood roar is presented as recovered historical sound.
- Physics is used to enforce coherence, not to claim exact prehistoric behavior.

## 17. Universal rejection criteria

Reject any clip with:

- visible loaded-foot skate or arbitrary foot rotation;
- root displacement inconsistent with stride;
- instantaneous acceleration, stop, or heading change;
- rigid-body legs with no compression;
- head-only major action;
- constant tail waving or undamped oscillation;
- human-like forelimb pumping;
- permanent open mouth;
- loop reset;
- transition pop in pose, root, velocity, contact, or tail state;
- action cancellation inside a non-interruptible window;
- body motion that contradicts support or target geometry;
- numeric PASS that remains visibly poor in fixed-camera review.
