# Factory movement roadmap and acceptance tracker

Updated 2026-09-10. This is a living evidence tracker, not a fixed plan inherited from an earlier model. Update it at every visual checkpoint. Game-design chapters retain product authority.

## Current accepted baseline

The user approved iteration 16 as smooth and credible, while correctly distinguishing locomotion from a living animal's attention and intent. Preserve Allosaurus iteration 14 and Tarbosaurus iteration 15 normal walks; iteration 16 adds the connected speed sequence. Approved motion is not automatically production certified.

| Movement family | Allosaurus | Tarbosaurus | Current boundary |
|---|---|---|---|
| Grounded stance / held idle | Reviewed | Reviewed | Neutral/held pose; spontaneous breathing and attention still to add |
| Normal walking | Visually approved, iteration 14 | Visually approved, iteration 15 | Same reusable solver; researched/authored stride and body differences in data |
| Faster walking | Sequence approved | Sequence approved | 1.35× cadence, still grounded; not running |
| Idle → start → walk → faster → slow → stop | Visually approved, iteration 16 | Visually approved, iteration 16 | 18.68-second source-driven sequence; runtime import not yet verified |
| Heel roll, toe-off, swing recovery | Reviewed | Reviewed | Shared articulation; Allosaurus has added intermediate toe joints |
| Lateral weight transfer / pelvis response | Reviewed engineering response | Reviewed reduced vertical response | Not a converged whole-body force simulation |
| Reverse walking | Reusable planner exists; not reviewed on this animal | Reusable planner exists; not reviewed on this animal | No game-ready claim |
| Turning / curved paths / pivots | Missing approved motion | Missing approved motion | Must preserve stance during heading changes |
| Running / sprinting | Missing approved transfer | Approved historical Run010 / Sprint006 references | Shared airborne generation exists; current two-animal/runtime acceptance missing |
| Independent gaze / neck attention | Next | Next | Game chooses target; bounded additive articulation must retain gait |
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
- Unity import/compression parity, runtime movement ownership, target-device budgets and attention-layer contact preservation are not yet verified.

## Active milestone: a living animal in a small world

Player question: does the approved gait still feel credible when viewed from animal height in a coherent landscape, with independent attention to surroundings?

1. **Tracker and safe cleanup — IN PROGRESS.** Preserve approved sources, media, unique work and recovery refs; remove only obsolete clean checkouts.
2. **Mini-world — NEXT.** A small Unity validation slice in the principal Eonwild repository: forest edge, open muddy clearing, shallow stream, rocks/logs/ferns and distant cliffs. Reuse the user's existing assets. Reference image informs composition and atmosphere; its quest/combat UI is not a product requirement.
3. **Motion consumer — NEXT.** Immutable packages for both animals; one movement owner; native-time review, scale/axes and landmark/contact comparisons. No sibling Factory code imports.
4. **Attention — NEXT.** Look left/right, hold and track a target, return smoothly. Neck distributes the turn within bounded range. Camera follows the body with its own damping and only restrained attention influence.
5. **Playable review — CHECKPOINT.** Movement/speed controls, animal switch and attention demonstration. Capture actual runtime visuals and pause for feedback.

The user approved Unity for this validation checkpoint. This does not silently replace the canonical browser-first distribution decision; shipping platform and performance acceptance remain separate.

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
