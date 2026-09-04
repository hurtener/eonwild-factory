# V7 Architecture — Contact-Locked Locomotion and Mass-Led Turning

## Why V7 exists

V6 demonstrated that a numerically plausible balance layer can still destroy locomotion when its transforms are exported outside the contact solution. V7 removes that class of failure by making transform ownership explicit.

## Pose ownership

| Layer | May translate root? | May translate pelvis? | May alter planted legs after solve? |
|---|---:|---:|---:|
| Path planner | Yes | No | No |
| Body/support planner | No | Yes | No |
| Terrain/contact solver | No | Reads final pelvis | Yes, owns legs/feet/toes |
| Upper-body expression | No | No | No |
| Tail dynamics | No | No | No |
| Jaw/arms/secondary motion | No | No | No |
| Exporter | No new motion | Emits exact solved value | Emits exact solved value |

This table is a hard architectural contract.

## Modules

```text
profile.py
    typed species and quality parameters

locomotion.py
    reference cadence, path/contact planning, body plan,
    leg IK, terrain/sole correction, turn anticipation,
    tail counter-shape, diagnostics

actions.py
    idle, alert, eating, mirrored power bites, roar

transitions.py
    RotationSpline + Hermite endpoint/velocity matched bridges,
    including root and pelvis translations

generator.py
    clip catalog, events, manifest, report, GLB writer

browser_demo/v7-viewer.js
    offline WebGL2 player, 12-influence GPU skinning,
    exact authored handoffs, root-loop accumulation
```

## Locomotion solve order

For internal sample `i`:

1. Sample path position, heading, speed, and acceleration.
2. Sample terrain at root and planned contacts.
3. Resolve left/right contact and swing targets.
4. Calculate support load and small pelvis compensation.
5. Construct root and pelvis transforms.
6. Generate spine, neck, head, jaw, tail, and arm baseline.
7. Solve left leg toward its final world-space target.
8. Skin selected left sole vertices and correct vertically.
9. Solve right leg and correct its sole.
10. Add turn-only upper-body lead and tail counter-shape.
11. Record local rotations plus exact root/pelvis translations.
12. Compute anatomical, contact, and smoothness diagnostics.

The turn-only upper-body additions are on branches that cannot invalidate the feet.

## Turning

The root follows an eased arc. Curvature ramps in and out with minimum-jerk envelopes. Turn direction is expressed across different systems at different times:

- head: strongest, earliest relative lead
- neck: distributed intermediate lead
- chest: smaller lead
- pelvis: late commitment, modest extra yaw
- feet: asymmetric inside/outside contact and swing geometry
- tail: opposite counter-shape with proximal stiffness and distal lag

Turn clips are non-looping and designed to hand off back to straight locomotion or into a future continuous steering controller.

## Browser runtime

The V7 player supports two transition classes:

1. **Direct manual selection** — one minimum-jerk snapshot blend with quaternion slerp and root continuity.
2. **Authored sequence** — contact-safe wait, authored transition, exact endpoint handoff, no second blend.

For looping root-motion clips, animation time is sampled modulo duration but root displacement is accumulated by completed cycle count. This prevents the browser from snapping the creature to the start of the root track at every loop.

## Scaling to other heavy bipeds

Reusable:

- path/contact planner
- signed leg constraints
- vertex sole selection
- terrain correction
- transform ownership
- transition and browser contracts

Species-specific:

- rest/neutral posture
- cadence and stride
- support shift
- joint ranges
- head/neck turn lead
- tail compliance
- attack grammar
- feeding height and descent
