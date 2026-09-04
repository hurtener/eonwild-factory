# Runtime metadata and animation specification format

## 1. Why metadata is part of the animation

A GLB clip containing only sampled bones cannot reliably support Eonwild’s combat, sound, AI, IK, condition, transitions, and networking. Every clip therefore ships with a machine-readable AnimationSpec and resolved runtime metadata.

## 2. Artifact distinction

- **MotionIntent:** a gameplay/AI request for movement or interaction.
- **MotionProgram:** reusable semantic algorithm and phase graph.
- **AnimationSpec:** one named Tarbosaurus performance contract.
- **BiomechanicalPlan:** one solved execution for a body, state, target, and environment.
- **Baked clip:** sampled skeletal representation of that plan.
- **Runtime metadata:** phases, contacts, events, windows, root/COM facts, and procedural authority.

Do not make the baked clip the only source of truth, and do not let the generic program erase the intended performance.

## 3. Required AnimationSpec fields

```yaml
schema: eonwild.animation_spec.v1
id: tarbosaurus_committed_power_bite
family: heavy_predatory_biped
program: bite_action
category: combat
priority: P0

duration:
  min_s: 1.6
  target_s: 2.1
  max_s: 2.6

loop: false
root_motion: true

entry:
  states: [idle, alert_idle, walk, fast_walk]
  maximum_speed: configured_low
  requirements:
    - target geometry is valid
    - a support/drive leg can be selected

exit:
  states: [combat_ready, bite_miss_recovery, feeding_entry, stumble]

phases:
  - id: anticipation
    range: [0.10, 0.28]
    support: ...
    centroidal_intent: ...
    body_chain: ...
    interruptibility: true

  - id: commitment
    range: [0.28, 0.62]
    interruptibility: false

events:
  - name: ANTICIPATION_START
    kind: point
    at: 0.10
  - name: NON_INTERRUPTIBLE
    kind: window
    range: [0.28, 0.78]
  - name: CONTACT_MISSED
    kind: condition

procedural_channels: ...
growth_response: ...
validation: ...
provenance: ...
```

The schemas in `schemas/` are the starting implementation contract.

## 4. Event semantics

### Point events

Point events occur exactly once per traversal and carry normalized phase plus resolved time. Examples:

```text
L_FOOT_CONTACT
R_TOE_OFF
ANTICIPATION_START
COMMIT_START
CONTACT_PEAK
JAW_OPEN
JAW_CLOSE
VOCAL_START
SNOUT_WATER_ENTER
```

### Window events

Windows remain active across a range:

```text
HEAD_TARGET_WINDOW
CONTACT_WINDOW
INTERRUPTIBLE
PARTIALLY_INTERRUPTIBLE
NON_INTERRUPTIBLE
LOOP_SAFE_WINDOW
```

### Condition events

Conditions are raised by runtime or interaction simulation:

```text
CONTACT_MISSED
TARGET_YIELDED
TARGET_RESISTED
TEAR_RELEASE
SUPPORT_FAILED
LANDING_FAILED
```

Do not bake `TEAR_RELEASE` to a fixed frame when the carcass/interaction system owns resistance.

## 5. Contact metadata

Per foot, expose:

```yaml
foot: left
state: loaded
patch_id: tarbo_left_primary_sole_v1
support_weight_fraction: 0.63
world_patch_transform: ...
friction_assumption: dry_compacted_ground
next_state: unloading
next_transition_time_s: ...
```

Runtime does not need full offline force optimization, but it needs enough state to preserve phase, select transitions, dispatch audio, and apply bounded terrain IK.

## 6. Root and velocity metadata

For root-motion clips include sampled or reconstructable:

- root position/orientation;
- linear and angular velocity;
- traveled distance and heading change;
- gait/support phase;
- start/end state packets;
- compatibility tags for transition search.

For V9 include whole-body COM and momentum facts in the plan/report. Runtime may use a reduced subset.

## 7. Procedural-channel authority

Each channel declares:

```yaml
gaze:
  enabled: true
  bone_mask: [neck_03, neck_04, neck_05, head]
  max_yaw_deg: 12
  max_pitch_deg: 8
  phase_windows: [vigilance]
  contact_authority: none
  com_authority: negligible

foot_ik:
  enabled: true
  contact_authority: preserving
  maximum_translation_m: configured
  maximum_rotation_deg: configured
```

If two channels compete, the authority ordering in the global contract decides.

## 8. Transition state packet

Every clip endpoint and authored bridge exposes:

```text
pose
root transform
root linear/angular velocity
whole-body COM/momentum when available
left/right contact state and patch
pelvis/support bias
tail angle/angular velocity state
breathing phase
target lock and commitment
interruptibility state
event cursor
```

A transition is compatible only when the bridge can connect these states inside tolerances. Endpoint pose equality alone does not guarantee a valid transition.

## 9. Runtime selection query

```ts
selectMotion({
  intent: "power_attack",
  structuralTier: "adult",
  ageFraction: 0.72,
  currentSpeed: 1.28,
  supportFoot: "left",
  gaitPhase: 0.43,
  targetDistance: 3.4,
  targetHeight: 1.1,
  terrainSlope: 0.03,
  substrate: "dry_compacted_ground",
  fatigue: 0.18,
  injuryState,
  continuation: "settle_to_feeding"
})
```

The result includes selected family/program/variant, phase-preserving entry, parameter scales, contact plan, events, fallback, and evidence/version IDs.

## 10. Runtime failure behavior

When a request is incompatible:

- do not teleport or crossfade through support;
- queue to the next valid contact window;
- choose a compatible left/right variant;
- select a grounded fallback;
- play a stumble/failure transition when a physical failure occurred;
- return a structured rejection reason for AI/gameplay.

## 11. Naming

Use semantic IDs for code and manifests. GLB display names may remain readable but runtime must not infer gameplay behavior solely from substrings such as `BITE`, `ROAR`, or `WALK`.
