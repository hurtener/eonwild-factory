# Factory movement roadmap and acceptance tracker

Updated 2026-09-12. This is a living evidence tracker, not a fixed plan inherited from an earlier model. Update it at every visual checkpoint. Game-design chapters retain product authority.

## Animal profile housekeeping

Canonical embodiment profiles now collect the approved rig bindings, explicit axes, sequence timing and consumer settings. Python reference evaluation, Unity parity vectors and Blender preview baking are documented in [the embodiment contract](ANIMAL_EMBODIMENT_CONTRACT.md). This is portability work, not a new animation family or blanket production acceptance.

## Active directional locomotion set — 2026-09-12

User requested walking turns, coordinated turns without forward travel, backward walking, and lateral balance-recovery steps. Work directly, without subagents. Preserve the approved straight gait and secondary-motion baseline.

| Checkpoint | Scope, both animals | Status |
|---|---|---|
| A — turning | Gentle walking curves, tighter low-speed turns, alternating stepping turns in place | Draft 10 accepted as a good turning baseline. Draft 11 adds numerical animal capabilities to the shared planner; both-rig Unity renders and all-frame audit complete, user re-review pending. Walking curves and final mass/contact remain open |
| B — reverse | Backward start, several coordinated steps, stop; its own grounded contact choreography | Requested, not yet implemented in this pass |
| C — lateral recovery | Left/right recovery steps, support transfer, whole-body settling | Requested, not yet implemented |
| D — connected controls | Blend the reviewed directional behaviors with idle and walking; runtime root ownership and contact | After visual acceptance of A–C |

Draft 10 is the user-accepted turning reference, preserved in `game/Evidence/continuous-release-turn-study/`. Draft 11 adds profile mass/inertia, authored force/torque budgets, walking speed/cadence, braking, lateral response and attention/response timing. The shared planner consumes these values without species branches. Both actual rigs generated and were captured in Unity; all 470 captured frames were visually inspected. Current evidence: principal game `game/Evidence/capability-turn-study/`. Pause for user re-review before changing the baseline.

Next, polish pelvis weight transfer and contact using the reviewed turn, then revisit walking curves and regenerate a walking comparison from the new capability resolver. The existing approved straight walks are preserved; this pass does not replace them. These limits constrain the locomotion path and heading, excluding local pelvis accommodation. Final whole-body force balance and material contact remain pending. Reverse walking and lateral recovery follow the directional review checkpoint.

## Current accepted baseline

The user approved iteration 16 as smooth and credible, while correctly distinguishing locomotion from a living animal's attention and intent. Preserve Allosaurus iteration 14 and Tarbosaurus iteration 15 normal walks; iteration 16 adds the connected speed sequence. Approved motion is not automatically production certified.

| Movement family | Allosaurus | Tarbosaurus | Current boundary |
|---|---|---|---|
| Grounded stance / held idle | Reviewed | Reviewed | Held pose reviewed; arm/jaw secondary life subsequently approved |
| Normal walking | Visually approved, iteration 14 | Visually approved, iteration 15 | Same reusable solver; researched/authored stride and body differences in data |
| Faster walking | Sequence approved | Sequence approved | 1.35× cadence, still grounded; not running |
| Idle → start → walk → faster → slow → stop | Visually approved, iteration 16 | Visually approved, iteration 16 | 18.68-second source-driven sequence; runtime import not yet verified |
| Heel roll, toe-off, swing recovery | Reviewed | Reviewed | Shared articulation; Allosaurus has added intermediate toe joints |
| Lateral weight transfer / pelvis response | Reviewed engineering response | Reviewed reduced vertical response | Not a converged whole-body force simulation |
| Reverse walking | Reusable planner exists; not reviewed on this animal | Reusable planner exists; not reviewed on this animal | No game-ready claim |
| Turning / curved paths / pivots | Turn 10 accepted baseline; 11 re-review pending | Turn 10 accepted baseline; 11 re-review pending | Walking curves, final mass and material contact remain pending |
| Running / sprinting | Missing approved transfer | Approved historical Run010 / Sprint006 references | Shared airborne generation exists; current two-animal/runtime acceptance missing |
| Independent gaze / neck attention | Runtime demonstration reviewed | Runtime demonstration reviewed | World interest points; not complete sensory behavior |
| Expressive idle / breathing / listening | Missing approved behavior | Missing approved behavior | Intentional responses, not random noise |
| Feeding / gripping / pulling | Missing approved transfer | Historical Feeding003 reference | Persistent support and oral contact need current-engine/runtime acceptance |
| Drinking / swallowing | Missing | Missing | Separate choreography and interaction authority |
| Rest / sit / lie down / rise / sleep | Missing | Missing | Topology and support transitions required |
| Bite / attack / recoil / defense | Missing | Missing | World confirms outcomes; animation only supplies windows |
| Injury / limp / stumble / fall / death | Missing | Missing | No current reusable, reviewed family |
| Jump / airborne landing / recovery | Missing reviewed behavior | Missing reviewed behavior | Airborne gait implementation does not certify jumping |
| Terrain adaptation / slopes / stepping over | Missing runtime acceptance | Missing runtime acceptance | Flat-floor factory evidence is not terrain proof |
| Swim / wade / enter/leave water | Missing | Missing | Mini-world water is scenery until interaction is implemented |
| Social / display / vocalization | Missing | Missing | Future breadth after embodiment checkpoint |

