# Connected walking checkpoint — iteration 16

Scope: idle → start → normal walk → faster walk → slow down → stop, on both admitted animals. Pause for user playback feedback at this checkpoint. No subsequent behaviors, Unity delivery, merge or push are included.

Approved normal-walk references remain Allosaurus iteration 14 and Tarbosaurus iteration 15 (quarter vertical body-control coefficients). The recipe under catalog/review-sequences records their controls. Neither prior GLB animation is an input to the new motion: poses are generated from admitted geometry, semantic rig data and the shared solver.

The sequence lasts 18.679456 seconds. Faster walking is an authored 1.35 cadence ratio with the same configured step length and grounded support choreography. Quintic cadence ramps integrate displacement continuously. Starts/stops use the existing integrated-support placement behavior. The approved body controls follow locomotion phase and activity, retaining the reduced Tarbosaurus vertical response. These remain engineering body-response controls, not a converged force simulation.

Material contact acquisitions are derived before body-control application and held during their support interval. Corrections run after body response. Each GLB has 1127 source keys (60 Hz plus stage joins); the saved GLB is reopened and its keys and interpolation midpoints measured. Source-key contact residuals do not substitute for saved playback checks.

The first pass exposed a shared transition defect: reduced-speed stance rolled into an unscaled full-speed swing heel angle. The second pass carries the push-off amplitude through lift-off and releases it smoothly. The normal walk retains a default release scale of one.

Focused verification: 40 passing tests covering stage continuity, integrated root speed, immobile stance placements, support availability, transition coordination, heel-release amplitude and rolling-plan binding. Production contact/dynamics acceptance, Unity parity and user approval of this sequence remain separate.

Final review packages: allo-sequence-b and tarbo-sequence-b. The earlier unsuffixed packages and interrupted render folders are superseded diagnostic attempts, not review baselines.

## Saved playback contact measurements

- allo: maximum loaded-material residual 0.131 mm; deepest full-mesh floor penetration 0.703 mm. Production contact gate remains unpassed.
- tarbo: maximum loaded-material residual 0.230 mm; deepest full-mesh floor penetration 5.646 mm. Production contact gate remains unpassed.

The Tarbosaurus residual floor dip is concentrated at its first toe-off interpolation interval. It is explicitly retained for playback review rather than holding the visual checkpoint for another correction pass. User approval of the full sequence is PENDING.

## Timeline

- 0.00–5.72 s: idle/start walking.
- 5.72–8.18 s: normal walk.
- 8.18–10.27 s: speed up.
- 10.27–12.10 s: faster walk.
- 12.10–14.19 s: slow down.
- 14.19–18.68 s: stop/idle.

## Reproduction

Use the archived source with its recorded environment. Run `tools/build_walk_sequence_preview.py` with `--repo`, the recorded `--motion-set`, `--mass-receipt` pointing to the final package body-support-coordination.json, and a new `--output`. Then run `tools/render_candidate.py` in Blender with the saved camera lock, 24 fps, root_motion mode. `tools/check_walk_sequence_preview.py` measures the reopened GLB against its recorded source baseline.

## Review media and pause

- allosaurus-connected-walk.mp4
- tarbosaurus-connected-walk.mp4

Both are 449 frames at 24 fps, 18.708333 seconds, side/front together. Hashes and decoded frame counts are recorded in review-media.json. All iteration-owned render/build/check processes have ended. PAUSED FOR USER PLAYBACK FEEDBACK.
