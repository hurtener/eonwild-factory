# Eonwild continuation prompt — original shared solvers, C39–C42

Prepared 21 September 2026. Give this entire document to an incoming agent.
It is self-contained and independent of the separate Moco continuation prompt.
The user wants to preserve and resume the original shared animation engine,
including its reduced-physics work. This handoff does not approve a new take.

## 1. Assignment and baseline decision

Continue the existing Python/SciPy shared running solver for **both Allosaurus and
Tarbosaurus**, preserving the reviewed walking, turning, backward movement,
balance and stumble library. Improve running articulation and coordination using
the physics already introduced in C39–C41 and the subsequent C42 task correction.
Produce actual-rig native-time videos, review them yourself, then pause for the
user at the next bounded checkpoint.

**C39 B is the preferred Tarbo visual baseline.** The user accepted the scientific
direction and said Tarbo remained good; Allo still looked restrained.
**C40 D and C41 B are experiments with changes requested**, not upgrades whose
approval should be assumed. C42 A is a later shared-solver experiment with a
useful knee-task correction, still pending review. It is not Moco.

Do not discard C40/C41's physics or reset the repository to C39. Retain their
implementation and diagnosis, compare against the C39 video, and selectively
improve the shared engine. A newer numerical model is not automatically a better
animation. Do not force Tarbo to inherit a visible regression to improve Allo.

This path uses existing planning, geometry, articulated IK, temporal optimization,
reduced dynamics and final material correction. **It does not need OpenSim**.
Moco remains a separately preserved alternate experiment; do not migrate this
task to it or mix its solve receipts into this solver's claims.

## 2. How the user expects you to work

- Work yourself, **no subagents**. This supersedes old delegation rules.
- Produce and watch motion early; aim for an initial native preview in about
  15 minutes. Open existing C39 videos immediately. Do not spend hours on tests,
  reports or sub-millimetre edge cases before showing useful movement.
- The incoming agent can see videos directly. Watch complete normal-speed
  sequences, then slow playback and frame-step transitions. Stills alone missed
  several earlier micro-stops.
- Make one coherent, reviewable change per pass. Do meaningful source checks
  and both-animal renders. Reject obvious visual regressions yourself.
- Send saved simple-stage MP4s **here**, not the full mini-world. Mac M4 is the
  minimum intended desktop target; mobile fidelity reduction is separate work.
- Stop at the next visual checkpoint for feedback. Never infer user approval.
- Keep implemented code, actual-rig output, visual review, import parity and
  physical/production certification separate. FAIL/PENDING/NOT_RUN are valid.
- No species branches or literal artist-bone names in shared mechanics. Anatomy,
  mass, strength, stance, speed and stride differences belong in semantic data.
- Preserve approved assets and immutable V8.2. Historical build/ and reports/
  are not runtime dependencies. Do not create another toolkit.
- No root teleport, silent foot sliding, loosened acceptance threshold or
  render-only joint clamp to conceal a solver problem.
- Do not merge PR #2, force push, clean old worktrees, wake stopped workers or
  restart automations. The existing animation goal is paused.

## 3. Repositories and exact preservation points

| Purpose | Current local location | Remote |
|---|---|---|
| Shared Python factory | /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration | https://github.com/hurtener/eonwild-factory |
| Principal game / Unity / evidence | /Volumes/m2-extended-disk/Repos/eonwild | https://github.com/hurtener/eonwild |

Both preservation branches are codex/animal-profile-housekeeping.
The factory local remote uses git@github.com-personal:hurtener/eonwild-factory.git;
the game uses HTTPS.

**Avoid the stale initial cwd** /Volumes/m2-extended-disk/Repos/eonwild-factory:
it is feat/motion-quality-and-breadth at 987bd6b82caf3ff661d6927aa530df40fe71b30e.
The active worktree above contains later shared-solver and Moco work together.

Before this handoff the preserved factory HEAD was
c3c6156773ca884cc3899db8e1d5241a8542add0 and game HEAD was
6a17a2dd0d46ed8d4c424d2c06f71ce5cd9f9288. Branch HEAD additionally includes the
commit adding this handoff. Fetch, inspect status/log, and preserve user changes.

| Candidate | Shared recipe | Factory implementation commit | Game evidence commit |
|---|---|---|---|
| C39 B | running-review.v11.json | 400a41e8e2796a0836f3a1584ac4e2ea3cac7b65 | d9143cd5b8252a940b68905edcbdc856f918a781 |
| C40 D | running-review.v12.json | e491b3c598f713d7ab308084deff234e1d3efd86 | 4c20b0ad533165d2c4c6a578de0eabb144a92509 |
| C41 B | running-review.v13.json | 69795a66bd3b9b4cea06bee81c9454b5ecdbf51a | 568097b93c7fdea60fd59b456ad3ea01b76fa7b1 |
| C42 A | running-review.v14.json | c4cbf5c95058c3e9a803457df51a6c0c57808a62 | d53c60679d14753c43eb87c8c6ef2de286e2f8f6 |

