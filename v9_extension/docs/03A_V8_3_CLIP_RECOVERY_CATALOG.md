# V8.3 recovered clip and transition catalog

Status: **migration contract**. This document maps every V5.5 base/action clip and authored bridge into the V8.3 semantic target. It does not authorize copying historical sampled curves.

## Global migration rules

- Final V8.3 compatibility scope recovers the 21 V5.5 base/action clips and 16 authored bridges semantically, not necessarily sample-for-sample.
- The relaxed walk uses V8.2 as the authoritative source and later body-balance corrections must prove contact/root equivalence.
- Root-motion and in-place outputs are derived views of one world-space plan.
- Generic roar is migrated to threat_call; long-distance contact_call is a separate later animation contract.

## Base and action clips

| # | V5.5 source | V8.3 target | Family | Priority | Migration |
|---:|---|---|---|:---:|---|
| 1 | `PROC_WALK_RELAXED_V5_5_ROOTMOTION` | `PROC_WALK_RELAXED_V8_3_ROOTMOTION` | `relaxed_walk` | P0 | V8.2 authoritative trajectory; V5.5 name is historical |
| 2 | `PROC_WALK_RELAXED_V5_5_INPLACE` | `PROC_WALK_RELAXED_V8_3_INPLACE` | `relaxed_walk` | P0 | derive in-place from same world plan |
| 3 | `PROC_WALK_UNEVEN_TERRAIN_V5_5_ROOTMOTION` | `PROC_WALK_UNEVEN_TERRAIN_V8_3_ROOTMOTION` | `terrain_fixture` | P1 | parameterized terrain adaptation fixture |
| 4 | `PROC_WALK_UNEVEN_TERRAIN_V5_5_INPLACE` | `PROC_WALK_UNEVEN_TERRAIN_V8_3_INPLACE` | `terrain_fixture` | P1 | derived view |
| 5 | `PROC_WALK_UPSLOPE_V5_5_ROOTMOTION` | `PROC_WALK_UPSLOPE_V8_3_ROOTMOTION` | `slope_fixture` | P1 | parameterized slope fixture |
| 6 | `PROC_WALK_UPSLOPE_V5_5_INPLACE` | `PROC_WALK_UPSLOPE_V8_3_INPLACE` | `slope_fixture` | P1 | derived view |
| 7 | `PROC_TURN_LEFT_35_V5_5_ROOTMOTION` | `PROC_WALK_TURN_LEFT_35_V8_3_ROOTMOTION` | `turn` | P1 | signed-curvature program preset |
| 8 | `PROC_TURN_LEFT_35_V5_5_INPLACE` | `PROC_WALK_TURN_LEFT_35_V8_3_INPLACE` | `turn` | P1 | derived view |
| 9 | `PROC_TURN_RIGHT_35_V5_5_ROOTMOTION` | `PROC_WALK_TURN_RIGHT_35_V8_3_ROOTMOTION` | `turn` | P1 | signed-curvature program preset |
| 10 | `PROC_TURN_RIGHT_35_V5_5_INPLACE` | `PROC_WALK_TURN_RIGHT_35_V8_3_INPLACE` | `turn` | P1 | derived view |
| 11 | `PROC_START_WALK_V5_5_ROOTMOTION` | `PROC_START_WALK_V8_3_ROOTMOTION` | `gait_transition` | P0 | support transfer and acceleration |
| 12 | `PROC_START_WALK_V5_5_INPLACE` | `PROC_START_WALK_V8_3_INPLACE` | `gait_transition` | P0 | derived view |
| 13 | `PROC_BRAKE_TO_IDLE_V5_5_ROOTMOTION` | `PROC_BRAKE_TO_IDLE_V8_3_ROOTMOTION` | `gait_transition` | P0 | momentum-resolving braking |
| 14 | `PROC_BRAKE_TO_IDLE_V5_5_INPLACE` | `PROC_BRAKE_TO_IDLE_V8_3_INPLACE` | `gait_transition` | P0 | derived view |
| 15 | `PROC_ALERT_WALK_V5_5_ROOTMOTION` | `PROC_ALERT_WALK_V8_3_ROOTMOTION` | `alert_gait` | P0 | V8.2 gait plus attention posture |
| 16 | `PROC_ALERT_WALK_V5_5_INPLACE` | `PROC_ALERT_WALK_V8_3_INPLACE` | `alert_gait` | P0 | derived view |
| 17 | `PROC_IDLE_BREATH_V5_5` | `PROC_NEUTRAL_IDLE_V8_3` | `state` | P0 | animation 01 specification |
| 18 | `PROC_ALERT_IDLE_V5_5` | `PROC_ALERT_IDLE_V8_3` | `state` | P0 | animation 02 specification |
| 19 | `PROC_EAT_LOOP_V5_5` | `PROC_FEED_LOOP_V8_3` | `feeding` | P0 | modular feed search/bite/process under one compatibility sequence |
| 20 | `PROC_BITE_ATTACK_V5_5` | `PROC_COMMITTED_POWER_BITE_V8_3` | `combat` | P0 | grounded committed bite, not airborne |
| 21 | `PROC_ROAR_V5_5` | `PROC_THREAT_CALL_V8_3` | `vocal` | P0 | explicit threat/territorial semantics |

