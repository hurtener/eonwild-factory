# Eonwild — self-contained continuation prompt (28 September 2026)

You are taking over Eonwild animal-animation work on this Mac. The user is testing
another coding agent. Read this as a factual handoff and working procedure, not
an instruction to preserve the previous agent's algorithms or proposed solution.
Investigate the motion yourself, explain your diagnosis, choose the implementation,
produce a bounded reviewable iteration, and pause for feedback. Do not launch a
large unattended rewrite or replay the entire historical experiment series.

## 1. Purpose and boundaries

We want convincing, living, heavy dinosaurs for a Unity game: currently Tarbosaurus
and Allosaurus. They should share reusable mechanics and semantic animal data.
Different anatomy, mass, strength and behavior can produce different motion without
species-specific patches. Distinct movement tasks may need different formulations;
there is no requirement to force every behavior through one gait algorithm.

We are investigating whether offline OpenSim/Moco biomechanics can give stronger,
more transferable starting motions than the older extensively authored solver.
We want scientifically defensible inputs and clear uncertainty, plus animation
that reads well at native speed. The aim is not a perfect numerical score at the
expense of visible progress, nor attractive motion mislabeled as validated physics.
Unity consumes the resulting assets and provides gameplay interaction. The precise
numerical method, model detail, controller architecture and correction strategy
for your next experiment are yours to evaluate. Existing code is evidence, not a
mandated answer. Older documents' “next implementation” sections are historical
proposals, not obligations for this continuation.

Work directly, without subagents. The latest user workflow overrides older
AGENTS.md sections requesting orchestration. Do not wake historical agents,
optimizations or scheduled automations. Preserve accepted assets and unrelated
working files. No merge to main or automatic visual approval.

## 2. Exact computer locations and Git state

All large work belongs on the external SSD, not the main system drive or /tmp.
These paths and remote heads were checked on 2026-09-28. Recheck before modifying.

```sh
export TASK=/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526
export W="$TASK/worktrees/stride-hip-visual-iteration"
export G=/Volumes/m2-extended-disk/Repos/eonwild
export M="$TASK/research/opensim-2026-09-20/moco-venv/bin/python"
export P="$TASK/venvs/contact-mass/bin/python"
export UNITY=/Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity
export PLAYER="$G/game/Builds/Eonwild Moco.app/Contents/MacOS/Eonwild Floodplain"
export ENCOUNTER="$G/game/Builds/Eonwild Encounter.app/Contents/MacOS/Eonwild Floodplain"
export PATH="/opt/homebrew/bin:$PATH"
```

| Repository | Active location / branch | Verified saved head |
| --- | --- | --- |
| Motion factory | `$W`, `codex/moco-c52-walk-turn` | `eaa909b85e50320a5a09e302479bd0f9c53e90b4` |
| Principal game / Unity / review evidence | `$G`, `codex/moco-c52-walk-turn-review` | `20d337d70f09455c5c1aecd4867184a9c44bf74f` |

Remotes: https://github.com/hurtener/eonwild-factory and
https://github.com/hurtener/eonwild. Both review heads above were pushed.
Factory uses the personal SSH host alias `github.com-personal`; game uses HTTPS.
Use their configured origin, not a different account.

`/Volumes/m2-extended-disk/Repos/eonwild-factory` is the principal factory checkout,
but is **not the current animation worktree**. Its README/branch can be stale.
Use `$W` for current mechanics. Branch names still say C52 but contain C62.

Preserved remote main heads contain C50-era baseline work:
- Factory: `9868716ae029a43d4c16715f8c06a1e6f10d7451`.
- Game: `9b16390cf5ef9c9a6e08d681ffaa9189b7893bcd`.

Tracked working state was clean before this handoff. There are many untracked
historical/pilot assets, research outputs and catalog variants. Do not run
`git clean`, broad deletion, reset, or `git add .`. Inventory ownership first.
The generated app is local and not committed. Environments are machine-specific.