Recipes are under factory catalog/behaviors/. Exact geometry, profile, GLB and
video hashes for both animals at all four checkpoints are preserved beside this
prompt in **SHARED_SOLVERS_BASELINES_2026-09-21.json**. All eight saved GLBs and
eight profiles were checked against their original generation receipts when
preparing the handoff. Existing animation bytes were not modified.

Capture-time metadata can be stale: C39 README/manifest still says PENDING, but
its later user-review.json records Tarbo acceptance and Allo changes requested.
C40's user-review.json also retains an earlier PENDING; later C41 review and both
roadmaps record changes requested for C40. Use the chronology above and the
current roadmap, while preserving historical receipts unchanged.

If another agent is working on Moco, **use separate factory and game worktrees**
on a new codex/ branch, based on the preservation branch. Do not share writable
source directories, Unity project locks or build outputs. Section 8 shows a
concrete setup. New development can be pushed to that separate branch without
changing the Moco branch.

## 4. Read and watch before modifying anything

Factory:

1. AGENTS.md, README.md, docs/FACTORY_ROADMAP.md.
2. docs/research/RUNNING_EVIDENCE_BASELINE.md, especially C39–C41 sections.
3. docs/UNITY_MOTION_CONTRACT.md and docs/ANIMAL_EMBODIMENT_CONTRACT.md.
4. docs/research/LOCOMOTION_CONFIGURATION_REVIEW.md for the supplied paper review.
5. This prompt and SHARED_SOLVERS_BASELINES_2026-09-21.json.

Game:

- docs/ANIMATION_ART_DIRECTION.md, especially C29–C42 and the approved stumble
  direction; also retain later useful user intent about an engaged body and gaze.
- docs/IMPLEMENTATION_ROADMAP.md.
- The README, manifest, user review where present, and knee audit in each evidence
  folder below. Historical references to Moco being unavailable are superseded
  by later work, but do not affect this continuation.

| Checkpoint | Game evidence folder | Imported assets |
|---|---|---|
| C39 B | game/Evidence/coupled-stride-running-study/ | game/Assets/Eonwild/Running39/ |
| C40 D | game/Evidence/floating-body-running-study/ | game/Assets/Eonwild/Running40/ |
| C41 B | game/Evidence/actuated-running-study/ | game/Assets/Eonwild/Running41/ |
| C42 A | game/Evidence/endpoint-running-study/ | game/Assets/Eonwild/Running42/ |

Each evidence folder contains **allo-sustained-running.mp4** and
**tarbo-sustained-running.mp4**. Each is 9 seconds, 24 fps, 1280x720:
6 seconds side followed by 3 seconds quarter view. The camera cut is not a motion
transition. Start with C39 Tarbo, then C39 Allo, then C40/C41/C42 for each animal.
C42 also includes labeled recovery slow-motion details.

Relevant reference clips in the factory:

- assets/examples/tarbosaurus/allo-turning-example.mp4 — actually Allosaurus;
  originally mislabeled Tarbosaurus. Good whole-body choreography, inside/outside
  leg adaptation, weight shift and small adjustment steps.
- assets/examples/allosaurus/allo-walking-reference.mp4.
- assets/examples/tarbosaurus/v9_evidence/running-sustained-left.mp4.
- assets/examples/tarbosaurus/v9_evidence/sprint-left.mp4.
- assets/examples/tarbosaurus/v9_evidence/RUN START-RUN-RUN STOP.mp4.
- https://www.youtube.com/watch?v=0tvANFTJXN0 — user running reference: powered
  rear push, relaxed flexed recovery, forward catch, birdlike neck compensation,
  engaged gaze and broad lateral tail movement.

These are artistic/historical references, not measured dinosaur biomechanics.
Watch video timing, not only isolated poses.

## 5. What the original physics actually does

### C39 B: useful visual foundation

The opt-in whole-stride fitter optimizes the remaining metatarsal-pitch redundancy
at 64 periodic samples per leg. Hip/knee/ankle are geometrically coupled by IK.
Body path, foot path, toe choreography, contacts and support force remain prescribed.

Reduced sagittal Newton-Euler inverse dynamics estimates distal-segment moments.
Costs include reference tracking, acceleration, jerk, normalized effort and
effort rate. Segment COMs are midpoints, inertias are uniform rods m*L^2/12,
and per-leg mass fractions are 0.035 / 0.018 / 0.006. These are engineering priors.
The pelvis reaction is not constrained; this is not full-body equilibrium or
muscle simulation. The seed is freshly generated from admitted geometry/recipe,
never an old animated take.

