# Tarbosaurus V9 animation catalog

Status: **implementation specification**, not an approved V9 animation release.

The 29 animation contracts remain semantically independent while sharing 12 reusable motion programs. Each contract defines entry/exit state, performance, support/COM/dynamics, complete phase progression, events, procedural authority, growth response, and release-blocking validation.

## Index

| # | Animation | Program | Priority | Loop | Root motion | Target duration |
|---:|---|---|---|:---:|:---:|---:|
| 1 | Neutral idle | `stationary_support` | P0 | yes | no | 8.00s |
| 2 | Alert idle | `stationary_support` | P0 | yes | no | 6.00s |
| 3 | Walk | `alternating_gait` | P0 | yes | yes | 4.44s |
| 4 | Fast walk / transitional gait | `alternating_gait` | P0 | yes | yes | 3.15s |
| 5 | Run | `alternating_gait` | P0 | yes | yes | 2.15s |
| 6 | Sprint | `alternating_gait` | P0 | yes | yes | 1.55s |
| 7 | Walk start | `gait_transition` | P0 | no | yes | 3.00s |
| 8 | Walk stop | `gait_transition` | P0 | no | yes | 3.20s |
| 9 | Run start / acceleration | `gait_transition` | P0 | no | yes | 3.80s |
| 10 | Run stop / deceleration | `gait_transition` | P0 | no | yes | 4.50s |
| 11 | Investigate / scent | `attention_reaction` | P1 | no | no | 5.50s |
| 12 | Alert / listen reaction | `attention_reaction` | P0 | no | no | 1.60s |
| 13 | Quick bite / snap | `bite_action` | P0 | no | yes | 0.90s |
| 14 | Committed power bite | `bite_action` | P0 | no | yes | 2.10s |
| 15 | Low / downward bite | `bite_action` | P1 | no | no | 2.20s |
| 16 | Bite miss / overextension recovery | `recovery_failure` | P0 | no | yes | 1.60s |
| 17 | Body shove / pressure | `body_pressure` | P1 | no | yes | 2.10s |
| 18 | Head-down feeding | `feeding_interaction` | P0 | yes | no | 8.00s |
| 19 | Tear / pull | `feeding_interaction` | P1 | no | yes | 2.80s |
| 20 | Swallow | `feeding_interaction` | P1 | no | no | 1.60s |
| 21 | Drink | `feeding_interaction` | P1 | no | no | 8.50s |
| 22 | Lie down | `ground_posture` | P1 | no | yes | 6.80s |
| 23 | Rest / lying loop | `ground_posture` | P1 | yes | no | 10.00s |
| 24 | Rise to standing | `ground_posture` | P1 | no | yes | 5.80s |
| 25 | Wounded idle | `stationary_support` | P0 | yes | no | 7.00s |
| 26 | Stumble | `recovery_failure` | P0 | no | yes | 2.10s |
| 27 | Threat / territorial call | `vocal_display` | P1 | no | no | 5.20s |
| 28 | Long-distance / contact call | `vocal_display` | P1 | no | no | 6.80s |
| 29 | Collapse / death | `terminal_fall` | P0 | no | yes | 6.20s |

## Detailed contracts

## 01 — Neutral idle

**ID:** `tarbosaurus_neutral_idle`  
**Program:** `stationary_support`  
**Category / priority:** `state` / `P0`  
**Duration envelope:** 6.0–10.0 s; target 8.0 s  
**Loop / root motion:** True / False

**Purpose.** Default relaxed standing state that remains alive, balanced, asymmetrical, and interruptible without constant decorative movement.

**Performance character.** Relaxed confidence: a heavy animal quietly supporting itself, breathing, sampling its surroundings, and making slow load corrections.

### Entry and exit

```yaml
entry:
  allowed:
  - spawn_settled
  - walk_stop
  - feeding_exit
  - drink_exit
  - rise_complete
  requirements:
  - both feet reachable and planted
  - COM velocity near zero
exit:
  allowed:
  - alert_idle
  - walk_start
  - investigate_scent
  - listen_reaction
  - lie_down
  - threat_call
  handoff: preserve support bias, breathing phase, gaze, and tail state
```

### Phase progression

#### `settled_support` — 0.00–0.18
**Goal:** Establish an asymmetric but stable bilateral stance.  
**Support:** Both foot/toe patches contact; left nominally 60–68% load, right 32–40%.  
**COM:** Projected COM remains inside bilateral support with positive margin and a mild shift toward the principal leg.  
**Dynamics:** Quasi-static; ankle/metatarsal compression and pelvis placement carry the load.  
**Interruptibility:** `true`

- **Pelvis:** Shift a small fraction toward the principal support; knees remain flexed and pelvis stays below a locked-leg posture.
- **Hindlimbs:** Principal leg bears more vertical load; secondary leg remains grounded and available.
- **Feet Toes:** All support witnesses stay planted; toes spread/load without visible skate.
- **Thorax Spine:** Horizontal trunk with small counter-roll, not rigid.
- **Neck Head:** Comfortable S-curve; skull close to neutral.
- **Tail:** Base follows pelvis; distal chain settles opposite the support shift with damping.
- **Forelimbs:** Flexed, close, slightly asymmetric.
- **Jaw Throat:** Mouth closed or minimally parted at calibrated living-neutral.

#### `inspiration` — 0.18–0.36
**Goal:** Complete a subtle respiratory expansion without turning it into locomotor bob.  
**Support:** Same contacts and load bias.  
**COM:** COM height changes only within breathing tolerance; support margin stays positive.  
**Dynamics:** Thorax, abdomen, throat, and cervical base expand with phase offsets.  
**Interruptibility:** `true`

- **Pelvis:** Nearly unchanged; tiny vertical compliance only.
- **Hindlimbs:** Maintain load with micro ankle response.
- **Feet Toes:** No movement beyond tissue/load deformation.
- **Thorax Spine:** Ribcage volume expands; no uniform rigid-body lift.
- **Neck Head:** Cervical base rises imperceptibly after thorax expansion.
- **Tail:** No intentional wag; only minute base reaction.
- **Forelimbs:** Shoulders follow thorax expansion with sub-degree response.
- **Jaw Throat:** Subtle throat expansion and nasal airflow cue.

#### `micro_attention` — 0.36–0.52
**Goal:** Make one low-amplitude non-periodic attention adjustment.  
**Support:** Contacts unchanged.  
**COM:** COM remains essentially fixed; no need for a corrective step.  
**Dynamics:** Skull leads a few degrees; upper and middle neck absorb and then settle.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** No load transfer beyond micro-correction.
- **Thorax Spine:** Thorax may yaw less than the skull and only if gaze excursion approaches the attention limit.
- **Neck Head:** Small target sampling with no rhythmic head bob.
- **Tail:** Tiny counter-torque only if thorax participates.
- **Forelimbs:** No synchronized motion.
- **Jaw Throat:** Neutral.

#### `weight_redistribution` — 0.52–0.82
**Goal:** Transfer principal support gradually to the opposite side without moving either foot.  
**Support:** Bilateral support; load evolves approximately 65/35 → 50/50 → 40/60.  
**COM:** COM crosses the inter-foot region smoothly and remains inside support.  
**Dynamics:** Pelvis lateral translation leads; ankle load and chest/tail counter-response follow with delay.  
**Interruptibility:** `true`

- **Pelvis:** Translate and roll gradually toward the new support side; no sudden height change.
- **Hindlimbs:** Old support unloads while the new support knee/ankle accepts load.
- **Feet Toes:** Loaded patch pressure migrates but witness positions remain fixed.
- **Thorax Spine:** Small counter-roll limits skull disturbance.
- **Neck Head:** Head remains calm and does not mirror pelvis sway.
- **Tail:** Base follows pelvis; mid/distal tail make a tiny delayed opposite correction.
- **Forelimbs:** Subtle shoulder inertia only.

#### `exhale_and_loop` — 0.82–1.00
**Goal:** Settle breathing, gaze, load, and derivatives into a loop-safe continuation.  
**Support:** Both feet planted with the next-cycle support bias initialized.  
**COM:** COM velocity and acceleration match the start seam.  
**Dynamics:** Damp all secondary motion; close the state loop in pose and derivatives.  
**Interruptibility:** `true`

- **Pelvis:** Completes support transfer and matches loop seam.
- **Hindlimbs:** Remain flexed; no knee snap.
- **Feet Toes:** Contacts continuous across seam.
- **Thorax Spine:** Exhalation settles volume.
- **Neck Head:** Returns near neutral without exact mechanical symmetry.
- **Tail:** Velocity approaches seam-compatible value.
- **Forelimbs:** Return to bounded relaxed pose.
- **Jaw Throat:** Mouth and throat return to calibrated rest.

### Events

```yaml
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 1.0
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.34
  - 0.55
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
gaze:
  authority: limited
  max_yaw_deg: 12
  max_pitch_deg: 8
breathing:
  enabled: true
  rate_input: true
foot_ik:
  enabled: true
  authority: contact_preserving
terrain_alignment:
  enabled: true
  slope_limit: standing envelope
tail_balance:
  enabled: true
  noise: very_low
injury_overlay:
  enabled: true
  max_severity: moderate
biological_variation:
  enabled: true
  aperiodic: true
  seeded: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- support load must not remain perfectly symmetric for the whole loop
- no visible loop reset
- head micro-attention must occur at most once per nominal loop
- tail tip peak-to-peak motion remains below calm-idle envelope
- breathing may not create foot pressure discontinuities

---

## 02 — Alert idle

**ID:** `tarbosaurus_alert_idle`  
**Program:** `stationary_support`  
**Category / priority:** `state` / `P0`  
**Duration envelope:** 4.0–8.0 s; target 6.0 s  
**Loop / root motion:** True / False

**Purpose.** Sustain serious attention while preserving undecided ecological intent and immediate readiness to move.

**Performance character.** Concentrated and economical: less wandering motion than neutral idle, elevated readiness without threat-display theatricality.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - listen_reaction
  - walk
  - feeding_pause
  - drink_pause
  requirements:
  - stimulus direction available
  - no committed attack state
exit:
  allowed:
  - neutral_idle
  - investigate_scent
  - walk_start
  - run_start
  - threat_call
  - quick_bite
  - power_attack
  handoff: do not bake the behavioral decision into the loop
```

### Phase progression

#### `target_lock` — 0.00–0.16
**Goal:** Acquire and hold the stimulus with head-led orientation.  
**Support:** Bilateral support; move toward a more even ready stance.  
**COM:** COM moves from prior bias toward the center of the support region.  
**Dynamics:** Attention leads; breathing amplitude briefly reduces.  
**Interruptibility:** `true`

- **Pelvis:** Centers subtly.
- **Hindlimbs:** Both limbs become available to initiate movement.
- **Feet Toes:** Remain planted.
- **Thorax Spine:** Stiffens modestly after head orientation.
- **Neck Head:** Skull and upper neck orient first; neck extends slightly.
- **Tail:** Settles to reduce unnecessary oscillation.
- **Forelimbs:** Quiet and close.
- **Jaw Throat:** Jaw remains closed; no automatic aggression.

#### `posture_elevation` — 0.16–0.34
**Goal:** Elevate readiness without becoming upright.  
**Support:** Both feet loaded with a small selected launch-side preference.  
**COM:** COM height rises only slightly; horizontal projection stays central.  
**Dynamics:** Neck extends forward/up; thorax firms; joints retain flexion.  
**Interruptibility:** `true`

- **Pelvis:** Near-centered, stable.
- **Hindlimbs:** Flexion becomes spring-ready rather than locked.
- **Feet Toes:** Pressure becomes more bilateral.
- **Thorax Spine:** Horizontal silhouette preserved with subtle firmness.
- **Neck Head:** Head raises and advances slightly while maintaining target.
- **Tail:** Aligns as a quiet counterbalance.
- **Forelimbs:** Low amplitude shoulder tension.

#### `body_alignment` — 0.34–0.54
**Goal:** Allow torso and support to catch up to the head target.  
**Support:** Bilateral support; optional micro-step may be requested when target azimuth exceeds planted-turn limit.  
**COM:** COM shifts toward any selected adjustment foot before it unloads.  
**Dynamics:** Thorax rotates below skull target; pelvis follows only as required; tail opposes yaw.  
**Interruptibility:** `conditional`

- **Pelvis:** Small yaw/translation toward target; never spins over fixed feet.
- **Hindlimbs:** One foot may unload for a configured adjustment step.
- **Feet Toes:** Loaded foot yaw is bounded; adjustment foot follows contact-state machine.
- **Thorax Spine:** Distributed yaw, not a single chest hinge.
- **Neck Head:** Head remains target-locked while body catches up.
- **Tail:** Opposes torso yaw with lag and damping.
- **Forelimbs:** Follow thorax inertia.

#### `sustained_vigilance` — 0.54–0.88
**Goal:** Hold a low-motion vigilant loop with tiny corrections.  
**Support:** Ready bilateral support.  
**COM:** COM remains centered with minimal drift.  
**Dynamics:** Low-amplitude gaze corrections and restrained breathing; no rhythmic scanning.  
**Interruptibility:** `true`

- **Pelvis:** Nearly still except pressure corrections.
- **Hindlimbs:** Maintain prepared flexion.
- **Feet Toes:** Planted.
- **Thorax Spine:** Subtle breath and target stabilization.
- **Neck Head:** Tiny target correction; movement amplitude lower than neutral idle.
- **Tail:** Quiet.
- **Forelimbs:** Quiet.
- **Jaw Throat:** Closed; throat reflects restrained breathing.

#### `loop_settle` — 0.88–1.00
**Goal:** Match support, target, breathing, and derivatives for seamless repetition.  
**Support:** Same ready support.  
**COM:** COM and velocities match seam.  
**Dynamics:** Damp secondary motion without relaxing alertness.  
**Interruptibility:** `true`

- **Pelvis:** Seam-compatible.
- **Hindlimbs:** No phase reset.
- **Feet Toes:** Continuous contact.
- **Thorax Spine:** Breath phase closes.
- **Neck Head:** Target remains held.
- **Tail:** State closes.
- **Forelimbs:** State closes.
- **Jaw Throat:** State closes.

### Events

```yaml
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 1.0
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 1.0
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
gaze:
  authority: target_locked
  max_yaw_deg: 28
  max_pitch_deg: 18
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
breathing:
  enabled: true
  amplitude: reduced_by_alertness
tail_balance:
  enabled: true
micro_step:
  enabled: true
  azimuth_threshold_input: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- mouth stays closed unless another state explicitly overrides
- alert silhouette must remain distinct from threat display
- movement amplitude lower than neutral idle
- large target azimuth cannot be achieved by neck twist alone
- optional adjustment step preserves support and target continuity

---

## 03 — Walk

**ID:** `tarbosaurus_walk`  
**Program:** `alternating_gait`  
**Category / priority:** `locomotion` / `P0`  
**Duration envelope:** 3.8–5.2 s; target 4.44 s  
**Loop / root motion:** True / True

**Purpose.** Primary walk locomotion contract for player control, root motion, contacts, turning, terrain, fatigue, injury, and growth.

**Performance character.** Deliberate, efficient, confident travel with large body translation and restrained secondary motion.

### Entry and exit

```yaml
entry:
  allowed:
  - phase_matched_locomotion
  - compatible_start_transition
  requirements:
  - incoming support phase known
  - desired speed within regime envelope
exit:
  allowed:
  - phase_matched_locomotion
  - compatible_stop_transition
  - action_at_declared_window
  handoff: preserve support foot, phase, COM/root velocity, angular momentum, and tail state
```

### Phase progression

#### `left_contact` — 0.00–0.10
**Goal:** Establish left contact without stopping forward travel.  
**Support:** Right remains loaded briefly; left transitions approaching→contact→loading; possible brief bilateral transfer.  
**COM:** COM continues forward with no velocity reset and approaches the left support line.  
**Dynamics:** Contact placement is solved relative to COM velocity; knee/ankle prepare for small compression.  
**Interruptibility:** `partial`

- **Pelvis:** Moves forward with stable bias and begins left-side load acceptance.
- **Hindlimbs:** Left reaches economically; right remains load-bearing until transfer is real.
- **Feet Toes:** Left toes/sole contact progressively; right does not release early.
- **Thorax Spine:** Small phase-lagged response.
- **Neck Head:** Stabilizes world trajectory without becoming rigid.
- **Tail:** Opposes pelvis yaw with bounded lag.
- **Forelimbs:** Low-amplitude inertial response.

#### `left_load` — 0.10–0.27
**Goal:** Accept body load and move the pelvis over the left support.  
**Support:** Left becomes fully loaded; right unloads.  
**COM:** COM advances over/relative to left support according to dynamic regime.  
**Dynamics:** Vertical and fore-aft impulse is absorbed through foot, ankle/metatarsus, knee, hip, and pelvis.  
**Interruptibility:** `partial`

- **Pelvis:** Drops/rolls only enough for load acceptance; no exaggerated vertical bounce.
- **Hindlimbs:** Left chain compresses small; right begins posterior unload.
- **Feet Toes:** Left patch remains planted; pressure moves through digits.
- **Thorax Spine:** Counter-rotation is small and distributed.
- **Neck Head:** Head lags pelvis impact fractionally, then is stabilized.
- **Tail:** Base responds to pelvis; distal chain delayed.
- **Forelimbs:** Shoulders reflect thorax inertia without pumping.

#### `right_toe_off` — 0.27–0.38
**Goal:** Complete right propulsion and release from the toes last.  
**Support:** Left loaded; right unloading→toe_off.  
**COM:** COM is propelled forward while left remains the current support.  
**Dynamics:** Right hip extension and toe push finish before recovery begins.  
**Interruptibility:** `partial`

- **Pelvis:** Continues forward progression.
- **Hindlimbs:** Right extends posteriorly, then knee begins flexing after toe-off.
- **Feet Toes:** Right heel/metatarsal region unloads before toes; no rigid-board lift.
- **Thorax Spine:** Preserves forward flow.
- **Neck Head:** Stable.
- **Tail:** Small correction.
- **Forelimbs:** No synchronized swing.

#### `right_swing` — 0.38–0.50
**Goal:** Recover the right limb with economical terrain clearance.  
**Support:** Left is sole or principal support.  
**COM:** COM continues through the planned support interval.  
**Dynamics:** Hip flexion leads, knee flexion shortens the limb, foot clears, lower leg extends late for contact.  
**Interruptibility:** `partial`

- **Pelvis:** Travels over left support.
- **Hindlimbs:** Right recovery remains compact; no high step.
- **Feet Toes:** Swing toes clear terrain with configured margin and remain relaxed until pre-contact.
- **Thorax Spine:** Small inertial wave, not snake-like.
- **Neck Head:** Moderate stabilization.
- **Tail:** Counterbalances limb/pelvis yaw at low amplitude.
- **Forelimbs:** Quiet.

#### `right_contact` — 0.50–0.60
**Goal:** Establish right contact as the mirrored but not mathematically identical half-cycle.  
**Support:** Left remains loaded briefly; right approaches and begins loading.  
**COM:** COM velocity remains continuous and moves toward right support.  
**Dynamics:** Placement and impact solve repeat with bounded asymmetry.  
**Interruptibility:** `partial`

- **Pelvis:** Begins right load acceptance.
- **Hindlimbs:** Right reaches under the body, avoiding visible over-stride braking.
- **Feet Toes:** Right contact progresses toes/sole; left stays planted until transfer.
- **Thorax Spine:** Counter-rotation reverses smoothly.
- **Neck Head:** Head does not bob in lockstep with pelvis.
- **Tail:** Response reverses without a whip.
- **Forelimbs:** Asymmetric micro-inertia allowed.

#### `right_load` — 0.60–0.77
**Goal:** Accept load and advance over the right support.  
**Support:** Right fully loaded; left unloads.  
**COM:** COM follows the regime-specific dynamic support relation.  
**Dynamics:** Right chain absorbs and redirects momentum.  
**Interruptibility:** `partial`

- **Pelvis:** Compression and progression mirror left with natural asymmetry.
- **Hindlimbs:** Right chain compresses small; left becomes posterior.
- **Feet Toes:** Right remains planted and load-aware.
- **Thorax Spine:** Distributed response.
- **Neck Head:** Impact filtered through neck.
- **Tail:** Damped support correction.
- **Forelimbs:** Quiet.

#### `left_toe_off` — 0.77–0.88
**Goal:** Finish left propulsion and release toes last.  
**Support:** Right loaded; left unloads→toe_off.  
**COM:** COM remains continuous.  
**Dynamics:** Left posterior drive finishes before recovery.  
**Interruptibility:** `partial`

- **Pelvis:** Continues.
- **Hindlimbs:** Left extends then folds.
- **Feet Toes:** Toe-off is sequential, not a board lift.
- **Thorax Spine:** Continues phase.
- **Neck Head:** Stable.
- **Tail:** Small response.
- **Forelimbs:** Quiet.

#### `left_swing_and_loop` — 0.88–1.00
**Goal:** Recover left limb and close all cyclic states into the next left contact.  
**Support:** Right support; left swing.  
**COM:** COM, root velocity, angular momentum, and contact state approach loop-compatible values.  
**Dynamics:** Late extension prepares the next left contact; cyclic derivatives close.  
**Interruptibility:** `partial`

- **Pelvis:** Returns to seam-compatible phase without reset.
- **Hindlimbs:** Left clears and reaches the next contact pose.
- **Feet Toes:** No terrain penetration; left enters approaching state at seam.
- **Thorax Spine:** Loop derivative continuous.
- **Neck Head:** Loop derivative continuous.
- **Tail:** Angle and angular velocity close.
- **Forelimbs:** Close naturally.

### Events

```yaml
- name: L_FOOT_CONTACT
  kind: point
  at: 0.0
  phase: left_contact
- name: L_FOOT_LOAD
  kind: point
  at: 0.13
  phase: left_load
- name: R_TOE_OFF
  kind: point
  at: 0.32
  phase: right_toe_off
- name: R_FOOT_CONTACT
  kind: point
  at: 0.5
  phase: right_contact
- name: R_FOOT_LOAD
  kind: point
  at: 0.63
  phase: right_load
- name: L_TOE_OFF
  kind: point
  at: 0.82
  phase: left_toe_off
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.12
  - 0.27
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.62
  - 0.77
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
speed:
  enabled: true
  within_regime_only: true
stride:
  enabled: true
cadence:
  enabled: true
curvature:
  enabled: true
  loaded_foot_yaw: bounded
foot_ik:
  enabled: true
  authority: contact_preserving
terrain_alignment:
  enabled: true
head_target:
  enabled: true
  authority: limited_by_gait
tail_balance:
  enabled: true
  damped: true
breathing:
  enabled: true
  scales_with_exertion: true
fatigue:
  enabled: true
injury_overlay:
  enabled: true
  may_force_regime_exit: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- root displacement must match measured stride
- loaded-foot skate and arbitrary yaw forbidden
- pelvis vertical excursion remains within regime envelope
- head is stabilized but not frozen
- tail does not visibly wag
- left/right halves permit bounded asymmetry but preserve phase semantics
- walk must remain perceptually distinct from adjacent regimes

---

## 04 — Fast walk / transitional gait

**ID:** `tarbosaurus_fast_walk`  
**Program:** `alternating_gait`  
**Category / priority:** `locomotion` / `P0`  
**Duration envelope:** 2.6–3.8 s; target 3.15 s  
**Loop / root motion:** True / True

**Purpose.** Primary fast walk locomotion contract for player control, root motion, contacts, turning, terrain, fatigue, injury, and growth.

**Performance character.** Purposeful travel that bridges calm walking and pursuit without becoming a run.

### Entry and exit

