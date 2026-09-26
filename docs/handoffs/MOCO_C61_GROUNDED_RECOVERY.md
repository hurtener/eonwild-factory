# C61 — body-floor contact and whole-body recovery

Status: **VISUAL REVIEW PENDING; PHYSICAL ACCEPTANCE FAILED**. Stop for user review.
C60 floor actions were rejected for hovering and unsupported rising. C61 is a focused
foundation checkpoint: eight takes, four families, both admitted animals. It does not
replace the approved locomotion baseline or complete the remaining 29-family polish.

## Review media

All comparisons are native time, 24 fps, 1280×720. Tarbo top, Allo bottom;
side view left, quarter view right. Individual full-resolution views are alongside them.

- [Running fall, 6 seconds](../../game/Evidence/moco-c61-grounded-recovery/running-fall-comparison.mp4)
- [Roll and get up, 9 seconds](../../game/Evidence/moco-c61-grounded-recovery/get-up-comparison.mp4)
- [Rest, sleep and rise, 16 seconds](../../game/Evidence/moco-c61-grounded-recovery/rest-sleep-rise-comparison.mp4)
- [Standing impact recoil, 12 seconds](../../game/Evidence/moco-c61-grounded-recovery/standing-hit-comparison.mp4)

Factory readers: these relative video links resolve in the principal game repository.
Evidence root: /Volumes/m2-extended-disk/Repos/eonwild/game/Evidence/moco-c61-grounded-recovery.

## What changed

The old floor handling used approximate body radii plus root clearance; it could keep
a rigid floating body above ground and raise it without first forming a useful stance.
Fresh source-skin support witnesses now describe the chest, trunk, thighs, head and
tail. A shared bounded coordinator solves body support, foot anchors and root position
together. This remains an approximate rigid-body representation of deforming skin.

Recovery folds the legs while low, rolls with coordinated chest/neck/head/tail motion,
plants the two feet asymmetrically from the admitted stable standing stance, then
extends the legs and raises the body. Body clearance increases continuously during
the rise. Axial velocity/acceleration regularization removed the sharp head release
observed in an internal pilot. No species-specific solver or widened joint range was
introduced. Behavior timing and pose intent remain authored data.

Running falls include a lateral catch-foot target and torso counterbend before body
support. Standing hits add opposing pelvis/chest yaw, neck response and delayed tail
bend. These are visual attempts at the requested failed catch and C-shaped recoil;
they do not establish real injury, damage or collision force.

## Scientific and visible limitations

**No new predictive Moco solve converged.** These are bounded authored coordination
candidates with OpenSim inverse-dynamics replay. Large force residuals and actuator
commands fail physical acceptance. Do not describe the result as a validated muscle-
powered recovery. More hip rotation does not itself establish more available torque.

Existing hip yaw ±0.22 rad, hip roll ±0.30 rad and sagittal limits were retained.
These are engineering priors, not measured dinosaur maximum recovery ranges.
Future deep-pose admission needs defensible joint axes/ranges, moment arms, and
self-collision/contact treatment; never silently increase limits for a prettier pose.

Actual reopened skin still penetrates the floor during deep folding: up to about
15.8 cm on Tarbo and 23.7 cm on Allo body regions, and 6.0 cm on feet across this
batch. This is a remaining contact defect, not a production pass. The rigid witness
model does not exactly follow blended skin. Global root lifting would restore the
original hover and is not an acceptable correction. The leg-driven rise and roll
choreography can be reviewed independently of those unresolved contact/force errors.
The failed-catch step and impact bend may still need stronger artistic emphasis.

| Take | Dense root residual RMS / BW | Maximum command | Sampled joint violations |
| --- | ---: | ---: | ---: |
| tarbo-running-fall | 1.897 | 21.36 | 0 |
| tarbo-get-up | 8.256 | 200.74 | 0 |
| allo-running-fall | 1.461 | 423.08 | 0 |
| allo-get-up | 10.825 | 89.29 | 0 |
| tarbo-rest-sleep-rise | 10.002 | 332.83 | 0 |
| tarbo-standing-hit | 0.080 | 9.69 | 0 |
| allo-rest-sleep-rise | 14.997 | 242.26 | 0 |
| allo-standing-hit | 0.113 | 4.53 | 0 |

Dense replay metrics above are diagnostic; native-frame sampling is used for skin
retargeting to avoid spline overshoot. Reopened knee/ankle checks also report no
sampled violations. Neither sampled bounds nor attractive media prove dynamics.

## Exact provenance and continuation

Factory branch: codex/moco-c52-walk-turn.
Game review branch: codex/moco-c52-walk-turn-review. Accepted main remains unchanged.
Final fall/hit takes were generated at factory b6f233b; get-up/rest at
5af23e1315d735ac4f94d75a8fd6170735c388d2. Each take has exact provenance hashes,
stage commands, process exits, plan, model, solution, native replay, dense replay
(gzip), retarget report and GLB. Do not use intermediate callback trajectories.

Selected research directories under task storage:
- research/moco-c61-grounded-recovery-e: running-fall and standing-hit only.
- research/moco-c61-grounded-recovery-h: get-up and rest-sleep-rise only.

Other C61 pilots are not selected. In particular G get-up had a sharp head release.
Do not accidentally present or overwrite the selected media with those candidates.

The evidence scripts/batch.json identifies all eight exact takes. scripts contains
generation, rendering, compact-sheet and archive commands. takes/<id>/process.json
is the authoritative generation command list; render.json and capture receipts
record the Unity replay. scripts/generate.py skips preserved E takes intentionally.
For regeneration of an E take, use its archived process commands at b6f233b.

Run from the factory worktree with PYTHONPATH=src, OPENBLAS_NUM_THREADS=1,
OMP_NUM_THREADS=1. OpenSim Python is research/opensim-2026-09-20/moco-venv/bin/python;
retarget/test Python is venvs/contact-mass/bin/python, both under task storage.
Unity is /Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity.

Inputs are archived once by SHA in inputs/*.json.gz, indexed by archived-inputs.json.
Unpack into a fresh research directory and replace original absolute paths in copied
plans/commands. Keep originals and receipts immutable. Catalog/geometry dependencies
remain in the factory repository at the source commit; admission profiles are archived.
Do not execute archived scripts blindly: their absolute output paths target originals.

## Verification and remaining work

12 focused tests passed: ground support, behavior intent, living intent, placement task.
Every captured quarter-view frame was inspected as ordered frame sheets (24 fps);
side-view inspection covered fall/impact 2–4s, get-up 4–6s, rest 2–4s and 12–14s.
This was frame-sequence inspection, not direct perception of continuous video.
Capture counts and complete MP4 decoding are recorded in media-validation.json.
User approval remains pending. Unity diagnostic rendering is not gameplay parity.

After feedback: fix deep-pose surface contact and force feasibility, then propagate
the reviewed foundation to walking/sprint falls, death and moving hits. Preserve
all approved walking/running/turning takes. Do not declare the 29 families polished
or production-ready based on candidate breadth.