In the reduced fit, acceleration RMS fell ~23–35% and estimated moment RMS ~4–6%.
This does not prove every emitted joint is smoother. Early post-release knee
reopening remained 5.84 degrees Allo / 3.48 Tarbo. C39 uses LINEAR emission.
Authored anterior trunk yaw was separately reduced from 8 to 2 degrees while
retaining pelvic/tail movement. Do not attribute that change to dynamics.

### C40 D: bilateral floating-body fit

Both legs' three sagittal segment angles, mean body placement and torso pitch
are optimized together with foot tasks and angular-momentum residuals.
Reduced COM is reconstructed exactly for the assumed rod legs/lumped body;
contact and momentum are finite-weight penalties, not hard feasibility.
Swing can move away from the initial foot path; stance is strongly constrained.
A fresh actual-rig pass provides material-clearance information before fitting.

The pose reference weakened from 8.0 to 0.7. C40 D uses CUBICSPLINE emission.
C40 C and D have identical solved key poses; much of the lower dense force proxy
residual comes from interpolation, not more accurate biology:

| Dense vertical residual RMS / BW | C39 linear | C40 C linear | C40 D cubic |
|---|---:|---:|---:|
| Allo | 0.629 | 0.698 | 0.093 |
| Tarbo | 0.425 | 0.474 | 0.091 |

The user found Tarbo recovery too slow/lingering and Allo still too short/restrained.
Tarbo's source-key maximum knee opening increased from ~143.8 to ~153.3 degrees.
Do not select C40 merely because a fit objective improved.

### C41 B: distributed axial mass and actuator surrogate

The fit adds semantic trunk, neck/head and tail point masses. Axial shares are
0.65 / 0.10 / 0.25 of mass remaining after the rod legs; tail weights taper.
A signed torque actuator uses angle/speed-dependent capacity and first-order
excitation. Mass distribution, capacity envelopes and time constants are
engineering estimates, not reconstructed muscles.

Support forces/timing, toe choreography and artistic axial movement remain
prescribed. Contact, angular momentum and capacity remain soft penalties.
Heavier mass alone does not automatically slow animation: normalized costs can
cancel mass, while geometry, timing and calibrated capacity change behavior.

**The Allo knee audit matters more than another arbitrary joint-limit change.**

Both animal profiles have identical knee envelopes: hard 65–180 degrees,
preferred 68–175. The fit additionally uses a 6-degree projection margin and a
152-degree opening target. Those are distinct from hard emitted-rig limits.

Allo's projected thigh/shin/metatarsus fractions are 0.415/0.376/0.208;
Tarbo's are 0.349/0.403/0.248. Same endpoint/timing preferences can produce
different silhouettes. The knee numerically bends, but whole-thigh excursion
and timing still looked restrained.

| Fit-only audit | Peak forward thigh inclination |
|---|---:|
| Allo C41 | 38.47 degrees |
| Unchanged warm-start control | 38.46 |
| Relax actuator-limit weight 40 → 0.01 | 38.33 |
| Relax early knee-opening weight 9 → 0.01 | 49.65 |
| Tarbo C41 comparison | 51.49 |

The early minimum-opening timetable conflicts with gathering/forward thigh travel.
It was target_knee = radians(82 + 65*smoothstep((swing-.20)/.62)).
Relaxing strength alone does not fix it. Simply deleting the knee task is not a
finished animation either: forward extension then occurs too late. Counterfactual
fits in the audit were not emitted or approved clips.

The user clarified **“freer” means more knee extension on the forward path**,
not just deeper folding. Seek coordinated gathering, advance, extension and soft
landing. Do not copy Tarbo angles onto Allo or add an Allo-specific exception.

C41 regressed post-release reopening to 7.98 / 5.98 degrees (Allo/Tarbo);
catch foot-base distance ahead of hip fell to 0.595 / 0.693 m.
Maximum excitation demand exceeded 1 by ~0.39% / 1.19%. Soft constraints did not
establish actuator feasibility.

### C42 A: useful unapproved endpoint correction

v14 keeps the spatial foot corridor, removes the early knee-angle timetable,
adds late-swing foot-approach velocity and early-release extension-rate penalties.
The same coupled solver serves both animals. A retained extension_weight field
does not mean the old timetable executes: inspect forward_recovery.mode.

| Emitted diagnostic | Allo C41 → C42 | Tarbo C41 → C42 |
|---|---:|---:|
| Forward thigh inclination | 38.52 → 48.54 degrees | 51.65 → 48.89 |
| Foot base ahead of hip at catch | 0.595 → 0.714 m | 0.693 → 0.697 m |
| Post-release knee reopening | 7.98 → 5.89 degrees | 5.98 → 5.13 |
| Maximum knee interior angle | 155.64 → 151.55 degrees | 153.00 → 152.28 |