```yaml
entry:
  allowed:
  - phase_matched_locomotion
  - compatible_start_transition
  requirements:
  - incoming support phase known
  - desired speed within regime envelope
exit:
  allowed:
  - phase_matched_locomotion
  - compatible_stop_transition
  - action_at_declared_window
  handoff: preserve support foot, phase, COM/root velocity, angular momentum, and tail state
```

### Phase progression

#### `left_contact` — 0.00–0.10
**Goal:** Establish left contact without stopping forward travel.  
**Support:** Right remains loaded briefly; left transitions approaching→contact→loading; short bilateral transfer.  
**COM:** COM continues forward with no velocity reset and approaches the left support line.  
**Dynamics:** Contact placement is solved relative to COM velocity; knee/ankle prepare for moderate compression.  
**Interruptibility:** `partial`

- **Pelvis:** Moves forward with forward bias and begins left-side load acceptance.
- **Hindlimbs:** Left reaches economically; right remains load-bearing until transfer is real.
- **Feet Toes:** Left toes/sole contact progressively; right does not release early.
- **Thorax Spine:** Small phase-lagged response.
- **Neck Head:** Stabilizes world trajectory without becoming rigid.
- **Tail:** Opposes pelvis yaw with bounded lag.
- **Forelimbs:** Low-amplitude inertial response.

#### `left_load` — 0.10–0.27
**Goal:** Accept body load and move the pelvis over the left support.  
**Support:** Left becomes fully loaded; right unloads.  
**COM:** COM advances over/relative to left support according to dynamic regime.  
**Dynamics:** Vertical and fore-aft impulse is absorbed through foot, ankle/metatarsus, knee, hip, and pelvis.  
**Interruptibility:** `partial`

- **Pelvis:** Drops/rolls only enough for load acceptance; no exaggerated vertical bounce.
- **Hindlimbs:** Left chain compresses moderate; right begins posterior unload.
- **Feet Toes:** Left patch remains planted; pressure moves through digits.
- **Thorax Spine:** Counter-rotation is small and distributed.
- **Neck Head:** Head lags pelvis impact fractionally, then is stabilized.
- **Tail:** Base responds to pelvis; distal chain delayed.
- **Forelimbs:** Shoulders reflect thorax inertia without pumping.

#### `right_toe_off` — 0.27–0.38
**Goal:** Complete right propulsion and release from the toes last.  
**Support:** Left loaded; right unloading→toe_off.  
**COM:** COM is propelled forward while left remains the current support.  
**Dynamics:** Right hip extension and toe push finish before recovery begins.  
**Interruptibility:** `partial`

- **Pelvis:** Continues forward progression.
- **Hindlimbs:** Right extends posteriorly, then knee begins flexing after toe-off.
- **Feet Toes:** Right heel/metatarsal region unloads before toes; no rigid-board lift.
- **Thorax Spine:** Preserves forward flow.
- **Neck Head:** Stable.
- **Tail:** Small correction.
- **Forelimbs:** No synchronized swing.

#### `right_swing` — 0.38–0.50
**Goal:** Recover the right limb with economical terrain clearance.  
**Support:** Left is sole or principal support.  
**COM:** COM continues through the planned support interval.  
**Dynamics:** Hip flexion leads, knee flexion shortens the limb, foot clears, lower leg extends late for contact.  
**Interruptibility:** `partial`

- **Pelvis:** Travels over left support.
- **Hindlimbs:** Right recovery remains compact; no high step.
- **Feet Toes:** Swing toes clear terrain with configured margin and remain relaxed until pre-contact.
- **Thorax Spine:** Small inertial wave, not snake-like.
- **Neck Head:** Moderate stabilization.
- **Tail:** Counterbalances limb/pelvis yaw at low amplitude.
- **Forelimbs:** Quiet.

#### `right_contact` — 0.50–0.60
**Goal:** Establish right contact as the mirrored but not mathematically identical half-cycle.  
**Support:** Left remains loaded briefly; right approaches and begins loading.  
**COM:** COM velocity remains continuous and moves toward right support.  
**Dynamics:** Placement and impact solve repeat with bounded asymmetry.  
**Interruptibility:** `partial`

- **Pelvis:** Begins right load acceptance.
- **Hindlimbs:** Right reaches under the body, avoiding visible over-stride braking.
- **Feet Toes:** Right contact progresses toes/sole; left stays planted until transfer.
- **Thorax Spine:** Counter-rotation reverses smoothly.
- **Neck Head:** Head does not bob in lockstep with pelvis.
- **Tail:** Response reverses without a whip.
- **Forelimbs:** Asymmetric micro-inertia allowed.

#### `right_load` — 0.60–0.77
**Goal:** Accept load and advance over the right support.  
**Support:** Right fully loaded; left unloads.  
**COM:** COM follows the regime-specific dynamic support relation.  
**Dynamics:** Right chain absorbs and redirects momentum.  
**Interruptibility:** `partial`

- **Pelvis:** Compression and progression mirror left with natural asymmetry.
- **Hindlimbs:** Right chain compresses moderate; left becomes posterior.
- **Feet Toes:** Right remains planted and load-aware.
- **Thorax Spine:** Distributed response.
- **Neck Head:** Impact filtered through neck.
- **Tail:** Damped support correction.
- **Forelimbs:** Quiet.

#### `left_toe_off` — 0.77–0.88
**Goal:** Finish left propulsion and release toes last.  
**Support:** Right loaded; left unloads→toe_off.  
**COM:** COM remains continuous.  
**Dynamics:** Left posterior drive finishes before recovery.  
**Interruptibility:** `partial`

- **Pelvis:** Continues.
- **Hindlimbs:** Left extends then folds.
- **Feet Toes:** Toe-off is sequential, not a board lift.
- **Thorax Spine:** Continues phase.
- **Neck Head:** Stable.
- **Tail:** Small response.
- **Forelimbs:** Quiet.

#### `left_swing_and_loop` — 0.88–1.00
**Goal:** Recover left limb and close all cyclic states into the next left contact.  
**Support:** Right support; left swing.  
**COM:** COM, root velocity, angular momentum, and contact state approach loop-compatible values.  
**Dynamics:** Late extension prepares the next left contact; cyclic derivatives close.  
**Interruptibility:** `partial`

- **Pelvis:** Returns to seam-compatible phase without reset.
- **Hindlimbs:** Left clears and reaches the next contact pose.
- **Feet Toes:** No terrain penetration; left enters approaching state at seam.
- **Thorax Spine:** Loop derivative continuous.
- **Neck Head:** Loop derivative continuous.
- **Tail:** Angle and angular velocity close.
- **Forelimbs:** Close naturally.

### Events

```yaml
- name: L_FOOT_CONTACT
  kind: point
  at: 0.0
  phase: left_contact
- name: L_FOOT_LOAD
  kind: point
  at: 0.13
  phase: left_load
- name: R_TOE_OFF
  kind: point
  at: 0.32
  phase: right_toe_off
- name: R_FOOT_CONTACT
  kind: point
  at: 0.5
  phase: right_contact
- name: R_FOOT_LOAD
  kind: point
  at: 0.63
  phase: right_load
- name: L_TOE_OFF
  kind: point
  at: 0.82
  phase: left_toe_off
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.12
  - 0.27
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.62
  - 0.77
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
speed:
  enabled: true
  within_regime_only: true
stride:
  enabled: true
cadence:
  enabled: true
curvature:
  enabled: true
  loaded_foot_yaw: bounded
foot_ik:
  enabled: true
  authority: contact_preserving
terrain_alignment:
  enabled: true
head_target:
  enabled: true
  authority: limited_by_gait
tail_balance:
  enabled: true
  damped: true
breathing:
  enabled: true
  scales_with_exertion: true
fatigue:
  enabled: true
injury_overlay:
  enabled: true
  may_force_regime_exit: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- root displacement must match measured stride
- loaded-foot skate and arbitrary yaw forbidden
- pelvis vertical excursion remains within regime envelope
- head is stabilized but not frozen
- tail does not visibly wag
- left/right halves permit bounded asymmetry but preserve phase semantics
- fast_walk must remain perceptually distinct from adjacent regimes

---

## 05 — Run

**ID:** `tarbosaurus_run`  
**Program:** `alternating_gait`  
**Category / priority:** `locomotion` / `P0`  
**Duration envelope:** 1.7–2.7 s; target 2.15 s  
**Loop / root motion:** True / True

**Purpose.** Primary run locomotion contract for player control, root motion, contacts, turning, terrain, fatigue, injury, and growth.

**Performance character.** Sustainable pursuit gait with visible force absorption, forward commitment, and controlled mass.

### Entry and exit

```yaml
entry:
  allowed:
  - phase_matched_locomotion
  - compatible_start_transition
  requirements:
  - incoming support phase known
  - desired speed within regime envelope
exit:
  allowed:
  - phase_matched_locomotion
  - compatible_stop_transition
  - action_at_declared_window
  handoff: preserve support foot, phase, COM/root velocity, angular momentum, and tail state
```

### Phase progression

#### `left_contact` — 0.00–0.10
**Goal:** Establish left contact without stopping forward travel.  
**Support:** Right remains loaded briefly; left transitions approaching→contact→loading; minimal or absent bilateral transfer.  
**COM:** COM continues forward with no velocity reset and approaches the left support line.  
**Dynamics:** Contact placement is solved relative to COM velocity; knee/ankle prepare for strong compression.  
**Interruptibility:** `false`

- **Pelvis:** Moves forward with forward_lower bias and begins left-side load acceptance.
- **Hindlimbs:** Left reaches economically; right remains load-bearing until transfer is real.
- **Feet Toes:** Left toes/sole contact progressively; right does not release early.
- **Thorax Spine:** Small phase-lagged response.
- **Neck Head:** Stabilizes world trajectory without becoming rigid.
- **Tail:** Opposes pelvis yaw with bounded lag.
- **Forelimbs:** Low-amplitude inertial response.

#### `left_load` — 0.10–0.27
**Goal:** Accept body load and move the pelvis over the left support.  
**Support:** Left becomes fully loaded; right unloads.  
**COM:** COM advances over/relative to left support according to dynamic regime.  
**Dynamics:** Vertical and fore-aft impulse is absorbed through foot, ankle/metatarsus, knee, hip, and pelvis.  
**Interruptibility:** `false`

- **Pelvis:** Drops/rolls only enough for load acceptance; no exaggerated vertical bounce.
- **Hindlimbs:** Left chain compresses strong; right begins posterior unload.
- **Feet Toes:** Left patch remains planted; pressure moves through digits.
- **Thorax Spine:** Counter-rotation is small and distributed.
- **Neck Head:** Head lags pelvis impact fractionally, then is stabilized.
- **Tail:** Base responds to pelvis; distal chain delayed.
- **Forelimbs:** Shoulders reflect thorax inertia without pumping.

#### `right_toe_off` — 0.27–0.38
**Goal:** Complete right propulsion and release from the toes last.  
**Support:** Left loaded; right unloading→toe_off.  
**COM:** COM is propelled forward while left remains the current support.  
**Dynamics:** Right hip extension and toe push finish before recovery begins.  
**Interruptibility:** `false`

- **Pelvis:** Continues forward progression.
- **Hindlimbs:** Right extends posteriorly, then knee begins flexing after toe-off.
- **Feet Toes:** Right heel/metatarsal region unloads before toes; no rigid-board lift.
- **Thorax Spine:** Preserves forward flow.
- **Neck Head:** Stable.
- **Tail:** Small correction.
- **Forelimbs:** No synchronized swing.

#### `right_swing` — 0.38–0.50
**Goal:** Recover the right limb with economical terrain clearance.  
**Support:** Left is sole or principal support.  
**COM:** COM continues through the planned support interval.  
**Dynamics:** Hip flexion leads, knee flexion shortens the limb, foot clears, lower leg extends late for contact.  
**Interruptibility:** `partial`

- **Pelvis:** Travels over left support.
- **Hindlimbs:** Right recovery remains compact; no high step.
- **Feet Toes:** Swing toes clear terrain with configured margin and remain relaxed until pre-contact.
- **Thorax Spine:** Small inertial wave, not snake-like.
- **Neck Head:** Moderate stabilization.
- **Tail:** Counterbalances limb/pelvis yaw at low amplitude.
- **Forelimbs:** Quiet.

#### `right_contact` — 0.50–0.60
**Goal:** Establish right contact as the mirrored but not mathematically identical half-cycle.  
**Support:** Left remains loaded briefly; right approaches and begins loading.  
**COM:** COM velocity remains continuous and moves toward right support.  
**Dynamics:** Placement and impact solve repeat with bounded asymmetry.  
**Interruptibility:** `false`

- **Pelvis:** Begins right load acceptance.
- **Hindlimbs:** Right reaches under the body, avoiding visible over-stride braking.
- **Feet Toes:** Right contact progresses toes/sole; left stays planted until transfer.
- **Thorax Spine:** Counter-rotation reverses smoothly.
- **Neck Head:** Head does not bob in lockstep with pelvis.
- **Tail:** Response reverses without a whip.
- **Forelimbs:** Asymmetric micro-inertia allowed.

#### `right_load` — 0.60–0.77
**Goal:** Accept load and advance over the right support.  
**Support:** Right fully loaded; left unloads.  
**COM:** COM follows the regime-specific dynamic support relation.  
**Dynamics:** Right chain absorbs and redirects momentum.  
**Interruptibility:** `false`

- **Pelvis:** Compression and progression mirror left with natural asymmetry.
- **Hindlimbs:** Right chain compresses strong; left becomes posterior.
- **Feet Toes:** Right remains planted and load-aware.
- **Thorax Spine:** Distributed response.
- **Neck Head:** Impact filtered through neck.
- **Tail:** Damped support correction.
- **Forelimbs:** Quiet.

#### `left_toe_off` — 0.77–0.88
**Goal:** Finish left propulsion and release toes last.  
**Support:** Right loaded; left unloads→toe_off.  
**COM:** COM remains continuous.  
**Dynamics:** Left posterior drive finishes before recovery.  
**Interruptibility:** `false`

- **Pelvis:** Continues.
- **Hindlimbs:** Left extends then folds.
- **Feet Toes:** Toe-off is sequential, not a board lift.
- **Thorax Spine:** Continues phase.
- **Neck Head:** Stable.
- **Tail:** Small response.
- **Forelimbs:** Quiet.

#### `left_swing_and_loop` — 0.88–1.00
**Goal:** Recover left limb and close all cyclic states into the next left contact.  
**Support:** Right support; left swing.  
**COM:** COM, root velocity, angular momentum, and contact state approach loop-compatible values.  
**Dynamics:** Late extension prepares the next left contact; cyclic derivatives close.  
**Interruptibility:** `partial`

- **Pelvis:** Returns to seam-compatible phase without reset.
- **Hindlimbs:** Left clears and reaches the next contact pose.
- **Feet Toes:** No terrain penetration; left enters approaching state at seam.
- **Thorax Spine:** Loop derivative continuous.
- **Neck Head:** Loop derivative continuous.
- **Tail:** Angle and angular velocity close.
- **Forelimbs:** Close naturally.

### Events

```yaml
- name: L_FOOT_CONTACT
  kind: point
  at: 0.0
  phase: left_contact
- name: L_FOOT_LOAD
  kind: point
  at: 0.13
  phase: left_load
- name: R_TOE_OFF
  kind: point
  at: 0.32
  phase: right_toe_off
- name: R_FOOT_CONTACT
  kind: point
  at: 0.5
  phase: right_contact
- name: R_FOOT_LOAD
  kind: point
  at: 0.63
  phase: right_load
- name: L_TOE_OFF
  kind: point
  at: 0.82
  phase: left_toe_off
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.12
  - 0.27
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.62
  - 0.77
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
speed:
  enabled: true
  within_regime_only: true
stride:
  enabled: true
cadence:
  enabled: true
curvature:
  enabled: true
  loaded_foot_yaw: bounded
foot_ik:
  enabled: true
  authority: contact_preserving
terrain_alignment:
  enabled: true
head_target:
  enabled: true
  authority: limited_by_gait
tail_balance:
  enabled: true
  damped: true
breathing:
  enabled: true
  scales_with_exertion: true
fatigue:
  enabled: true
injury_overlay:
  enabled: true
  may_force_regime_exit: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- root displacement must match measured stride
- loaded-foot skate and arbitrary yaw forbidden
- pelvis vertical excursion remains within regime envelope
- head is stabilized but not frozen
- tail does not visibly wag
- left/right halves permit bounded asymmetry but preserve phase semantics
- run must remain perceptually distinct from adjacent regimes

---

## 06 — Sprint

**ID:** `tarbosaurus_sprint`  
**Program:** `alternating_gait`  
**Category / priority:** `locomotion` / `P0`  
**Duration envelope:** 1.2–2.0 s; target 1.55 s  
**Loop / root motion:** True / True

**Purpose.** Primary sprint locomotion contract for player control, root motion, contacts, turning, terrain, fatigue, injury, and growth.

**Performance character.** Short maximum-effort locomotion with stronger propulsion, contact compression, active stabilization, and obvious exertion.

### Entry and exit

```yaml
entry:
  allowed:
  - phase_matched_locomotion
  - compatible_start_transition
  requirements:
  - incoming support phase known
  - desired speed within regime envelope
exit:
  allowed:
  - phase_matched_locomotion
  - compatible_stop_transition
  - action_at_declared_window
  handoff: preserve support foot, phase, COM/root velocity, angular momentum, and tail state
```

### Phase progression

#### `left_contact` — 0.00–0.10
**Goal:** Establish left contact without stopping forward travel.  
**Support:** Right remains loaded briefly; left transitions approaching→contact→loading; possible brief unsupported interval.  
**COM:** COM continues forward with no velocity reset and approaches the left support line.  
**Dynamics:** Contact placement is solved relative to COM velocity; knee/ankle prepare for very_strong compression.  
**Interruptibility:** `false`

- **Pelvis:** Moves forward with strong_forward bias and begins left-side load acceptance.
- **Hindlimbs:** Left reaches economically; right remains load-bearing until transfer is real.
- **Feet Toes:** Left toes/sole contact progressively; right does not release early.
- **Thorax Spine:** Small phase-lagged response.
- **Neck Head:** Stabilizes world trajectory without becoming rigid.
- **Tail:** Opposes pelvis yaw with bounded lag.
- **Forelimbs:** Low-amplitude inertial response.

#### `left_load` — 0.10–0.27
**Goal:** Accept body load and move the pelvis over the left support.  
**Support:** Left becomes fully loaded; right unloads.  
**COM:** COM advances over/relative to left support according to dynamic regime.  
**Dynamics:** Vertical and fore-aft impulse is absorbed through foot, ankle/metatarsus, knee, hip, and pelvis.  
**Interruptibility:** `false`

- **Pelvis:** Drops/rolls only enough for load acceptance; no exaggerated vertical bounce.
- **Hindlimbs:** Left chain compresses very_strong; right begins posterior unload.
- **Feet Toes:** Left patch remains planted; pressure moves through digits.
- **Thorax Spine:** Counter-rotation is small and distributed.
- **Neck Head:** Head lags pelvis impact fractionally, then is stabilized.
- **Tail:** Base responds to pelvis; distal chain delayed.
- **Forelimbs:** Shoulders reflect thorax inertia without pumping.

#### `right_toe_off` — 0.27–0.38
**Goal:** Complete right propulsion and release from the toes last.  
**Support:** Left loaded; right unloading→toe_off.  
**COM:** COM is propelled forward while left remains the current support.  
**Dynamics:** Right hip extension and toe push finish before recovery begins.  
**Interruptibility:** `false`

- **Pelvis:** Continues forward progression.
- **Hindlimbs:** Right extends posteriorly, then knee begins flexing after toe-off.
- **Feet Toes:** Right heel/metatarsal region unloads before toes; no rigid-board lift.
- **Thorax Spine:** Preserves forward flow.
- **Neck Head:** Stable.
- **Tail:** Small correction.
- **Forelimbs:** No synchronized swing.

#### `right_swing` — 0.38–0.50
**Goal:** Recover the right limb with economical terrain clearance.  
**Support:** Left is sole or principal support.  
**COM:** COM continues through the planned support interval.  
**Dynamics:** Hip flexion leads, knee flexion shortens the limb, foot clears, lower leg extends late for contact.  
**Interruptibility:** `partial`

- **Pelvis:** Travels over left support.
- **Hindlimbs:** Right recovery remains compact; no high step.
- **Feet Toes:** Swing toes clear terrain with configured margin and remain relaxed until pre-contact.
- **Thorax Spine:** Small inertial wave, not snake-like.
- **Neck Head:** Moderate stabilization.
- **Tail:** Counterbalances limb/pelvis yaw at low amplitude.
- **Forelimbs:** Quiet.

#### `right_contact` — 0.50–0.60
**Goal:** Establish right contact as the mirrored but not mathematically identical half-cycle.  
**Support:** Left remains loaded briefly; right approaches and begins loading.  
**COM:** COM velocity remains continuous and moves toward right support.  
**Dynamics:** Placement and impact solve repeat with bounded asymmetry.  
**Interruptibility:** `false`

- **Pelvis:** Begins right load acceptance.
- **Hindlimbs:** Right reaches under the body, avoiding visible over-stride braking.
- **Feet Toes:** Right contact progresses toes/sole; left stays planted until transfer.
- **Thorax Spine:** Counter-rotation reverses smoothly.
- **Neck Head:** Head does not bob in lockstep with pelvis.
- **Tail:** Response reverses without a whip.
- **Forelimbs:** Asymmetric micro-inertia allowed.

#### `right_load` — 0.60–0.77
**Goal:** Accept load and advance over the right support.  
**Support:** Right fully loaded; left unloads.  
**COM:** COM follows the regime-specific dynamic support relation.  
**Dynamics:** Right chain absorbs and redirects momentum.  
**Interruptibility:** `false`

- **Pelvis:** Compression and progression mirror left with natural asymmetry.
- **Hindlimbs:** Right chain compresses very_strong; left becomes posterior.
- **Feet Toes:** Right remains planted and load-aware.
- **Thorax Spine:** Distributed response.
- **Neck Head:** Impact filtered through neck.
- **Tail:** Damped support correction.
- **Forelimbs:** Quiet.

#### `left_toe_off` — 0.77–0.88
**Goal:** Finish left propulsion and release toes last.  
**Support:** Right loaded; left unloads→toe_off.  
**COM:** COM remains continuous.  
**Dynamics:** Left posterior drive finishes before recovery.  
**Interruptibility:** `false`

- **Pelvis:** Continues.
- **Hindlimbs:** Left extends then folds.
- **Feet Toes:** Toe-off is sequential, not a board lift.
- **Thorax Spine:** Continues phase.
- **Neck Head:** Stable.
- **Tail:** Small response.
- **Forelimbs:** Quiet.

#### `left_swing_and_loop` — 0.88–1.00
**Goal:** Recover left limb and close all cyclic states into the next left contact.  
**Support:** Right support; left swing.  
**COM:** COM, root velocity, angular momentum, and contact state approach loop-compatible values.  
**Dynamics:** Late extension prepares the next left contact; cyclic derivatives close.  
**Interruptibility:** `partial`

- **Pelvis:** Returns to seam-compatible phase without reset.
- **Hindlimbs:** Left clears and reaches the next contact pose.
- **Feet Toes:** No terrain penetration; left enters approaching state at seam.
- **Thorax Spine:** Loop derivative continuous.
- **Neck Head:** Loop derivative continuous.
- **Tail:** Angle and angular velocity close.
- **Forelimbs:** Close naturally.

### Events

