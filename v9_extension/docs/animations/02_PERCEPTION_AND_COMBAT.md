# Animations 11–17 — perception, bites, recovery, and body pressure

Status: **implementation specification**. These are semantic contracts, not approved baked clips.

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