Some ankle sharpness/reopening remains. Do not replace C39's accepted Tarbo
baseline merely because Allo gains travel. C42 is a diagnostic option, not approval.

### Technical limitations shared across these candidates

- Historical focused checks: C39 88, C40 90, C41/C42 92. These are recorded
  results, not tests newly executed by reading this prompt.
- Sampled source reach/hard-ROM violations are zero in the selected outputs.
  That does not certify off-key motion or continuous skin contact.
- Cubic sampling can overshoot. Measure keys, midpoints and dense trajectories.
  Largest adjacent irregular-key change is **not angular velocity**.
- Unity landmark parity still fails the unchanged **2 mm** gate:
  C40 6.76 / 6.51 mm, C41 7.35 / 6.74 mm, C42 5.58 / 6.57 mm (Allo/Tarbo).
  The cause is unresolved. Do not call it a confirmed compression bug.
- C40 Tarbo side capture saved all frames but exited 255 in Metal/CVDisplayLink.
  Keep capture completion separate from clean shutdown.
- C42 sampled loaded skin floor: Allo -0.377 to +0.549 mm,
  Tarbo -0.400 to +0.219 mm. These are source samples, not certified Unity skin.
- Unlike the Moco review player, the conventional ConnectedMotionPlayer uses
  its connected-motion adapter and profile secondary layer. Source GLB,
  direct importer parity and actual runtime output are separate evidence.

## 6. Artistic direction and the next bounded pass

Preserve a muscular rear push that generates short flight, forward weight
reception, yielding joints and one uninterrupted heel/toe/recovery sequence.
Do not make running a speeded-up walk. No micro-stop at unloading, no post-release
straightening/flick and no hovering leg that appears to support weight.

Keep body/hip response credible and engaged, a compensating neck with focused
head, restrained lateral head motion, and lateral tail momentum beginning at
the proximal links. Avoid jelly torso, pogo pelvis and springy vertical tail.
Maintain arm carriage and subtle jaw life. Planted weight should be received at
the hip, not through lateral ankle/knee buckling.

Recommended next pass:

1. Directly watch C39–C42; compare each animal separately. Identify the precise
   time/phase where C39 succeeds and Allo loses range or fluidity.
2. Reproduce C39 settings as a control. Keep its Tarbo video/GLB immutable.
3. Inspect task conflicts and final IK/material correction: desired endpoint,
   whole-leg excursion, ankle orientation preference, knee reserve, toe roll,
   projection limits and post-fit corrections. Diagnose the final emitted chain,
   not just the reduced fit.
4. Make one small shared-mechanics change. C42's endpoint task is a useful
   experiment; do not blindly combine every later weight with C39. Keep animal
   differences as sourced/explicitly estimated semantic parameters.
5. Evaluate both animals, especially Allo's forward extension and Tarbo's
   previously good timing. Add scientific detail only when it addresses the
   observed problem and survives emitted-video review.
6. Show both native videos plus C39 comparison, state remaining physics/parity
   limits, and pause. Do not move into sprint or new impact families unseen.

Current approved library to preserve: walking/fast-walking and start/stop,
turn-in-place C12, walking turns C17, backward/glance C19/20, lateral recovery C21,
standing impact C25, walking stumble C26, braking C27, connected state adoption C28.
The stumble/recovery work was particularly convincing to the user.
Running/sprinting impacts, actual knockdown/get-up and sprinting remain future work.
Any eventual transition must adopt actual pose, velocity, heading and support,
not force an animal back to a canonical start stance after a hit.

## 7. Code, scientific inputs and save locations

Core source:

- tools/build_running_preview.py: fresh admission, support plan, initial material
  solve, optional full-stride fit, final articulated solve/correction, GLB emission
  and reopening. Refuses to overwrite output.
- src/eonwild_motion/planning/running.py: profile gait intent.
- planning/running_support.py: support cycle, contact/flight timing, body response.
- planning/running_evidence.py: extant-evidence transfer and diagnostics.
- solve/running_stride_fit.py: periodic derivatives, inverse dynamics, independent
  leg mode, floating-body/distributed mass, actuator demand, endpoint task.
- solve/airborne_gait.py: articulated actual-rig solve.
- solve/skin_rig.py, solve/turn_contact.py: material geometry/contact operations.
- glb/animation.py and the preview emitter: interpolation and final sampling.
- catalog/behaviors/running-review.v11–v14.json: preserved configurations.
- catalog/embodiment/allo.v1.json and tarbo.v1.json: canonical profiles.
  Use archived exported profiles for exact historical comparisons.
- tests/test_running.py, test_embodiment.py, test_running_stride_fit.py,
  test_running_evidence.py, test_running_support.py.