```yaml
- name: L_FOOT_CONTACT
  kind: point
  at: 0.0
  phase: left_contact
- name: L_FOOT_LOAD
  kind: point
  at: 0.13
  phase: left_load
- name: R_TOE_OFF
  kind: point
  at: 0.32
  phase: right_toe_off
- name: R_FOOT_CONTACT
  kind: point
  at: 0.5
  phase: right_contact
- name: R_FOOT_LOAD
  kind: point
  at: 0.63
  phase: right_load
- name: L_TOE_OFF
  kind: point
  at: 0.82
  phase: left_toe_off
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.12
  - 0.27
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.62
  - 0.77
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
speed:
  enabled: true
  within_regime_only: true
stride:
  enabled: true
cadence:
  enabled: true
curvature:
  enabled: true
  loaded_foot_yaw: bounded
foot_ik:
  enabled: true
  authority: contact_preserving
terrain_alignment:
  enabled: true
head_target:
  enabled: true
  authority: limited_by_gait
tail_balance:
  enabled: true
  damped: true
breathing:
  enabled: true
  scales_with_exertion: true
fatigue:
  enabled: true
injury_overlay:
  enabled: true
  may_force_regime_exit: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- root displacement must match measured stride
- loaded-foot skate and arbitrary yaw forbidden
- pelvis vertical excursion remains within regime envelope
- head is stabilized but not frozen
- tail does not visibly wag
- left/right halves permit bounded asymmetry but preserve phase semantics
- sprint must remain perceptually distinct from adjacent regimes

---

## 07 — Walk start

**ID:** `tarbosaurus_walk_start`  
**Program:** `gait_transition`  
**Category / priority:** `transition` / `P0`  
**Duration envelope:** 2.2–4.0 s; target 3.0 s  
**Loop / root motion:** False / True

**Purpose.** Physically continuous walk start contract between stationary or locomotor states.

**Performance character.** Standing mass deliberately transfers support and grows into a mature walk over two to three steps.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - alert_idle
  - walk
  - fast_walk
  - run
  - sprint
  requirements:
  - incoming pose, contact phase, COM/root velocity, tail state known
exit:
  allowed:
  - neutral_idle
  - walk
  - fast_walk
  - run
  handoff: exact state handoff, no root offset reset
```

### Phase progression

#### `idle_intent` — 0.00–0.12
**Goal:** Declare movement direction before lifting a foot.  
**Support:** Both feet planted.  
**COM:** COM begins shifting toward selected support leg.  
**Dynamics:** Head or thorax orients subtly; desired velocity remains near zero.  
**Interruptibility:** `true`

- **Pelvis:** Begins lateral support shift.
- **Hindlimbs:** Selected support flexes; swing-side load reduces.
- **Feet Toes:** Both planted.
- **Thorax Spine:** Small directional orientation.
- **Neck Head:** May lead by a few degrees.
- **Tail:** Counterbalances orientation.

#### `unload_first_foot` — 0.12–0.28
**Goal:** Unload and release the selected first swing foot.  
**Support:** Support leg loaded; swing foot loaded→unloading→toe_off.  
**COM:** COM remains over reachable support margin.  
**Dynamics:** Pelvis translation precedes toe-off.  
**Interruptibility:** `partial`

- **Pelvis:** Moves over support.
- **Hindlimbs:** Swing knee flexes after unloading.
- **Feet Toes:** Toes leave last; support foot fixed.
- **Thorax Spine:** Maintains horizontal mass.
- **Neck Head:** Stable.
- **Tail:** Small delayed correction.

#### `short_first_step` — 0.28–0.52
**Goal:** Take a deliberately shorter-than-mature first step.  
**Support:** Single support until first contact.  
**COM:** COM begins forward acceleration but remains below mature walk speed.  
**Dynamics:** Support leg produces initial impulse; swing foot targets a short placement.  
**Interruptibility:** `partial`

- **Pelvis:** Accelerates gradually.
- **Hindlimbs:** Support extends; swing clears economically.
- **Feet Toes:** First foot approaches terrain.
- **Thorax Spine:** Lags acceleration slightly.
- **Neck Head:** Head lags then stabilizes.
- **Tail:** Adjusts to forward acceleration.

#### `first_contact_load` — 0.52–0.68
**Goal:** Accept first contact and transfer weight.  
**Support:** New foot contacts and loads; old foot releases only after real transfer.  
**COM:** COM progresses through contact without pause.  
**Dynamics:** First loading impulse is smaller than mature gait.  
**Interruptibility:** `partial`

- **Pelvis:** Moves onto new support.
- **Hindlimbs:** Contact knee/ankle compress.
- **Feet Toes:** Contact markers measured.
- **Thorax Spine:** Small impact response.
- **Neck Head:** Filtered.
- **Tail:** Damped.

#### `second_step_build` — 0.68–0.88
**Goal:** Use a more normal second step to approach mature stride and cadence.  
**Support:** Alternating support.  
**COM:** COM velocity approaches walk target smoothly.  
**Dynamics:** Stride and cadence ramp without phase discontinuity.  
**Interruptibility:** `partial`

- **Pelvis:** Approaches walk waveform.
- **Hindlimbs:** Second propulsion stronger.
- **Feet Toes:** Clean toe-off and contact.
- **Thorax Spine:** Approaches walk phase.
- **Neck Head:** Approaches walk stabilization.
- **Tail:** Approaches walk state.

#### `walk_handoff` — 0.88–1.00
**Goal:** Arrive at the exact target phase of the walk loop.  
**Support:** Target support/contact state matches walk.  
**COM:** COM/root position, velocity, and acceleration are handoff-compatible.  
**Dynamics:** No crossfade is allowed to hide root/contact mismatch.  
**Interruptibility:** `partial`

- **Pelvis:** Matches walk.
- **Hindlimbs:** Match walk phase.
- **Feet Toes:** Match walk contact.
- **Thorax Spine:** Match walk.
- **Neck Head:** Match walk.
- **Tail:** Angle and angular velocity match walk.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.02
- name: COMMIT_START
  kind: point
  at: 0.2
- name: RECOVERY_START
  kind: point
  at: 0.72
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.14
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.72
  - 1.0
```

### Procedural channels

```yaml
incoming_speed:
  enabled: true
desired_speed:
  enabled: true
step_count:
  computed: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
breathing:
  enabled: true
fatigue:
  enabled: true
injury:
  enabled: true
  may_extend_horizon: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- position, orientation, COM/root velocity, angular momentum, support phase, and tail state continuous
- step placement reachable and friction-feasible
- starts cannot lift a foot before support shift
- stops cannot halt root translation before body absorption
- handoff target phase exact

---

## 08 — Walk stop

**ID:** `tarbosaurus_walk_stop`  
**Program:** `gait_transition`  
**Category / priority:** `transition` / `P0`  
**Duration envelope:** 2.4–4.5 s; target 3.2 s  
**Loop / root motion:** False / True

**Purpose.** Physically continuous walk stop contract between stationary or locomotor states.

**Performance character.** Walking momentum is shortened, absorbed, and settled rather than frozen.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - alert_idle
  - walk
  - fast_walk
  - run
  - sprint
  requirements:
  - incoming pose, contact phase, COM/root velocity, tail state known
exit:
  allowed:
  - neutral_idle
  - walk
  - fast_walk
  - run
  handoff: exact state handoff, no root offset reset
```

### Phase progression

#### `incoming_walk` — 0.00–0.12
**Goal:** Capture the exact incoming gait state and momentum.  
**Support:** Current support state from walk.  
**COM:** COM/root velocity equals incoming walk velocity.  
**Dynamics:** No pre-emptive velocity clamp.  
**Interruptibility:** `partial`

- **Pelvis:** Incoming waveform.
- **Hindlimbs:** Incoming support.
- **Feet Toes:** Incoming contact.
- **Thorax Spine:** Incoming motion.
- **Neck Head:** Incoming stabilization.
- **Tail:** Incoming state.

#### `shortened_braking_step` — 0.12–0.36
**Goal:** Place the next foot to begin braking without absurd overreach.  
**Support:** Current support releases into a forward braking contact.  
**COM:** COM continues forward; planned foot placement creates decelerating ground impulse.  
**Dynamics:** Contact lies modestly ahead of normal but inside reach and friction limits.  
**Interruptibility:** `false`

- **Pelvis:** Continues forward over impending contact.
- **Hindlimbs:** Braking leg reaches with flexion available.
- **Feet Toes:** Progressive contact.
- **Thorax Spine:** Begins relative forward lag.
- **Neck Head:** Head continues fractionally.
- **Tail:** Begins pitch counteraction.

#### `brake_absorb` — 0.36–0.56
**Goal:** Absorb the first braking impulse through the whole chain.  
**Support:** Braking foot fully loaded; opposite foot unloading.  
**COM:** COM speed decreases continuously, never resets.  
**Dynamics:** Foot/ankle/knee/hip/pelvis absorb; torso/head lag indicates mass.  
**Interruptibility:** `false`

- **Pelvis:** Moves forward while lowering/compressing slightly.
- **Hindlimbs:** Loaded chain flexes under braking.
- **Feet Toes:** Fixed under load.
- **Thorax Spine:** Pitches subtly relative to pelvis.
- **Neck Head:** Lags and absorbs.
- **Tail:** Counters pitch with damping.

#### `stabilizing_step` — 0.56–0.76
**Goal:** Take a shorter opposite step to create stable bilateral support.  
**Support:** Opposite foot contacts; first remains loaded until transfer.  
**COM:** COM velocity approaches zero over the widened support relation.  
**Dynamics:** Second impulse is smaller and resolves residual momentum.  
**Interruptibility:** `partial`

- **Pelvis:** Centers progressively.
- **Hindlimbs:** Second leg accepts remaining load.
- **Feet Toes:** No skate.
- **Thorax Spine:** Returns toward neutral.
- **Neck Head:** Settles after torso.
- **Tail:** Continues settling.

#### `momentum_resolution` — 0.76–0.90
**Goal:** Stop translation while allowing body segments to finish moving.  
**Support:** Both feet planted.  
**COM:** COM velocity reaches zero smoothly; internal angular motion damps afterward.  
**Dynamics:** Ankle/pelvis/head/tail settle in causal order.  
**Interruptibility:** `partial`

- **Pelvis:** Small final centering.
- **Hindlimbs:** Maintain flexion.
- **Feet Toes:** Planted.
- **Thorax Spine:** Damps.
- **Neck Head:** Settles after pelvis.
- **Tail:** Settles last.

#### `idle_handoff` — 0.90–1.00
**Goal:** Enter idle with a natural support bias and no freeze.  
**Support:** Bilateral idle support.  
**COM:** COM is stable with seam-compatible derivatives.  
**Dynamics:** Preserve breathing/gaze and choose an idle support side.  
**Interruptibility:** `true`

- **Pelvis:** Idle-compatible.
- **Hindlimbs:** Idle-compatible.
- **Feet Toes:** Planted.
- **Thorax Spine:** Idle-compatible.
- **Neck Head:** Idle-compatible.
- **Tail:** Idle-compatible.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.02
- name: COMMIT_START
  kind: point
  at: 0.2
- name: RECOVERY_START
  kind: point
  at: 0.72
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.14
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.72
  - 1.0
```

### Procedural channels

```yaml
incoming_speed:
  enabled: true
desired_speed:
  enabled: true
step_count:
  computed: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
breathing:
  enabled: true
fatigue:
  enabled: true
injury:
  enabled: true
  may_extend_horizon: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- position, orientation, COM/root velocity, angular momentum, support phase, and tail state continuous
- step placement reachable and friction-feasible
- starts cannot lift a foot before support shift
- stops cannot halt root translation before body absorption
- handoff target phase exact

---

## 09 — Run start / acceleration

**ID:** `tarbosaurus_run_start`  
**Program:** `gait_transition`  
**Category / priority:** `transition` / `P0`  
**Duration envelope:** 2.7–5.5 s; target 3.8 s  
**Loop / root motion:** False / True

**Purpose.** Physically continuous run start / acceleration contract between stationary or locomotor states.

**Performance character.** Heavy-predator acceleration takes distance and visibly begins at a loaded hindlimb.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - alert_idle
  - walk
  - fast_walk
  - run
  - sprint
  requirements:
  - incoming pose, contact phase, COM/root velocity, tail state known
exit:
  allowed:
  - neutral_idle
  - walk
  - fast_walk
  - run
  handoff: exact state handoff, no root offset reset
```

### Phase progression

#### `prepare` — 0.00–0.12
**Goal:** Align direction and select propulsion support before large acceleration.  
**Support:** Standing/fast-walk support state.  
**COM:** COM shifts toward selected drive foot.  
**Dynamics:** Head comes forward; tail and thorax align.  
**Interruptibility:** `partial`

- **Pelvis:** Selects support and yaw.
- **Hindlimbs:** Drive leg loads.
- **Feet Toes:** Support patch fixed.
- **Thorax Spine:** Aligns after pelvis.
- **Neck Head:** Forward intent.
- **Tail:** Balances heading.

#### `crouched_loading` — 0.12–0.28
**Goal:** Store visible launch energy without a feline crouch.  
**Support:** Drive leg principal support; other foot may remain lightly planted.  
**COM:** COM moves down/back within reachable support.  
**Dynamics:** Hip/knee/ankle flexion increases and horizontal launch impulse is prepared.  
**Interruptibility:** `false`

- **Pelvis:** Lowers and retracts modestly.
- **Hindlimbs:** Drive chain compresses.
- **Feet Toes:** Loaded toes grip within friction.
- **Thorax Spine:** Body remains theropod-horizontal.
- **Neck Head:** Draws forward but lags pelvis launch.
- **Tail:** Adjusts vertical posture.

#### `first_propulsion` — 0.28–0.46
**Goal:** Produce the first strong acceleration from the loaded hindlimb.  
**Support:** Drive foot loaded→toe_off.  
**COM:** COM accelerates forward; torso/head initially lag pelvic acceleration.  
**Dynamics:** Leg extension and toe impulse create measurable momentum change.  
**Interruptibility:** `false`

- **Pelvis:** Accelerates strongly.
- **Hindlimbs:** Drive leg extends; opposite reaches.
- **Feet Toes:** Drive toes leave last.
- **Thorax Spine:** Lags then follows.
- **Neck Head:** Fractional lag.
- **Tail:** Counters acceleration.

#### `first_running_contact` — 0.46–0.62
**Goal:** Accept the first long running contact without braking overreach.  
**Support:** Reaching foot contacts near projected COM.  
**COM:** COM continues accelerating through contact.  
**Dynamics:** Strong compression follows decisive contact.  
**Interruptibility:** `false`

- **Pelvis:** Moves over foot.
- **Hindlimbs:** Contact chain compresses.
- **Feet Toes:** Plant and load.
- **Thorax Spine:** Impact response.
- **Neck Head:** Filtered.
- **Tail:** Damped correction.

#### `second_propulsion` — 0.62–0.80
**Goal:** Build speed through a stronger second propulsion.  
**Support:** Alternating support.  
**COM:** COM velocity rises toward run target.  
**Dynamics:** Stride length and cadence continue ramping.  
**Interruptibility:** `false`

- **Pelvis:** Forward bias increases.
- **Hindlimbs:** Second push strong.
- **Feet Toes:** Clean toe-off.
- **Thorax Spine:** Approaches run.
- **Neck Head:** Approaches run stabilization.
- **Tail:** Approaches run state.

#### `run_handoff` — 0.80–1.00
**Goal:** Match a stable run phase after several accelerating steps.  
**Support:** Target run support state.  
**COM:** COM/root velocities and angular momentum match target run.  
**Dynamics:** Acceleration tapers to target speed without clip reset.  
**Interruptibility:** `partial`

- **Pelvis:** Run-compatible.
- **Hindlimbs:** Run-compatible.
- **Feet Toes:** Run contact-compatible.
- **Thorax Spine:** Run-compatible.
- **Neck Head:** Run-compatible.
- **Tail:** Run-compatible.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.02
- name: COMMIT_START
  kind: point
  at: 0.2
- name: RECOVERY_START
  kind: point
  at: 0.72
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.14
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.72
  - 1.0
```

### Procedural channels

```yaml
incoming_speed:
  enabled: true
desired_speed:
  enabled: true
step_count:
  computed: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
breathing:
  enabled: true
fatigue:
  enabled: true
injury:
  enabled: true
  may_extend_horizon: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- position, orientation, COM/root velocity, angular momentum, support phase, and tail state continuous
- step placement reachable and friction-feasible
- starts cannot lift a foot before support shift
- stops cannot halt root translation before body absorption
- handoff target phase exact

---

## 10 — Run stop / deceleration

**ID:** `tarbosaurus_run_stop`  
**Program:** `gait_transition`  
**Category / priority:** `transition` / `P0`  
**Duration envelope:** 3.0–6.5 s; target 4.5 s  
**Loop / root motion:** False / True

**Purpose.** Physically continuous run stop / deceleration contract between stationary or locomotor states.

**Performance character.** Incoming pursuit momentum determines braking contacts, distance, step count, body lag, and recovery.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - alert_idle
  - walk
  - fast_walk
  - run
  - sprint
  requirements:
  - incoming pose, contact phase, COM/root velocity, tail state known
exit:
  allowed:
  - neutral_idle
  - walk
  - fast_walk
  - run
  handoff: exact state handoff, no root offset reset
```

### Phase progression

#### `incoming_run` — 0.00–0.10
**Goal:** Capture full incoming pursuit momentum and support phase.  
**Support:** Incoming run contact state.  
**COM:** COM velocity equals incoming speed input.  
**Dynamics:** No hidden speed clamp.  
**Interruptibility:** `partial`

- **Pelvis:** Incoming.
- **Hindlimbs:** Incoming.
- **Feet Toes:** Incoming.
- **Thorax Spine:** Incoming.
- **Neck Head:** Incoming.
- **Tail:** Incoming.

#### `first_braking_contact` — 0.10–0.30
**Goal:** Place a reachable forward braking foot according to speed and friction.  
**Support:** Incoming support releases into braking contact.  
**COM:** COM continues forward; required deceleration remains within contact/friction/capacity limits.  
**Dynamics:** Foot is ahead of normal run contact but not an implausible pole vault.  
**Interruptibility:** `false`

- **Pelvis:** Forward momentum continues.
- **Hindlimbs:** Braking leg reaches with flexion.
- **Feet Toes:** Decisive progressive plant.
- **Thorax Spine:** Torso rises slightly relative to run posture.
- **Neck Head:** Continues forward fractionally.
- **Tail:** Counters pitching.

#### `first_absorption` — 0.30–0.48
**Goal:** Absorb the largest braking impulse through leg, pelvis, torso, neck, and tail.  
**Support:** Braking foot fully loaded.  
**COM:** COM speed decreases continuously.  
**Dynamics:** Knee/ankle/hip compress; head/neck lag; tail supplies bounded counter-moment.  
**Interruptibility:** `false`

- **Pelvis:** Compresses and advances over foot.
- **Hindlimbs:** Strong flexion under load.
- **Feet Toes:** No slide beyond substrate tolerance.
- **Thorax Spine:** Rises and lags.
- **Neck Head:** Neck absorbs forward head inertia.
- **Tail:** Stronger but damped correction.

#### `second_braking_step` — 0.48–0.66
**Goal:** Take a shorter, slightly more stable second braking step.  
**Support:** Second foot contacts; first releases after transfer.  
**COM:** COM speed reduces further.  
**Dynamics:** Impulse is lower than first and increases support stability.  
**Interruptibility:** `false`

- **Pelvis:** Recenters.
- **Hindlimbs:** Second chain accepts load.
- **Feet Toes:** Clean contact.
- **Thorax Spine:** Moves toward neutral.
- **Neck Head:** Still settling.
- **Tail:** Damps.

#### `optional_third_step` — 0.66–0.80
**Goal:** Use an additional stabilization step when incoming speed demands it.  
**Support:** Conditional alternating contact.  
**COM:** COM approaches walking/zero speed without violating capacity.  
**Dynamics:** Step count and distance derive from incoming speed rather than fixed animation timing.  
**Interruptibility:** `conditional`

- **Pelvis:** Progressively neutral.
- **Hindlimbs:** Short reachable step.
- **Feet Toes:** Measured contact.
- **Thorax Spine:** Neutralizing.
- **Neck Head:** Neutralizing.
- **Tail:** Neutralizing.

#### `final_settle` — 0.80–0.94
**Goal:** Resolve residual translation and internal motion.  
**Support:** Both feet establish stable support.  
**COM:** COM velocity reaches zero or requested continuation speed.  
**Dynamics:** Ankle, pelvis, torso, head, and tail settle in order.  
**Interruptibility:** `partial`

- **Pelvis:** Centers.
- **Hindlimbs:** Flexed.
- **Feet Toes:** Planted.
- **Thorax Spine:** Damps.
- **Neck Head:** Settles.
- **Tail:** Settles last.

#### `handoff` — 0.94–1.00
**Goal:** Enter idle, walk, or fast walk at an exact compatible state.  
**Support:** Target support state.  
**COM:** State continuity exact.  
**Dynamics:** Continuation intent selects target without teleport.  
**Interruptibility:** `true`

- **Pelvis:** Target-compatible.
- **Hindlimbs:** Target-compatible.
- **Feet Toes:** Target-compatible.
- **Thorax Spine:** Target-compatible.
- **Neck Head:** Target-compatible.
- **Tail:** Target-compatible.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.02
- name: COMMIT_START
  kind: point
  at: 0.2
- name: RECOVERY_START
  kind: point
  at: 0.72
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.14
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.72
  - 1.0
```

### Procedural channels

```yaml
incoming_speed:
  enabled: true
desired_speed:
  enabled: true
step_count:
  computed: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
breathing:
  enabled: true
fatigue:
  enabled: true
injury:
  enabled: true
  may_extend_horizon: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- position, orientation, COM/root velocity, angular momentum, support phase, and tail state continuous
- step placement reachable and friction-feasible
- starts cannot lift a foot before support shift
- stops cannot halt root translation before body absorption
- handoff target phase exact

---

## 11 — Investigate / scent

**ID:** `tarbosaurus_investigate_scent`  
**Program:** `attention_reaction`  
**Category / priority:** `sensory` / `P1`  
**Duration envelope:** 3.5–8.0 s; target 5.5 s  
**Loop / root motion:** False / False

**Purpose.** Convert airborne or ground evidence into deliberate sensory sampling and an undecided movement-ready result.

**Performance character.** Curious, analytical, and restrained; reads as collecting ecological information rather than performing dog-like sniffing.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - alert_idle
  - walk
  - feeding_pause
  requirements:
  - evidence direction and modality available
exit:
  allowed:
  - neutral_idle
  - alert_idle
  - walk_start
  - feeding
  - pursuit
  handoff: preserve evidence direction, support bias, gaze, and decision confidence
```

### Phase progression

#### `curiosity_orient` — 0.00–0.12
**Goal:** Notice and orient toward the evidence.  
**Support:** Existing support remains valid; no foot movement unless required by azimuth.  
**COM:** COM remains stable while skull and neck begin the query.  
**Dynamics:** Skull/upper neck lead; thorax follows only within attention limit.  
**Interruptibility:** `true`

- **Pelvis:** Holds prior support.
- **Hindlimbs:** Remain available.
- **Feet Toes:** Planted.
- **Thorax Spine:** Small delayed yaw.
- **Neck Head:** Muzzle deliberately orients to evidence.
- **Tail:** Tiny counter-response if thorax yaws.
- **Forelimbs:** Quiet.
- **Jaw Throat:** Jaw closed; nostril/throat motion subtle.

#### `air_sample` — 0.12–0.30
**Goal:** Sample airborne evidence with elongated neck and controlled inspiration.  
**Support:** Bilateral or current principal support.  
**COM:** COM stays inside support with minimal forward movement.  
**Dynamics:** Muzzle rises modestly; breath/throat envelope reflects deliberate sampling.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable flexion.
- **Feet Toes:** No slide.
- **Thorax Spine:** Ribcage expands subtly.
- **Neck Head:** Neck extends forward/up; no exaggerated repeated sniff.
- **Tail:** Quiet.
- **Forelimbs:** Close.
- **Jaw Throat:** Nasal/throat inhalation cue; mouth remains closed or minimally parted.