Start with:
```sh
cd "$W"
git status --short
git log -3 --oneline
git -C "$G" status --short
git -C "$G" log -3 --oneline
"$M" -c 'import opensim as o; print(o.GetVersionAndDate())'
"$P" -c 'import numpy, scipy, PIL; print(numpy.__version__, scipy.__version__, PIL.__version__)'
```
Verified here: OpenSim `4.6-2026-06-22-85aaf64`; scientific environment NumPy
2.5.2, SciPy 1.18.1, Pillow 12.3.0. The former Fortran/IPOPT loading problem in
old research notes was resolved. Do not reinstall everything on that old claim.

## 3. Read these authorities, with their dates in mind

- `$W/AGENTS.md`, `$W/README.md`.
- `$W/docs/FACTORY_ROADMAP.md` — current top section, then historical inventory.
- `$W/docs/UNITY_MOTION_CONTRACT.md`.
- `$G/docs/IMPLEMENTATION_ROADMAP.md`.
- `$G/docs/ANIMATION_ART_DIRECTION.md` — accumulated user feedback.
- `$G/docs/handoffs/C62_INTERACTIVE_ENCOUNTER.md`.
- `$G/game/Evidence/moco-c62-encounter/REVIEW.md`.
- `$G/docs/handoffs/MOCO_C61_GROUNDED_RECOVERY.md`.
- `$G/docs/handoffs/MOCO_C60_LIVING_LIBRARY.md`.

The roadmaps retain historical sections, some of which say “missing” after a
later section has added a candidate. Read top-down and distinguish existence
from approval. Older README pointers still name C47; they are not current status.

`$W/docs/handoffs/MOCO_CONTINUATION_2026-09-21.md` is a detailed older scientific
handoff with command examples. Its branch names, source choice and next checkpoint
are obsolete. Use it as history, not as a request to restart C47.
The independent old-solver fallback is documented in
`$W/docs/handoffs/SHARED_SOLVERS_CONTINUATION_2026-09-21.md` (also in game docs).
That preserves C39 B as a preferred Tarbo reference and distinguishes C40–C42
experiments. Do not conflate old shared-solver approval with Moco approval.

## 4. Animation status: what exists versus what is approved

Earlier Moco-path visual decisions, preserved independently:

| Motion | Tarbo | Allo |
| --- | --- | --- |
| Straight walk/start/stop | C52B H visually approved | C58B received positive feedback except missing distal relaxation; C58C adds it, pending explicit review |
| Sustained run | C51 A visually approved | C58B candidate; not approved |
| Walking turn | C53 A approved; C54 B received positive feedback | Newer library transfer exists; not approved |
| Backward retreat | C56 visually approved; later C59B variation exists | C59B candidate |
| Mixed walk/turn/reverse/run sequence | C57C diagnostic, polish deferred | No equivalent approved sequence |

These are visual approvals, not muscle/force certification. Conventional pre-Moco
walks, turns, reverse, balance steps, impact recovery and connected controls also
have approved historical baselines. Preserve their separate handoff/evidence.

C60 delivered a **29-family candidate library for both animals**. Its video is
not evidence that 29 families were approved. C60 floor motions were explicitly
rejected for hovering and unsupported recovery. C61 revised four affected families;
C62 combined selected clips in a live interaction prototype. Neither has subsequent
user approval recorded at this handoff.