## Detailed base/action expectations

### 01 — `PROC_WALK_RELAXED_V8_3_ROOTMOTION`

- **Historical source:** `PROC_WALK_RELAXED_V5_5_ROOTMOTION`
- **Family:** `relaxed_walk`
- **Priority:** P0
- **Migration rule:** V8.2 authoritative trajectory; V5.5 name is historical
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 02 — `PROC_WALK_RELAXED_V8_3_INPLACE`

- **Historical source:** `PROC_WALK_RELAXED_V5_5_INPLACE`
- **Family:** `relaxed_walk`
- **Priority:** P0
- **Migration rule:** derive in-place from same world plan
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 03 — `PROC_WALK_UNEVEN_TERRAIN_V8_3_ROOTMOTION`

- **Historical source:** `PROC_WALK_UNEVEN_TERRAIN_V5_5_ROOTMOTION`
- **Family:** `terrain_fixture`
- **Priority:** P1
- **Migration rule:** parameterized terrain adaptation fixture
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 04 — `PROC_WALK_UNEVEN_TERRAIN_V8_3_INPLACE`

- **Historical source:** `PROC_WALK_UNEVEN_TERRAIN_V5_5_INPLACE`
- **Family:** `terrain_fixture`
- **Priority:** P1
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 05 — `PROC_WALK_UPSLOPE_V8_3_ROOTMOTION`

- **Historical source:** `PROC_WALK_UPSLOPE_V5_5_ROOTMOTION`
- **Family:** `slope_fixture`
- **Priority:** P1
- **Migration rule:** parameterized slope fixture
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 06 — `PROC_WALK_UPSLOPE_V8_3_INPLACE`

- **Historical source:** `PROC_WALK_UPSLOPE_V5_5_INPLACE`
- **Family:** `slope_fixture`
- **Priority:** P1
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 07 — `PROC_WALK_TURN_LEFT_35_V8_3_ROOTMOTION`

- **Historical source:** `PROC_TURN_LEFT_35_V5_5_ROOTMOTION`
- **Family:** `turn`
- **Priority:** P1
- **Migration rule:** signed-curvature program preset
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 08 — `PROC_WALK_TURN_LEFT_35_V8_3_INPLACE`

- **Historical source:** `PROC_TURN_LEFT_35_V5_5_INPLACE`
- **Family:** `turn`
- **Priority:** P1
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 09 — `PROC_WALK_TURN_RIGHT_35_V8_3_ROOTMOTION`

- **Historical source:** `PROC_TURN_RIGHT_35_V5_5_ROOTMOTION`
- **Family:** `turn`
- **Priority:** P1
- **Migration rule:** signed-curvature program preset
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 10 — `PROC_WALK_TURN_RIGHT_35_V8_3_INPLACE`

- **Historical source:** `PROC_TURN_RIGHT_35_V5_5_INPLACE`
- **Family:** `turn`
- **Priority:** P1
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 11 — `PROC_START_WALK_V8_3_ROOTMOTION`

- **Historical source:** `PROC_START_WALK_V5_5_ROOTMOTION`
- **Family:** `gait_transition`
- **Priority:** P0
- **Migration rule:** support transfer and acceleration
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 12 — `PROC_START_WALK_V8_3_INPLACE`

- **Historical source:** `PROC_START_WALK_V5_5_INPLACE`
- **Family:** `gait_transition`
- **Priority:** P0
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 13 — `PROC_BRAKE_TO_IDLE_V8_3_ROOTMOTION`

- **Historical source:** `PROC_BRAKE_TO_IDLE_V5_5_ROOTMOTION`
- **Family:** `gait_transition`
- **Priority:** P0
- **Migration rule:** momentum-resolving braking
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 14 — `PROC_BRAKE_TO_IDLE_V8_3_INPLACE`

- **Historical source:** `PROC_BRAKE_TO_IDLE_V5_5_INPLACE`
- **Family:** `gait_transition`
- **Priority:** P0
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 15 — `PROC_ALERT_WALK_V8_3_ROOTMOTION`

- **Historical source:** `PROC_ALERT_WALK_V5_5_ROOTMOTION`
- **Family:** `alert_gait`
- **Priority:** P0
- **Migration rule:** V8.2 gait plus attention posture
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 16 — `PROC_ALERT_WALK_V8_3_INPLACE`

- **Historical source:** `PROC_ALERT_WALK_V5_5_INPLACE`
- **Family:** `alert_gait`
- **Priority:** P0
- **Migration rule:** derived view
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 17 — `PROC_NEUTRAL_IDLE_V8_3`