#### `directional_comparison` — 0.30–0.58
**Goal:** Compare scent strength across a small left-center-right arc.  
**Support:** Support remains stable; an adjustment step is permitted only beyond neck/torso range.  
**COM:** COM drift remains negligible or follows an explicit step plan.  
**Dynamics:** Head sweeps slowly; neck and thorax share motion; each comparison includes a brief sampling pause.  
**Interruptibility:** `true`

- **Pelvis:** Mostly stable; optional yaw after support plan.
- **Hindlimbs:** Prepared but not restless.
- **Feet Toes:** Loaded foot does not twist.
- **Thorax Spine:** Shares large part of sweep at low amplitude.
- **Neck Head:** Slow bounded comparison, not rhythmic scanning.
- **Tail:** Opposes torso yaw with damping.
- **Forelimbs:** Subtle inertia.
- **Jaw Throat:** Sampling breaths separated by natural pauses.

#### `ground_evidence_branch` — 0.58–0.76
**Goal:** Optionally lower toward a footprint, blood, carcass sign, or disturbed vegetation.  
**Support:** Feet stabilize before the head descends.  
**COM:** COM shifts rearward enough to preserve support as head/neck move down and forward.  
**Dynamics:** Thorax and cervical chain lower progressively; runtime ground/evidence point is authoritative.  
**Interruptibility:** `conditional`

- **Pelvis:** Shifts slightly rearward and lowers only as needed.
- **Hindlimbs:** Share support with increased flexion.
- **Feet Toes:** Remain planted and terrain-aware.
- **Thorax Spine:** Pitches down in distributed segments.
- **Neck Head:** Extends to target without final-neck-bone hinge.
- **Tail:** Raises/adjusts slightly to maintain balance.
- **Forelimbs:** Follow thorax.
- **Jaw Throat:** Muzzle remains clear of terrain.

#### `stronger_detection` — 0.76–0.90
**Goal:** Convert a compelling signal into decisive orientation and movement readiness.  
**Support:** Support centers or selects a likely first-step leg.  
**COM:** COM begins a small preparatory shift but does not launch movement yet.  
**Dynamics:** Head lock strengthens; torso aligns; breathing changes from sampling to readiness.  
**Interruptibility:** `true`

- **Pelvis:** Begins alignment.
- **Hindlimbs:** Select possible support.
- **Feet Toes:** Still grounded.
- **Thorax Spine:** Catches up to target.
- **Neck Head:** Locks more decisively.
- **Tail:** Counterbalances alignment.
- **Forelimbs:** Quiet.
- **Jaw Throat:** Sampling stops.

#### `decision_ready` — 0.90–1.00
**Goal:** Return a stable state from which AI/player can choose approach, pursuit, feeding, or withdrawal.  
**Support:** Explicit handoff support state.  
**COM:** COM/root velocities match target state.  
**Dynamics:** No baked decision; emit evidence heading and confidence.  
**Interruptibility:** `true`

- **Pelvis:** Handoff-compatible.
- **Hindlimbs:** Handoff-compatible.
- **Feet Toes:** Handoff-compatible.
- **Thorax Spine:** Handoff-compatible.
- **Neck Head:** Evidence direction maintained.
- **Tail:** State preserved.
- **Forelimbs:** State preserved.

### Events

```yaml
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.92
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 1.0
```

### Procedural channels

```yaml
gaze:
  authority: evidence_locked
evidence_target_ik:
  enabled: true
  airborne_and_ground: true
wind:
  enabled: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
breathing:
  enabled: true
  sampling_envelope: true
tail_balance:
  enabled: true
micro_step:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- no repeated rapid dog-sniff cycle
- ground target endpoint is runtime-relative
- large lowering recruits thorax and full cervical chain
- alert/aggression is not automatically selected
- loaded feet remain planted during directional comparison

---

## 12 — Alert / listen reaction

**ID:** `tarbosaurus_listen_reaction`  
**Program:** `attention_reaction`  
**Category / priority:** `sensory_transition` / `P0`  
**Duration envelope:** 1.0–2.4 s; target 1.6 s  
**Loop / root motion:** False / False

**Purpose.** Create the immediate physically plausible transition from an ongoing behavior into sustained acoustic vigilance.

**Performance character.** Fast recognition followed by a meaningful processing freeze; the stillness makes distant ecology readable.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - walk
  - feeding
  - drinking
  - resting_alert
  requirements:
  - sound direction and salience available
exit:
  allowed:
  - alert_idle
  handoff: exact target direction, support readiness, reduced breathing amplitude, and tail stabilization
```

### Phase progression

#### `interrupt_current_behavior` — 0.00–0.12
**Goal:** Arrest the current low-priority behavior without teleporting its body state.  
**Support:** Preserve current support/contact.  
**COM:** COM/root motion follows current state; only low-authority overlays stop rapidly.  
**Dynamics:** Current head/jaw activity decelerates before reorientation.  
**Interruptibility:** `conditional`

- **Pelvis:** Preserves current.
- **Hindlimbs:** Preserve current support.
- **Feet Toes:** Preserve contact.
- **Thorax Spine:** Current motion damps.
- **Neck Head:** Stops current attention path.
- **Tail:** Preserves state.
- **Jaw Throat:** Feeding/drinking motion yields only at legal interruption point.

#### `acoustic_recognition` — 0.12–0.28
**Goal:** Snap attention toward the sound within anatomical velocity limits.  
**Support:** Support unchanged.  
**COM:** COM nearly unchanged.  
**Dynamics:** Skull starts first, upper neck follows, then middle/base neck; high acceleration remains bounded.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Begins delayed yaw if needed.
- **Neck Head:** Fast but non-instant orientation to azimuth/elevation.
- **Tail:** Small opposite response if thorax turns.
- **Jaw Throat:** Mouth closes if it can do so without breaking active contact.

#### `processing_freeze` — 0.28–0.52
**Goal:** Hold near stillness to imply sensory processing.  
**Support:** Existing support remains.  
**COM:** COM drift and secondary motion minimize.  
**Dynamics:** Breathing amplitude reduces; gaze locks; no decorative tail movement.  
**Interruptibility:** `partial`

- **Pelvis:** Nearly still.
- **Hindlimbs:** Maintain flexion.
- **Feet Toes:** Planted.
- **Thorax Spine:** Near still with restrained respiration.
- **Neck Head:** Fixed to acoustic direction with tiny localization correction.
- **Tail:** Stabilized.
- **Forelimbs:** Still.
- **Jaw Throat:** Quiet.

#### `lower_body_preparation` — 0.52–0.76
**Goal:** Convert upper-body attention into a ready whole-body state.  
**Support:** Move toward bilateral support or select a first-step support.  
**COM:** COM centers or shifts toward selected support.  
**Dynamics:** Pelvis, thorax, and tail align below the maintained head target.  
**Interruptibility:** `true`

- **Pelvis:** Centers/yaws within planted limit.
- **Hindlimbs:** Become movement-ready.
- **Feet Toes:** Optional adjustment step only when required.
- **Thorax Spine:** Rotates under target.
- **Neck Head:** Maintains acoustic lock while body catches up.
- **Tail:** Balances body yaw and then damps.
- **Forelimbs:** Follow thorax.

#### `alert_handoff` — 0.76–1.00
**Goal:** Enter alert idle without losing the listening target or support state.  
**Support:** Alert-idle support.  
**COM:** COM stable and handoff-compatible.  
**Dynamics:** Breathing and secondary motion match alert loop.  
**Interruptibility:** `true`

- **Pelvis:** Matches alert idle.
- **Hindlimbs:** Match.
- **Feet Toes:** Match.
- **Thorax Spine:** Match.
- **Neck Head:** Target retained.
- **Tail:** Angle/velocity retained.
- **Forelimbs:** Match.
- **Jaw Throat:** Match.

### Events

```yaml
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.12
  - 1.0
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.12
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.52
  - 1.0
```

### Procedural channels

```yaml
audio_target:
  enabled: true
  azimuth_elevation: true
gaze:
  authority: locked
breathing:
  enabled: true
  freeze_reduction: true
foot_ik:
  enabled: true
micro_step:
  enabled: true
tail_balance:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- processing freeze must be perceptible at normal speed
- orientation cannot exceed configured skull/neck angular acceleration
- body catches up after head rather than rotating simultaneously
- transition endpoint matches alert-idle support and derivatives

---

## 13 — Quick bite / snap

**ID:** `tarbosaurus_quick_bite`  
**Program:** `bite_action`  
**Category / priority:** `combat` / `P0`  
**Duration envelope:** 0.65–1.2 s; target 0.9 s  
**Loop / root motion:** False / True

**Purpose.** Fast short-range head attack with low-to-moderate commitment, target-relative contact, and a real recoil/recovery.

**Performance character.** Sharp and dangerous but economical; the pelvis remains comparatively stable while neck and thorax provide a bounded strike.

### Entry and exit

```yaml
entry:
  allowed:
  - combat_idle
  - alert_idle
  - slow_walk
  - feeding_defense
  requirements:
  - target inside quick-bite reach cone
  - speed below configured limit
exit:
  allowed:
  - combat_ready
  - quick_bite_chain_after_recovery
  - withdraw
  handoff: contact result and recovery complete before full redirection
```

### Phase progression

#### `acquire` — 0.00–0.12
**Goal:** Acquire target and prepare the cervical chain without telegraphing a full-body lunge.  
**Support:** Stable bilateral or current combat support.  
**COM:** COM shifts only slightly toward a stable support relation.  
**Dynamics:** Eyes/skull fix target; neck begins controlled retraction.  
**Interruptibility:** `true`

- **Pelvis:** Mostly stable.
- **Hindlimbs:** Brace lightly.
- **Feet Toes:** Planted.
- **Thorax Spine:** Small preparation.
- **Neck Head:** Target lock and initial retraction.
- **Tail:** Tiny balance response.
- **Forelimbs:** Close.
- **Jaw Throat:** Jaw closed.

#### `anticipation_retract` — 0.12–0.25
**Goal:** Compress/retract neck and preload a short strike.  
**Support:** Support remains planted.  
**COM:** COM remains inside support with small rearward shift.  
**Dynamics:** Cervical chain shortens; thorax contributes minimally.  
**Interruptibility:** `partial`

- **Pelvis:** Stable/rearward millimetric shift.
- **Hindlimbs:** Increase readiness.
- **Feet Toes:** No pivot.
- **Thorax Spine:** Subtle retract.
- **Neck Head:** Draws back in a connected curve.
- **Tail:** Counteracts slight pitch.
- **Forelimbs:** Inertial response.
- **Jaw Throat:** Begins pre-gape tension.

#### `jaw_open` — 0.25–0.38
**Goal:** Open jaw before forward target arrival.  
**Support:** Support unchanged.  
**COM:** COM stable.  
**Dynamics:** Mandible opens while head is still retracting/transitioning.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Hindlimbs:** Braced.
- **Feet Toes:** Planted.
- **Thorax Spine:** Begins forward contribution.
- **Neck Head:** Reversal from retract to extension.
- **Tail:** Damped.
- **Forelimbs:** Close.
- **Jaw Throat:** Rapid bounded gape; upper skull does not unrealistically hinge.

#### `strike` — 0.38–0.58
**Goal:** Extend head toward target with neck-led, thorax-assisted motion.  
**Support:** Feet remain supporting.  
**COM:** COM may advance slightly but remains within low-commitment envelope.  
**Dynamics:** Velocity builds through cervical base→mid neck→upper neck→skull.  
**Interruptibility:** `false`

- **Pelvis:** Small forward shift only.
- **Hindlimbs:** Maintain support and absorb reaction.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Adds a small forward pulse.
- **Neck Head:** Primary delivery chain.
- **Tail:** Counters pitch/translation subtly.
- **Forelimbs:** Lag thorax.
- **Jaw Throat:** Gape maintained.

#### `contact` — 0.58–0.66
**Goal:** Close jaws through the target-relative contact window.  
**Support:** Support stays grounded.  
**COM:** COM continues small forward momentum; no instant stop.  
**Dynamics:** Jaw closure and neck stiffening absorb/contact reaction.  
**Interruptibility:** `false`

- **Pelvis:** Receives small reaction.
- **Hindlimbs:** Brace.
- **Feet Toes:** No slide.
- **Thorax Spine:** Continues slightly.
- **Neck Head:** Velocity peaks near contact then reduces.
- **Tail:** Reaction correction.
- **Forelimbs:** Small recoil.
- **Jaw Throat:** Sharp closure; contact system owns confirmed hit.

#### `recoil` — 0.66–0.82
**Goal:** Withdraw from contact or empty target space without resetting.  
**Support:** Support remains or requests a small correction if target reaction is strong.  
**COM:** COM returns toward support center continuously.  
**Dynamics:** Neck compresses; jaw may rebound minutely then closes.  
**Interruptibility:** `partial`

- **Pelvis:** Recenters.
- **Hindlimbs:** Absorb.
- **Feet Toes:** Remain planted.
- **Thorax Spine:** Recoil propagates backward.
- **Neck Head:** Retracts with damped rebound.
- **Tail:** Damps reaction.
- **Forelimbs:** Settle.
- **Jaw Throat:** Closed by end.

#### `recovery` — 0.82–1.00
**Goal:** Restore combat-ready posture and interruption authority.  
**Support:** Stable support.  
**COM:** COM and segment velocities settle to target state.  
**Dynamics:** Neck, thorax, pelvis, and tail recover in sequence.  
**Interruptibility:** `true`

- **Pelvis:** Ready.
- **Hindlimbs:** Ready.
- **Feet Toes:** Stable.
- **Thorax Spine:** Ready.
- **Neck Head:** Target-aware ready pose.
- **Tail:** Settled.
- **Forelimbs:** Close.
- **Jaw Throat:** Living-neutral closure.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.12
- name: JAW_OPEN
  kind: point
  at: 0.25
- name: COMMIT_START
  kind: point
  at: 0.38
- name: CONTACT_BEGIN
  kind: point
  at: 0.58
- name: JAW_CONTACT
  kind: point
  at: 0.62
- name: CONTACT_PEAK
  kind: point
  at: 0.63
- name: JAW_CLOSE
  kind: point
  at: 0.66
- name: CONTACT_END
  kind: point
  at: 0.68
- name: RECOVERY_START
  kind: point
  at: 0.66
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.66
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.38
  - 0.68
- name: CONTACT_CONFIRMED
  kind: condition
  phase: contact
- name: CONTACT_MISSED
  kind: condition
  phase: contact
```

### Procedural channels

```yaml
target_ik:
  enabled: true
  reach: bounded_quick_bite
jaw_contact:
  enabled: true
foot_ik:
  enabled: true
tail_balance:
  enabled: true
gaze:
  enabled: true
  locked_until: 0.66
injury:
  enabled: true
  may_reduce_reach: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- jaw opens before the head reaches target
- pelvis displacement remains substantially below committed bite
- strike velocity and jaw contact are temporally coherent
- no immediate cancel during commit/contact
- miss branch transfers to bite-miss recovery when overextension exceeds local quick-recoil envelope

---

## 14 — Committed power bite

**ID:** `tarbosaurus_committed_power_bite`  
**Program:** `bite_action`  
**Category / priority:** `combat` / `P0`  
**Duration envelope:** 1.6–2.8 s; target 2.1 s  
**Loop / root motion:** False / True

**Purpose.** Signature grounded Tarbosaurus bite in which alignment, hindlimb load, body propulsion, gape, contact, follow-through, and long recovery communicate mass and commitment.

**Performance character.** Frightening through mechanics rather than monster acting: a leg-driven whole-body action that becomes difficult to redirect after target lock.

### Entry and exit

```yaml
entry:
  allowed:
  - combat_idle
  - alert_idle
  - slow_walk
  - grounded_power_attack
  requirements:
  - target inside commitment cone
  - support and terrain feasible
  - current speed below configured grounded-bite limit
exit:
  allowed:
  - combat_ready
  - bite_miss_recovery
  - hold_interaction
  - feeding
  handoff: branch result owns target relation; full authority returns only after recovery
```

### Phase progression

#### `target_commitment` — 0.00–0.10
**Goal:** Fix target and define a limited redirection cone.  
**Support:** Current support preserved.  
**COM:** COM state captured; no immediate translation.  
**Dynamics:** Head/gaze lock starts; planner freezes major target-choice changes.  
**Interruptibility:** `true`

- **Pelvis:** Captures heading.
- **Hindlimbs:** Ready.
- **Feet Toes:** Current support.
- **Thorax Spine:** Begins orientation.
- **Neck Head:** Target locked.
- **Tail:** State preserved.
- **Forelimbs:** Close.
- **Jaw Throat:** Closed.

#### `body_alignment` — 0.10–0.23
**Goal:** Align pelvis, torso, and stance behind the intended bite line.  
**Support:** Bilateral support or one preparatory adjustment step.  
**COM:** COM shifts into a powerful support relation.  
**Dynamics:** Pelvis alignment and optional foot placement precede load.  
**Interruptibility:** `partial`

- **Pelvis:** Yaw/translate toward bite line.
- **Hindlimbs:** Select drive distribution.
- **Feet Toes:** Adjustment foot unloads only after COM shift; loaded foot does not spin.
- **Thorax Spine:** Distributed alignment.
- **Neck Head:** Maintains target while body catches up.
- **Tail:** Opposes yaw.
- **Forelimbs:** Follow torso.
- **Jaw Throat:** Closed/tensioned.

#### `load` — 0.23–0.38
**Goal:** Store visible energy by flexing hips/knees and retracting torso/head.  
**Support:** Powerful bilateral or rear-biased stance.  
**COM:** COM moves back/down within support while potential launch direction is prepared.  
**Dynamics:** Hindlimbs compress; torso and neck retract; jaw begins opening late in phase.  
**Interruptibility:** `false`

- **Pelvis:** Lowers/retracts.
- **Hindlimbs:** Hip/knee/ankle flexion increases.
- **Feet Toes:** Pressure rises within friction.
- **Thorax Spine:** Retracts after pelvis.
- **Neck Head:** Draws back.
- **Tail:** Adjusts to rearward COM.
- **Forelimbs:** Inertial tension.
- **Jaw Throat:** Gape initiates before propulsion.

#### `propulsion` — 0.38–0.54
**Goal:** Drive the bite from ground through hindlimbs, pelvis, torso, neck, and skull.  
**Support:** Feet loaded, then rearward support may unload according to plan.  
**COM:** COM accelerates forward continuously.  
**Dynamics:** Force chain is leg→pelvis→thorax→cervical chain→skull.  
**Interruptibility:** `false`

- **Pelvis:** Primary forward drive.
- **Hindlimbs:** Extend strongly without snapping knees.
- **Feet Toes:** Toe pressure contributes; no skate.
- **Thorax Spine:** Follows pelvis with phase lag.
- **Neck Head:** Extends after thorax begins.
- **Tail:** Counters acceleration/pitch.
- **Forelimbs:** Lag torso.
- **Jaw Throat:** Gape increases.

#### `maximum_gape` — 0.54–0.62
**Goal:** Reach delivery gape shortly before target contact while maintaining aim.  
**Support:** Support still active; any release is planned.  
**COM:** COM continues forward.  
**Dynamics:** Jaw reaches configured gape; head trajectory remains target-relative.  
**Interruptibility:** `false`

- **Pelvis:** Continues drive.
- **Hindlimbs:** Continue/finish propulsion.
- **Feet Toes:** Respect contact plan.
- **Thorax Spine:** Strong forward posture.
- **Neck Head:** Near full delivery extension within limits.
- **Tail:** Balances.
- **Forelimbs:** Inertial.
- **Jaw Throat:** Maximum gape before contact, not after.

#### `contact_force_peak` — 0.62–0.70
**Goal:** Close jaws, stiffen neck, and transmit reaction through the supporting body.  
**Support:** At least one reliable grounded support unless entered from another explicit program.  
**COM:** COM momentum continues through initial contact.  
**Dynamics:** Contact solver handles target reaction; jaws close and body absorbs/transmits force.  
**Interruptibility:** `false`

- **Pelvis:** Continues slightly forward then reacts.
- **Hindlimbs:** Absorb reaction.
- **Feet Toes:** Loaded patches fixed.
- **Thorax Spine:** Continues through contact.
- **Neck Head:** Stiffens without becoming a rigid block.
- **Tail:** Counteracts reaction.
- **Forelimbs:** Recoil.
- **Jaw Throat:** Closure peaks at target contact.

#### `follow_through` — 0.70–0.80
**Goal:** Continue body travel beyond first contact rather than stopping at jaw closure.  
**Support:** Support/target branch dependent.  
**COM:** COM decelerates according to target and ground reaction, never resets.  
**Dynamics:** Hit may become hold; miss continues into overextension; yielding target changes resistance.  
**Interruptibility:** `false`

- **Pelvis:** Continues and starts arrest.
- **Hindlimbs:** Absorb or step.
- **Feet Toes:** Follow contact plan.
- **Thorax Spine:** Passes through target line.
- **Neck Head:** Maintains or releases based on branch.
- **Tail:** Damps angular response.
- **Forelimbs:** Settle.
- **Jaw Throat:** Closed on hit/hold; branch-controlled on miss.

#### `disengagement` — 0.80–0.90
**Goal:** Separate or stabilize the target relation and reposition support.  
**Support:** One or both feet may take a recovery step.  
**COM:** COM returns toward a viable support relation.  
**Dynamics:** Head pulls back only after whole-body momentum is addressed.  
**Interruptibility:** `partial`

- **Pelvis:** Recenters/steps.
- **Hindlimbs:** Recovery placement.
- **Feet Toes:** Measured step.
- **Thorax Spine:** Rises/retracts.
- **Neck Head:** Disengages.
- **Tail:** Balances step.
- **Forelimbs:** Settle.
- **Jaw Throat:** Returns toward closed.

#### `long_recovery` — 0.90–1.00
**Goal:** Expose a readable vulnerability window and restore combat readiness.  
**Support:** Stable final support.  
**COM:** COM and angular momentum settle.  
**Dynamics:** Neck, pelvis, torso, and tail recover with body-tier-dependent time constants.  
**Interruptibility:** `partial`

- **Pelvis:** Stabilizes.
- **Hindlimbs:** Remain flexed.
- **Feet Toes:** Stable.
- **Thorax Spine:** Settles.
- **Neck Head:** Returns to ready target-aware posture.
- **Tail:** Settles last.
- **Forelimbs:** Close.
- **Jaw Throat:** Living-neutral closure.

### Events

```yaml
- name: TARGET_LOCK
  kind: point
  at: 0.0
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.62
- name: ANTICIPATION_START
  kind: point
  at: 0.23
- name: JAW_OPEN
  kind: point
  at: 0.32
- name: COMMIT_START
  kind: point
  at: 0.38
- name: CONTACT_BEGIN
  kind: point
  at: 0.62
- name: JAW_CONTACT
  kind: point
  at: 0.66
- name: CONTACT_PEAK
  kind: point
  at: 0.67
- name: JAW_CLOSE
  kind: point
  at: 0.7
- name: CONTACT_END
  kind: point
  at: 0.78
- name: RECOVERY_START
  kind: point
  at: 0.8
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.38
  - 0.8
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.8
  - 1.0
- name: CONTACT_CONFIRMED
  kind: condition
  phase: contact_force_peak
- name: CONTACT_MISSED
  kind: condition
  phase: contact_force_peak
- name: TARGET_YIELDED
  kind: condition
  phase: follow_through
- name: TARGET_RESISTED
  kind: condition
  phase: follow_through