Other existing paths: tools/build_walk_sequence_preview.py,
tools/build_directional_preview.py, planning/stumble_recovery.py,
planning/impact_response.py, planning/support_balance.py,
solve/whole_body_walk.py and solve/turn_*.py. Preserve them; do not rewrite
approved behaviors as a side effect of this running pass.

Game: game/Assets/Eonwild/Editor/ConnectedReviewBuilder.cs,
Scripts/ConnectedReview.cs, Scripts/ConnectedMotionPlayer.cs,
Editor/ImportParity.cs. Connected28 libraries provide prior clips/segments.
Running39–42 each append their own run while preserving that baseline.

Research to use without guessing:

- docs/research/RUNNING_EVIDENCE_BASELINE.md: primary source roles, uncertainty,
  BIRDS transfer, joint-coordinate cautions and reduced-model scope.
- BIRDS: https://doi.org/10.1371/journal.pone.0192172, 12 extant birds,
  0.045–80 kg. Multi-tonne extrapolation is a prior, not a dinosaur measurement.
- Ostrich kinematics: https://doi.org/10.1242/jeb.02792.
- Articulated toes: https://doi.org/10.7717/peerj.2857.
- Supplied four PDFs, workbook, proposal JSON and Classic analysis:
  docs/research/inputs/2026-09-21/, PDFs under papers/.
- Central interpretation: docs/research/LOCOMOTION_CONFIGURATION_REVIEW.md.
  Cuff 2022, Bishop 2021, Sellers 2017 and Bishop 2018 constrain assumptions,
  not exact Allo/Tarbo ROM or muscle strengths. See their cited pages/tables.

The BIRDS regressions naturally predict duty above 0.5 at these large-body
inputs/speeds; the current aerial variant retains an authored duty around 0.43
and derives compatible impulse. Do not claim the prescribed 14% flight is a
scientific prediction. Preserve speed/stride consistency and report this choice.

Current run intent: Allo 1512 kg estimate, 3.8 m/s, step 1.70 m / stride 3.40 m;
Tarbo 2816.3 kg, 3.4 m/s, step 2.02 m / stride 4.04 m. Speeds/strides here are
authored moderate-run targets with provenance, not reconstructed maxima.

For future anatomy: one fixed calibrated standing hip height, explicit angle
axes/zero, segment masses/COM/inertia, contact surfaces and capacity uncertainty.
Fr=v²/(g*h); a stride is same-foot to same-foot, width is full left/right distance,
clearance is lowest articulated material. Never silently shorten researched
stride. Distinguish world segment heading from anatomical joint flexion.
The five proposed new taxa remain uncalibrated/disabled, not newly onboarded.

Save shared changes in factory src/tools/tests and versioned catalog data;
research in the central docs, not scattered notes. Numerical trials and raw PNGs
go in task storage. Selected clips/profiles/Unity metadata go in a **new**
game/Assets/Eonwild/RunningShared… folder. Review videos, exact recipes,
receipts/scripts and hashes go in a **new flat child** of game/Evidence/.
The legacy evidence scripts assume that directory depth. Never overwrite C39–42.

## 8. Environment and isolated setup

Existing working Python on this Mac:
TASK/venvs/contact-mass/bin/python, Python 3.12.10, NumPy 2.5.2, SciPy 1.18.1,
Pillow 12.3.0, Matplotlib 3.11.2. ffmpeg/ffprobe are in /opt/homebrew/bin.
Use this ordinary scientific environment, **not moco-venv**.
Factory pyproject.toml and uv.lock describe core/test dependencies.
On another machine provision compatible dependencies and Unity separately;
do not copy a Mac virtual environment across platforms.

This setup isolates the continuation from another agent working on Moco:

~~~bash
export TASK=/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526
export BASE_FACTORY="$TASK/worktrees/stride-hip-visual-iteration"
export BASE_GAME=/Volumes/m2-extended-disk/Repos/eonwild
export P="$TASK/venvs/contact-mass/bin/python"
export UNITY=/Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity
export PATH="/opt/homebrew/bin:$PATH"
export BRANCH=codex/shared-solvers-continuation
export W="$TASK/worktrees/shared-solvers-continuation"
export G="$TASK/worktrees/eonwild-shared-solvers-continuation"
git -C "$BASE_FACTORY" status --short
git -C "$BASE_GAME" status --short
git -C "$BASE_FACTORY" fetch origin
git -C "$BASE_GAME" fetch origin
~~~

Inspect the branch/worktree inventory. If these names exist, inspect and reuse
the intended continuation or choose new names; never force replacement.
When both names are unused:

~~~bash
git -C "$BASE_FACTORY" worktree add -b "$BRANCH" "$W" origin/codex/animal-profile-housekeeping
git -C "$BASE_GAME" worktree add -b "$BRANCH" "$G" origin/codex/animal-profile-housekeeping
cd "$W"
"$P" -c 'import numpy, scipy, PIL, matplotlib, pytest; print(numpy.__version__, scipy.__version__)'
PYTHONPATH=src "$P" tools/build_running_preview.py --help
~~~