| # | Family | Latest relevant candidate / status |
| --- | --- | --- |
| 01 | Idle / alert | C59B preserved in C60; review pending |
| 02 | Walk | C60 library candidate; earlier approved/positive baselines above remain separate |
| 03 | Fast walk | C60, pending |
| 04 | Start / stop | C60, pending; preserve earlier Tarbo approval |
| 05 | Walking turns | C60, pending; preserve earlier Tarbo approval |
| 06 | Pivot in place | C59B preserved in C60, pending |
| 07 | Retreat | C59B preserved in C60, pending; preserve C56 Tarbo |
| 08 | Lateral balance step | C59B preserved in C60, pending |
| 09 | Standing hit | C61 revision, pending |
| 10 | Walking hit | C60, pending |
| 11 | Running hit | C60, pending |
| 12 | Sprint hit | C60, pending; known contact defects |
| 13 | Walking fall | C60 floor candidate rejected; revision pending |
| 14 | Running fall | C61 revision, pending; used in C62 |
| 15 | Sprint fall | C60 floor candidate rejected; revision pending |
| 16 | Get up | C61 revision, pending; used in C62 |
| 17 | Run | C60 candidate; preserve C51 Tarbo baseline |
| 18 | Sprint | C60, pending; capability not physically certified |
| 19 | Feed | C60, pending |
| 20 | Drink | C60, pending |
| 21 | Rest / sleep / rise | C60 rejected; C61 revision pending |
| 22 | Attack / defense | C60, pending |
| 23 | Limp | C60, pending |
| 24 | Death | C60 ground-support candidate; not accepted |
| 25 | Jump / land | C60 authored capability, pending |
| 26 | Terrain step | C60 one-obstacle demonstration; general terrain unvalidated |
| 27 | Wade | C60 prescribed water-load candidate, pending |
| 28 | Swim | C60 authored candidate; not a predictive swimming simulation |
| 29 | Display | C60, pending |

Broader gaps include convincing ground recovery, physical feasibility, animal
collision handling, more general interruptions/terrain, production performance,
and contextual living behavior. Do not count infrastructure/secondary layers as
extra completed movement families.

## 5. Latest output and saved images — inspect these first

All paths below are beneath `$G/game/Evidence/` unless absolute.

**C62 interactive encounter**: `moco-c62-encounter/`.
- `encounter-native-120s.mp4`: 120 seconds, native 24 fps, 1280×720, 2,880 frames.
- `candidate-final/frames/00000.png` through `02879.png`: **all raw images exist
  locally**, not committed. These are the selected final generation, not `candidate/`
  or `pilot-*`. At 24 fps, frame number = time × 24.
- Useful full-size examples: `00312.png` (13 s), `00420.png` (17.5 s), `01800.png`
  (75 s). These expose recovery/body overlap rather than hiding it.
- `frame-review/00.jpg` through `23.jpg`: committed chronological sheets covering
  every frame, 120 frames per sheet. `frame-review.json` includes frame hashes.
- `candidate-final/runtime.json`, `tarbo-contacts.csv`, `allo-contacts.csv`.
- `performance-final/runtime.json`, `runtime-invariants.json`, `validation.json`,
  `provenance.json`, `recipe.json`, `video.json`, `REVIEW.md`.
- Video captured from `88ae3febff86252eb2f75641e4bfbdf8736c5cba`; delivery commit
  `20d337d...` adds evidence and manual-session lifecycle fixes. Provenance records
  both source states; do not silently claim the capture used later source code.

Remote video:
https://github.com/hurtener/eonwild/blob/20d337d70f09455c5c1aecd4867184a9c44bf74f/game/Evidence/moco-c62-encounter/encounter-native-120s.mp4

C62 implements a shared clip consumer, current-pose adoption, root-motion ownership,
kinematic skin-contact accommodation and threat-directed attention. World proximity
and closing speed trigger authored reactions. It is **not a new Moco solution**,
not a validated collision/impulse system and not AA ready.

Observed C62 defects/evidence:
- Body overlap during recovery; long repetitive retreat. The camera cannot fix
  actual overlap. Do not claim these are polished encounter choreography.
- Final skin penetration maxima: 2.49 mm Tarbo / 2.86 mm Allo. But support-witness
  mismatch reaches 194 / 201 mm and body corrections reach 454 / 491 mm.
- Eight actual-rig pose-adoption checks pass. This does not prove angular-velocity,
  force continuity, complete interruption coverage or continuous runtime parity.