```

### Procedural channels

```yaml
target_ik:
  enabled: true
  authority: limited_after_target_lock
jaw_contact:
  enabled: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
contact_reaction:
  enabled: true
injury:
  enabled: true
  may_reject_action: true
fatigue:
  enabled: true
  extends_recovery: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- major propulsion visibly starts in hindlimbs
- target redirection after COMMIT_START remains inside configured cone
- maximum gape precedes contact
- whole body continues through jaw closure
- hit, miss, yield, and resist branches preserve velocities
- long recovery remains gameplay-readable and cannot be erased by a generic crossfade

### Branches

- `hit_disengage`
- `hit_hold`
- `target_yields`
- `target_resists`
- `miss_to_tarbosaurus_bite_miss_recovery`

---

## 15 — Low / downward bite

**ID:** `tarbosaurus_low_downward_bite`  
**Program:** `bite_action`  
**Category / priority:** `combat_interaction` / `P1`  
**Duration envelope:** 1.6–3.0 s; target 2.2 s  
**Loop / root motion:** False / False

**Purpose.** Reach small prey, prone targets, carcass tissue, or near-foot targets through support-aware whole-chain lowering and target-relative jaw contact.

**Performance character.** Controlled downward commitment: body shifts back and lowers before the heavy head moves near the ground.

### Entry and exit

```yaml
entry:
  allowed:
  - idle
  - combat_ready
  - feeding_stance
  requirements:
  - runtime target point and terrain height known
exit:
  allowed:
  - combat_ready
  - feeding
  - bite_miss_recovery
  handoff: preserve final support, target relation, and head clearance
```

### Phase progression

#### `acquire_low_target` — 0.00–0.10
**Goal:** Locate the target below the head and calculate safe lowering corridor.  
**Support:** Current support.  
**COM:** COM state captured.  
**Dynamics:** Gaze/head angles down within upper-neck limit while planner evaluates body lowering.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Ready.
- **Feet Toes:** Planted.
- **Thorax Spine:** Begins target orientation.
- **Neck Head:** Looks down without final-neck hinge.
- **Tail:** State preserved.
- **Jaw Throat:** Closed.

#### `stabilize_support` — 0.10–0.22
**Goal:** Broaden or offset support before moving the head downward/forward.  
**Support:** Bilateral support; optional small foot adjustment.  
**COM:** COM shifts rearward and toward stable center.  
**Dynamics:** Support change precedes head descent.  
**Interruptibility:** `partial`

- **Pelvis:** Moves back/centers.
- **Hindlimbs:** Increase flexion.
- **Feet Toes:** Adjustment follows contact state machine.
- **Thorax Spine:** Remains horizontal initially.
- **Neck Head:** Target maintained.
- **Tail:** Shifts to counter forward head moment.
- **Forelimbs:** Quiet.

#### `shared_lowering` — 0.22–0.42
**Goal:** Lower through pelvis/thorax/cervical chain, not neck tip alone.  
**Support:** Both feet loaded.  
**COM:** COM descends/retracts while remaining within support.  
**Dynamics:** Hip/knee flexion and thorax pitch create most reach; neck adds final alignment.  
**Interruptibility:** `partial`

- **Pelvis:** Lowers/retracts.
- **Hindlimbs:** Flex under support.
- **Feet Toes:** Loaded and fixed.
- **Thorax Spine:** Distributed downward pitch.
- **Neck Head:** Progressive extension/lowering.
- **Tail:** Raises or shifts slightly for balance.
- **Forelimbs:** Follow thorax.

#### `jaw_open_and_approach` — 0.42–0.55
**Goal:** Open before target arrival and complete runtime-relative approach.  
**Support:** Stable support.  
**COM:** COM remains controlled.  
**Dynamics:** Jaw opens while snout approaches target point with collision clearance.  
**Interruptibility:** `false`

- **Pelvis:** Stable under lowered posture.
- **Hindlimbs:** Support.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Holds.
- **Neck Head:** Targets point/normal.
- **Tail:** Balances.
- **Forelimbs:** Close.
- **Jaw Throat:** Gape opens before contact.

#### `downward_contact` — 0.55–0.65
**Goal:** Close jaws at target without penetrating terrain.  
**Support:** Both feet support; target may add external reaction.  
**COM:** COM continues small intended movement.  
**Dynamics:** Jaw contact and neck compression absorb reaction; ground clearance projected.  
**Interruptibility:** `false`

- **Pelvis:** Receives reaction.
- **Hindlimbs:** Absorb.
- **Feet Toes:** No slide.
- **Thorax Spine:** Maintains lowered support.
- **Neck Head:** Stops against target/contact, not absolute floor.
- **Tail:** Counters.
- **Jaw Throat:** Closure and contact event.

#### `absorb_or_hold` — 0.65–0.76
**Goal:** Resolve target resistance and avoid head/terrain penetration.  
**Support:** Support remains stable.  
**COM:** COM stops/redirects continuously.  
**Dynamics:** Cervical chain compresses slightly; target branch may become hold/feeding.  
**Interruptibility:** `false`

- **Pelvis:** Stabilizes.
- **Hindlimbs:** Maintain flexion.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Absorbs.
- **Neck Head:** Damped compression.
- **Tail:** Damped.
- **Jaw Throat:** Closed on target or branch-controlled.

#### `raise_and_recover` — 0.76–1.00
**Goal:** Raise head through the same body chain and restore COM over support.  
**Support:** Stable bilateral support.  
**COM:** COM shifts forward/up smoothly as head returns.  
**Dynamics:** Neck initiates recovery, thorax and pelvis follow; no snap upright.  
**Interruptibility:** `partial`

- **Pelvis:** Moves forward/up.
- **Hindlimbs:** Extend without locking.
- **Feet Toes:** Planted.
- **Thorax Spine:** Rises after neck begins.
- **Neck Head:** Returns with target awareness.
- **Tail:** Returns toward neutral.
- **Forelimbs:** Settle.
- **Jaw Throat:** Closed/living-neutral.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.1
- name: JAW_OPEN
  kind: point
  at: 0.42
- name: COMMIT_START
  kind: point
  at: 0.48
- name: CONTACT_BEGIN
  kind: point
  at: 0.55
- name: JAW_CONTACT
  kind: point
  at: 0.6
- name: CONTACT_PEAK
  kind: point
  at: 0.62
- name: JAW_CLOSE
  kind: point
  at: 0.65
- name: CONTACT_END
  kind: point
  at: 0.72
- name: RECOVERY_START
  kind: point
  at: 0.76
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.65
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.48
  - 0.76
- name: CONTACT_MISSED
  kind: condition
  phase: downward_contact
```

### Procedural channels

```yaml
target_ik:
  enabled: true
  terrain_relative: true
ground_clearance:
  enabled: true
jaw_contact:
  enabled: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- target endpoint comes from runtime target/terrain, never an absolute baked floor
- support stabilizes before lowering
- pelvis and thorax contribute materially to reach
- head, teeth, and jaw do not penetrate ground
- recovery restores COM without foot slide

---

## 16 — Bite miss / overextension recovery

**ID:** `tarbosaurus_bite_miss_recovery`  
**Program:** `recovery_failure`  
**Category / priority:** `combat_recovery` / `P0`  
**Duration envelope:** 1.0–2.4 s; target 1.6 s  
**Loop / root motion:** False / True

**Purpose.** Preserve the physical consequence of a committed bite that expected resistance but found empty space.

**Performance character.** Awkward and costly but still animal-capable: the head and torso travel farther than intended, support catches the imbalance, and readiness returns only after a real recovery step.

### Entry and exit

```yaml
entry:
  allowed:
  - committed_power_bite_miss
  - low_bite_miss
  - dynamic_attack_miss
  requirements:
  - incoming pose, expected-contact impulse, COM/root velocity, and support known
exit:
  allowed:
  - combat_ready
  - stumble
  - stop
  handoff: recovery outcome and support feasibility choose exit
```

### Phase progression

#### `missing_resistance` — 0.00–0.12
**Goal:** Continue through expected target space when contact impulse is absent.  
**Support:** Incoming support preserved.  
**COM:** COM/head velocities remain those delivered by the bite.  
**Dynamics:** Do not apply the expected contact deceleration.  
**Interruptibility:** `false`

- **Pelvis:** Continues incoming momentum.
- **Hindlimbs:** Still supporting/propelling.
- **Feet Toes:** Incoming contact state.
- **Thorax Spine:** Continues forward.
- **Neck Head:** Passes target point.
- **Tail:** Incoming angular response.
- **Jaw Throat:** Closure timing may continue but no target resistance.

#### `safe_overextension` — 0.12–0.28
**Goal:** Reach bounded biomechanical extension without clipping or hyperextension.  
**Support:** Support begins to lose ideal COM relation.  
**COM:** COM continues farther than hit branch.  
**Dynamics:** Neck approaches safe range; torso/pelvis still carry forward momentum.  
**Interruptibility:** `false`

- **Pelvis:** Advances.
- **Hindlimbs:** Begin emergency load.
- **Feet Toes:** Loaded patches resist slide.
- **Thorax Spine:** Pitches farther.
- **Neck Head:** Extends to configured limit, not beyond.
- **Tail:** Larger correction begins.
- **Jaw Throat:** May reopen minimally after empty closure.

#### `imbalance` — 0.28–0.48
**Goal:** Let the absent resistance produce readable forward imbalance.  
**Support:** Existing support margin becomes small/negative dynamically; next contact is required.  
**COM:** Extrapolated COM escapes the current support capture region.  
**Dynamics:** Pelvis drops/pitches; planner selects reachable recovery foot.  
**Interruptibility:** `false`

- **Pelvis:** Drops/continues forward.
- **Hindlimbs:** One leg unloads for emergency step.
- **Feet Toes:** Support foot remains planted; recovery foot releases.
- **Thorax Spine:** Forward pitch visible.
- **Neck Head:** Begins protective retraction.
- **Tail:** Emergency counter-motion, still damped.
- **Forelimbs:** Inertial recoil.

#### `emergency_step` — 0.48–0.68
**Goal:** Place a foot to catch the forward-moving body.  
**Support:** Recovery foot approaching→contact→loading; prior support remains until transfer.  
**COM:** COM trajectory intersects the new capture region.  
**Dynamics:** Foot placement derives from incoming velocity, reach, terrain, and friction.  
**Interruptibility:** `false`

- **Pelvis:** Moves toward new support.
- **Hindlimbs:** Recovery leg reaches and compresses.
- **Feet Toes:** Decisive plant without teleport.
- **Thorax Spine:** Still moving forward.
- **Neck Head:** Retracts.
- **Tail:** Counteracts pitch/yaw.

#### `neck_and_body_recovery` — 0.68–0.84
**Goal:** Absorb the catch and draw the head back after the body is controlled.  
**Support:** Recovery foot loaded; second support may re-establish.  
**COM:** COM speed reduces continuously.  
**Dynamics:** Leg/pelvis absorb first; thorax/neck recover afterward.  
**Interruptibility:** `partial`

- **Pelvis:** Compresses/recenters.
- **Hindlimbs:** Absorb.
- **Feet Toes:** Plant.
- **Thorax Spine:** Rises/retracts.
- **Neck Head:** Returns from extension.
- **Tail:** Damps.
- **Jaw Throat:** Returns closed.

#### `posture_reset` — 0.84–1.00
**Goal:** Restore a vulnerable but viable hunting stance.  
**Support:** Stable support selected.  
**COM:** COM and angular momentum settle.  
**Dynamics:** Recovery duration remains mass/fatigue/injury dependent.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Flexed/ready.
- **Feet Toes:** Stable.
- **Thorax Spine:** Ready.
- **Neck Head:** Target-aware but not instantly re-committed.
- **Tail:** Settled.
- **Forelimbs:** Close.
- **Jaw Throat:** Neutral.

### Events

```yaml
- name: CONTACT_MISSED
  kind: condition
  phase: missing_resistance
- name: RECOVERY_START
  kind: point
  at: 0.28
- name: L_FOOT_CONTACT
  kind: point
  phase: emergency_step
  note: side selected by planner
  trigger: condition_resolved_at_runtime
- name: R_FOOT_CONTACT
  kind: point
  phase: emergency_step
  note: side selected by planner
  trigger: condition_resolved_at_runtime
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.68
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.68
  - 1.0
- name: SUPPORT_FAILED
  kind: condition
  phase: emergency_step
```

### Procedural channels

```yaml
incoming_momentum:
  required: true
emergency_step:
  enabled: true
  side: planner
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
  emergency_amplitude: true
fall_escalation:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- head continues farther than hit branch
- neck limit never exceeded
- emergency foot is reachable and contact-timed
- no instant return to neutral
- failed catch branches to stumble/fall without state reset

---

## 17 — Body shove / pressure

**ID:** `tarbosaurus_body_shove`  
**Program:** `body_pressure`  
**Category / priority:** `combat` / `P1`  
**Duration envelope:** 1.4–2.9 s; target 2.1 s  
**Loop / root motion:** False / True

**Purpose.** Use flank, rib, chest, or hip mass to apply grounded pressure through hindlimbs and body rotation.

**Performance character.** Heavy, positional, and sustained rather than a jumping shoulder tackle.

### Entry and exit

```yaml
entry:
  allowed:
  - combat_idle
  - slow_walk
  - carcass_contest
  requirements:
  - target contact region reachable
  - ground/friction support feasible
exit:
  allowed:
  - combat_ready
  - continue_pressure
  - withdraw
  handoff: target simulation result and recovery foot determine exit
```

### Phase progression

#### `align_contact_region` — 0.00–0.14
**Goal:** Bring the chosen body region into a useful approach angle.  
**Support:** Current support; optional step planned.  
**COM:** COM remains viable while body yaws.  
**Dynamics:** Pelvis and thorax align; head keeps target awareness.  
**Interruptibility:** `true`

- **Pelvis:** Yaw/translate toward approach.
- **Hindlimbs:** Prepare offset stance.
- **Feet Toes:** Loaded foot does not twist.
- **Thorax Spine:** Rotates in distributed chain.
- **Neck Head:** Target-aware.
- **Tail:** Opposes yaw.
- **Forelimbs:** Protected close to torso.

#### `establish_stance` — 0.14–0.28
**Goal:** Create a modestly wider/offset support base.  
**Support:** Near-side and far-side feet establish useful pressure geometry.  
**COM:** COM shifts toward the near-side drive relation.  
**Dynamics:** Foot placement precedes load; no magical body translation.  
**Interruptibility:** `partial`

- **Pelvis:** Centers in offset stance.
- **Hindlimbs:** Near-side accepts more load.
- **Feet Toes:** Adjustment contact measured.
- **Thorax Spine:** Poised.
- **Neck Head:** Stable.
- **Tail:** Balances stance.

#### `load` — 0.28–0.42
**Goal:** Preload near-side support and rotational drive.  
**Support:** Near-side principal support; far side stabilizes.  
**COM:** COM moves toward drive foot while retaining counter-support.  
**Dynamics:** Hip/knee flex and pelvis retract/rotate slightly.  
**Interruptibility:** `false`

- **Pelvis:** Loads and winds up.
- **Hindlimbs:** Near leg compresses.
- **Feet Toes:** Ground pressure rises.
- **Thorax Spine:** Counter-rotates modestly.
- **Neck Head:** Maintains safe target orientation.
- **Tail:** Stores opposite response.

#### `body_drive` — 0.42–0.60
**Goal:** Drive pelvis and torso into target contact from the ground.  
**Support:** Both feet contribute; near-side drive dominates.  
**COM:** COM and body contact region accelerate toward target.  
**Dynamics:** Hindlimb extension→pelvis translation/rotation→thorax contact.  
**Interruptibility:** `false`

- **Pelvis:** Primary drive.
- **Hindlimbs:** Extend under load.
- **Feet Toes:** No slide beyond friction tolerance.
- **Thorax Spine:** Rotates/translates into contact.
- **Neck Head:** Stabilizes and avoids target clipping.
- **Tail:** Opposes rotational impulse.
- **Forelimbs:** Remain tucked.

#### `contact_peak` — 0.60–0.70
**Goal:** Reach target contact and transmit pressure without instant stop.  
**Support:** Ground supports remain active.  
**COM:** COM continues through initial contact according to target reaction.  
**Dynamics:** Target simulation computes displacement/impulse; body solver maintains contact surface.  
**Interruptibility:** `false`

- **Pelvis:** Continues slightly.
- **Hindlimbs:** Absorb/drive.
- **Feet Toes:** Loaded.
- **Thorax Spine:** Firm but not rigid.
- **Neck Head:** Balances reaction.
- **Tail:** Counters.
- **Forelimbs:** Protected.

#### `maintain_pressure` — 0.70–0.82
**Goal:** Hold bounded pressure briefly when target resists.  
**Support:** Stable offset support.  
**COM:** COM settles against contact without toppling.  
**Dynamics:** Force is sustained within capacity; no passive stat-buff behavior.  
**Interruptibility:** `false`

- **Pelvis:** Maintains drive.
- **Hindlimbs:** Isometric-looking support.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Maintains contact.
- **Neck Head:** Target-aware.
- **Tail:** Damped balance.

#### `recovery_step` — 0.82–1.00
**Goal:** Release pressure and restore stable support.  
**Support:** One foot repositions as target reaction demands.  
**COM:** COM returns inside final support.  
**Dynamics:** Pelvis unwinds; torso and tail settle after contact release.  
**Interruptibility:** `partial`

- **Pelvis:** Recenters.
- **Hindlimbs:** Recovery step.
- **Feet Toes:** Clean release/contact.
- **Thorax Spine:** Unwinds.
- **Neck Head:** Returns ready.
- **Tail:** Damps after torso.
- **Forelimbs:** Remain close.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.28
- name: COMMIT_START
  kind: point
  at: 0.42
- name: CONTACT_BEGIN
  kind: point
  at: 0.6
- name: CONTACT_PEAK
  kind: point
  at: 0.66
- name: CONTACT_END
  kind: point
  at: 0.82
- name: RECOVERY_START
  kind: point
  at: 0.82
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.42
  - 0.82
- name: TARGET_YIELDED
  kind: condition
  phase: contact_peak
- name: TARGET_RESISTED
  kind: condition
  phase: maintain_pressure
```

### Procedural channels

```yaml
target_body_contact:
  enabled: true
  regions:
  - flank
  - rib
  - chest
  - hip
contact_wrench:
  enabled: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- contact force originates at ground supports
- contact body region remains collision-safe
- target simulation owns target displacement
- tail correction opposes rotation and damps
- recovery restores support after target yields or resists

---

## 18 — Head-down feeding

**ID:** `tarbosaurus_head_down_feeding`  
**Program:** `feeding_interaction`  
**Category / priority:** `feeding` / `P0`  
**Duration envelope:** 5.0–11.0 s; target 8.0 s  
**Loop / root motion:** True / False

**Purpose.** Provide modular carcass assessment, stable lowering, tissue acquisition, processing, gaze interruption, and target reset without a simplistic bend-and-chew loop.

**Performance character.** Vulnerable, focused, and physically supported; feeding creates readable ecological exposure and can be interrupted only at declared windows.

### Entry and exit

```yaml
entry:
  allowed:
  - idle_beside_carcass
  - feeding_transition
  requirements:
  - carcass target surface and ownership available
  - stable stance feasible
exit:
  allowed:
  - feeding_loop
  - swallow
  - tear_pull
  - alert_reaction
  - idle
  handoff: preserve carcass point, jaw state, support, and alertness
```

### Phase progression

#### `carcass_assessment` — 0.00–0.12
**Goal:** Inspect and sample the carcass point before committing the head downward.  
**Support:** Standing support near carcass.  
**COM:** COM remains stable.  
**Dynamics:** Head/gaze target carcass; short scent/visual assessment.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Ready to adjust.
- **Feet Toes:** Planted.
- **Thorax Spine:** Small orientation.
- **Neck Head:** Target assessment.
- **Tail:** Quiet.
- **Jaw Throat:** Closed/sampling.

#### `feeding_stance` — 0.12–0.25
**Goal:** Adjust feet and pelvis to support prolonged head-down work.  
**Support:** Bilateral offset stance established.  
**COM:** COM moves rearward/central as required.  
**Dynamics:** Stance adjustment occurs before lowering.  
**Interruptibility:** `partial`

- **Pelvis:** Centers/retracts.
- **Hindlimbs:** Increase flexion.
- **Feet Toes:** Adjustment measured; no slide.
- **Thorax Spine:** Prepares lower posture.
- **Neck Head:** Maintains target.
- **Tail:** Balances.

#### `progressive_lowering` — 0.25–0.40
**Goal:** Lower thorax and cervical chain toward the runtime carcass point.  
**Support:** Both feet loaded.  
**COM:** COM descends/retracts inside support.  
**Dynamics:** Pelvis/knees support; thorax lowers; cervical segments follow progressively.  
**Interruptibility:** `partial`

- **Pelvis:** Lowers modestly.
- **Hindlimbs:** Flex and support.
- **Feet Toes:** Loaded.
- **Thorax Spine:** Distributed pitch down.
- **Neck Head:** Reaches toward target without single-bone bend.
- **Tail:** Adjusts upward/rearward slightly.
- **Forelimbs:** Follow thorax.

#### `mouth_acquisition` — 0.40–0.52
**Goal:** Open jaw and position snout/teeth at a selected tissue point.  
**Support:** Stable feeding support.  
**COM:** COM controlled.  
**Dynamics:** Target IK and collision define endpoint.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Holds.
- **Neck Head:** Fine target positioning.
- **Tail:** Balances.
- **Jaw Throat:** Jaw opens before tissue contact.

#### `feeding_bite` — 0.52–0.60
**Goal:** Close on tissue with bounded head motion.  
**Support:** Support remains.  
**COM:** COM changes minimally.  
**Dynamics:** Jaw closes; neck stiffens locally; carcass interaction confirms acquisition.  
**Interruptibility:** `false`

- **Pelvis:** Receives small reaction.
- **Hindlimbs:** Brace.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Small response.
- **Neck Head:** Small contact movement.
- **Tail:** Tiny correction.
- **Jaw Throat:** Closure/contact.

#### `head_manipulation` — 0.60–0.72
**Goal:** Reposition tissue with small lateral/vertical motions.  
**Support:** Stable support.  
**COM:** COM stays viable.  
**Dynamics:** Neck/head manipulate within contact and collision limits; target point can migrate.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Pressure corrections.
- **Feet Toes:** Planted.
- **Thorax Spine:** Shares larger motion.
- **Neck Head:** Small bounded manipulation.
- **Tail:** Opposes any torso yaw.
- **Jaw Throat:** Clamped or controlled release.

#### `process` — 0.72–0.88
**Goal:** Process food with species-appropriate bounded jaw/throat behavior.  
**Support:** Same stance.  
**COM:** COM stable.  
**Dynamics:** Avoid exaggerated mammalian chewing; use bite reposition, compression, and swallow preparation.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Breathing constrained by feeding.
- **Neck Head:** Small stable posture.
- **Tail:** Nearly still.
- **Jaw Throat:** Bounded processing and throat preparation.

#### `target_reset_and_loop` — 0.88–1.00
**Goal:** Select another nearby carcass point or hand off to tear/swallow while closing the loop safely.  
**Support:** Feeding support preserved.  
**COM:** COM and derivatives match loop seam or declared branch.  
**Dynamics:** Head shifts to a nearby non-identical point; procedural variation avoids exact repetition.  
**Interruptibility:** `true`

- **Pelvis:** Seam-compatible.
- **Hindlimbs:** Seam-compatible.
- **Feet Toes:** Continuous.
- **Thorax Spine:** Seam-compatible.
- **Neck Head:** Target point variation bounded.
- **Tail:** State closes.
- **Jaw Throat:** Ready for next acquisition or branch.

### Events

```yaml
- name: JAW_OPEN
  kind: point
  at: 0.4