Independent repositories may use the same new branch name. Worktree creation
does not copy dirty changes or Unity Library caches. First Unity import can
take longer. Never run two editors against the same game checkout.

If the user explicitly chooses direct work and no other agent owns it, use
BASE_FACTORY/BASE_GAME as W/G and the preservation branch as BRANCH.
Do not reset it to a historical checkpoint.

For exact historical C39 code, create a separate detached factory worktree at
400a41e8e2796a0836f3a1584ac4e2ea3cac7b65. Use it only for reproduction; develop
from current source so later work stays preserved. Check backward compatibility
rather than assuming every historical byte survives future compiler changes.

## 9. Baseline reproduction and new candidate generation

Run blocks sequentially and inspect each result, not as an unattended script.
The two animal solves are independent and can be batched if memory allows;
cap native BLAS threads to avoid oversubscription.

~~~bash
export N="$TASK/research/shared-running-resume-01"
export E="$G/game/Evidence/endpoint-running-study"
export NE="$G/game/Evidence/shared-running-resume-01"
export ASSET=RunningShared01
export CP=48
export LABEL=SHARED-C48-A
export PLAYER="$G/game/Builds/Eonwild Running.app/Contents/MacOS/Eonwild Floodplain"
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
test ! -e "$N" && test ! -e "$NE" && test ! -e "$G/game/Assets/Eonwild/$ASSET"
~~~

CP=48 is an example after C47. Check both trackers for the actual next number,
particularly if Moco progressed. Keep distinct asset/evidence names.
If a directory test fails, choose another name before continuing:

~~~bash
mkdir -p "$N" "$NE/scripts"
~~~

The fastest baseline is the saved C39 video. When reproduction is useful,
run both animals with the same v11 recipe and preserved exported profiles:

~~~bash
PYTHONPATH=src "$P" tools/build_running_preview.py \
  --motion-set catalog/motion-sets/allosaurus-engineering-native-walk.v21.json \
  --profile "$G/game/Assets/Eonwild/Running39/allo.profile.json" \
  --recipe catalog/behaviors/running-review.v11.json \
  --output "$N/allo-c39-control" >"$N/allo-c39-control.log" 2>&1

PYTHONPATH=src "$P" tools/build_running_preview.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.json \
  --profile "$G/game/Assets/Eonwild/Running39/tarbo.profile.json" \
  --recipe catalog/behaviors/running-review.v11.json \
  --output "$N/tarbo-c39-control" >"$N/tarbo-c39-control.log" 2>&1
~~~

Compare hashes with the baseline JSON. A changed GLB is not automatically wrong,
but is not the exact approved file. Investigate compiler/environment differences
or use the pinned historical worktree. Never overwrite Running39.

Choose a starting recipe from the observed hypothesis:

- v11 preserves the simpler C39 control.
- v12 enables floating-body bilateral physics.
- v13 adds distributed mass/actuators but retains the problematic knee timetable.
- v14 includes the endpoint-task correction; it is an unapproved comparison.

Copy your selected starting recipe and record the reason before editing:

~~~bash
cp catalog/behaviors/running-review.v11.json "$N/recipe.json"
"$P" - <<'PY'
import json, os
from pathlib import Path
p=Path(os.environ["N"])/"recipe.json"
d=json.loads(p.read_text())
d["checkpoint"]=int(os.environ["CP"])
d["classification"]="Shared solver continuation candidate; engineering priors; pending visual review."
p.write_text(json.dumps(d,indent=2)+"\n")
PY
~~~

Implement the actual bounded shared change. An unchanged copy is not a new
improvement. If selecting v14 instead, do so explicitly and document which C39
qualities must survive. Save the chosen new recipe in the next unused catalog
version and bind its hash in evidence.

Generate both animals with identical solver/recipe:

~~~bash
PYTHONPATH=src "$P" tools/build_running_preview.py \
  --motion-set catalog/motion-sets/allosaurus-engineering-native-walk.v21.json \
  --profile "$G/game/Assets/Eonwild/Running39/allo.profile.json" \
  --recipe "$N/recipe.json" --output "$N/allo-candidate" \
  >"$N/allo-candidate.log" 2>&1

PYTHONPATH=src "$P" tools/build_running_preview.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.json \
  --profile "$G/game/Assets/Eonwild/Running39/tarbo.profile.json" \
  --recipe "$N/recipe.json" --output "$N/tarbo-candidate" \
  >"$N/tarbo-candidate.log" 2>&1
~~~

