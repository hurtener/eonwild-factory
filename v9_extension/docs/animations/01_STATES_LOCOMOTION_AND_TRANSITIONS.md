# Animations 01–10 — states, locomotion, starts, and stops

Status: **implementation specification**. These are semantic contracts, not approved baked clips.

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
