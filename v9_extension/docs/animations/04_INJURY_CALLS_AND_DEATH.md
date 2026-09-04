# Animations 25–29 — injury, stumble, calls, and collapse

Status: **implementation specification**. These are semantic contracts, not approved baked clips.

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