- M4 MacBook Air, 24 GB, uncaptured 40-second test: median 16.93 ms, p95 31.53 ms,
  p99 33.35 ms. Not locked 60 FPS; no mobile claim. Variable-time contact results
  differ from the fixed-rate recording.
- Manual keyboard smoke was blocked by a locked Mac. Autonomous playback was run.

**C61 individual motion revision**: `moco-c61-grounded-recovery/`.
- `running-fall-comparison.mp4`, `get-up-comparison.mp4`,
  `rest-sleep-rise-comparison.mp4`, `standing-hit-comparison.mp4`.
- Native 24 fps comparisons: Tarbo top, Allo bottom; side left, quarter right.
- `inspection/<take-id>/side-*.jpg` and `quarter-*.jpg`: saved frame sheets.
- `takes/<take-id>/`: exact model.osim, solution.sto, plan.json, process/provenance,
  replay/retarget receipts. Inspect files; some dense replay is compressed.
- `scripts/batch.json` resolves the eight takes and inputs.
- Selected raw working research: `$TASK/research/moco-c61-grounded-recovery-e`
  for fall/hit, `...-h` for get-up/rest. Other letters are pilots, not selections.
- C61 still has substantial deep-pose skin penetration and force/effort failures;
  C62's runtime correction does not retroactively fix C61's physical evidence.

**Full library**: `moco-c60-library/`.
- `index.html`, `C60-all-29-families.mp4`, individual numbered `*-review.mp4`.
- `README.md`, `input-map.json`, `physical-summary.json`,
  `visual-inspection.json`, `sha256-manifest.json`.
- Root of numerical working batch: `$TASK/research/moco-c60-library-final`.

**Allo distal walking refinement**: `moco-c58c-distal-release/`:
`c58c-allo-walk-side.mp4` and `c58c-allo-walk-quarter.mp4`.

## 6. What “Moco” means in the current work

The research path includes an OpenSim articulated model, contact mechanics,
mass/inertia and finite estimated actuator capacities, numerical initializers,
authored task coordination, inverse-dynamics replay, optional full Moco studies,
and rig retargeting. A directory or tool named moco does **not** mean its output
was independently predicted or converged by Moco.

C51's bounded full Moco attempts ended without convergence. C60/C61 are primarily
bounded authored coordination candidates with OpenSim replay, not 29 independently
converged predictive motions. C62 is a Unity runtime layer over selected takes.
No new full Moco solve converged for C62. Prior tiny runtime smoke examples are
not dinosaur convergence. Read exact receipts before making stronger claims.

The scientific question remains whether anatomy, contact, mass, inertia and
credible capacity estimates can explain and generate convincing coordinated
motion across animals and tasks with less hand-authored joint choreography.
Muscle-driven physiology, reduced torque actuation, fitting and runtime kinematic
correction are different claims. State which one you implemented and tested.

Separate: generated candidate; optimizer termination; force/contact feasibility;
independent stability; final skinned geometry; Unity behavior; visual approval.
A failed solve remains failed, even if its initializer looks good. Never render
variable-scaled optimizer callback trajectories as physical motion; replay the
returned unscaled solution.sto, or explicitly identify a diagnostic initializer.

The current Tarbo source has 12 connected tail links / 13 ordered tail nodes.
An earlier 12-controls-to-8-link mismatch caused artifacts and was repaired.
See `$W/docs/handoffs/MOCO_C50_TAIL_REPAIR.md`. Its admitted motion set is
`catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.tail12-connected.json`.
Do not silently use the older tail source or assume “12 bones” identifies a rig.
Allo current C61 motion set is
`catalog/motion-sets/allosaurus-engineering-native-walk.v21.json`.
Exact profiles, sources and hashes are in each take's process/provenance receipt.