Outputs include root_motion.glb, source-animal.profile.json and running.json.
The receipt contains hashes, plan, fit, key checks and reopened material samples.
The compiler intercepts admission before the walk solve; the “walk” motion-set
name does not mean a previous animation drives the run.

## 10. Prepare review helpers without overwriting old evidence

Legacy scripts embed candidate names and derive the game path from their own
location. Keep NE directly under game/Evidence/, not a nested candidate folder,
unless you revise that logic. Copy first. Do not use old capture.py: it hardcodes
the principal game, old evidence and /tmp output paths.

~~~bash
for name in stage.py measure-motion.py package-capture.py join-views.py verify.py import-reference.py compare.py
do
  cp "$E/scripts/$name" "$NE/scripts/$name"
done

"$P" - <<'PY'
import os
from pathlib import Path
root=Path(os.environ["NE"])/"scripts"
asset=os.environ["ASSET"]; label=os.environ["LABEL"]
for p in root.glob("*.py"):
    s=p.read_text().replace("Running42",asset)
    if p.name=="stage.py":
        old="args.outputs/(animal+'-run42-a'+('-v15' if animal=='tarbo' else ''))"
        assert old in s, "Inspect stage helper; source naming changed"
        s=s.replace(old,"args.outputs/(animal+'-candidate')")
        s=s.replace("Shared foot-approach and gathering coordination candidate;",
                    "Shared solver continuation candidate;")
    if p.name=="compare.py":
        s=s.replace("C42",label)
    p.write_text(s)
PY

PYTHONPATH=src "$P" "$NE/scripts/measure-motion.py" \
  "$N/allo-candidate" "$N/tarbo-candidate" >"$N/motion-measurements.log" 2>&1
"$P" "$NE/scripts/stage.py" "$N"
~~~

Inspect helper output paths before execution. Staging appends the new run to
Connected28 libraries while preserving all prior clips/segments.
The copied comparison caption still describes the C42 endpoint experiment:
rewrite it to state your actual change. Do not put a false description on a
C39-based candidate. The legacy measure-motion helper assumes these rigs'
+Z-forward frame; use semantic frame data before applying it to future rigs.

## 11. Build the simple stage and capture

~~~bash
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod ConnectedReviewBuilder.Build \
  -running-review -running-folder "$ASSET" -logFile "$N/unity-build.log"
~~~

Require CONNECTED_BUILD_SUCCESS. Never run a stale app after build failure.
This mode uses the simple stage, not the world. One Unity editor per checkout.
The isolated checkout may need initial import.

Capture four processes sequentially, with exact native timing. This Python
wrapper uses the existing player/packager and records native exit codes:

~~~bash
"$P" - <<'PY'
import json, os, subprocess, sys
from pathlib import Path
n=Path(os.environ["N"]); e=Path(os.environ["NE"])
results=[]
for animal in ("tarbo","allo"):
    for view,count in (("side",144),("quarter",72)):
        name=animal+("-quarter" if view=="quarter" else "")
        dest=n/("frames-"+name)
        assert not dest.exists(), "Do not overwrite a capture"
        cmd=[os.environ["PLAYER"],"-sustained-run","-checkpoint",os.environ["LABEL"],
             "-capture-dir",str(dest),"-capture-frames",str(count),
             "-screen-width","1280","-screen-height","720","-screen-fullscreen","0",
             "-logFile",str(n/("capture-"+name+".log"))]
        if animal=="allo":cmd.append("-capture-allo")
        if view=="quarter":cmd.append("-front-quarter")
        result=subprocess.run(cmd,cwd=os.environ["G"])
        actual=len(list(dest.glob("[0-9][0-9][0-9][0-9][0-9].png")))
        results.append(dict(animal=animal,view=view,exit_code=result.returncode,frames=actual))
        (e/"capture-results.json").write_text(json.dumps(results,indent=2)+"\n")
        assert actual==count, results[-1]
        if result.returncode:
            print("Nonzero native exit after complete capture:",results[-1],flush=True)
        subprocess.run([sys.executable,str(e/"scripts/package-capture.py"),name,
                        str(dest),"--count",str(count),"--candidate","a"],check=True)
subprocess.run([sys.executable,str(e/"scripts/join-views.py")],check=True)
PY
~~~

The packager saves source-frame hashes, chronological sheets, trace and handoffs.
Outputs include individual views and both animal-sustained-running.mp4 files,
each 216 frames / 9 seconds. Record any exit failure even with complete frames.
Do not retime native comparison to conceal timing defects.

The adapter starts in sustained run, so this reviews the cycle, not entry/braking.
Those transitions need a later checkpoint.

## 12. Verify and watch the actual result

After staging, generate direct-import references and run Unity parity:

~~~bash
PYTHONPATH=src "$P" "$NE/scripts/import-reference.py"
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod ImportParity.Verify -motion-folder "$ASSET" \
  -reference-json "$NE/import-reference.json" \
  -parity-output "$NE/import-parity.json" -logFile "$N/import-parity.log"

