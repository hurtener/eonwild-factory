# V8 Pronounced Head/Neck-Led Turning

## Goal

A large predatory biped should not look like a straight walk rotated around its root. Reorientation begins as attention, propagates through the neck and chest, commits through the pelvis and feet, and is opposed by the tail.

## V8 sequence

```text
eyes / skull predict path
→ neck develops curvature
→ chest follows attention
→ inside and outside steps diverge
→ pelvis commits to the arc
→ tail remains opposed
→ head settles toward new forward
→ tail releases last
```

## Authored relative targets

- skull lead: 18.5° before overshoot;
- neck lead: 12.2°;
- chest lead: 4.8°;
- pelvis lead: 1.35°;
- head overshoot: +22% during early commitment;
- neck overshoot: +11%;
- head focus pitch: 1.25°;
- distributed neck roll: 0.85°;
- distal tail counter target: 9.6°.

These values are authored local contributions. Baked world-space relative angles include the cumulative chest, neck, and head layers and are validated separately.

## Foot mechanics

- inside step travels a shorter contact arc;
- outside step travels farther;
- foot heading follows the local path tangent;
- outside swing receives more clearance;
- pelvis support shift is included before IK;
- planted contacts remain fixed in their contact frames.

## Perceptual gates

A turn fails if:

- skull lead is visually negligible;
- neck remains straight while the head rotates alone;
- chest and pelvis commit at exactly the same time as the skull;
- tail follows immediately instead of opposing;
- inside/outside steps are indistinguishable;
- foot contact or anatomical leg constraints regress.