- name: JAW_CONTACT
  kind: point
  at: 0.56
- name: JAW_CLOSE
  kind: point
  at: 0.6
- name: CONTACT_BEGIN
  kind: point
  at: 0.52
- name: CONTACT_END
  kind: point
  at: 0.72
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.52
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.25
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.72
  - 1.0
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
carcass_target_ik:
  enabled: true
  moving_point: true
jaw_contact:
  enabled: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
gaze:
  enabled: true
  can_interrupt_at_windows: true
breathing:
  enabled: true
  feeding_masked: true
tail_balance:
  enabled: true
variation:
  enabled: true
  target_point_seeded: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- lowering shared by pelvis/thorax/neck
- feeding stance established before descent
- jaw endpoint tied to carcass target and collision
- processing avoids exaggerated mammalian chew
- loop varies target and timing without breaking semantics
- alert interruption only at declared windows

---

## 19 — Tear / pull

**ID:** `tarbosaurus_tear_pull`  
**Program:** `feeding_interaction`  
**Category / priority:** `feeding` / `P1`  
**Duration envelope:** 2.0–4.2 s; target 2.8 s  
**Loop / root motion:** False / True

**Purpose.** Pull against resistant carcass tissue using planted feet, rearward COM motion, whole-body force transmission, and dynamic release response.

**Performance character.** One of the strongest non-combat actions: jaw, neck, torso, pelvis, and legs visibly act as one connected system.

### Entry and exit

```yaml
entry:
  allowed:
  - feeding_bite_hold
  requirements:
  - jaw grip confirmed
  - resistance model available
  - rearward corridor and support feasible
exit:
  allowed:
  - swallow
  - feeding
  - alert_idle
  handoff: release result determines whether food remains in jaw
```

### Phase progression

#### `acquire_tissue` — 0.00–0.10
**Goal:** Confirm a stable jaw grip before applying pull force.  
**Support:** Existing feeding stance.  
**COM:** COM stable.  
**Dynamics:** Jaw clamps; target interaction establishes attachment and resistance estimate.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Aligned.
- **Neck Head:** Grip aligned.
- **Tail:** Quiet.
- **Jaw Throat:** Clamp confirmed.

#### `establish_rear_support` — 0.10–0.25
**Goal:** Plant and load feet for rearward force production.  
**Support:** Bilateral offset support; rearward pressure distribution.  
**COM:** COM shifts rearward inside support.  
**Dynamics:** Knees/hips flex; pelvis retracts before pull.  
**Interruptibility:** `partial`

- **Pelvis:** Moves back/down.
- **Hindlimbs:** Load for backward ground reaction.
- **Feet Toes:** Pressure increases without slide.
- **Thorax Spine:** Follows pelvis.
- **Neck Head:** Maintains grip.
- **Tail:** Balances rearward posture.

#### `preload_grip` — 0.25–0.38
**Goal:** Take up slack with a small forward/downward set before the main pull.  
**Support:** Support fixed.  
**COM:** COM pauses/reaches preload position.  
**Dynamics:** Head moves subtly into tissue; jaw remains clamped.  
**Interruptibility:** `false`

- **Pelvis:** Holds.
- **Hindlimbs:** Tensioned.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Small forward set.
- **Neck Head:** Preloads grip.
- **Tail:** Counterbalances.
- **Jaw Throat:** Clamped.

#### `whole_body_pull` — 0.38–0.60
**Goal:** Generate rearward pull from ground through pelvis, torso, neck, and jaw.  
**Support:** Both feet loaded.  
**COM:** COM moves rearward; external resistance determines acceleration.  
**Dynamics:** Legs push against ground→pelvis travels back→torso rises/back→neck contracts→head pulls.  
**Interruptibility:** `false`

- **Pelvis:** Primary rearward translation.
- **Hindlimbs:** Extend/brace against ground.
- **Feet Toes:** Loaded within friction.
- **Thorax Spine:** Rises and retracts.
- **Neck Head:** Contracts while maintaining bite line.
- **Tail:** Balances rearward moment.
- **Forelimbs:** Inertial.
- **Jaw Throat:** Clamp maintained.

#### `maximum_tension` — 0.60–0.72
**Goal:** Reach peak sustainable tension without disconnected bone motion.  
**Support:** Support and grip both active.  
**COM:** COM/force settle against resistance or approach release threshold.  
**Dynamics:** All segments remain linked; force capacity and fatigue bounded.  
**Interruptibility:** `false`

- **Pelvis:** Rearward/low.
- **Hindlimbs:** Strong support.
- **Feet Toes:** No skate.
- **Thorax Spine:** Engaged.
- **Neck Head:** Engaged.
- **Tail:** Counterbalance.
- **Jaw Throat:** Clamped.

#### `release_or_hold` — 0.72–0.84
**Goal:** Respond to external tissue release or continued resistance.  
**Support:** Branch dependent; support remains active.  
**COM:** Release causes sudden permitted rearward acceleration; hold causes stall, not fake motion.  
**Dynamics:** Carcass system emits TEAR_RELEASE; solver catches recoil. If resistance remains, motion stalls and grip may release.  
**Interruptibility:** `false`

- **Pelvis:** Catches release or holds tension.
- **Hindlimbs:** Compress on release; remain braced on hold.
- **Feet Toes:** Stay planted or take planned catch.
- **Thorax Spine:** Recoil on release.
- **Neck Head:** Brief rear acceleration then damping.
- **Tail:** Opposes recoil.
- **Jaw Throat:** Keeps food on success; opens on failed release.

#### `recover` — 0.84–1.00
**Goal:** Stabilize body and either raise food or return to carcass.  
**Support:** Stable final support.  
**COM:** COM returns to viable stance.  
**Dynamics:** Leg/pelvis catch precedes neck/head settling.  
**Interruptibility:** `partial`

- **Pelvis:** Recenters.
- **Hindlimbs:** Absorb.
- **Feet Toes:** Stable.
- **Thorax Spine:** Settles.
- **Neck Head:** Raises with food or returns.
- **Tail:** Damps.
- **Jaw Throat:** Branch state preserved.

### Events

```yaml
- name: CONTACT_BEGIN
  kind: point
  at: 0.0
- name: ANTICIPATION_START
  kind: point
  at: 0.1
- name: COMMIT_START
  kind: point
  at: 0.38
- name: CONTACT_PEAK
  kind: point
  at: 0.68
- name: TEAR_RELEASE
  kind: point
  phase: release_or_hold
  trigger: condition_resolved_at_runtime
- name: TARGET_RESISTED
  kind: condition
  phase: release_or_hold
- name: RECOVERY_START
  kind: point
  at: 0.84
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.38
  - 0.84
```

### Procedural channels

```yaml
carcass_attachment:
  enabled: true
resistance:
  enabled: true
  external_authority: true
foot_ik:
  enabled: true
friction:
  enabled: true
tail_balance:
  enabled: true
release_recoil:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- legs and pelvis initiate the pull
- jaw attachment remains consistent with target
- TEAR_RELEASE comes from carcass simulation, not fixed frame
- release recoil has continuous velocity and is caught by support
- failed pull visibly stalls and repositions rather than pretending success

---

## 20 — Swallow

**ID:** `tarbosaurus_swallow`  
**Program:** `feeding_interaction`  
**Category / priority:** `feeding` / `P1`  
**Duration envelope:** 1.0–2.3 s; target 1.6 s  
**Loop / root motion:** False / False

**Purpose.** Complete a small but readable food-processing event through head posture, jaw closure, throat transit, pause, and context-sensitive exit.

**Performance character.** Subtle and useful; communicates ingestion without cartoon gulping.

### Entry and exit

```yaml
entry:
  allowed:
  - feeding_process
  - tear_success_with_food
  requirements:
  - food state compatible with swallow
exit:
  allowed:
  - feeding
  - alert_idle
  - neutral_idle
  handoff: return gaze/attention and respiratory control after throat transit
```

### Phase progression

#### `raise_with_food` — 0.00–0.15
**Goal:** Raise the head enough to place food for processing.  
**Support:** Stable feeding stance.  
**COM:** COM shifts only as needed to counter head elevation.  
**Dynamics:** Neck leads slightly; thorax/pelvis rebalance.  
**Interruptibility:** `partial`

- **Pelvis:** Small forward shift.
- **Hindlimbs:** Maintain support.
- **Feet Toes:** Planted.
- **Thorax Spine:** Rises subtly.
- **Neck Head:** Raises to swallow angle.
- **Tail:** Tiny balance response.
- **Jaw Throat:** Food/jaw state maintained.

#### `jaw_manipulation` — 0.15–0.30
**Goal:** Position food and complete jaw closure.  
**Support:** Support unchanged.  
**COM:** COM stable.  
**Dynamics:** Small bounded jaw/head adjustments; no mammalian chew cycle.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Stable.
- **Neck Head:** Small positioning.
- **Tail:** Quiet.
- **Jaw Throat:** Jaw closes/manipulates.

#### `swallow_posture` — 0.30–0.45
**Goal:** Align head and cervical chain for throat transit.  
**Support:** Support stable.  
**COM:** COM stable.  
**Dynamics:** Cervical chain lengthens/adjusts slightly; breathing yields.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Thorax Spine:** Restrained breath.
- **Neck Head:** Swallow alignment.
- **Tail:** Quiet.
- **Jaw Throat:** Throat prepared.

#### `throat_transit` — 0.45–0.68
**Goal:** Move a subtle throat deformation downward through the cervical base.  
**Support:** Support unchanged.  
**COM:** No meaningful COM change.  
**Dynamics:** Sequential throat/cervical-base deformation indicates transit; jaw remains closed.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Breathing briefly interrupted.
- **Neck Head:** Mostly still.
- **Tail:** Still.
- **Jaw Throat:** Visible but restrained top-to-bottom throat motion.

#### `post_swallow_pause` — 0.68–0.82
**Goal:** Hold a brief physiological pause.  
**Support:** Stable stance.  
**COM:** COM stable.  
**Dynamics:** No immediate return to repeated feeding; breath resumes after pause.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Thorax Spine:** Breathing resumes late.
- **Neck Head:** Holds.
- **Tail:** Quiet.
- **Jaw Throat:** Transit complete.

#### `jaw_relax` — 0.82–0.92
**Goal:** Relax jaw and throat to living-neutral.  
**Support:** Support unchanged.  
**COM:** Stable.  
**Dynamics:** Small tissue settling only.  
**Interruptibility:** `true`

- **Neck Head:** Minor settle.
- **Jaw Throat:** Returns to calibrated closure.

#### `context_exit` — 0.92–1.00
**Goal:** Return to carcass or raise attention according to context.  
**Support:** Handoff support preserved.  
**COM:** State continuous.  
**Dynamics:** Gaze and head path branch without reset.  
**Interruptibility:** `true`

- **Pelvis:** Handoff.
- **Hindlimbs:** Handoff.
- **Feet Toes:** Handoff.
- **Thorax Spine:** Handoff.
- **Neck Head:** Feeding or alert branch.
- **Tail:** Handoff.
- **Jaw Throat:** Neutral.

### Events

```yaml
- name: JAW_CLOSE
  kind: point
  at: 0.3
- name: CONTACT_BEGIN
  kind: point
  at: 0.45
  note: swallow transit begins
- name: CONTACT_END
  kind: point
  at: 0.68
  note: swallow transit ends
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.68
  - 1.0
```

### Procedural channels

```yaml
food_state:
  required: true
throat_deformation:
  enabled: true
  direction: cranial_to_caudal
breathing:
  enabled: true
  masked_during_transit: true
gaze:
  enabled: true
  after: 0.82
foot_ik:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- throat motion remains subtle and directional
- breathing pauses during transit then resumes
- jaw closes before throat transit
- no repetitive cartoon gulp
- exit supports feeding or alert context without pose reset

---

## 21 — Drink

**ID:** `tarbosaurus_drink`  
**Program:** `feeding_interaction`  
**Category / priority:** `survival_interaction` / `P1`  
**Duration envelope:** 6.0–12.0 s; target 8.5 s  
**Loop / root motion:** False / False

**Purpose.** Approach a runtime water surface from stable support, lower the body and cervical chain, drink with subtle throat/jaw behavior, pause, raise, and rebalance.

**Performance character.** Careful and vulnerable; the large head moving low materially changes support and attention.

### Entry and exit

```yaml
entry:
  allowed:
  - idle_at_water_edge
  - walk_stop_at_water
  requirements:
  - water surface height/normal known
  - bank support and head corridor feasible
exit:
  allowed:
  - neutral_idle
  - alert_idle
  - walk_start
  handoff: preserve shoreline support, wetness state, gaze, and final swallow
```

### Phase progression

#### `inspect_water` — 0.00–0.10
**Goal:** Look down and verify the water surface and shoreline geometry.  
**Support:** Stable standing support.  
**COM:** COM remains stable.  
**Dynamics:** Head/eyes locate runtime surface; planner checks reach and collision.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Ready.
- **Feet Toes:** Planted above shoreline.
- **Thorax Spine:** Small downward orientation.
- **Neck Head:** Looks to surface without overflexing final neck joint.
- **Tail:** Quiet.
- **Jaw Throat:** Closed.

#### `stabilize_stance` — 0.10–0.22
**Goal:** Adjust support before lowering the head.  
**Support:** Bilateral, slightly offset/wider stance.  
**COM:** COM shifts rearward enough to counter forward/down head moment.  
**Dynamics:** Feet adjust before neck descent; substrate friction and mud limits apply.  
**Interruptibility:** `partial`

- **Pelvis:** Retracts/centers.
- **Hindlimbs:** Increase flexion.
- **Feet Toes:** Adjustment follows contact states; soft-ground penetration bounded.
- **Thorax Spine:** Prepares descent.
- **Neck Head:** Maintains water target.
- **Tail:** Balances rearward shift.

#### `progressive_lowering` — 0.22–0.40
**Goal:** Lower thorax, cervical base, middle neck, and skull toward the water surface.  
**Support:** Both feet loaded.  
**COM:** COM descends/retracts inside support.  
**Dynamics:** Lowering is shared; water height drives endpoint.  
**Interruptibility:** `partial`

- **Pelvis:** Lowers modestly.
- **Hindlimbs:** Flex under load.
- **Feet Toes:** Planted.
- **Thorax Spine:** Distributed downward pitch.
- **Neck Head:** Progressive reach to surface.
- **Tail:** Adjusts upward/rearward slightly.
- **Forelimbs:** Follow thorax.
- **Jaw Throat:** Begins drinking posture.

#### `snout_water_contact` — 0.40–0.47
**Goal:** Enter the water surface without overshoot or bank/ground penetration.  
**Support:** Stable stance.  
**COM:** COM controlled.  
**Dynamics:** Snout target IK and collision constrain entry; ripple/audio event emitted.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Fixed.
- **Thorax Spine:** Holds.
- **Neck Head:** Fine vertical adjustment to surface.
- **Tail:** Balances.
- **Jaw Throat:** Mouth reaches drinking configuration.

#### `drinking_pulses` — 0.47–0.68
**Goal:** Perform a bounded series of drinking pulses at the runtime surface.  
**Support:** Support unchanged.  
**COM:** COM nearly fixed.  
**Dynamics:** Subtle jaw/throat motion and tiny head corrections; respiratory timing changes.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Pressure corrections only.
- **Feet Toes:** Planted.
- **Thorax Spine:** Breathing interrupted/reduced around drinking pulses.
- **Neck Head:** Maintains surface with millimetric corrections.
- **Tail:** Nearly still.
- **Jaw Throat:** Small non-mammalian-assumption-neutral drinking motions; exact reconstruction remains gameplay interpretation.

#### `water_pause` — 0.68–0.76
**Goal:** Pause at the surface to listen/look without immediately raising.  
**Support:** Same support.  
**COM:** COM stable.  
**Dynamics:** Drinking stops; head remains low; attention may interrupt at this window.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Breathing resumes slightly.
- **Neck Head:** Low vigilant pause.
- **Tail:** Quiet.
- **Jaw Throat:** Drinking motion stops.

#### `raise_and_rebalance` — 0.76–0.92
**Goal:** Exit water and raise head gradually while COM returns forward/central.  
**Support:** Both feet remain support.  
**COM:** COM shifts forward/up smoothly.  
**Dynamics:** Neck initiates; thorax follows; pelvis rebalances; no upward snap.  
**Interruptibility:** `partial`

- **Pelvis:** Moves forward/up.
- **Hindlimbs:** Extend without locking.
- **Feet Toes:** Planted.
- **Thorax Spine:** Rises after neck begins.
- **Neck Head:** Clears surface and raises.
- **Tail:** Returns toward neutral.
- **Forelimbs:** Settle.
- **Jaw Throat:** Water-exit and pre-swallow state.

#### `post_drink_swallow` — 0.92–1.00
**Goal:** Complete optional throat motion and enter idle/alert.  
**Support:** Stable standing support.  
**COM:** COM stable and handoff-compatible.  
**Dynamics:** Subtle swallow; gaze branch selected.  
**Interruptibility:** `true`

- **Pelvis:** Handoff.
- **Hindlimbs:** Handoff.
- **Feet Toes:** Handoff.
- **Thorax Spine:** Breathing normalizes.
- **Neck Head:** Neutral or alert branch.
- **Tail:** Handoff.
- **Jaw Throat:** Small swallow then living-neutral.

### Events

```yaml
- name: SNOUT_WATER_ENTER
  kind: point
  at: 0.4
- name: DRINK_START
  kind: point
  at: 0.47
- name: DRINK_STOP
  kind: point
  at: 0.68
- name: SNOUT_WATER_EXIT
  kind: point
  at: 0.76
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.47
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 0.22
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.68
  - 1.0
```

### Procedural channels

```yaml
water_surface_ik:
  enabled: true
  height_and_normal: true
snout_collision:
  enabled: true
ripples_audio:
  events: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
  soft_ground: true
breathing:
  enabled: true
  drinking_mask: true
gaze:
  enabled: true
  pause_window: true
tail_balance:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- snout contact follows runtime water height
- feet remain stable on bank/substrate
- body lowering is shared across pelvis/thorax/neck
- drinking pulses do not become cartoon lapping
- head raise has no snap
- water events align with measured surface crossing

---

## 22 — Lie down

**ID:** `tarbosaurus_lie_down`  
**Program:** `ground_posture`  
**Category / priority:** `posture_transition` / `P1`  
**Duration envelope:** 5.0–10.0 s; target 6.8 s  
**Loop / root motion:** False / True

**Purpose.** Transfer a multi-ton biped from standing foot support into a configured resting support arrangement without teleporting the pelvis or collapsing casually.

**Performance character.** Careful, deliberate, and balance-conscious; resting posture is an explicit gameplay reconstruction with uncertainty, not claimed fossil certainty.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - wounded_idle
  requirements:
  - rest area collision-clear
  - terrain slope and support compatible
  - rest pose variant selected
exit:
  allowed:
  - rest_lying_loop
  handoff: all ground/body contacts and breathing state match resting loop
```

### Phase progression

#### `standing_assessment` — 0.00–0.10
**Goal:** Become still and evaluate the chosen resting side and terrain.  
**Support:** Both feet planted.  
**COM:** COM centers and velocity approaches zero.  
**Dynamics:** Head lowers slightly; secondary motion damps.  
**Interruptibility:** `true`

- **Pelvis:** Centers.
- **Hindlimbs:** Balanced flexion.
- **Feet Toes:** Planted.
- **Thorax Spine:** Still.
- **Neck Head:** Lowers slightly to inspect.
- **Tail:** Settles.
- **Forelimbs:** Close.

#### `reposition_first_foot` — 0.10–0.22
**Goal:** Move one foot into the configured descent geometry.  
**Support:** Opposite foot becomes principal support.  
**COM:** COM shifts over support foot before repositioning.  
**Dynamics:** Selected foot unloads, steps, and recontacts; loaded foot does not pivot.  
**Interruptibility:** `partial`

- **Pelvis:** Shifts over support.
- **Hindlimbs:** One supports, one repositions.
- **Feet Toes:** Explicit unload/toe-off/contact.
- **Thorax Spine:** Balances.
- **Neck Head:** Counterbalances direction.
- **Tail:** Opposes pelvis shift.

#### `lowering_begins` — 0.22–0.38
**Goal:** Reduce pelvis height through hip/knee flexion while maintaining control.  
**Support:** Both feet or staged support according to pose variant.  
**COM:** COM descends inside current capture region.  
**Dynamics:** Hindlimbs eccentrically absorb; head/tail adjust to keep balance.  
**Interruptibility:** `false`

- **Pelvis:** Descends and may translate toward resting side.
- **Hindlimbs:** Flex deeply within limits.
- **Feet Toes:** Loaded contacts stable.
- **Thorax Spine:** Preserves horizontal mass.
- **Neck Head:** Moves to counterbalance.
- **Tail:** Changes vertical posture and approaches ground corridor.

#### `first_ground_support` — 0.38–0.52
**Goal:** Establish the first non-foot body/limb support contact.  
**Support:** Feet plus configured lower-limb/pelvic-side contact.  
**COM:** COM transitions toward expanded support set.  
**Dynamics:** Contact is measured and load ramps; no pelvis teleport.  
**Interruptibility:** `false`

- **Pelvis:** Approaches first contact.
- **Hindlimbs:** One side folds/contacts according to variant.
- **Feet Toes:** Remain support until load transfer is real.
- **Thorax Spine:** Begins controlled rotation.
- **Neck Head:** Protects and balances.
- **Tail:** May make first terrain contact.

#### `pelvis_to_ground` — 0.52–0.66
**Goal:** Transfer substantial body weight into pelvic/body support.  
**Support:** Mixed feet, folded limb, pelvis/body, and tail contacts.  
**COM:** COM descends and shifts toward resting support.  
**Dynamics:** Contact loads ramp continuously; feet unload in sequence.  
**Interruptibility:** `false`

- **Pelvis:** Makes controlled ground approach/contact.
- **Hindlimbs:** Fold and unload without clipping.
- **Feet Toes:** Release only after body support is established.
- **Thorax Spine:** Rotates carefully.
- **Neck Head:** Moves opposite body roll.
- **Tail:** Slides/settles only within contact rules.

#### `torso_settle` — 0.66–0.78
**Goal:** Bring thorax and body mass into final supported orientation.  
**Support:** Pelvis/body/folded hindlimb/tail support.  
**COM:** COM lowers into final support polygon/hull.  
**Dynamics:** Torso contact is damped; avoid sudden impact.  
**Interruptibility:** `false`

- **Pelvis:** Supported.
- **Hindlimbs:** Folded/positioning.
- **Feet Toes:** No longer primary support unless variant keeps one planted.
- **Thorax Spine:** Settles onto configured side/ventral support.
- **Neck Head:** Held clear.
- **Tail:** Terrain-aware contact.

#### `final_leg_positioning` — 0.78–0.90
**Goal:** Finish folding/repositioning limbs after most mass is supported.  
**Support:** Body contacts carry the animal.  
**COM:** COM changes minimally.  
**Dynamics:** Legs move under low load; collision and comfort limits dominate.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Complete fold with no mesh intersection.
- **Feet Toes:** Settle naturally.
- **Thorax Spine:** Stable.
- **Neck Head:** Still counterbalancing.
- **Tail:** Settle.

#### `head_neck_settle` — 0.90–1.00
**Goal:** Lower neck/head into resting-ready posture and close all contact derivatives.  
**Support:** Final resting support set.  
**COM:** COM stable; velocities seam-compatible with rest loop.  
**Dynamics:** Head settles last; breathing expands into rest pattern.  
**Interruptibility:** `true`