Existing code map, for navigation rather than implementation prescription:
- `$W/src/eonwild_motion/solve/moco_*.py` — current reduced model, task,
  coordination, support, contact, attention and replay-related logic.
- `$W/tools/*moco*.py` — admission/build/sequence/replay/retarget/audit entrypoints.
- `$W/catalog/` — animal, rig, embodiment, behavior, motion-set and baseline data.
- `$G/game/Assets/Eonwild/Scripts/EncounterMotionMotor.cs`, `CreatureEncounter.cs`.
- `$G/game/Assets/Eonwild/Editor/EncounterReviewBuilder.cs`,
  `EncounterRuntimeChecks.cs`, `MocoPrototypeReviewBuilder.cs`.
- `$G/game/Assets/Eonwild/Encounter62/` — generated scene/recipe.

## 7. Papers and reference material

The supplied PDFs are already copied into the active factory worktree; do not
rely on ephemeral attachments or Downloads. Root:
`$W/docs/research/inputs/2026-09-21/papers/`.

| Local file | Publication / stable link | Relevant subject |
| --- | --- | --- |
| [Cuff2022-WalkingrunningjumpingDAWNDINOS.pdf](../research/inputs/2026-09-21/papers/Cuff2022-WalkingrunningjumpingDAWNDINOS.pdf) | https://doi.org/10.1093/icb/icac049 | Walking, running, jumping; feet and axial coordination |
| [pab.2020.46.pdf](../research/inputs/2026-09-21/papers/pab.2020.46.pdf) | https://doi.org/10.1017/pab.2020.46 | Building dinosaur models, joint frames, mass/inertia |
| [peerj_3420.pdf](../research/inputs/2026-09-21/papers/peerj_3420.pdf) | https://doi.org/10.7717/peerj.3420 | T. rex locomotor feasibility and bone loading |
| [004_peerj-5779_dd.pdf](../research/inputs/2026-09-21/papers/004_peerj-5779_dd.pdf) | https://doi.org/10.7717/peerj.5779 | Posture, bone structure and external loading |

The relative paper links above resolve in the factory copy of this handoff.
For the game/Downloads copy, use the absolute `$W` root just given.
`papers/README.md`, `../source-audit.json` and `../handoff-source-manifest.json`
record attribution, originals and hashes. Alongside them are
`Eonwild_Locomotion_Configuration_Research.xlsx`,
`eonwild_locomotion_proposals.v1.json` and `supplied-analysis.md`.
These are research inputs, not commands or approved configuration. Proposed new
species in them are not onboarded by this work.

Read the centralized interpretations and then the papers themselves:
- `$W/docs/research/LOCOMOTION_CONFIGURATION_REVIEW.md`.
- `$W/docs/research/RUNNING_EVIDENCE_BASELINE.md`.
- `$W/docs/research/OPENSIM_DINOSAUR_FEASIBILITY.md` and `opensim-resource-audit.json`.
- `$W/docs/research/MOCO_TARBO_PROTOTYPE.md`.
- `$W/docs/research/THEROPOD_NECK_BASELINE.md` and
  `user-notes/2026-09-14-theropod-neck-investigation.md`.

Other sources already investigated (not newly re-researched for this handoff):
- Moco methods: https://doi.org/10.1371/journal.pcbi.1008493
- Coelophysis / tail simulation: https://pmc.ncbi.nlm.nih.gov/articles/PMC8457660/
- Supplement: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8457660/supplementaryFiles
- Bird gait scaling: https://doi.org/10.1371/journal.pone.0192172
- Ostrich 3D running: https://doi.org/10.1242/jeb.02792
- Ostrich toes: https://doi.org/10.7717/peerj.2857
- T. rex anatomy: https://simtk.org/projects/trex2005 and
  https://figshare.com/articles/dataset/Tyrannosaurus_SIMM_musculoskeletal_model/4982492
