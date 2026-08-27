# Actions and Transitions

## Action design

Every action is a whole-body event. Jaw motion alone is never considered a bite or roar.

### Idle

Breathing, slow support shifts, small pelvis roll/yaw, head scan, distal tail life and asymmetric foot loading.

### Alert idle and alert walk

Raised chest/neck/head, wider and slower scanning, increased arm tone, slightly higher cadence, shorter stride and greater tail readiness.

### Eating

Pelvis shifts back and down, knees retain anatomical support, torso and neck lower in distributed arcs, head searches laterally, jaw alternates bite and chew rhythms, and the tail counterbalances the lowered front mass.

### Bite attack

Anticipation/crouch -> jaw opening and neck retraction -> root/body commitment -> rapid neck/head delivery and jaw snap -> recoil -> recovery. The root lunge is bounded by hip height and returns through an explicit transition.

### Roar

Inhale and brace -> chest expansion -> neck/head raise -> jaw opening -> sustained display with small head motion -> jaw close -> postural recovery.

## Transition classes

1. **Pose transitions** use minimum-jerk quaternion and translation blends with exact endpoints.
2. **Phase-matched loop transitions** advance two locomotion loops at matching normalized phase while changing style.
3. **Urgent action bridges** connect walk directly to bite/roar/eat and back.
4. **Natural routing** may use braking -> idle -> action when gameplay permits more preparation.

## Runtime priority

```text
bite > roar > eat > alert > locomotion > idle
```

One-shots remember the prior locomotion state. Eating loops until cancelled. An urgent bite cannot be interrupted by a lower-priority eating request.