- **Pelvis:** Rest state.
- **Hindlimbs:** Rest state.
- **Feet Toes:** Rest state.
- **Thorax Spine:** Rest state breathing begins.
- **Neck Head:** Resting height, still able to attend.
- **Tail:** Nearly still.
- **Forelimbs:** Rest state.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.1
- name: COMMIT_START
  kind: point
  at: 0.22
- name: CONTACT_BEGIN
  kind: point
  at: 0.38
- name: CONTACT_PEAK
  kind: point
  at: 0.66
- name: CONTACT_END
  kind: point
  at: 0.9
- name: RECOVERY_START
  kind: point
  at: 0.78
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.22
  - 0.78
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.78
  - 1.0
```

### Procedural channels

```yaml
rest_pose_variant:
  required: true
body_contact_solver:
  enabled: true
terrain_alignment:
  enabled: true
collision:
  enabled: true
foot_ik:
  enabled: true
tail_ground_contact:
  enabled: true
injury:
  enabled: true
  may_select_side: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- pelvis path is continuous and never teleports
- first body contact and load transfer are measured
- feet unload only after alternative support exists
- all body/head/tail terrain penetrations forbidden
- rest pose is labeled gameplay interpretation
- endpoint matches rest loop contacts and breathing

---

## 23 — Rest / lying loop

**ID:** `tarbosaurus_rest_lying_loop`  
**Program:** `ground_posture`  
**Category / priority:** `state` / `P1`  
**Duration envelope:** 8.0–16.0 s; target 10.0 s  
**Loop / root motion:** True / False

**Purpose.** Maintain a fully supported resting animal with breathing, rare attention, gradual relaxation, alertness layering, and injury-side options.

**Performance character.** Quiet enough to feel genuinely at rest; most motion is respiratory or rare, and the tail is almost stationary.

### Entry and exit

```yaml
entry:
  allowed:
  - lie_down_complete
  - resting_alert_transition
  requirements:
  - final body contact set resolved
exit:
  allowed:
  - rise_to_standing
  - resting_alert
  - death_from_rest
  handoff: preserve contact set, breathing phase, head height, and injury side
```

### Phase progression

#### `supported_rest` — 0.00–0.22
**Goal:** Hold the configured body, folded-limb, and tail support arrangement.  
**Support:** Body/pelvis/folded hindlimbs/tail contacts fixed.  
**COM:** COM rests inside the final support hull.  
**Dynamics:** No locomotor correction unless contact pressure drifts outside tolerance.  
**Interruptibility:** `true`

- **Pelvis:** Fully supported.
- **Hindlimbs:** Folded/relaxed.
- **Feet Toes:** Resting contact.
- **Thorax Spine:** Relaxed posture.
- **Neck Head:** Comfortable held position.
- **Tail:** Grounded/nearly still.
- **Forelimbs:** Relaxed close.

#### `deep_breath` — 0.22–0.45
**Goal:** Show relaxed volume change more visibly than standing idle.  
**Support:** Contact set unchanged.  
**COM:** COM movement remains very small.  
**Dynamics:** Thorax/abdomen expand against ground and gravity; cervical base follows subtly.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Thorax Spine:** Visible relaxed breath with contact-aware deformation.
- **Neck Head:** Small response.
- **Tail:** No wag.
- **Jaw Throat:** Relaxed airway motion.

#### `small_head_adjustment` — 0.45–0.60
**Goal:** Perform one rare head/neck comfort or attention correction.  
**Support:** Body support unchanged.  
**COM:** COM remains in support.  
**Dynamics:** Neck redistributes support; skull movement is slow and bounded.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Thorax Spine:** Tiny counter-response.
- **Neck Head:** Small lift/turn/settle; runtime alertness controls amplitude.
- **Tail:** Still.
- **Forelimbs:** Still.

#### `relaxation_drift` — 0.60–0.82
**Goal:** Allow head height and muscle tone to lower slightly for deeper rest.  
**Support:** Contacts stable.  
**COM:** COM settles marginally.  
**Dynamics:** Damped, one-way relaxation rather than cyclic bob.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Hindlimbs:** Relaxed.
- **Thorax Spine:** Tone reduces.
- **Neck Head:** Head lowers a small amount.
- **Tail:** Settled.
- **Jaw Throat:** Jaw may relax slightly within safe closure.

#### `breath_and_loop_close` — 0.82–1.00
**Goal:** Return respiratory, head, tail, and contact states to a loop-safe continuation.  
**Support:** Same support set.  
**COM:** COM and derivatives close.  
**Dynamics:** Aperiodic overlays use seeded longer sequences so the nominal loop seam is not perceptible.  
**Interruptibility:** `true`

- **Pelvis:** Seam-compatible.
- **Hindlimbs:** Seam-compatible.
- **Thorax Spine:** Breath closes.
- **Neck Head:** State closes.
- **Tail:** Angle/velocity close.
- **Forelimbs:** State closes.
- **Jaw Throat:** State closes.

### Events

```yaml
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.44
  - 0.62
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 1.0
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
breathing:
  enabled: true
  rest_amplitude: true
alertness:
  enabled: true
  range:
  - deep_rest
  - resting
  - resting_alert
gaze:
  enabled: true
  rare: true
blink:
  enabled: true
injury:
  enabled: true
  favored_side: true
contact_solver:
  enabled: true
tail_balance:
  enabled: false
  ground_settle_only: true
variation:
  enabled: true
  long_seeded_sequence: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- tail remains nearly stationary
- head adjustments are rare and non-rhythmic
- breathing respects ground contacts
- alertness overlay does not require standing
- loop seam invisible in contact, breath, and head derivatives

---

## 24 — Rise to standing

**ID:** `tarbosaurus_rise_to_standing`  
**Program:** `ground_posture`  
**Category / priority:** `posture_transition` / `P1`  
**Duration envelope:** 4.0–8.5 s; target 5.8 s  
**Loop / root motion:** False / True

**Purpose.** Generate a separate effortful rise program that unfolds hindlimbs, establishes reliable foot contacts, lifts the pelvis, corrects stance, and settles.

**Performance character.** Powerful and deliberate; perceptually different from lie-down played backward.

### Entry and exit

```yaml
entry:
  allowed:
  - rest_lying_loop
  - resting_alert
  requirements:
  - standing corridor clear
  - terrain and injury permit selected rise side
exit:
  allowed:
  - neutral_idle
  - alert_idle
  - walk_start
  handoff: final foot contacts, COM, tail, breathing, and support bias exact
```

### Phase progression

#### `head_up_first` — 0.00–0.10
**Goal:** Raise the head and restore attention before loading limbs.  
**Support:** Resting body contacts.  
**COM:** COM changes minimally.  
**Dynamics:** Neck/head lift creates room and begins counterbalance.  
**Interruptibility:** `true`

- **Pelvis:** Grounded.
- **Hindlimbs:** Folded.
- **Feet Toes:** Resting.
- **Thorax Spine:** Begins activation.
- **Neck Head:** Raises first.
- **Tail:** Grounded.
- **Forelimbs:** Close.

#### `prepare_body` — 0.10–0.22
**Goal:** Rotate/shift torso and pelvis into an advantageous push geometry.  
**Support:** Body and limb contacts remain.  
**COM:** COM shifts toward future first foot contact.  
**Dynamics:** Thorax/pelvis reposition; tail contact assists only within configured support role.  
**Interruptibility:** `partial`

- **Pelvis:** Shifts/rotates.
- **Hindlimbs:** Begin unfolding.
- **Feet Toes:** One foot approaches planting geometry.
- **Thorax Spine:** Aligns for rise.
- **Neck Head:** Counterbalances.
- **Tail:** Slides/loads only if allowed.

#### `first_foot_engagement` — 0.22–0.34
**Goal:** Establish one reliable hindfoot/toe patch on terrain.  
**Support:** Body contacts plus first planted foot.  
**COM:** COM remains supported by mixed contacts.  
**Dynamics:** Foot reaches, contacts, and ramps load before major lift.  
**Interruptibility:** `false`

- **Pelvis:** Still low.
- **Hindlimbs:** First leg unfolds into load-bearing flexion.
- **Feet Toes:** Measured contact/load.
- **Thorax Spine:** Prepared.
- **Neck Head:** Counterbalance.
- **Tail:** Ground contact persists.

#### `push_initiation` — 0.34–0.48
**Goal:** Begin lifting torso/pelvis using first leg and body support.  
**Support:** First foot plus body/tail contacts.  
**COM:** COM rises and moves toward the first foot.  
**Dynamics:** Hip/knee extension produces upward/forward impulse; head moves to balance.  
**Interruptibility:** `false`

- **Pelvis:** Begins rise.
- **Hindlimbs:** First leg drives.
- **Feet Toes:** Loaded and fixed.
- **Thorax Spine:** Rises after pelvis starts.
- **Neck Head:** Counterbalances.
- **Tail:** Begins unloading.

#### `second_foot_engagement` — 0.48–0.60
**Goal:** Plant the second hindfoot before full extension.  
**Support:** Both feet plus residual body contact.  
**COM:** COM moves into bilateral support.  
**Dynamics:** Second foot contact ramps; body contact unloads.  
**Interruptibility:** `false`

- **Pelvis:** Rises/centers.
- **Hindlimbs:** Second leg accepts load.
- **Feet Toes:** Second contact measured.
- **Thorax Spine:** Continues rise.
- **Neck Head:** Stabilizes.
- **Tail:** Unloads ground.

#### `powerful_extension` — 0.60–0.74
**Goal:** Lift pelvis and torso using both hindlimbs.  
**Support:** Both feet loaded; body contacts release.  
**COM:** COM rises into standing height with continuous velocity.  
**Dynamics:** Hip/knee/ankle extension shared bilaterally; no knee snap.  
**Interruptibility:** `false`

- **Pelvis:** Primary upward rise.
- **Hindlimbs:** Powerful extension while retaining flexion.
- **Feet Toes:** Planted.
- **Thorax Spine:** Follows and approaches horizontal.
- **Neck Head:** Stabilizes heavy head.
- **Tail:** Lifts from ground and resumes counterbalance.

#### `near_standing` — 0.74–0.84
**Goal:** Reach standing height without locking joints.  
**Support:** Both feet support.  
**COM:** COM settles near standing support center.  
**Dynamics:** Extension decelerates; body inertia continues and is absorbed.  
**Interruptibility:** `partial`

- **Pelvis:** Near standing.
- **Hindlimbs:** Flexed, not locked.
- **Feet Toes:** Stable.
- **Thorax Spine:** Horizontalizes.
- **Neck Head:** Settles.
- **Tail:** Damps.

#### `corrective_step` — 0.84–0.94
**Goal:** Take at least one small support correction when required.  
**Support:** One foot remains support; other may reposition.  
**COM:** COM shifts before foot release and recenters after contact.  
**Dynamics:** Corrective placement resolves asymmetry from rising.  
**Interruptibility:** `partial`

- **Pelvis:** Shifts over support.
- **Hindlimbs:** One small step.
- **Feet Toes:** Explicit release/contact.
- **Thorax Spine:** Balances.
- **Neck Head:** Stable.
- **Tail:** Counters.

#### `standing_settle` — 0.94–1.00
**Goal:** Enter idle/alert with stable contacts and breathing.  
**Support:** Bilateral standing support.  
**COM:** COM velocity reaches target state.  
**Dynamics:** Pelvis, head, and tail settle in causal order.  
**Interruptibility:** `true`

- **Pelvis:** Idle-compatible.
- **Hindlimbs:** Idle-compatible.
- **Feet Toes:** Planted.
- **Thorax Spine:** Breathing resumes.
- **Neck Head:** Neutral/alert branch.
- **Tail:** Settles.
- **Forelimbs:** Close.

### Events

```yaml
- name: ANTICIPATION_START
  kind: point
  at: 0.1
- name: L_FOOT_CONTACT
  kind: point
  phase: first_foot_engagement
  trigger: condition_resolved_at_runtime
- name: R_FOOT_CONTACT
  kind: point
  phase: first_foot_engagement
  trigger: condition_resolved_at_runtime
- name: COMMIT_START
  kind: point
  at: 0.34
- name: CONTACT_BEGIN
  kind: point
  at: 0.22
  note: first reliable foot engagement
- name: CONTACT_PEAK
  kind: point
  at: 0.66
  note: maximum rise support demand
- name: RECOVERY_START
  kind: point
  at: 0.84
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.34
  - 0.74
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.74
  - 1.0
```

### Procedural channels

```yaml
rest_pose_variant:
  required: true
foot_ik:
  enabled: true
body_contact_solver:
  enabled: true
terrain_alignment:
  enabled: true
tail_ground_contact:
  enabled: true
injury:
  enabled: true
  selects_first_leg: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- not generated by reversing lie-down
- reliable first foot contact precedes major lift
- second foot loads before full extension
- knees remain flexed near standing
- body and tail ground contacts release continuously
- corrective step follows COM shift

---

## 25 — Wounded idle

**ID:** `tarbosaurus_wounded_idle`  
**Program:** `stationary_support`  
**Category / priority:** `condition_state` / `P0`  
**Duration envelope:** 5.0–10.0 s; target 7.0 s  
**Loop / root motion:** True / False

**Purpose.** Provide an injury reference state whose support, pelvis, spine, tail, breathing, guarding, and pain events can be continuously parameterized at runtime.

**Performance character.** Animal pain and fatigue rather than human melodrama; injury is visible in mechanics and decision readiness.

### Entry and exit

```yaml
entry:
  allowed:
  - injury_event
  - walk_stop_injured
  - combat_recovery
  requirements:
  - injury side, site, severity, pain, fatigue, and blood-loss inputs
exit:
  allowed:
  - wounded_walk_start
  - neutral_idle_if_recovered
  - lie_down
  - stumble
  handoff: preserve injured-side loading limits and breathing
```

### Phase progression

#### `guarded_support` — 0.00–0.20
**Goal:** Establish a stable asymmetric stance favoring the healthy side.  
**Support:** Healthy-side principal support; injured foot may remain in light contact.  
**COM:** COM shifts toward healthy support while remaining inside bilateral/healthy patch envelope.  
**Dynamics:** Pelvis translation/tilt and joint guarding reflect injury site.  
**Interruptibility:** `true`

- **Pelvis:** Shifted toward healthy side with bounded tilt.
- **Hindlimbs:** Healthy leg bears most load; injured joint guarded, never generically limp for all injuries.
- **Feet Toes:** Injured foot contact pressure reduced according to site/severity.
- **Thorax Spine:** Compensates mildly for pelvis asymmetry.
- **Neck Head:** May lower with pain/fatigue.
- **Tail:** Offsets asymmetric balance.
- **Forelimbs:** Quiet.
- **Jaw Throat:** Breathing more visible.

#### `pain_breath` — 0.20–0.38
**Goal:** Show elevated respiratory cost and guarded muscle tone.  
**Support:** Support unchanged.  
**COM:** COM stable.  
**Dynamics:** Breathing rate/amplitude responds to pain/fatigue without whole-body bounce.  
**Interruptibility:** `true`

- **Pelvis:** Stable guarded.
- **Hindlimbs:** Maintain asymmetry.
- **Feet Toes:** No slide.
- **Thorax Spine:** Higher respiratory motion.
- **Neck Head:** Small fatigue response.
- **Tail:** Quiet balance.
- **Jaw Throat:** Throat/flank exertion.

#### `cautious_unload` — 0.38–0.54
**Goal:** Periodically reduce injured-limb pressure before discomfort accumulates.  
**Support:** Healthy support increases; injured foot unloads but need not leave ground.  
**COM:** COM moves farther over healthy side.  
**Dynamics:** Pelvis shift precedes pressure reduction.  
**Interruptibility:** `true`

- **Pelvis:** Moves toward healthy leg.
- **Hindlimbs:** Injured leg flexes/guards.
- **Feet Toes:** Injured contact pressure falls; witness may remain touching.
- **Thorax Spine:** Counterbalances.
- **Neck Head:** Brief pain attention possible.
- **Tail:** Stronger asymmetry correction.

#### `injured_reposition` — 0.54–0.70
**Goal:** Make a small cautious injured-foot reposition when configured.  
**Support:** Healthy foot sole support; injured foot unloads→toe_off→short step.  
**COM:** COM remains over healthy support.  
**Dynamics:** Short reach and slow contact reduce impact.  
**Interruptibility:** `conditional`

- **Pelvis:** Stable over healthy side.
- **Hindlimbs:** Injured leg moves carefully.
- **Feet Toes:** Short clearance and cautious recontact.
- **Thorax Spine:** Minimal movement.
- **Neck Head:** Pain/fatigue response bounded.
- **Tail:** Balances single support.

#### `pain_event_optional` — 0.70–0.82
**Goal:** Allow a rare brief pain/tension event without anthropomorphic acting.  
**Support:** Support remains safe.  
**COM:** COM remains viable.  
**Dynamics:** Momentary muscle tension, shortened breath, or head reaction; no roaring by default.  
**Interruptibility:** `true`

- **Pelvis:** Small tension.
- **Hindlimbs:** Guard.
- **Feet Toes:** Stable.
- **Thorax Spine:** Brief stiffness.
- **Neck Head:** Small involuntary reaction.
- **Tail:** Small counter-response.
- **Jaw Throat:** Breath catches briefly.

#### `guarded_loop_close` — 0.82–1.00
**Goal:** Return to the reference guarded stance with loop-safe derivatives.  
**Support:** Healthy-biased support.  
**COM:** COM, breath, and tail states close.  
**Dynamics:** Aperiodic runtime variation prevents exact repetitive pain pattern.  
**Interruptibility:** `true`

- **Pelvis:** Seam-compatible.
- **Hindlimbs:** Seam-compatible.
- **Feet Toes:** Continuous.
- **Thorax Spine:** Breath closes.
- **Neck Head:** State closes.
- **Tail:** Closes.
- **Jaw Throat:** Closes.

### Events

```yaml
- name: INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 1.0
- name: L_FOOT_CONTACT
  kind: point
  phase: injured_reposition
  trigger: condition_resolved_at_runtime
- name: R_FOOT_CONTACT
  kind: point
  phase: injured_reposition
  trigger: condition_resolved_at_runtime
- name: LOOP_SAFE
  kind: point
  at: 1.0
```

### Procedural channels

```yaml
injury:
  enabled: true
  dimensions:
  - side
  - site
  - severity
  - pain
  - fatigue
  - blood_loss
  - confidence
foot_ik:
  enabled: true
breathing:
  enabled: true
  pain_scaled: true
tail_balance:
  enabled: true
gaze:
  enabled: true
variation:
  enabled: true
  pain_events_rare: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- injury mechanics depend on site and side rather than one generic limp
- healthy-side support shift precedes injured unload
- pelvis/spine/tail compensate coherently
- pain events remain rare and restrained
- loop does not repeat a conspicuous pain beat at a fixed cadence

---

## 26 — Stumble

**ID:** `tarbosaurus_stumble`  
**Program:** `recovery_failure`  
**Category / priority:** `failure_recovery` / `P0`  
**Duration envelope:** 1.2–3.2 s; target 2.1 s  
**Loop / root motion:** False / True

**Purpose.** Create a recoverable support failure from bad footing, collision, injury, missed attack, or fatigue, with a real pelvis drop, emergency tail response, catch step, and continue/stop/fall branch.

**Performance character.** Initially unpolished and involuntary, then powerfully corrected; one of the rare cases where larger tail motion is justified.

### Entry and exit

```yaml
entry:
  allowed:
  - walk
  - fast_walk
  - run
  - sprint
  - bite_miss_recovery
  - injured_motion
  requirements:
  - failure side/type, incoming momentum, terrain, and available support known
exit:
  allowed:
  - continue_locomotion
  - run_stop
  - wounded_idle
  - collapse
  handoff: outcome chosen from recovery feasibility, not predetermined by clip
```

### Phase progression

#### `normal_incoming_motion` — 0.00–0.10
**Goal:** Preserve the exact motion state before failure.  
**Support:** Incoming contact schedule.  
**COM:** COM/root velocity and angular momentum unchanged.  
**Dynamics:** No anticipation telegraph unless trigger itself provides one.  
**Interruptibility:** `partial`

- **Pelvis:** Incoming.
- **Hindlimbs:** Incoming.
- **Feet Toes:** Incoming.
- **Thorax Spine:** Incoming.
- **Neck Head:** Incoming.
- **Tail:** Incoming.

#### `unexpected_support_failure` — 0.10–0.22
**Goal:** Remove or reduce expected support abruptly according to the trigger.  
**Support:** One foot slips, lands poorly, or cannot carry expected load.  
**COM:** COM continues while support wrench collapses or shifts.  
**Dynamics:** Failed contact is measured; body cannot pre-compensate perfectly.  
**Interruptibility:** `false`

- **Pelvis:** Begins response after failure.
- **Hindlimbs:** Failing leg yields/slips.
- **Feet Toes:** Failure geometry explicit.
- **Thorax Spine:** Still follows incoming momentum.
- **Neck Head:** Begins reflex response.
- **Tail:** Response starts after failure.

#### `pelvis_drop` — 0.22–0.36
**Goal:** Show immediate mass response toward the failing side.  
**Support:** Remaining support overloaded.  
**COM:** COM drops/laterally escapes current support relation.  
**Dynamics:** Pelvis falls before a polished recovery pose; torso rotates and head counters.  
**Interruptibility:** `false`

- **Pelvis:** Drops and rolls toward failure.
- **Hindlimbs:** Remaining leg compresses.
- **Feet Toes:** Support foot fixed if friction holds.
- **Thorax Spine:** Rotates with lag.
- **Neck Head:** Moves opposite/downstream to protect balance.
- **Tail:** Accelerates into emergency counter-motion.

#### `tail_emergency_correction` — 0.36–0.48
**Goal:** Use a noticeable but bounded tail and torso counteraction while selecting a catch foot.  
**Support:** Remaining support active; catch foot unloads/moves.  
**COM:** Angular momentum redistributes; COM still needs a new contact.  
**Dynamics:** Tail cannot solve translational capture alone; it buys orientation/time.  
**Interruptibility:** `false`

- **Pelvis:** Continues but begins arrest.
- **Hindlimbs:** Catch leg rapidly folds/reaches.
- **Feet Toes:** Catch foot clears terrain.
- **Thorax Spine:** Counter-rotates.
- **Neck Head:** Stabilizes.
- **Tail:** Largest permitted non-contact tail response, then damping begins.

#### `recovery_foot_placement` — 0.48–0.64
**Goal:** Place the opposite/reachable foot to broaden support.  
**Support:** Catch foot approaching→contact→loading.  
**COM:** Extrapolated COM enters new capture region if recovery is feasible.  
**Dynamics:** Foot placement derives from momentum, reach, terrain, friction, and injury.  
**Interruptibility:** `false`

- **Pelvis:** Moves toward catch.
- **Hindlimbs:** Catch leg reaches.
- **Feet Toes:** Decisive contact; no teleport.
- **Thorax Spine:** Still correcting.
- **Neck Head:** Protective orientation.
- **Tail:** Opposes residual rotation.

#### `body_catch` — 0.64–0.78
**Goal:** Absorb momentum strongly through the catch leg and pelvis.  
**Support:** Catch foot loaded; second support may re-establish.  
**COM:** COM velocity decreases/redirects continuously.  
**Dynamics:** Leg compression is pronounced; pelvis/torso/head rebound in sequence.  
**Interruptibility:** `false`

- **Pelvis:** Compresses.
- **Hindlimbs:** Catch leg flexes under high load.
- **Feet Toes:** Loaded and fixed within substrate tolerance.
- **Thorax Spine:** Rebound delayed.
- **Neck Head:** Rebounds after body stabilizes.
- **Tail:** Damps.

#### `head_neck_rebound` — 0.78–0.88
**Goal:** Allow head/neck to return after primary support is restored.  
**Support:** Stable or stabilizing support.  
**COM:** COM near viable state.  
**Dynamics:** Cervical chain follows torso recovery rather than leading.  
**Interruptibility:** `partial`

- **Pelvis:** Stabilizing.
- **Hindlimbs:** Stabilizing.
- **Feet Toes:** Stable.
- **Thorax Spine:** Settles.
- **Neck Head:** Damped rebound to target-aware pose.
- **Tail:** Settles.

#### `outcome_branch` — 0.88–1.00
**Goal:** Continue, stop, or escalate to fall according to measured feasibility.  
**Support:** Branch-specific support.  
**COM:** State handed off without reset.  
**Dynamics:** RECOVERY_FEASIBLE continues/stops; SUPPORT_FAILED/FALL_TRIGGERED enters collapse from current state.  
**Interruptibility:** `conditional`

- **Pelvis:** Branch-compatible.
- **Hindlimbs:** Branch-compatible.
- **Feet Toes:** Branch-compatible.
- **Thorax Spine:** Branch-compatible.
- **Neck Head:** Branch-compatible.
- **Tail:** Angle/velocity preserved.

### Events

```yaml
- name: SUPPORT_FAILED
  kind: condition
  phase: unexpected_support_failure