"$P" "$NE/scripts/verify.py" >"$NE/verification.log" 2>&1
"$P" "$NE/scripts/compare.py" >"$NE/comparison.log" 2>&1

PYTHONPATH=src "$P" -m pytest \
  tests/test_running.py tests/test_embodiment.py tests/test_running_stride_fit.py \
  tests/test_running_evidence.py tests/test_running_support.py -q \
  >"$NE/focused-tests.txt" 2>&1
~~~

The verifier checks source/library hashes, unchanged prior clips and full video
decoding. It reports sampled errors; it does not certify force feasibility or
automatically include separate failed import parity. Read both reports and
preserve the 2 mm gate.

For physics/interpolation analysis, C40 scripts/measure-physics.py and
compare-emission.py are useful methods. They hardcode C39/C40 paths and use a
lumped COM proxy. Adapt copies into NE and match the actual new mass model.
Do not report a lumped-body plot as distributed-mass validation.
C41 scripts/knee-ablation.py also hardcodes experiment paths; inspect/adapt it,
rather than running blindly.

Direct-video evaluation procedure:

1. Watch both whole new movies at 1x, then C39 from the same view. Compare C41/C42
   so you recognize previously attempted corrections.
2. Watch at 0.25x/0.5x playback. Inspect all 432 frames, especially release,
   forward recovery, catch and loop wrap. Sheets supplement continuous viewing.
3. Check Allo's gathering followed by **forward extension** through whole-thigh
   travel. Look for endpoint conflicts making it appear rigid even while numeric
   knee angle changes.
4. Check Tarbo retains C39 rhythm. Reject prolonged hanging recovery, micro-stops,
   late post-release straightening or ankle flicks.
5. Evaluate heel/toe roll under load, rear propulsion, relaxed airborne foot,
   forward reception and body compression together as one coordinated action.
6. Check focused head, compensating neck, restrained chest, arm/jaw life and
   lateral momentum through tail base. Avoid frozen or springy axial motion.
7. Plot joint angles/velocities/accelerations in physical seconds, support phase,
   foot-ahead-of-hip, skin floor and slip. Uniformly sample final GLB motion;
   uneven adjacent-key differences are not velocity.
8. Separate reduced-fit metrics, emitted source geometry, direct Unity import
   and connected-player output. Passing one does not certify the others.

A lower numerical effort with worse coordination is a regression. Scientific
detail should explain and improve movement, not replace watching the animal.

## 13. Archive, push, update the tracker, and pause

Save in NE:

- README and PENDING user-review state.
- Both native videos, C39 before/after, optional labeled slow motion,
  chronological sheets and raw-frame hashes.
- Exact new recipe, geometry/profile/source/GLB hashes, running receipts,
  measurements, fit diagnostics, parity, decode and focused checks.
- Source commits, environment versions, capture exits/logs and reproduction
  commands. Preserve enough input to regenerate without scratch storage.
- A manifest binding implementation, recipe, animal data, emitted assets and media.
- Explicit visible/physical/import limitations and regressions.

Raw PNGs and disposable builds remain in task storage. Never edit C39 evidence
to make a new candidate look approved. Preserve unrelated user files.

Update factory FACTORY_ROADMAP.md, game IMPLEMENTATION_ROADMAP.md, central running
research and game ANIMATION_ART_DIRECTION.md. Record this as the **shared-solver
continuation**, distinct from Moco progress. Both investigations can learn from
the same artistic/scientific sources while retaining separate solution provenance.

Inspect diffs, explicitly stage task paths and commit both repositories.
Then push the actual continuation branch:

~~~bash
git -C "$W" status --short
git -C "$W" diff --check
git -C "$G" status --short
# Inspect and explicitly stage task files; commit before the pushes below.
git -C "$W" push -u origin "HEAD:refs/heads/$BRANCH"
git -C "$G" push -u origin "HEAD:refs/heads/$BRANCH"
git -C "$W" rev-parse HEAD
git -C "$W" ls-remote origin "refs/heads/$BRANCH"
git -C "$G" rev-parse HEAD
git -C "$G" ls-remote origin "refs/heads/$BRANCH"
~~~

Verify exact remote SHA equality. If someone advanced a branch, inspect and
integrate safely; never force push/reset their work. Do not merge PR #2.

Deliver both actual MP4s inline where supported, using absolute local paths,
a before/after, the main change and measured tradeoffs. Give exact remote commits.
Stop owned solve/capture processes and **pause for feedback**.

The existing Codex goal is paused. This handoff does not restart old tasks,
agents or automations. Continue one bounded shared-engine pass, retain C39 as the
Tarbo visual benchmark, and let reviewed evidence decide which later physics
is worth keeping.
