# C60 living library — review checkpoint

The user requested all remaining animation families with living polish on both
animals, then one combined review. Work was direct; no subagents. The 29-family
normalization excludes secondary layers and infrastructure from the count.
Visual approval remains pending. Do not merge, auto-approve, or resume polishing
without the next user direction.

## Open the review

Principal evidence directory: `game/Evidence/moco-c60-library/`.
Open `index.html` for the offline family player and optional local feedback.
`C60-all-29-families.mp4` is the chaptered four-view reel, native 24 fps.
Top row Tarbo; bottom Allo. Side left; quarter right.
Every family also has individual animal/camera MP4s. Finite actions are not
seamless loops. This is plain-stage Unity playback, not the full demo world.

## Implementation and provenance

Factory worktree:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration`.

Research:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c60-library-final`.

Game: `/Volumes/m2-extended-disk/Repos/eonwild`.
Review branches: `codex/moco-c52-walk-turn` (factory) and
`codex/moco-c52-walk-turn-review` (game). No change to accepted main.

Generation is pinned to factory `28b2c4988e79815ae0a6c9ebd656455b10f3da67`;
native-state export correction is `ded3d42`. Viewer context is game
`4adf5cf`. These are source commits, not the later documentation/evidence commits.
Per-take provenance and input-map preserve exact source and plan hashes.

Read the archived README and scripts for complete commands. Python P is task
storage `venvs/contact-mass/bin/python`; OpenSim Python M is
`research/opensim-2026-09-20/moco-venv/bin/python`.
Set `PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` in the factory.
Generate with the recorded sequence command, exact-model replay, then retarget.
Use ONE renderqueue against Unity 6000.3.23f1; it stages the selected GLB/profile,
builds the review player and captures side/quarter at 24 fps. Never render scaled
optimizer callback files. Create new output directories for another candidate.

Native-state correction avoids unconstrained resampling-spline overshoot without
changing original source coordinates or joint limits. Original dense diagnostics,
GLBs and media remain archived. This does not fix failed dynamics or certify
continuous-time behavior. Environment-inclusive force balance is reported
separately for water because the legacy metric includes ground forces only.

## What is still unfinished

All new families are authored bounded coordination and inverse-dynamics
candidates, not independently converged Moco predictive solutions. Contact,
slip and high effort/residual failures remain measurable. Never weaken their
thresholds to promote a visual candidate. Model proxies for fallen/resting
body support remain approximate; get-up can read lifted during its middle
phase. Water uses time-baked buoyancy/drag, terrain is one defined obstacle,
and hit/jump/sprint capability is an engineering/artistic proposal.

Every native video frame was inspected in ordered contact sheets/overviews;
this is image-sequence inspection, not direct video perception. Notes and
measurements are in visual-inspection.json and physical-summary.json.
Eleven focused behavior/living/placement tests passed. Viewer playback does
not establish production gameplay parity. All 29 visual decisions remain
pending; use the user's feedback to choose the next bounded pass.

| # | Family | Saved review | Reel start | Open work |
| --- | --- | --- | --- | --- |
| 01 | idle-alert | C59B preserved, both animals | 00:00 | Visual decision pending; force/contact not certified |
| 02 | walk | C60 candidate, both animals | 00:12 | Visual decision pending; force/contact not certified |
| 03 | fast-walk | C60 candidate, both animals | 00:28 | Visual decision pending; force/contact not certified |
| 04 | start-stop | C60 candidate, both animals | 00:40 | Visual decision pending; force/contact not certified |
| 05 | walking-turn | C60 candidate, both animals | 00:56 | Visual decision pending; force/contact not certified |
| 06 | pivot | C59B preserved, both animals | 01:12 | Visual decision pending; force/contact not certified |
| 07 | retreat | C59B preserved, both animals | 01:24 | Visual decision pending; force/contact not certified |
| 08 | lateral | C59B preserved, both animals | 01:36 | Visual decision pending; force/contact not certified |
| 09 | standing-hit | C60 candidate, both animals | 01:48 | Visual decision pending; force/contact not certified |
| 10 | walking-hit | C60 candidate, both animals | 02:00 | Visual decision pending; force/contact not certified |
| 11 | running-hit | C60 candidate, both animals | 02:12 | Visual decision pending; force/contact not certified |
| 12 | sprint-hit | C60 candidate, both animals | 02:24 | Allo foot penetration up to 4.6 cm; force/contact not accepted |
| 13 | walking-fall | C60 candidate, both animals | 02:36 | Ground/body support approximate |
| 14 | running-fall | C60 candidate, both animals | 02:48 | Impact and body support approximate |
| 15 | sprint-fall | C60 candidate, both animals | 03:00 | Impact and body support approximate |
| 16 | get-up | C60 candidate, both animals | 03:12 | Middle ascent needs more muscular support |
| 17 | run | C60 candidate, both animals | 03:24 | Visual decision pending; force/contact not certified |
| 18 | sprint | C60 candidate, both animals | 03:36 | Visual decision pending; force/contact not certified |
| 19 | feed | C60 candidate, both animals | 03:48 | Visual decision pending; force/contact not certified |
| 20 | drink | C60 candidate, both animals | 04:00 | Visual decision pending; force/contact not certified |
| 21 | rest-sleep-rise | C60 candidate, both animals | 04:12 | Side-lying contact and rise need refinement |
| 22 | attack-defense | C60 candidate, both animals | 04:30 | Visual decision pending; force/contact not certified |
| 23 | limp | C60 candidate, both animals | 04:42 | Visual decision pending; force/contact not certified |
| 24 | death | C60 candidate, both animals | 04:54 | Ground support approximate; living motion fades |
| 25 | jump-land | C60 candidate, both animals | 05:06 | Authored capability; landing force not certified |
| 26 | terrain-step | C60 candidate, both animals | 05:18 | One specified obstacle; general terrain pending |
| 27 | wade | C60 candidate, both animals | 05:30 | Prescribed water loads; no fluid feedback |
| 28 | swim | C60 candidate, both animals | 05:42 | Authored propulsion; no swimming prediction |
| 29 | display | C60 candidate, both animals | 05:54 | Visual decision pending; force/contact not certified |