- **Historical source:** `PROC_IDLE_BREATH_V5_5`
- **Family:** `state`
- **Priority:** P0
- **Migration rule:** animation 01 specification
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 18 — `PROC_ALERT_IDLE_V8_3`

- **Historical source:** `PROC_ALERT_IDLE_V5_5`
- **Family:** `state`
- **Priority:** P0
- **Migration rule:** animation 02 specification
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 19 — `PROC_FEED_LOOP_V8_3`

- **Historical source:** `PROC_EAT_LOOP_V5_5`
- **Family:** `feeding`
- **Priority:** P0
- **Migration rule:** modular feed search/bite/process under one compatibility sequence
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 20 — `PROC_COMMITTED_POWER_BITE_V8_3`

- **Historical source:** `PROC_BITE_ATTACK_V5_5`
- **Family:** `combat`
- **Priority:** P0
- **Migration rule:** grounded committed bite, not airborne
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

### 21 — `PROC_THREAT_CALL_V8_3`

- **Historical source:** `PROC_ROAR_V5_5`
- **Family:** `vocal`
- **Priority:** P0
- **Migration rule:** explicit threat/territorial semantics
- **Required common evidence:** resolved source lineage, changed-channel report, root/in-place equivalence where paired, contact/event validation, fixed-camera review.

## Authored bridges

| # | V5.5 source | V8.3 target | From | To | Priority |
|---:|---|---|---|---|:---:|
| 1 | `PROC_IDLE_TO_WALK_V5_5` | `PROC_IDLE_TO_WALK_V8_3` | `idle` | `walk` | P0 |
| 2 | `PROC_WALK_TO_IDLE_V5_5` | `PROC_WALK_TO_IDLE_V8_3` | `walk` | `idle` | P0 |
| 3 | `PROC_WALK_TO_ALERT_WALK_V5_5` | `PROC_WALK_TO_ALERT_WALK_V8_3` | `walk` | `alert_walk` | P0 |
| 4 | `PROC_ALERT_WALK_TO_WALK_V5_5` | `PROC_ALERT_WALK_TO_WALK_V8_3` | `alert_walk` | `walk` | P0 |
| 5 | `PROC_IDLE_TO_ALERT_IDLE_V5_5` | `PROC_IDLE_TO_ALERT_IDLE_V8_3` | `idle` | `alert_idle` | P0 |
| 6 | `PROC_ALERT_IDLE_TO_IDLE_V5_5` | `PROC_ALERT_IDLE_TO_IDLE_V8_3` | `alert_idle` | `idle` | P0 |
| 7 | `PROC_IDLE_TO_EAT_V5_5` | `PROC_IDLE_TO_FEED_V8_3` | `idle` | `feeding` | P0 |
| 8 | `PROC_EAT_TO_IDLE_V5_5` | `PROC_FEED_TO_IDLE_V8_3` | `feeding` | `idle` | P0 |
| 9 | `PROC_IDLE_TO_ROAR_READY_V5_5` | `PROC_IDLE_TO_THREAT_READY_V8_3` | `idle` | `threat_call` | P0 |
| 10 | `PROC_ROAR_TO_IDLE_V5_5` | `PROC_THREAT_TO_IDLE_V8_3` | `threat_call` | `idle` | P0 |
| 11 | `PROC_WALK_TO_BITE_READY_V5_5` | `PROC_WALK_TO_BITE_READY_V8_3` | `walk` | `committed_bite` | P0 |
| 12 | `PROC_BITE_TO_WALK_V5_5` | `PROC_BITE_TO_WALK_V8_3` | `committed_bite` | `walk` | P0 |
| 13 | `PROC_WALK_TO_ROAR_READY_V5_5` | `PROC_WALK_TO_THREAT_READY_V8_3` | `walk` | `threat_call` | P0 |
| 14 | `PROC_ROAR_TO_WALK_V5_5` | `PROC_THREAT_TO_WALK_V8_3` | `threat_call` | `walk` | P0 |
| 15 | `PROC_WALK_TO_EAT_V5_5` | `PROC_WALK_TO_FEED_V8_3` | `walk` | `feeding` | P0 |
| 16 | `PROC_EAT_TO_WALK_V5_5` | `PROC_FEED_TO_WALK_V8_3` | `feeding` | `walk` | P0 |

## Bridge generation contract

Every bridge is regenerated against the actual V8.3 source and target endpoints. It must preserve or explicitly solve:

- source and target pose;
- root position/orientation;
- linear and angular velocity;
- left/right support and contact states;
- pelvis support bias;
- tail angle and angular velocity;
- breathing/overlay state where visible;
- commitment and interruptibility;
- event cursor so point events do not duplicate or disappear.

Normalized source phase alone is not enough. A walk-to-action bridge selects a mechanically valid support phase and may choose left/right variants. If a requested bridge cannot be made compatible inside tolerances, runtime queues, selects a fallback, or rejects the request; it does not teleport or hide the mismatch in a crossfade.