- name: RECOVERY_START
  kind: point
  at: 0.22
- name: L_FOOT_CONTACT
  kind: point
  phase: recovery_foot_placement
  trigger: condition_resolved_at_runtime
- name: R_FOOT_CONTACT
  kind: point
  phase: recovery_foot_placement
  trigger: condition_resolved_at_runtime
- name: RECOVERY_FEASIBLE
  kind: condition
  phase: outcome_branch
- name: FALL_TRIGGERED
  kind: condition
  phase: outcome_branch
- name: RECOVERY_END
  kind: point
  at: 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.1
  - 0.78
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.78
  - 1.0
```

### Procedural channels

```yaml
failure_model:
  enabled: true
  types:
  - slip
  - bad_contact
  - injury_yield
  - collision
  - fatigue
emergency_step:
  enabled: true
foot_ik:
  enabled: true
terrain_alignment:
  enabled: true
tail_balance:
  enabled: true
  emergency: true
fall_escalation:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- pelvis drop begins before polished recovery
- tail response is larger but cannot replace catch contact
- catch foot is reachable and terrain-aware
- loaded catch foot compression is visible
- continue/stop/fall branch preserves full state

---

## 27 — Threat / territorial call

**ID:** `tarbosaurus_threat_call`  
**Program:** `vocal_display`  
**Category / priority:** `social` / `P1`  
**Duration envelope:** 3.5–7.5 s; target 5.2 s  
**Loop / root motion:** False / False

**Purpose.** Communicate “do not come closer” through orientation, stable presentation, respiratory preparation, resonant call, post-call hold, and response waiting.

**Performance character.** Deliberate territorial pressure, not a generic victory roar or constant Hollywood gape.

### Entry and exit

```yaml
entry:
  allowed:
  - alert_idle
  - carcass_contest
  - territorial_standoff
  requirements:
  - rival direction and call audio envelope available
exit:
  allowed:
  - alert_idle
  - body_shove
  - committed_power_bite
  - withdraw
  handoff: maintain rival orientation and post-call decision state
```

### Phase progression

#### `target_orientation` — 0.00–0.12
**Goal:** Face the rival enough to make the display readable.  
**Support:** Stable support; optional adjustment step.  
**COM:** COM centers/aligns before vocal effort.  
**Dynamics:** Head locks; torso/pelvis follow within planted-turn limits.  
**Interruptibility:** `true`

- **Pelvis:** Aligns.
- **Hindlimbs:** Prepare broad support.
- **Feet Toes:** Adjustment if needed.
- **Thorax Spine:** Distributed yaw.
- **Neck Head:** Rival target lock.
- **Tail:** Opposes yaw.
- **Forelimbs:** Close.

#### `presentation_stance` — 0.12–0.25
**Goal:** Increase apparent readiness through posture, not fantasy inflation.  
**Support:** Feet stabilize in powerful bilateral stance.  
**COM:** COM central and hard to displace.  
**Dynamics:** Thorax firms, neck presentation becomes deliberate, head prominent.  
**Interruptibility:** `partial`

- **Pelvis:** Stable/centered.
- **Hindlimbs:** Flexed and ready.
- **Feet Toes:** Loaded.
- **Thorax Spine:** Firm but horizontal.
- **Neck Head:** Prominent target presentation.
- **Tail:** Strong quiet counterbalance.
- **Forelimbs:** Tucked.

#### `inhalation` — 0.25–0.38
**Goal:** Take a visible preparatory breath.  
**Support:** Support unchanged.  
**COM:** COM nearly fixed.  
**Dynamics:** Thorax, throat, and cervical base expand in sequence; jaw begins opening late.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Respiratory expansion.
- **Neck Head:** Acoustic projection posture.
- **Tail:** Quiet.
- **Jaw Throat:** Deep inhalation and beginning gape.

#### `jaw_and_resonance_setup` — 0.38–0.48
**Goal:** Set jaw/throat/neck for the selected plausible call envelope.  
**Support:** Stable support.  
**COM:** COM stable.  
**Dynamics:** Gape is semantically/audio driven and need not be maximal.  
**Interruptibility:** `false`

- **Pelvis:** Stable.
- **Thorax Spine:** Holds inhaled volume.
- **Neck Head:** Projection orientation fixed.
- **Tail:** Stable.
- **Jaw Throat:** Resonant configuration.

#### `call_onset` — 0.48–0.60
**Goal:** Begin vocal output with visible body-generated resonance.  
**Support:** Support firm.  
**COM:** Small reaction only.  
**Dynamics:** Audio envelope drives throat/cervical base/thorax deformation.  
**Interruptibility:** `false`

- **Pelvis:** Firm.
- **Hindlimbs:** Firm.
- **Feet Toes:** Loaded.
- **Thorax Spine:** Resonates within bounded amplitude.
- **Neck Head:** Fixed to rival.
- **Tail:** Small damping response.
- **Jaw Throat:** Call onset.

#### `peak_display` — 0.60–0.74
**Goal:** Sustain peak threat meaning and a small forward emphasis.  
**Support:** Stable stance.  
**COM:** COM may shift minimally forward but remains supported.  
**Dynamics:** Breath pressure decays according to audio envelope; no repeated monster head thrash.  
**Interruptibility:** `false`

- **Pelvis:** Small forward emphasis.
- **Hindlimbs:** Maintain support.
- **Feet Toes:** No slide.
- **Thorax Spine:** Firm/resonant.
- **Neck Head:** Target fixed.
- **Tail:** Counters.
- **Jaw Throat:** Peak semantic call.

#### `call_decay` — 0.74–0.84
**Goal:** Let breath and jaw/throat motion decay naturally.  
**Support:** Support unchanged.  
**COM:** COM recenters.  
**Dynamics:** Jaw gradually closes; thorax volume falls.  
**Interruptibility:** `partial`

- **Pelvis:** Recenters.
- **Thorax Spine:** Exhalation settles.
- **Neck Head:** Still facing rival.
- **Tail:** Damps.
- **Jaw Throat:** Call decays and gape closes.

#### `post_call_hold` — 0.84–0.94
**Goal:** Remain facing the rival and wait for a response.  
**Support:** Ready support.  
**COM:** COM stable.  
**Dynamics:** Silence/stillness is part of the social signal.  
**Interruptibility:** `true`

- **Pelvis:** Ready.
- **Hindlimbs:** Ready.
- **Feet Toes:** Planted.
- **Thorax Spine:** Breathing pauses then resumes.
- **Neck Head:** Target held.
- **Tail:** Quiet.
- **Jaw Throat:** Closed.

#### `recovery` — 0.94–1.00
**Goal:** Resume breathing while retaining the rival decision context.  
**Support:** Alert-ready support.  
**COM:** State handoff exact.  
**Dynamics:** No instant relaxation to neutral unless behavior selects it.  
**Interruptibility:** `true`

- **Pelvis:** Alert-compatible.
- **Hindlimbs:** Alert-compatible.
- **Feet Toes:** Stable.
- **Thorax Spine:** Breath resumes.
- **Neck Head:** Target retained.
- **Tail:** Stable.

### Events

```yaml
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.0
  - 0.94
- name: VOCAL_START
  kind: point
  at: 0.48
- name: VOCAL_END
  kind: point
  at: 0.84
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.48
  - 0.84
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.84
  - 1.0
```

### Procedural channels

```yaml
audio_envelope:
  required: true
jaw_throat_resonance:
  enabled: true
gaze:
  enabled: true
  rival_locked: true
foot_ik:
  enabled: true
breathing:
  enabled: true
  vocal_authority: true
tail_balance:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- call onset and decay align with audio envelope
- visible inhalation precedes call
- gape not forced to Hollywood maximum
- post-call hold remains perceptible
- threat posture remains distinct from alert idle and long-distance call

---

## 28 — Long-distance / contact call

**ID:** `tarbosaurus_long_distance_contact_call`  
**Program:** `vocal_display`  
**Category / priority:** `social` / `P1`  
**Duration envelope:** 4.5–9.5 s; target 6.8 s  
**Loop / root motion:** False / False

**Purpose.** Project a distant location/presence signal through open-space orientation, deep inspiration, resonant posture, pulse-capable vocalization, directional sweep, and listening pause.

**Performance character.** Expansive and ecological rather than aggressive; emotionally distinct from immediate territorial threat.

### Entry and exit

```yaml
entry:
  allowed:
  - neutral_idle
  - walk_stop
  - alert_idle
  requirements:
  - call semantic and audio envelope available
  - open-space direction optionally supplied
exit:
  allowed:
  - listen_reaction
  - neutral_idle
  - walk_start
  handoff: listening direction and social context persist after call
```

### Phase progression

#### `pause_current_activity` — 0.00–0.10
**Goal:** Stop or slow enough to call without abrupt motion reset.  
**Support:** Establish stable support.  
**COM:** COM/root velocity reaches call-compatible state through a short deceleration if needed.  
**Dynamics:** Current locomotion/action hands off at a legal phase.  
**Interruptibility:** `conditional`

- **Pelvis:** Settles.
- **Hindlimbs:** Establish support.
- **Feet Toes:** Plant.
- **Thorax Spine:** Current motion damps.
- **Neck Head:** Begins orienting.
- **Tail:** Settles.

#### `orient_open_space` — 0.10–0.23
**Goal:** Choose a direction with useful acoustic projection.  
**Support:** Stable support.  
**COM:** COM remains centered.  
**Dynamics:** Head and neck rise modestly; torso follows direction.  
**Interruptibility:** `true`

- **Pelvis:** Small alignment.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Distributed yaw.
- **Neck Head:** Raised/extended, not skyward roaring.
- **Tail:** Counterbalances.
- **Forelimbs:** Close.

#### `deep_inspiration` — 0.23–0.38
**Goal:** Prepare a larger resonant breath than threat onset.  
**Support:** Support unchanged.  
**COM:** COM stable.  
**Dynamics:** Ribcage, abdomen, throat, and cervical base expand in sequence.  
**Interruptibility:** `partial`

- **Pelvis:** Stable.
- **Hindlimbs:** Stable.
- **Feet Toes:** Planted.
- **Thorax Spine:** Deep expansion.
- **Neck Head:** Projection posture.
- **Tail:** Quiet.
- **Jaw Throat:** Inhalation and gradual opening.

#### `resonant_posture` — 0.38–0.48
**Goal:** Set extended neck and jaw/throat geometry for long-range projection.  
**Support:** Stable support.  
**COM:** COM remains viable as head elevates.  
**Dynamics:** Posture maximizes semantic projection without threat lean.  
**Interruptibility:** `false`

- **Pelvis:** Centered.
- **Thorax Spine:** Open respiratory posture.
- **Neck Head:** Extended forward/up.
- **Tail:** Balances.
- **Jaw Throat:** Resonant configuration.

#### `vocal_pulses` — 0.48–0.72
**Goal:** Emit one or more audio-driven pulses with whole-body respiratory rhythm.  
**Support:** Support firm.  
**COM:** Small COM shifts only.  
**Dynamics:** Throat/thorax/jaw follow pulse envelope; semantic identity preserved across variation.  
**Interruptibility:** `false`

- **Pelvis:** Firm.
- **Hindlimbs:** Firm.
- **Feet Toes:** Loaded.
- **Thorax Spine:** Pulse-coupled volume change.
- **Neck Head:** Projection direction held.
- **Tail:** Minimal.
- **Jaw Throat:** Pulse-coupled movement.

#### `directional_sweep` — 0.72–0.82
**Goal:** Optionally sweep projection direction a small amount without turning it into scanning threat.  
**Support:** Support remains; micro-step only beyond safe planted range.  
**COM:** COM follows any step plan.  
**Dynamics:** Head/neck/torso yaw slowly while call decays.  
**Interruptibility:** `partial`

- **Pelvis:** Small alignment.
- **Hindlimbs:** Stable.
- **Feet Toes:** No loaded twist.
- **Thorax Spine:** Shares sweep.
- **Neck Head:** Small acoustic sweep.
- **Tail:** Opposes yaw.
- **Jaw Throat:** Decay.

#### `end_and_settle` — 0.82–0.90
**Goal:** Close jaw/throat and settle respiratory effort.  
**Support:** Stable stance.  
**COM:** COM centered.  
**Dynamics:** Call ends; breath volume falls.  
**Interruptibility:** `true`

- **Pelvis:** Stable.
- **Thorax Spine:** Exhalation settles.
- **Neck Head:** Remains elevated enough to listen.
- **Tail:** Quiet.
- **Jaw Throat:** Closes.

#### `listening_pause` — 0.90–1.00
**Goal:** Wait meaningfully for a distant response.  
**Support:** Alert-ready support.  
**COM:** COM stable.  
**Dynamics:** Motion and breathing reduce; head/gaze listen into the world.  
**Interruptibility:** `true`

- **Pelvis:** Ready.
- **Hindlimbs:** Ready.
- **Feet Toes:** Planted.
- **Thorax Spine:** Quiet respiration.
- **Neck Head:** Listening orientation.
- **Tail:** Still.
- **Jaw Throat:** Closed.

### Events

```yaml
- name: VOCAL_START
  kind: point
  at: 0.48
- name: VOCAL_END
  kind: point
  at: 0.82
- name: HEAD_TARGET_WINDOW
  kind: window
  range:
  - 0.1
  - 1.0
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.48
  - 0.82
- name: PARTIALLY_INTERRUPTIBLE
  kind: window
  range:
  - 0.82
  - 1.0
```

### Procedural channels

```yaml
audio_envelope:
  required: true
  pulses: true
open_space_direction:
  enabled: true
jaw_throat_resonance:
  enabled: true
breathing:
  enabled: true
  vocal_authority: true
gaze:
  enabled: true
  listening_after: 0.9
foot_ik:
  enabled: true
tail_balance:
  enabled: true
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- emotion and posture distinct from threat call
- deep inspiration precedes vocalization
- neck is extended but not exaggerated skyward
- audio pulses and body resonance align
- listening pause remains visible and can transition to listen reaction

---

## 29 — Collapse / death

**ID:** `tarbosaurus_collapse_death`  
**Program:** `terminal_fall`  
**Category / priority:** `terminal` / `P0`  
**Duration envelope:** 4.0–10.0 s; target 6.2 s  
**Loop / root motion:** False / True

**Purpose.** Create a grounded, consequential death from fatal impairment through attempted correction, irreversible lateral-diagonal fall, first major contact, constrained physical settling, and stillness.

**Performance character.** Physical and non-celebratory; the animal attempts not to fall, which makes the failure feel real rather than scripted spectacle.

### Entry and exit

```yaml
entry:
  allowed:
  - standing
  - walking
  - running_stop
  - stumble_failure
  requirements:
  - fatal state, failing side, terrain, incoming momentum, and final-corpse policy known
exit:
  allowed:
  - corpse_state
  handoff: author animation through first major contact, then constrained physics with preserved momentum
    and collision limits
```

### Phase progression

#### `fatal_impairment` — 0.00–0.10
**Goal:** Show coordination/strength failing while preserving incoming motion context.  
**Support:** Current support still partly active.  
**COM:** COM follows incoming state; support capacity begins reducing.  
**Dynamics:** Head lowers, posture loses precision, breathing/strength fails.  
**Interruptibility:** `false`

- **Pelvis:** Begins losing control.
- **Hindlimbs:** Capacity falls asymmetrically.
- **Feet Toes:** Current contact.
- **Thorax Spine:** Tone decreases.
- **Neck Head:** Lowers/protects.
- **Tail:** Still attempts normal balance.
- **Jaw Throat:** Breathing fails/changes.

#### `support_failure` — 0.10–0.22
**Goal:** Make one hindlimb cease to provide expected support.  
**Support:** Failing foot/leg unloads or yields unintentionally; opposite support overloaded.  
**COM:** COM shifts/drops toward failing side.  
**Dynamics:** Failure is causal and measured.  
**Interruptibility:** `false`

- **Pelvis:** Drops toward side.
- **Hindlimbs:** Failing leg yields.
- **Feet Toes:** Failure contact state explicit.
- **Thorax Spine:** Begins rotation.
- **Neck Head:** Moves opposite.
- **Tail:** Emergency correction begins.

#### `correction_attempt` — 0.22–0.36
**Goal:** Attempt to recover with opposite leg, tail, and head.  
**Support:** Opposite foot steps/reloads if reachable.  
**COM:** COM may temporarily approach a capture region but capacity is insufficient.  
**Dynamics:** Animal visibly tries not to fall; correction starts but fails.  
**Interruptibility:** `false`

- **Pelvis:** Attempts arrest.
- **Hindlimbs:** Opposite leg steps/compresses.
- **Feet Toes:** Emergency contact.
- **Thorax Spine:** Counter-rotates.
- **Neck Head:** Protective counter-motion.
- **Tail:** Large emergency swing.

#### `irreversible_failure` — 0.36–0.48
**Goal:** Cross the point where recovery cannot succeed.  
**Support:** Support wrench/capacity insufficient.  
**COM:** COM and angular momentum commit to lateral-diagonal fall.  
**Dynamics:** Planner locks fall side/corridor; no arbitrary mid-fall redirection.  
**Interruptibility:** `false`

- **Pelvis:** Descends/rotates irreversibly.
- **Hindlimbs:** Collapse/fold.
- **Feet Toes:** Contacts unload or drag only within physics.
- **Thorax Spine:** Follows fall.
- **Neck Head:** Positions to avoid direct uncontrolled skull impact.
- **Tail:** Continues correction but cannot recover.

#### `first_body_contact` — 0.48–0.60
**Goal:** Make the first major lower-body/pelvis/lateral contact with terrain.  
**Support:** Ground contact expands from body region.  
**COM:** COM velocity changes through measured impact impulse.  
**Dynamics:** Authored pose reaches contact with collision-safe geometry; physical correction starts blending in.  
**Interruptibility:** `false`

- **Pelvis:** First impact/contact.
- **Hindlimbs:** Fold/impact according to fall.
- **Feet Toes:** May leave support.
- **Thorax Spine:** Still airborne/descending partly.
- **Neck Head:** Held clear/protected.
- **Tail:** Continues momentum.

#### `torso_collapse` — 0.60–0.72
**Goal:** Bring remaining torso mass to ground under continuous momentum.  
**Support:** Pelvis/body contact plus expanding torso contact.  
**COM:** COM descends and translates; impact energy dissipates through contacts.  
**Dynamics:** Controlled physics adapts to terrain while preserving authored fall character.  
**Interruptibility:** `false`

- **Pelvis:** Grounded/sliding within friction.
- **Hindlimbs:** Settle/collide.
- **Thorax Spine:** Secondary impact.
- **Neck Head:** Continues protective placement.
- **Tail:** Ground contact begins or continues.

#### `head_neck_contact` — 0.72–0.82
**Goal:** Place head and neck against terrain without clipping or snapping.  
**Support:** Body contacts support most mass; head contact added.  
**COM:** COM nearly at final height.  
**Dynamics:** Neck remains constrained; terrain solver defines final contact point.  
**Interruptibility:** `false`

- **Pelvis:** Supported.
- **Hindlimbs:** Settling.
- **Thorax Spine:** Supported.
- **Neck Head:** Terrain-aware contact.
- **Tail:** Still moving.
- **Jaw Throat:** No performative roar required.

#### `residual_momentum` — 0.82–0.90
**Goal:** Let tail, limbs, and soft body motion continue after major contacts.  
**Support:** Multiple body contacts.  
**COM:** Linear/angular momentum dissipates through friction, impact, and damping.  
**Dynamics:** No repeated canned twitch; only causal settling.  
**Interruptibility:** `false`

- **Pelvis:** Small settle.
- **Hindlimbs:** Residual movement.
- **Thorax Spine:** Residual movement.
- **Neck Head:** Small settle.
- **Tail:** Last significant motion then damping.
- **Forelimbs:** Settle under gravity/contact.

#### `physical_settle` — 0.90–0.97
**Goal:** Resolve final limb/tail placement through constrained physical pose correction.  
**Support:** Final corpse contact set.  
**COM:** COM velocity approaches zero.  
**Dynamics:** Ragdoll/physics remains bounded by anatomy, collision, and authored target pose.  
**Interruptibility:** `false`

- **Pelvis:** Final.
- **Hindlimbs:** Final collision-safe.
- **Feet Toes:** Final.
- **Thorax Spine:** Final.
- **Neck Head:** Final.
- **Tail:** Final.
- **Forelimbs:** Final.

#### `stillness` — 0.97–1.00
**Goal:** Enter final non-breathing corpse state.  
**Support:** Final contacts locked for corpse simulation/LOD.  
**COM:** COM stationary within tolerance.  
**Dynamics:** Breathing and active stabilization stop; no default repeated twitch.  
**Interruptibility:** `false`

- **Pelvis:** Still.
- **Hindlimbs:** Still.
- **Feet Toes:** Still.
- **Thorax Spine:** Breathing stopped.
- **Neck Head:** Still.
- **Tail:** Still.
- **Forelimbs:** Still.
- **Jaw Throat:** Still/final state.

### Events

```yaml
- name: SUPPORT_FAILED
  kind: condition
  phase: support_failure
- name: FALL_TRIGGERED
  kind: condition
  phase: irreversible_failure
- name: CONTACT_BEGIN
  kind: point
  at: 0.48
- name: CONTACT_PEAK
  kind: point
  at: 0.64
- name: CONTACT_END
  kind: point
  at: 0.9
- name: NON_INTERRUPTIBLE
  kind: window
  range:
  - 0.0
  - 1.0
```

### Procedural channels

```yaml
fall_direction:
  enabled: true
  default: lateral_diagonal
authored_to_physics_handoff:
  enabled: true
  start_range:
  - 0.48
  - 0.6
body_collision:
  enabled: true
terrain_alignment:
  enabled: true
ragdoll:
  enabled: true
  constrained: true
breathing:
  enabled: true
  stops_at: 0.97
gore:
  default: restrained_state_communication
```

### Growth response

- **Juvenile:** shorter time constants and smaller absolute momentum; preserve semantics and contacts
- **Subadult:** stronger acceleration and quicker recovery within capacity
- **Adult:** reference performance with deliberate support and visible momentum
- **Heavy Adult:** longer preload, braking, absorption, and recovery; reduced redirection authority

### Reject / release-blocking checks

- animal visibly attempts correction before irreversible fall
- pure standing ragdoll forbidden
- first major contact authored and measured
- head/neck/tail never penetrate terrain
- momentum remains continuous through physics handoff
- no celebratory spectacle or repeated default twitch
- final breathing stops

---