## Current limitations

- Saved sequence contact residuals: Allosaurus 0.131 mm; Tarbosaurus 0.230 mm at loaded material anchors.
- Brief interpolation floor dips: Allosaurus 0.703 mm; Tarbosaurus 5.646 mm at first toe-off. Production contact acceptance remains open; these do not block visual iteration.
- Body controls are approved engineering responses, not newly converged dynamics solutions.
- Focused Unity landmark and secondary-layer parity were verified in housekeeping. Full material contact, arbitrary terrain and worst-case device performance remain open.

## Completed mini-world and portability checkpoints

The user approved the mini-world, its FPS improvement, attention demonstration and full-transition arm/jaw life. The source walk remains preserved. The game tracker records native Unity captures, import parity, focused secondary-contact checks and measured M4 performance. Canonical embodiment profiles, explicit axes, Python/Unity secondary-motion parity and Blender preview imports were implemented in the housekeeping checkpoint. These are focused validations, not full production contact or terrain acceptance.

Unity remains the approved validation consumer; shipping platform decisions are separate. Directional checkpoint A is the active work above.

## Following checkpoints (not started)

- Player-driven turns, stopping and terrain contact; improve the remaining observed contact issue.
- Transfer approved running/sprinting into the current shared engine and both animals.
- Persistent-support feeding, drinking and interaction handoff.
- Resting, injury and other movement breadth, in response to the playable loop.
- Ecology, sensory behavior, world expansion and deployment/device budgets.

## Status discipline

Track **implemented**, **source-rig generated**, **exported**, **human reviewed**, **runtime verified**, and **production accepted** separately. Record source identity, recipe, native-speed evidence and known gaps. Do not declare an entire movement family complete from a legacy reference or synthetic test. Keep iteration short and visible; broad release gates follow a reviewed candidate.

## Factory contracts

Continue `src/eonwild_motion`. Preserve immutable legacy capsules and approved references. Animal differences belong in semantic rig/body/behavior data. A behavior owns contact choreography. Reopen final emitted assets after contact-affecting changes. See `UNITY_MOTION_CONTRACT.md` for the consumer boundary.


## Adaptive turn checkpoint 07 — 2026-09-12

The previous continuous-turn study was rejected for robotic coordination. The user emphasized changing gait to preserve leg space and different inner/outer leg work, using the Allosaurus reference stored as `assets/examples/tarbosaurus/tarbo-turning-example.mp4`.

Implemented directly without subagents: unequal inner/outer step durations and heading contributions; outward recovery clearance and staggered intermediate placements; support shift before release; phase-dependent knee/ankle preferences; restored restrained toe articulation; reduced constant crouch; delayed tail response. The shared source-admission and limb solver remain in use, with no species branch or edits to approved straight walks.

Both real animals generated and reopened. Seven focused planner checks pass. Native Unity side and three-quarter captures are in principal game `game/Evidence/adaptive-turn-study/`. Visual approval is PENDING. This is a revised authored support choreography, not adaptive terrain steering or solved whole-body dynamics. Final material tangential locking and production contact/mass acceptance remain open. Pause here before further directional breadth.


## Wide stance / outside-opening turn 08 — 2026-09-12

