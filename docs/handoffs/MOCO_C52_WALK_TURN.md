# C52 — normal walking and walking turns with the spatial model

> Superseded for active work by [C52 B centered walking](MOCO_C52B_CENTERED_WALK.md).
> The user rejected the walking ankle artifacts. Historical media below is not
> approved; current priority is the corrected 16-second straight walk. Turning
> and broader locomotion generalization are held until that checkpoint.


User requested both motions together as ten-second native-time review clips.
Work directly, without subagents. C51 A is the approved fast-locomotion visual
baseline and stays unchanged. This is a separate walking task transfer, not
another full-Moco convergence attempt. Normal walking uses the existing profile:
1 m/s, 1.3705053503 m per step, 2.7410107007 m per same-foot stride. These are
preserved authored values, not new biological measurements.

## Task change

The spatial initializer previously assumed a straight reflected half-stride.
The optional `coordination.path_task` now admits a complete stride with separate
left/right variables. Walking uses a declared 0.62 duty-factor task, continuous
sole unrolling and world-fixed support anchors. The turn uses the same setup
with 0.12 rad/s curvature (8.333 m centerline radius); the inner and outer feet
therefore cover different distances. A path-relative neck/head attention task
looks into the curve. The model's joint limits, contact mechanics, masses,
actuator capacities and physical acceptance thresholds are unchanged.

This is still a guided inverse-dynamics initializer. Authored task-space foot
paths and a C51-derived warm body posture are explicit. Tail curves retain that
warm start at reduced excursion; they are not freely predicted in this bounded
pass. Contacts/torques/root residuals are reevaluated in the exact OpenSim model.
No conventional animation clip, frame playback slowdown, root assistance, or
render-only foot correction is introduced. The optional mode does not change
legacy C51 half-stride generation.

## Reproduce and preserve

Factory worktree: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration`.
Research directory: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c52-walk-turn`.
Source/commands are in `execution.json`; recipes are also catalogued as
`catalog/behaviors/moco-c52-{walk,turn}.v1.json`. Use new output paths on repeats.

Use `tools/replay_moco_prototype.py` on each returned initializer directory,
then `tools/retarget_moco_prototype.py` with the admitted v15 tail12 motion set
and original C50 source profile. The adapter reopens the GLB and measures all
exported samples. A full curved stride is repeated using its rigid ground-plane
transform without reflecting or exchanging the legs.

Unity: build `MocoPrototypeReviewBuilder.Build` with `-moco-folder MocoWalk52B`
and `-moco-alternate-folder MocoTurn52B`. The plain-stage saved-clip player
supports `-alternate` for the turn and `-capture-frames 240` for exactly ten
seconds at 24 fps. It composes both cycle rotation and translation; it does not
solve motion. Inspect all 240 frames per selected view before presenting them.

## Review state

C52 B is rendered and ready for user review. A first pair of 22-evaluation refinements reduced support forces to 0.77–1.17 BW and loaded-pad p95 speed to 0.076 m/s (walk) / 0.059 m/s (turn), but reopening skin revealed 37.6 / 48.9 mm material intrusion. A single targeted 16-evaluation refinement increases the existing material-clearance penalty from 400 to 1800. It changes no physical bound or acceptance threshold. All 480 frames were inspected in twenty chronological sheets, with enlarged contact poses. Both videos are exactly 240 frames / 24 fps / 10 seconds. Neither candidate is visually approved. Do not infer
Moco convergence, independent forward stability, biological validation, or
production contact acceptance from these previews. C51 and the independent
conventional walking/turning library remain approved in their existing scopes.

The optional full-stride task is currently supported by the inverse-dynamics
initializer/replay/retarget path. `make_study` explicitly refuses these recipes:
full Moco continuation still assumes straight reflected half-strides and must
not silently solve a different task. Extending that study is future work, not
part of this visual checkpoint.

## Saved checkpoint B

Evidence: principal game `game/Evidence/moco-c52-walk-turn/`.
Native videos: `candidate-b/walk/review/tarbo-c52-b-walk-10s.mp4` and
`candidate-b/turn/review/tarbo-c52-b-turn-10s.mp4`.
B reduces reopened skin intrusion to 7.35 mm (walk) / 13.05 mm (turn).
Initializer root residual RMS is 0.04811 / 0.05278 BW/BWL; peak commands are
1.05410 / 1.06940. Small distal digit bound violations remain (under one degree).
These are **not physical acceptance passes**. No acceptance tolerances, contact
parameters, masses, capacities or joint limits were weakened. Five focused
checks and the native Unity build/capture pass; user visual review is pending.
The approved C51 asset hash was rechecked unchanged.

Factory branches: C52 `codex/moco-c52-walk-turn`, prior C51
`codex/moco-c51-support-feasibility`. Game branches: C52
`codex/moco-c52-walk-turn-review`, prior C51 `codex/moco-c51-support-review`.
Motion source algorithm commit `2ef8462`; the added full-Moco incompatibility
guard and clearance-refinement recipes are `74b6d1f`. The guard does not change
initializer numerics. Model, recipe, returned solution, coefficients, replay,
retarget, commands, logs, frame hashes, inspected sheets and native media are
saved together. A failed A pair is retained in `experiments/`; raw PNG captures
remain on external task storage. No further solver or artistic pass is running.
Pause for the requested visual checkpoint.