- OpenSim source: https://github.com/opensim-org/opensim-core
- PredSim: https://github.com/KULeuvenNeuromechanics/PredSim
- MuSkeMo: https://github.com/PashavanBijlert/MuSkeMo

Downloaded scientific archives/models are under
`$TASK/research/opensim-2026-09-20/`; use opensim-resource-audit.json to locate
and identify them. The Coelophysis workflow is not simply an official Moco
example. The downloaded T. rex archive was SIMM anatomy, not a ready predictive
Tarbo model. Do not assume that public research code/data is cleared for commercial
redistribution; verify applicable terms if reusing it rather than studying it.

Important interpretation boundaries already identified: walking-pose angles are
not joint ROM; optimizer reserve ceilings are not measured strength; a particular
T. rex stress limit is not automatically our Tarbo speed limit; artist rig angles
need calibrated anatomical frames. Record units, source and uncertainty. Distinguish
measured evidence, comparative extrapolation and authored game choices. You may
challenge prior interpretations with evidence.

Animation references in `$W/assets/examples/`:
- `allosaurus/allo-walking-reference.mp4`.
- `tarbosaurus/allo-turning-example.mp4` (the user originally mislabeled this
  reference as Tarbo; it depicts Allo choreography).
- `tarbosaurus/tarbosaurus_walk.mp4`, `tarbosaurus-walking-looking.mp4`.
- `tarbosaurus/v9_evidence/running-sustained-left.mp4`, `sprint-left.mp4`,
  `RUN START-RUN-RUN STOP.mp4`, `BODY SHOVE → SMALL STUMBLE → RECOVERY.mp4`.
- User's external artistic reference: https://www.youtube.com/watch?v=0tvANFTJXN0
  (reference animation, not experimental dinosaur biomechanics).

## 8. User's visual expectations, without prescribing a solver

Movement should feel like one coordinated body, not a chain of start/stop joints.
The ankle must not flick back and forth or hyperextend while the knee stays frozen.
Allo previously looked constrained with a short stroke; “freer knee” meant more
extension on the forward path, not simply more flexion. Foot recovery includes
relaxation before preparing to receive weight. Starts should not take many sluggish
steps to reach normal cadence. Stops should not reverse an arbitrary half-step.

Turning uses head/neck interest and asymmetric footwork; the body is not a spinning
top. Rest/pivot support can be wider than straight walking. Avoid imposed outward
foot yaw in a turn. Mass transfer should not look like sideways ankle collapse or
a bouncing weightless pelvis. Running has powerful support and recovery; distinguish
artistic flight intent from what the physical model actually demonstrates.

Tail, proximal tail, torso, arms and jaw should feel alive. Focused running needs
a comparatively quiet nose with a compensating neck, not a jello neck/body or a
springing tail. Attention should have context, not continuous random noise.

The latest ground-motion complaint is especially important: no hovering body or
floating-matrix rise. Rolling/getting up must visibly use the whole body, with
feet brought into usable support and effort apparent through the rise. The user
expects an urgent attempted catch before a fall, possibly crossing steps, and
whole-body C-shaped impact recoil. Their suggestion of larger hip rotation/torque
is an artistic/biomechanical question to investigate, not authorization to invent
or silently widen anatomical limits. Study the current output before deciding how.

## 9. How to run existing tools (procedural examples, not a prescribed solution)

Use unique candidate names and output directories. Commands below show existing
interfaces. Inspect arguments/receipts for the selected task. Do not paste-run an
old archived batch script: it can contain hardcoded destinations and overwrite
historical render folders. Run generation, replay and rendering sequentially,
checking each result. Only one Unity editor/build owns `$G/game` at a time.

Working directory for Python mechanics:
```sh
cd "$W"
export PYTHONPATH=src
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
# Pick an UNUSED name; C63 is merely an example, not a reserved checkpoint.
export N="$TASK/research/moco-c63-example-a"
export NE="$G/game/Evidence/moco-c63-example-a"
mkdir "$N" "$NE"
```