The user rejected draft 07's narrow support stance and inner-first opening. Draft 08 separates the turning stance from walking width: authored full stance 0.36 body heights versus the previous 0.24, with an additional 0.045 body-height outside placement during opening. The outside leg opens first in either direction; the inner leg contributes more of the overlapping rotation and follows into broad support. The body center now travels around alternating support pivots instead of a fixed central axis. A fixed review camera exposes that travel. These are shared behavior parameters, not species branches or a new force model.

Both admitted animals exported and reopened; eight focused planner checks pass, including outside-first direction, support anchoring and moving-center continuity. Principal game evidence: `game/Evidence/wide-stance-turn-study/`. Visual review is PENDING. Approved straight walks remain preserved; final material contact and mass certification remain open. Pause at this checkpoint.


## Loaded hip / planted leg plane 09 — 2026-09-12

The user identified sideways knee/ankle articulation during weight acceptance. The turn now binds a world bend plane to each planted interval, reorients it during recovery, and accommodates that plane at the pelvis. Planted turn pitch is held instead of allowing the knee-shape objective to rock the ankle; recovery blends out that restriction. Ordinary walking does not opt into these constraints.

Both animals generated and reopened. Twelve focused checks pass. A direct comparison of reopened joint motion reduced maximum planted-interval knee travel across the foot lateral axis from 154 to 10.6 mm for Allosaurus and 213 to 13.5 mm for Tarbosaurus. This is a positional diagnostic, not a joint-stress or force certificate. The remaining lateral-axis component can include motion within an inclined leg plane. Allosaurus sampled floor dip is 2.73 mm, Tarbosaurus 0.19 mm. Final contact and mass acceptance remain pending. Principal game evidence: `game/Evidence/hip-support-turn-study/`; pause for visual review.


## Continuous articulation release 10 — 2026-09-12

Draft 09 was rejected for robotic stop–start motion. The next shared-engine candidate overlaps rotation across steps and replaces the planted/free pitch switch with continuous turn pitch and bend-plane recovery. Pelvis accommodation blends support-plane projections to avoid unstable double-support solves. Both animals generated, reopened and captured in Unity. All 187 frames of each new clip were visually inspected chronologically, with all-sample joint-angle differences; twelve focused checks pass. Evidence: principal game `game/Evidence/continuous-release-turn-study/`.

Peak ankle angle changes are reduced from about 403/387 to 103/120 degrees per second (Allosaurus/Tarbosaurus). This is not visual acceptance. Planted lateral knee travel rises to about 32 mm versus draft 09's 11/14 mm; that tradeoff is recorded, not hidden. Deliberate reversal settling remains. Final material contact and force/mass certification remain pending. Pause for user review; approved walking baselines remain untouched.


## Numerical animal capabilities 11 — 2026-09-12

The user accepted draft 10 as a good baseline and requested reusable numerical semantics before further mass polishing. Canonical profiles now retain units, classifications and sources for yaw inertia, mass, force/torque budgets, traction, walking speed/cadence, heading per step, effort and attention/response time. Published inertia/ilium evidence remains separate from authored control budgets and the engineering agility components. There is no universal species agility rank.

Shared Factory resolution, directional regeneration, profile export and labeled future-model similarity seeding are implemented. Both animals exported and were captured in Unity at 1280×720, 24 fps, 235 frames each. All frames were visually inspected chronologically. Twenty-nine focused checks pass; profile export and seeding CLI checks also pass. New capability sidecars bind profile and emitted turn hashes. Unity plays these baked clips and displays their metadata; live gameplay control integration is not claimed.

Allosaurus effective forward acceleration is 0.833 m/s² and yaw acceleration 95.8 deg/s²; Tarbosaurus 0.696 m/s² and 129.6 deg/s². These are authored effective responses derived using the stored mass/inertia, not measured animal performance. The turn in each direction can take a different time because its support path differs. Preferred walking speeds resolve to 1.05 and 1.00 m/s while preserving step/stride intent; approved straight-walk clips were not regenerated.

Review is PENDING. The deliberate reversal settling remains visible. Maximum planted-interval knee displacement along the foot lateral axis is 31.6 mm for Allosaurus and 33.8 mm for Tarbosaurus, close to draft 10's 31.9/32.5 mm. This is a positional diagnostic, not proof of joint loading. Locomotion-path acceleration limits exclude additional local pelvis support accommodation; final mass/contact correction is still open. Evidence and the next work are tracked in the current checkpoint above.
