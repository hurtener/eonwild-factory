# V8 Design-Lab Feeding Expression

## Behavioral target

The supplied reference shows a late mouth opening near the food, a clamped hold, a resisted pull, and a recovery toward another feeding decision. V8 turns that evidence into a side-readable whole-body feeding loop.

The animal does not eat by rotating only its neck. Its pelvis, legs, torso, neck, skull, jaw, arms, and tail maintain a connected support story.

## Base feeding posture

- pelvis slightly back and down;
- knees and ankles loaded without reverse bending;
- torso lowered in distributed segments;
- neck forms a long descending curve;
- head aligns to the target;
- tail offsets the forward mass;
- jaw stays mostly closed while acquiring the target.

## Event pattern

The 10.8-second loop contains three intentionally unequal events:

| Event | Phase | Pull direction | Relative strength |
|---|---:|---:|---:|
| Bite A | 0.165 | left | 1.00 |
| Bite B | 0.485 | right | 0.78 |
| Bite C | 0.785 | left | 1.08 |

This prevents a mechanical bite-every-N-frames rhythm.

## One feeding event

```text
small target search
→ jaw/neck retract
→ late gape
→ short target thrust
→ snap and clamp
→ brace through feet and pelvis
→ diagonal head/neck pull
→ chest resistance and tail counter-shape
→ chew
→ swallow lift
→ pause / reacquire
```

### Jaw timing

The mouth opens only shortly before contact. At contact, additive gape approaches zero. The pull occurs while the jaw is clamped. Small jaw oscillation is reserved for chewing after the hold.

### Side pull

Each pull coordinates:

- skull yaw and roll;
- distributed neck yaw;
- small chest yaw;
- pelvis shift opposite the head pull;
- complementary foot loading;
- tail counter-yaw;
- arm tension.

### Swallow

The swallow is a small head/neck rise after chewing, not a second bite. It creates a readable pause and keeps the loop from looking like continuous jaw chatter.

## Exact loop boundary

The full irregular sequence closes exactly only after all three events. Individual events are not forced to mirror one another. Breathing, low target search, pelvis offset, jaw, neck, and tail all match at the loop endpoint.

## Future runtime extensions

The V8 controller is target-agnostic. V9+ can bind it to:

- carcass surface point and normal;
- food resistance;
- tear direction from prey geometry;
- removable tissue state;
- blood/saliva effects;
- bite success/failure;
- head collision avoidance;
- interruption by threat or damage.