Exact previous command recipes:
`$G/game/Evidence/moco-c61-grounded-recovery/takes/<take-id>/process.json`.
Render args are in the associated render receipts and `scripts/render.py`.
`source`, `baseline`, `plan`, `motion_set` and `profile` are resolved by
`scripts/batch.json`. Inspect rather than guessing from the take name.

For example, the C61 behavior-generation interface (set SOURCE, BASELINE, PLAN,
MOTION_SET and PROFILE from a chosen receipt, and copy/edit the plan in `$N`):
```sh
"$M" tools/sequence_moco_behavior.py --source "$SOURCE" \
  --baseline "$BASELINE" --plan "$PLAN" --output "$N/take"
"$M" tools/replay_moco_prototype.py "$N/take"
"$P" tools/select_native_moco_replay.py \
  "$N/take/replay.json" "$N/take/replay-native.json"
"$P" tools/retarget_moco_prototype.py --motion-set "$MOTION_SET" \
  --profile "$PROFILE" --replay "$N/take/replay-native.json" --output "$N/skin"
```
Some existing tasks use `tools/sequence_moco_retreat.py` with the same four input
flags. Native selection avoids an export-resampling artifact; keep dense replay
for diagnostics. This command chain is not itself full Moco optimization.

The separate full Moco interface is:
```sh
"$M" tools/build_moco_prototype.py --help
# After choosing compatible admission, recipe, task and returned warm start:
"$M" tools/build_moco_prototype.py --admission "$ADMISSION" --recipe "$RECIPE" \
  --warm-start "$WARM_START" --mesh "$MESH_INTERVALS" --output "$N/full-solve"
```
Do not assume old periodic/reflected-stride studies support arbitrary finite
falls/turns. Check task compatibility before launching. Choose and report a bounded
budget; save PID, command, source SHA, timeout and exit status. Do not duplicate
an existing active optimization. User's overnight preference: inspect long-running
optimizers no more often than once every ten minutes. No optimizer is authorized
merely because an example command appears here.

To display a newly exported individual motion, choose an unused Unity asset folder:
```sh
export ASSET=Moco63ExampleA
export ANIMAL=tarbo
mkdir "$G/game/Assets/Eonwild/$ASSET"
cp "$N/skin/root_motion.glb" "$G/game/Assets/Eonwild/$ASSET/$ANIMAL.glb"
cp "$N/skin/source-animal.profile.json" "$G/game/Assets/Eonwild/$ASSET/$ANIMAL.profile.json"
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod MocoPrototypeReviewBuilder.Build \
  -moco-folder "$ASSET" -moco-animal "$ANIMAL" -logFile "$N/unity-build.log"
```
Verify successful exit and review-player build before capture. For a 10-second take:
```sh
"$PLAYER" -capture-dir "$N/side-frames" -capture-frames 240 \
  -animal-label TARBO -candidate 'C63 A / diagnostic / review pending' \
  -description '10 seconds / native 24 fps' -logFile "$N/side-player.log"
"$PLAYER" -capture-dir "$N/quarter-frames" -capture-frames 240 -front-quarter \
  -animal-label TARBO -candidate 'C63 A / diagnostic / review pending' \
  -description '10 seconds / native 24 fps' -logFile "$N/quarter-player.log"
/opt/homebrew/bin/ffmpeg -framerate 24 -i "$N/side-frames/%05d.png" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$NE/side.mp4"
/opt/homebrew/bin/ffmpeg -framerate 24 -i "$N/quarter-frames/%05d.png" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$NE/quarter.mp4"
```
Choose duration from the actual take. Finite actions are not seamless loops.
Do not change playback speed to conceal timing defects.

