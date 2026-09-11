# Factory movement roadmap and acceptance tracker

Updated 2026-09-10. This is a living evidence tracker, not a fixed plan inherited from an earlier model. Update it at every visual checkpoint. Game-design chapters retain product authority.

## Animal profile housekeeping

Canonical embodiment profiles now collect the approved rig bindings, explicit axes, sequence timing and consumer settings. Python reference evaluation, Unity parity vectors and Blender preview baking are documented in [the embodiment contract](ANIMAL_EMBODIMENT_CONTRACT.md). This is portability work, not a new animation family or blanket production acceptance.

## Active directional locomotion set — 2026-09-10

User requested walking turns, coordinated turns without forward travel, backward walking, and lateral balance-recovery steps. Work directly, without subagents. Preserve the approved straight gait and secondary-motion baseline.

| Checkpoint | Scope, both animals | Status |
|---|---|---|
| A — turning | Gentle walking curves, tighter low-speed turns, alternating stepping turns in place | Source-driven diagnostic generated; First draft rejected for forward-fixed gaze and micro-jumping footwork; revised leading-foot turn plus head/neck lead in native review |
| B — reverse | Backward start, several coordinated steps, stop; its own grounded contact choreography | Requested, not yet implemented in this pass |
| C — lateral recovery | Left/right recovery steps, support transfer, whole-body settling | Requested, not yet implemented |
| D — connected controls | Blend the reviewed directional behaviors with idle and walking; runtime root ownership and contact | After visual acceptance of A–C |

Checkpoint A currently uses fixed support positions/headings in the planner, foot reorientation during swing, shared leg/toe articulation, anticipatory foot placement, and authored lateral support shift. It is not a force simulation. Limited floor correction is present; final material contact locking and mass correction remain pending. The new directional files are separate from approved clips. Evidence: principal game `game/Evidence/directional-turns-checkpoint/`. Fifteen focused tests passed; both GLBs reopened for skin sampling. The revision demonstrates both in-place directions. The leading foot opens and plants before the main body rotation; the trailing foot follows with reduced lift. Turn attention now follows gaze stabilization so it is not cancelled. Heel release uses one continuous amplitude. Normal-speed curve coverage remains pending. Pause for user review at A before developing B/C. A numeric diagnostic is not an approved animation.

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
| Turning / curved paths / pivots | Directional draft A | Directional draft A | Generated, not yet approved; support material locking pending |
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
