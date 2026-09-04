# Animations 18–24 — feeding, drinking, lie/rest/rise

Status: **implementation specification**. These are semantic contracts, not approved baked clips.

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