To rebuild the existing C62 interactive prototype (this builder rewrites its
Encounter62 scene; inspect the Git diff afterward):
```sh
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod EncounterReviewBuilder.Build -logFile "$N/encounter-build.log"
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod EncounterRuntimeChecks.Run -logFile "$N/encounter-checks.log"
"$ENCOUNTER" -duration 120 -seed 62 -capture 1 \
  -evidence-dir "$N/encounter-capture" -logFile "$N/encounter-player.log"
/opt/homebrew/bin/ffmpeg -framerate 24 -i "$N/encounter-capture/frames/%05d.png" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p -movflags +faststart "$NE/encounter.mp4"
```
`EncounterRuntimeChecks.Run` currently writes its receipt into the C62 evidence
folder; preserve the existing receipt before running or give your new iteration a
new output path. Likewise, the saved C62 encode/analyze scripts hardcode C62 output;
copy/adapt their destinations rather than overwriting the review. These are known
tooling behaviors, not recommendations for the next implementation.

Performance must be measured separately, without concurrent capture/build/encoding:
```sh
"$ENCOUNTER" -duration 40 -seed 62 -capture 0 \
  -evidence-dir "$N/performance" -logFile "$N/performance-player.log"
```
For manual exploration run the encounter app without `-evidence-dir`: G auto/manual,
Tab animal, W walk, Shift+W run, S retreat, A/D steer, H impact, R rise, Space pause,
Escape quit. The Mac must be unlocked for UI interaction. Never bypass its lock.

## 10. Save locations, evaluation and delivery

| Item | Location |
| --- | --- |
| Shared factory source | `$W/src/eonwild_motion/` and relevant existing tools |
| Semantic animal/behavior data | `$W/catalog/` with provenance/units |
| Research interpretation | `$W/docs/research/` |
| New numerical attempts, full raw frames, temporary logs | `$TASK/research/<new-candidate-name>/` |
| Selected Unity asset/profile/metadata | `$G/game/Assets/Eonwild/<new-candidate-folder>/` |
| Review MP4s, selected model/trajectory/recipes, hashes and receipts | `$G/game/Evidence/<new-checkpoint>/` |
| Current status and next handoff | Both roadmaps and `docs/handoffs/` in W/G |

Do not make historical build/reports/evidence directories runtime dependencies.
Do not overwrite prior evidence. Avoid multiplying copies of textured geometry
unnecessarily. Don't delete unrelated experiments or worktrees as incidental cleanup.

First inspect the current and reference videos at native speed. If your agent can
see videos directly, use that capability; the prior agent inspected ordered frame
sheets and numeric traces. Inspect every frame for contact/continuity when practical,
with close views of the visible problem. Explain whether review was direct video,
frame sheets, numeric analysis or all three. Still images alone do not establish
smoothness. Do not present an obvious internally rejected render as a successful fix.

Aim for a first honest motion preview within about 15 minutes of starting an
iteration; if a numerical solve prevents that, report the concrete bottleneck.
Run focused checks appropriate to the change. Do not spend hours building broad
validation machinery before showing the animal. Small diagnostic errors need not
block a clearly labeled preview; preserve acceptance criteria and report failures.

At the bounded checkpoint deliver native-speed side/quarter videos for individual
motion (or an appropriate encounter video), exact source identity, a short account
of changes and remaining defects, and separate visual/physical/runtime statuses.
Keep both animals in scope when judging shared-mechanics changes. Do not infer
approval from the user's request to continue working.

The user requested Git preservation of the latest video, and C62 is already pushed.
Preserve subsequent selected source/evidence/video together on review branches,
using explicit task-owned paths. Check remote heads and report them; do not merge
main or stage unrelated files. If the user gives a different publication instruction,
follow it. Save raw PNGs on the SSD; commit useful contact sheets and the MP4 rather
than thousands of full-resolution frames by default.

Your next task is to review this state, independently identify the next useful
bounded improvement toward credible shared animal motion, implement and evaluate
it within the user's current scope, and pause at a reviewable checkpoint. The
handoff intentionally does not choose the equations, algorithm, joint treatment
or software architecture for that improvement.
