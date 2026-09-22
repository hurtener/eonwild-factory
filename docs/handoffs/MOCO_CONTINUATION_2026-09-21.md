# Eonwild continuation prompt — Moco running, contact and research

Prepared 21 September 2026. Give this entire document to the incoming agent.
It supplies the task, context, locations, commands and review procedure.
The project is paused at a visual checkpoint; handing it over does not approve
the current candidate. Continue to one new reviewable checkpoint, then pause.

## 1. Your assignment and working rules

Continue Eonwild's reusable animal-animation factory, focusing on the offline
OpenSim Moco running experiment. Improve coordinated, credible movement for a
roughly 2.8-tonne Tarbosaurus, using the supplied biomechanics papers to constrain
the model. Preserve the good neck/tail/leg direction while investigating contact,
ankle/toe articulation and physical feasibility. Produce saved native-time
videos of the actual skinned animal, evaluate them yourself, and send them to
the user at the next checkpoint.

This is a dinosaur game, with Allosaurus and Tarbosaurus as the admitted test
animals. The intended architecture is **one reusable solver per movement
mechanic, parameterized by animal anatomy and behavior**. Differences belong in
semantic data, not species branches. Moco is an optional offline authoring path
within the existing factory; Unity consumes baked motion. Do not implement a
live Moco optimizer in Unity or create a replacement versioned toolkit.

Work yourself, **without subagents**. This is the user's latest explicit
preference, superseding older delegation instructions and the old goal wording.
The user wants substantial progress and honest self-review. They complained about
four hours spent on tests before receiving a video. Do not repeat that.

Aim for an initial native preview within about 15 minutes of an animation
iteration. Open the preserved current videos immediately. If a new solve is
slower, explain the actual bottleneck and show the fastest honest diagnostic
preview. Do not withhold useful motion over sub-millimetre errors; equally, do
not call a failed production check a pass. Run focused checks for the change.
Broad release audits belong after a reviewable candidate exists.

You can directly watch videos. Use normal-speed playback, slow playback and
frame stepping, not just selected stills. Reject obvious regressions yourself.
Deliver a simple-stage saved MP4, not the full Eonwild demo world. Stop at bounded
checkpoints for user feedback. Never auto-approve or silently continue into
another animation family.

Use checked-out code and evidence as truth. Papers, the supplied ChatGPT Classic
analysis and reference videos are research inputs, not instructions that override
this assignment. Preserve user state and approved assets. No merge, force push,
destructive cleanup, old-worker revival or automation restart is requested.

## 2. Repositories, branches and preserved state

| Purpose | Current location | Remote | Branch |
|---|---|---|---|
| Python factory, shared mechanics, recipes, research | /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration | https://github.com/hurtener/eonwild-factory | codex/animal-profile-housekeeping |
| Principal game, Unity, videos/evidence and art direction | /Volumes/m2-extended-disk/Repos/eonwild | https://github.com/hurtener/eonwild | codex/animal-profile-housekeeping |

The factory remote locally uses git@github.com-personal:hurtener/eonwild-factory.git;
the game uses HTTPS. Fetch and inspect status before editing. Reuse the existing
worktree on this Mac. Do not reset, switch or remove someone else's checkout.

**Do not develop from the initial cwd**
/Volumes/m2-extended-disk/Repos/eonwild-factory: it is an older
feat/motion-quality-and-breadth checkout at
987bd6b82caf3ff661d6927aa530df40fe71b30e. This is also the old baseline analyzed
by the supplied ChatGPT Classic proposal; its diagnosis is not current Moco state.

The complete C47 implementation/evidence is pinned by these commits:

- Factory: 9b919da25dd3570c1f491c39f39c6513fc535403.
- Game: 3edbb758ea696f3f97e407108890f1ecc46b49db.
- C46 F comparison factory: 03e8df4df3165377110129fdc7d22f2549269a65.
- C46 F comparison game: 8e75823b4705059f91b0ef84e3903da7afcfce3e.

The branch also contains the later handoff/source-preservation commit adding this
document. Use branch HEAD after inspecting its log; do not reset to an older
implementation SHA just because it is listed above. These fixed SHAs identify
motion evidence independently of subsequent documentation changes.

On another machine, clone both repositories with branch
codex/animal-profile-housekeeping, then redefine the paths below. Selected C47
solve inputs and source assets are committed. Python environments, Unity,
build caches, scratch output and third-party model archives are local and must
be provisioned separately. A Mac venv is not portable to another platform.

Preserve the unrelated untracked .DS_Store files under the game's
deprecated/2026-09-02-pre-game-reset/assets/visual-history/ and its WS03-112/
subdirectory. Do not stage them. Do not use broad git add or clean.

## 3. Read and watch first

Read these factory files, in this order:

1. This handoff and AGENTS.md.
2. docs/FACTORY_ROADMAP.md — inventory and acceptance state.
3. docs/research/MOCO_TARBO_PROTOTYPE.md — chronological implementation; the
   **C47 section near the end** supersedes earlier runtime/status limitations.
4. docs/research/LOCOMOTION_CONFIGURATION_REVIEW.md.
5. docs/research/OPENSIM_DINOSAUR_FEASIBILITY.md — anatomy archives, methods and
   reuse terms. Its initial missing-Fortran error was subsequently fixed.
6. README.md, docs/UNITY_MOTION_CONTRACT.md, docs/ANIMAL_EMBODIMENT_CONTRACT.md.
7. As needed: docs/research/RUNNING_EVIDENCE_BASELINE.md and
   docs/research/THEROPOD_NECK_BASELINE.md.

In the principal game repository read:

- docs/ANIMATION_ART_DIRECTION.md, especially C43–C47 and earlier running feedback.
- docs/IMPLEMENTATION_ROADMAP.md.
- game/Evidence/moco-contact-support-study/candidate-c/README.md.
- game/Evidence/moco-contact-support-study/experiments.json.

Watch these actual videos directly at native speed before changing motion.
All following paths are relative to the game repository:

- game/Evidence/moco-contact-support-study/candidate-c/tarbo-moco-skinned.mp4:
  9 seconds, comprising 6-second side and 3-second quarter views.
- game/Evidence/moco-contact-support-study/candidate-c/tarbo-moco-side.mp4.
- game/Evidence/moco-contact-support-study/candidate-c/tarbo-moco-quarter.mp4.
- game/Evidence/moco-contact-support-study/candidate-c/tarbo-c46-vs-c47.mp4.
- Previous: game/Evidence/moco-supported-body-study/neck-correction/tarbo-moco-skinned.mp4.

**Directory trap:** videos directly inside moco-contact-support-study/ are
earlier candidate **A**, not selected candidate **C**. Already-shared paths remain
unchanged. Open the candidate-c/ subdirectory.

Reference videos, relative to the factory:

- assets/examples/tarbosaurus/allo-turning-example.mp4: **Allosaurus**, originally
  mislabeled Tarbosaurus by the user. Useful whole-body turning, transitions,
  adaptive stance width and inside/outside-leg choreography.
- assets/examples/allosaurus/allo-walking-reference.mp4: supplied walking clip.
- assets/examples/tarbosaurus/v9_evidence/running-sustained-left.mp4.
- assets/examples/tarbosaurus/v9_evidence/sprint-left.mp4.
- assets/examples/tarbosaurus/v9_evidence/RUN START-RUN-RUN STOP.mp4.
- assets/examples/tarbosaurus/tarbosaurus_walk.mp4.

The v9_evidence movies include historical project examples; do not confuse them
with measured living-animal biomechanics. User artistic running reference:
https://www.youtube.com/watch?v=0tvANFTJXN0 . Inspect the actual video if available.
Learn its powered rear push, forward catch, relaxed foot recovery, birdlike
compensating neck, focused skull and broad lateral tail motion. Authored
choreography is not scientific evidence of exact dinosaur angles or forces.

## 4. Animation inventory and artistic direction

“Approved” means user-approved appearance in the reviewed clips, not certification
for arbitrary terrain, impacts or gameplay blending.

| Family | Current position |
|---|---|
| Idle/standing and walking | Reviewed both; Allo walk iteration 14, Tarbo 15 |
| Start → walk → faster walk → stop | Approved both; braking C27 and connected controls C28 |
| Turn in place / walking turns | Approved baselines C12 / C17 |
| Backward walking / neck glance | Approved C19/C20 |
| Lateral balance step | Approved C21 |
| Standing impact / walking stumble-recovery | Approved C25 / C26; especially credible coordination |
| Conventional running | Experimental; C39 Tarbo direction liked, Allo restrained; C42 Allo pending |
| Alternate Moco running | C43 impressed user; C45 body rejected; C46 neck correction; C47 C pending |
| Sprint, run/sprint impacts, knockdown/get-up | Pending; do not expand into them now |

The user found the Allo knee almost fixed in angle. “Freer” meant more knee
**extension during forward reach**, not more folded flexion. Future Allo transfer
must diagnose geometry, contact and objective conflicts rather than copy Tarbo
curves or insert species branches. **Allo Moco transfer has not been attempted.**

Preserve these artistic and implementation rules:

- Support, heel lift, toe roll, release, recovery and forward catch are one
  coordinated action. Avoid a straightening leg that pauses before heel rise,
  micro-stops and chained mechanical phases.
- A strong rear push should cause flight; running is not a faster walk with
  an airborne offset. Landing must visibly receive and redirect mass.
- Preserve articulated distal recovery and a forward landing stroke. Do not
  silently shorten intended stride to fit an authored neutral-pose preference.
- Weight transfers through pelvis/hip over support. Planted knees/ankles must
  not collapse or twist laterally as a substitute for moving the body.
- The torso looks engaged and heavy, not gelatinous. Control the middle neck
  and shoulder junction while letting the neck compensate body motion.
  A quiet nose alone is insufficient.
- The skull remains focused toward pursuit; restrain left/right and up/down
  distraction. Jaw breathing is a separate modest authored layer.
- Carry the tail higher, with momentum through the base and lateral looping
  along the chain. Avoid a vertical spring or stiff first segments. The admitted
  Tarbo has **9 tail nodes / 8 physical links**, not 12.
- Arms have life and close carriage. Preserve the existing jaw/arm direction.
- Idle, turning and balance use wider/adaptive stance than normal walking.
  Turns need meaningful head/neck attention, shifting body center and asymmetric
  footwork. Preserve those approved movement families.
- Shared mechanics remain in src/eonwild_motion. Animal data remain semantic.
  Preserve approved Run010/Sprint006/Feeding003 and immutable V8.2 capsules.
  Historical build/ and reports/ are never runtime imports.
- No render-only ankle/knee/head clamps, root support motor, body teleport,
  silent foot sliding, weakened thresholds or fabricated biological claims.
- Constraints follow contact-affecting changes. Reopen the final skin and measure
  it. Skeleton parity does not prove material contact.
- Unity has one final movement owner. The review player samples a saved clip
  without runtime IK, support physics or secondary motion corrections.
- Use plain-stage MP4s. Mac M4 is the minimum intended desktop target;
  mobile reductions require future measured work.

## 5. What C47 actually is, and what remains wrong

The selected C47 C video comes from a smooth periodic **inverse-dynamics
initializer**. It uses exact OpenSim model/contact calculations in an optimization
over trajectory coefficients. It is **not a converged full Moco collocation
solution**, not reconstructed muscles, and not independently stable.

Model: 2,816.3 kg; target 3.4 m/s; step 2.02 m; full stride 4.04 m / 1.188235294 s.
It solves a 0.594117647 s half-stride with reflection and left/right exchange.
The emitted clip spans two full strides, 2.376470588 s, shown without retiming.
Leg segments are about 0.8300, 0.9930 and 0.5920 m. There are 23 bodies,
45 coordinates, 39 internal motors and six unactuated root freedoms.
Segment inertias, capacities and tonic bracing are estimates. There are no
calibrated muscle paths, tendons or bone-stress limits.

Each foot uses seven contact spheres and two reduced toe sections, approximating
the separately pivoted skin digits. C47 adds 21 geometry-derived material
clearance witnesses across the feet; they are constraints, not supporting forces.
Contact stiffness changed from 2e8 to 1e9 in the recipe's force formulation,
an engineering prior, not measured tissue. Units/scaling follow the component;
do not present it as a measured linear spring constant.

| Evidence | C46 F | C47 C |
|---|---:|---:|
| Emitted foot-skin penetration | 43.27 mm | 6.91 mm |
| Middle-neck vertical range | 7.58 cm | 7.20 cm |
| Neck-base vertical range | 16.93 cm | 15.29 cm |
| Nose vertical range | 5.44 cm | 3.76 cm |
| Nose lateral range | 3.04 cm | 4.35 cm — worse |
| Emitted pelvis vertical range | 18.86 cm | 18.23 cm |
| Tail-tip lateral range | 2.813 m | 2.448 m |
| Physical COM vertical range | 11.97 cm | 12.08 cm |
| Loaded contact-surface speed, p95 | 0.274 m/s | 0.272 m/s |
| Dense 3D force-balance RMS | 0.00519 BW | 0.00868 BW — worse |
| Peak normalized activation | 1.0005 | 0.9813 |
| Peak requested control | 1.0585 | 1.1105 — above 1 |
| Forward root-height error at half-stride | -235.65 mm | -272.65 mm — worse |

Production foot tolerance remains **0.5 mm**: C47 skin contact **fails**.
Forward physical replay also fails. Completion of integration is not validation.
Do not spend a whole iteration shaving millimetres while withholding a useful
video; do not relabel the failure either.

19 focused OpenSim tests pass. Bone lengths, loop closure after root translation
and 558 Unity landmarks pass; maximum Unity difference is about 0.00242 mm.
Saved model/solution reproduce byte-for-byte. These narrow checks do not establish
visual, physiological or gameplay approval. The prior agent inspected all
216 frames in chronological sheets and numerical curves, without claiming
continuous video perception. Add your direct temporal review.

Ankle findings:

- Sagittal hinge only. Hip yaw/roll determines the limb plane; no lateral ankle DOF.
- Model bounds 0.15–2.25 rad = 8.59–128.92 degrees flexion. Zero points shin and
  metatarsus straight down; interior opening is 180 degrees minus flexion.
  These are engineering bounds, not fossil-certified Tarbo ROM.
- C47 spans 8.43–122.70 degrees: soft lower-bound overrun ~0.16 degrees.
  Distal-toe upper-bound overrun ~0.08 degrees.
- Knee -2.0 to -0.16 rad; MTP +/-1.25 rad; digit -0.35 to +0.95 rad.
  Global coordinate speed bound +/-18 rad/s.
- Peak ankle speed increased from ~525 to ~572 degrees/s. Some sharpness remains.
- Peak ankle activation 0.593, MTP 0.981, distal digit 0.179. The ankle is moving
  substantially; the toe-base is nearer estimated capacity. Do not blindly
  increase ankle ROM or strength as a fix.

Unselected full Moco attempts are preserved separately:

| Trial | Setup | Outcome |
|---|---|---|
| B | 25 mesh, A warm start, continuation 100 / foot 500 | Assistant stopped after ~10 min; final iteration 19, primal 3.63, dual 7690 |
| D | 40 mesh, C warm start, continuation 300 / foot 1000 | Assistant stopped after ~16 min; final iteration 19, primal 0.84, dual 44.9 |
| D replay | Same physical model | Forward root error -157.87 mm, contact penetration 4.63 mm, dense balance 0.03237 BW; still failing |

Both returned User_Requested_Stop, triggered by the assistant's bounded-trial
stop mechanism. Neither proves biological or mathematical infeasibility.
D is a useful diagnostic warm start, **not the C video's source**, and its
native skinned render was not run.

Important SHA256 identities:

- Geometry: 2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f
- Profile: 0f1fdd0e1f55e7d6164181f4d9cb6d6a6316b93cae306d3553c79c03a3d3458a
- C47 C GLB: 1ba4a0ebf82cf41338d6c5f8188cd8a2623f35acf9ffa34f4c973036c11e41a6
- Model: 643f6f5c3c02c84749c534c5380f40280c491a0ca584c88eae18da82bda7861b
- Solution: 36781dddddd07cd0b34fae7d93de9eb520e3a57e0c4c3dfb48dcc00c800023c1

The parent evidence manifest.json binds 124 artifacts. Use hashes and source
commits rather than file timestamps to identify a candidate.

## 6. Papers and the next scientific investigation

The four supplied PDFs are archived in the factory at
docs/research/inputs/2026-09-21/papers/. Original paths/hashes are in
source-audit.json; handoff-source-manifest.json maps the copied papers and clips
to their committed locations.

The same input directory contains the original
Eonwild_Locomotion_Configuration_Research.xlsx,
eonwild_locomotion_proposals.v1.json and supplied-analysis.md.
Preserve originals; write interpretation into the centralized research review.

| Paper / archived filename | Use it for | Do not infer |
|---|---|---|
| Cuff et al. 2022, Cuff2022-WalkingrunningjumpingDAWNDINOS.pdf, https://doi.org/10.1093/icb/icac049 | Feet, grounded/aerial gait and tail/body coupling; PDF pp. 6–8, 14–15 | Exact Tarbo/Allo running ROM or gait values |
| Bishop, Cuff & Hutchinson 2021, pab.2020.46.pdf, https://doi.org/10.1017/pab.2020.46 | Frames, zero, masses/COM/inertia, reconstruction assumptions; PDF pp. 8–13 | Universal limits or a turnkey Moco predictor |
| Sellers et al. 2017, peerj_3420.pdf, https://doi.org/10.7717/peerj.3420 | Load/stress-limited feasibility of a particular 7,206.7 kg T. rex | An unchanged speed cap or flight prohibition for our smaller Tarbo |
| Bishop et al. 2018 Part II, 004_peerj-5779_dd.pdf, https://doi.org/10.7717/peerj.5779 | Static characteristic posture and external loading | Dynamic choreography or measured muscle strengths |

PDF page counts include covers. View tables/figures rather than trusting extracted
text: Cuff Table 1 toe-extension maxima are -8 / 56 degrees, not -85 / 6.
Those are representative **walking stance** values for crocodile/tinamou, not
joint limits for a running theropod. Bishop 2021's 119-degree ankle example needs
that specimen's anatomical zero. Bishop 2018's 1,000 Nm MTP reserve is an optimizer
ceiling, not measured biological capacity.

The workbook/JSON covers five future taxa and 14 nominal gait searches:
Alioramus, Gallimimus, Dilophosaurus, Prenocephale and Deinocheirus.
Seven workbook sheets and JSON agree on nominal values; calibrations are empty,
loader_compatible is false and all production flags are disabled. C47 did not
admit these animals. Additional source links are research leads requiring checks.
The Classic analysis's diagnostic-only mass claim describes its old checkout;
the optional Moco model already contains gravity, inertia, contact and actuation.

Use these conventions:

- Fr = v^2/(g*h), using one fixed calibrated standing hip height h.
- Full stride is same-foot touchdown to its next touchdown; T = stride_length/v.
- One step is not one full stride.
- Duty factor is actual per-foot support fraction, not proof of an aerial gait.
- Width is full left-to-right separation.
- Clearance is the lowest articulated material surface.
- Angles need anatomical frames, signs, zero and units.

Record each important calibration with parameter ID, units, anatomical meaning,
source DOI/page/table, source species/size, evidence class, transfer assumption,
plausible range, nominal value, confidence, solver consumer and sensitivity result.
Separate measurements, published estimates, comparative extrapolations and authored
game choices. Do not collapse mass, strength, contact and agility into one number.

Local research storage contains T. rex / Velociraptor SIMM anatomy, Gracilisuchus
and Coelophysis OpenSim files, and Coelophysis prediction code. The source audit
is docs/research/opensim-resource-audit.json. Downloaded T. rex/Velociraptor muscles
had placeholder 1.0 capacities; a public converted .osim was not verified.
Do not call these calibrated predictors. Coelophysis used custom MATLAB/CasADi
and OpenSim-derived dynamics, not a stock Moco script. PredSim is separate.

Study these methods without importing unexamined third-party code. The feasibility
review records OpenSim Apache-2.0, PredSim AGPL-3.0, Coelophysis article CC BY-NC
with no separately verified permissive supplement license, and MuSkeMo terms
requiring clarification. Dataset attribution is documented there. Recheck before
production reuse; a public download is not automatically a commercial grant.

### Recommended next checkpoint: C48, contact and support feasibility

This is a bounded research direction, not a promise that one solve converges.

1. Watch C47 C/C46 F and write time-coded observations of ankle/toes, loading,
   release and neck/body coordination. Preserve the visible gains.
2. Audit foot/MTP geometry, joint frames and moment arms. Compare physical spheres,
   material witnesses and actual articulated skin. Locate remaining penetration,
   slip and sharpness before changing bounds or capacity.
3. Diagnose why attractive state replay does not survive independent integration.
   Inspect all six root residuals, activation/control dynamics, contact
   interpolation and node-versus-dense errors. Separate unconverged optimization,
   discretization, open-loop instability and physical-model deficiencies.
4. Make one principled shared change with cited or explicitly estimated bounds.
   Use a small explained sensitivity comparison for toe strength, foot compliance
   or geometry, not a broad blind search or uniform strength inflation.
5. Attempt bounded full Moco refinement from suitable C and/or D initializations.
   Preserve free root, native speed, anatomy and contact semantics. Let feasible
   support/flight emerge for the physical candidate; do not force flight through
   hidden root assistance. Label any authored aerial variant separately.
6. Render early, directly watch the candidate and show a before/after with
   measured tradeoffs. Pause for feedback; physical failures remain explicit.

Do not immediately expand to detailed muscles/tendons, five species or maximum
sprint claims. First establish a persuasive, more grounded Tarbo stride.
Caudofemoralis/muscle architecture and Allo transfer come after a useful physical
baseline. Revisit approved walking only when the user chooses that scope.

## 7. Code map and save locations

Factory shared code:

- src/eonwild_motion/solve/moco_prototype.py — model, actuators, contact, study,
  bounds, conditioning and solve entry.
- moco_spatial.py — spatial joints, lateral freedoms, axial assembly/warm starts.
- moco_bracing.py — tonic support/passive engagement and admitted tail chain.
- moco_contact.py — material foot witnesses, with no extra support forces.
- moco_tasks.py — foot geometry, task/continuation/attention/support objectives.
- moco_coordination.py — periodic coefficient initializer and inverse dynamics.
  Check competing tasks here before blaming joint ROM.
- tools/admit_moco_prototype.py, coordinate_moco_prototype.py,
  build_moco_prototype.py, replay_moco_prototype.py, retarget_moco_prototype.py,
  render_moco_prototype.py, forward_moco_prototype.py.
- tests/test_moco*.py — focused OpenSim checks.
- catalog/behaviors/moco-contact-support.v1.json — C47 recipe.
- Related recipes: moco-supported-stride.v1.json, moco-focused-stride.v1.json,
  moco-spatial-stride.v1.json.
- catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.json — anatomy
  admission seam. It intercepts the compiler before motion solving; it does not
  use a previous walking trajectory despite the motion-set name.

Game code:

- game/Assets/Eonwild/Editor/MocoPrototypeReviewBuilder.cs — simple-stage build.
- game/Assets/Eonwild/Scripts/MocoPrototypeReview.cs — saved-clip capture.
- game/Assets/Eonwild/Editor/ImportParity.cs — actual import landmarks.
- game/Assets/Eonwild/MocoContact47C/ — preserved current assets.

| Material | Save location |
|---|---|
| Shared implementation / focused tests | Factory src/, tools/, tests/ |
| Anatomy, capacities and behavior tasks | Existing catalog/ semantic families; version changes |
| Interpretation and citations | docs/research/LOCOMOTION_CONFIGURATION_REVIEW.md and Moco report |
| Original supplied inputs | docs/research/inputs/2026-09-21/ |
| Numerical trials, raw frames, logs, venvs | Task storage research/, new directory per experiment |
| New clip/profile and Unity metadata | Game game/Assets/Eonwild/MocoContact48A/ or next unused name |
| New videos, solve archive, metrics | Game game/Evidence/moco-contact-c48-study/candidate-a/ |
| Movement inventory | Factory roadmap and game implementation roadmap |
| Lasting user artistic feedback | Game docs/ANIMATION_ART_DIRECTION.md |
| Canonical handoff | Factory docs/handoffs/MOCO_CONTINUATION_2026-09-21.md |

Never overwrite a delivered candidate. Archive exact selected solve inputs inside
the review evidence before pushing; scratch storage is not the sole reproducibility
source. Preserve unselected experiments with truthful status.

## 8. Verified local environment and shell setup

These are sequential recipe blocks, not one unattended script. Inspect each
stage's exit and receipt before dependent work. Batch independent checks if
supported, but never compete for the same Unity project.

Existing Moco environment: Apple Silicon Python 3.12.10, OpenSim 4.6
(build 4.6-2026-06-22-85aaf64), NumPy 2.5.3, SciPy 1.18.1.
Scientific/retarget environment: Python 3.12.10, NumPy 2.5.2, SciPy 1.18.1,
Pillow 12.3.0, Matplotlib 3.11.2. These are separate environments.

The Moco venv does not have pip installed. If rebuilding, use official OpenSim
4.6 arm64 instructions and compatible dependencies in a separate environment,
not global upgrades. Homebrew GCC supplies
/opt/homebrew/opt/gcc/lib/gcc/current/libgfortran.5.dylib.
ffmpeg is at /opt/homebrew/bin/ffmpeg. The earlier Fortran loading issue is fixed.

~~~bash
export TASK=/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526
export W="$TASK/worktrees/stride-hip-visual-iteration"
export G=/Volumes/m2-extended-disk/Repos/eonwild
export R="$TASK/research/opensim-2026-09-20"
export M="$R/moco-venv/bin/python"
export P="$TASK/venvs/contact-mass/bin/python"
export E="$G/game/Evidence/moco-contact-support-study"
export C="$E/candidate-c"
export PROFILE="$G/game/Assets/Eonwild/MocoContact47C/tarbo.profile.json"
export UNITY=/Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity
export PLAYER="$G/game/Builds/Eonwild Moco.app/Contents/MacOS/Eonwild Floodplain"
export PATH="/opt/homebrew/bin:$PATH"
cd "$W"
git status --short
git log -3 --oneline
git -C "$G" status --short
git -C "$G" log -3 --oneline
"$M" -c 'import opensim as o; print(o.GetVersionAndDate())'
"$P" -c 'import numpy, scipy, PIL, matplotlib; print(numpy.__version__, scipy.__version__, PIL.__version__, matplotlib.__version__)'
~~~

Choose unused names before creating output. A second attempt gets another name;
do not remove or overwrite the earlier attempt.

~~~bash
export N="$TASK/research/moco-c48-contact-a"
export NE="$G/game/Evidence/moco-contact-c48-study/candidate-a"
export ASSET=MocoContact48A
test ! -e "$N" && test ! -e "$NE" && test ! -e "$G/game/Assets/Eonwild/$ASSET"
~~~

If the test fails, stop and choose a new name. Only after it passes:

~~~bash
mkdir -p "$N" "$NE/scripts"
~~~

On another machine redefine these paths and use a compatible installed Unity
editor. Retain project-version/importer requirements.

## 9. Reproduce C47 without rerunning optimization

This is a quick environment/input proof, not another validation project.
The saved evidence already includes reproduction hashes. Skip redundant
rendering if watching the existing videos is enough.

**Coefficient trap:** C47 C coefficients are offsets from archived **C46 F
physical replay**, not C47 C. Using C47 C as baseline with C47 C coefficients
double-applies the offsets.

~~~bash
"$P" - <<'PY'
import gzip, os
from pathlib import Path
Path(os.environ["N"], "c46-baseline.json").write_bytes(
    gzip.decompress(Path(os.environ["C"], "model/baseline-replay.json.gz").read_bytes())
)
PY
PYTHONPATH=src "$M" tools/coordinate_moco_prototype.py \
  --admission "$C/model/admission.json" \
  --recipe "$C/model/recipe.json" \
  --baseline "$N/c46-baseline.json" \
  --initial "$C/model/coefficients.npy" \
  --evaluate-only --output "$N/reproduce-c47" \
  >"$N/reproduce-c47.log" 2>&1
~~~

Expect the model/solution hashes in section 5; archived reproduction.json records
the earlier byte-for-byte proof. Replay writes into the supplied directory.
Use the new scratch result, never the immutable tracked C47 model directory:

~~~bash
PYTHONPATH=src "$M" tools/replay_moco_prototype.py "$N/reproduce-c47" \
  >"$N/reproduce-c47-replay.log" 2>&1
~~~

This creates replay.json (large) and replay-receipt.json (compact). Read selected
metrics instead of dumping hundreds of thousands of lines. This is **state
replay**, not independent forward dynamics.

## 10. Generate a new numerical candidate

For a changed body/profile/source, re-admit geometry. For unchanged anatomy,
reusing the hash-bound admission is appropriate. The admission tool never imports
an animated take:

~~~bash
PYTHONPATH=src "$P" tools/admit_moco_prototype.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.json \
  --profile "$PROFILE" --output "$N/admission.json"
cp "$C/model/recipe.json" "$N/recipe.json"
~~~

Edit this new recipe and/or shared implementation for your actual hypothesis.
Record rationale/provenance. Save a versioned catalog recipe when selecting the
new behavior/model configuration.

For a local refinement using C47's existing coefficient basis:

~~~bash
PYTHONPATH=src "$M" tools/coordinate_moco_prototype.py \
  --admission "$N/admission.json" --recipe "$N/recipe.json" \
  --baseline "$N/c46-baseline.json" \
  --initial "$C/model/coefficients.npy" \
  --output "$N/coordinate-a" >"$N/coordinate-a.log" 2>&1
~~~

If coordinate topology or basis changes, inspect coefficient-layout.json before
reusing coefficients. To start a fresh C47-based search, use
"$N/reproduce-c47/replay.json" as baseline and omit --initial. That is a different
initialization, not exact C47 reproduction.

Inspect the optimizer receipt, then replay:

~~~bash
PYTHONPATH=src "$M" tools/replay_moco_prototype.py "$N/coordinate-a" \
  >"$N/coordinate-a-replay.log" 2>&1
export SELECTED="$N/coordinate-a"
~~~

Full Moco collocation is a separate experiment, using an explicit warm start:

~~~bash
PYTHONPATH=src "$M" tools/build_moco_prototype.py \
  --admission "$N/admission.json" --recipe "$N/recipe.json" \
  --warm-start "$SELECTED/solution.sto" \
  --mesh 25 --output "$N/moco-b" >"$N/moco-b.log" 2>&1
~~~

The archived D continuation recipe is at
$E/unselected-moco-d/recipe.json; its returned solution is another diagnostic
warm start. More mesh points are not automatically better. Monitor primal/dual
infeasibility and dense behavior, not only objective. Exit 2 on non-success still
preserves final model/solution/receipts.

OpenSim's official stop mechanism creates a file matching
delete_this_to_stop_optimization__*.txt. For a bounded stop, identify and remove
**only the current run's exact sentinel**, then wait for final solution/receipt.
Do not broadly delete files or kill unrelated processes.

**OpenSim 4.6 callback trap:** intermediate scaled callback .sto files can have
degenerate/zero times and scaled states. They are not usable physical trajectories.
Use the returned final unscaled MocoSolution written by the tool. Do not guess
scales to “repair” callback files.

Do not automatically replace SELECTED with moco-b. Replay, inspect and compare
first; a full-solver iterate may be worse. Preserve both. A bounded unsuccessful
solve does not establish biological or mathematical infeasibility.

The 1,000-kg numerical mass conditioning scales masses, inertias, forces and
passive parameters consistently; focused tests check acceleration invariance.
Do not casually alter it or reintroduce the fixed rotational-stop damping
degree/radian error.

## 11. Forward replay, retarget and native capture

Independent replay with saved controls and no tracking/root assistance:

~~~bash
"$M" "$C/scripts/forward_probe.py" "$SELECTED" \
  >"$N/forward.log" 2>&1
~~~

This script writes forward-incremental.json into SELECTED, not its own directory.
Inspect duration, orientation drift and all root/joint errors.
COMPLETE_MEASURED_NOT_CERTIFIED means completion only.
tools/forward_moco_prototype.py is the full OpenSim convenience-path alternative;
the incremental probe supplied C47's bounded drift measurement.

Optional fast mechanical movie from replay, not the final skinned deliverable:

~~~bash
"$P" tools/render_moco_prototype.py "$SELECTED" --seconds 6 \
  >"$N/mechanics-render.log" 2>&1
~~~

Retarget the actual source rig:

~~~bash
PYTHONPATH=src "$P" tools/retarget_moco_prototype.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.json \
  --profile "$PROFILE" --replay "$SELECTED/replay.json" \
  --output "$N/skin-a" >"$N/retarget.log" 2>&1
~~~

Outputs: root_motion.glb, source-animal.profile.json, retarget.json.
The tool validates source/profile identity, measures emitted skin and retains
articulation. Do not substitute an arbitrary historical animated GLB as anatomy.

Import into a **new** Unity folder and build the simple review player:

~~~bash
mkdir -p "$G/game/Assets/Eonwild/$ASSET"
cp "$N/skin-a/root_motion.glb" "$G/game/Assets/Eonwild/$ASSET/tarbo.glb"
cp "$N/skin-a/source-animal.profile.json" "$G/game/Assets/Eonwild/$ASSET/tarbo.profile.json"
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod MocoPrototypeReviewBuilder.Build \
  -moco-folder "$ASSET" -logFile "$N/unity-build.log"
~~~

Require MOCO_REVIEW_BUILD_SUCCESS before capture. Only one Unity editor may own
the project. If the user has it open, coordinate rather than killing it.
Do not launch an old player after a failed build. The builder replaces the
disposable app under game/Builds/; committed source/evidence are separate.

Capture side and quarter sequentially, waiting for each player to exit:

~~~bash
"$PLAYER" -capture-dir "$N/frames-side" -capture-frames 144 \
  -candidate "C48 A / CONTACT AND SUPPORT" \
  -description "Native time / experimental physics / pending review" \
  -logFile "$N/capture-side.log"

"$PLAYER" -capture-dir "$N/frames-quarter" -capture-frames 72 \
  -front-quarter -candidate "C48 A / CONTACT AND SUPPORT" \
  -description "Native time / experimental physics / pending review" \
  -logFile "$N/capture-quarter.log"
~~~

This captures 24 fps at 1280x720. Keep raw frames in task storage.
The player samples saved motion and accounts for cycle root travel without
runtime correction. Verify frame counts/receipts before packaging.

## 12. Package, measure and evaluate the emitted result

**Evidence-script trap:** most candidate-c/scripts/ tools write to their own parent
evidence directory. Do not execute them in place for a new candidate, or C47
outputs will be overwritten. Copy first:

~~~bash
cp "$C"/scripts/*.py "$NE/scripts/"
~~~

Edit copied labels/titles/filenames from C46 F / C47 C to C47 C / C48 A.
package.py hardcodes the comparison filename/labels; measure_attention.py,
measure_body.py and audit_ankle.py also hardcode some titles/baseline labels.
Adjust the comparison crop if framing changes. Retain measurement algorithms
unless the new hypothesis requires a deliberate documented change.

~~~bash
"$P" "$NE/scripts/package.py" \
  --side "$N/frames-side" --quarter "$N/frames-quarter" \
  --benchmark-video "$C/tarbo-moco-side.mp4"

PYTHONPATH=src "$P" "$NE/scripts/measure_attention.py" \
  --baseline "$G/game/Assets/Eonwild/MocoContact47C/tarbo.glb" \
  --candidate "$G/game/Assets/Eonwild/$ASSET/tarbo.glb" \
  --profile "$PROFILE" --admission "$N/admission.json"

"$P" "$NE/scripts/measure_body.py" \
  --baseline "$N/reproduce-c47/replay.json" \
  --candidate "$SELECTED/replay.json"

"$P" "$NE/scripts/audit_ankle.py" \
  --baseline "$N/reproduce-c47/replay.json" \
  --candidate "$SELECTED/replay.json" --label "C48 A"
~~~

Packaging creates MP4s, all-frame sheets and every source-frame hash.
Attention measurement also creates import-reference.json. Use that for parity:

~~~bash
"$UNITY" -batchmode -quit -projectPath "$G/game" \
  -executeMethod ImportParity.Verify -motion-folder "$ASSET" \
  -reference-json "$NE/import-reference.json" \
  -parity-output "$NE/import-parity.json" -logFile "$N/parity.log"
cp "$N/skin-a/retarget.json" "$NE/retarget.json"
"$P" "$NE/scripts/verify.py" >"$NE/verification.log" 2>&1

PYTHONPATH=src "$M" -m unittest discover -s tests -p 'test_moco*.py' \
  >"$NE/tests.txt" 2>&1
~~~

verify.py can report kinematic transfer PASS and skin contact FAIL simultaneously.
Read the JSON; command completion does not imply universal acceptance.
Use focused tests. Broad release/runtime certification is a later gate.

### Direct-video review procedure

1. Watch complete side/quarter clips at 1x, including multiple wraps. Compare
   C47 at the same speed/view. Write time-coded observations.
2. Watch at 0.25x/0.5x playback without replacing native deliverables.
   Frame-step transitions and inspect all 216 captured frames. Sheets help
   completeness; they cannot establish temporal smoothness by themselves.
3. Follow each foot: forward catch → loading → body passage → powered rear push
   → heel rise → toe release → relaxed recovery. Is it one action? Look for
   post-release extension, ankle flicks, hovering support, skating, penetration,
   knee overextension and abrupt joint reversals.
4. Follow pelvis, chest, neck base/middle, nose and proximal tail together.
   Reject jelly motion, pogo pelvis, uncontrolled neck bounce, rigid tail base,
   vertical spring tail or distracting pursuit-head sway.
5. Plot angles/velocities against actual contact forces and phase over the
   entire sequence. Explain a visible spike's cause before adding a filter.
6. Keep physical COM, emitted pelvis and neck landmarks distinct. Review
   ankle/MTP/digit bounds, capacity/control use, material clearance, loaded
   surface velocity, dense residuals and independent forward drift.
7. Reject obvious regressions before presenting. If the correction is useful
   with a remaining limitation, show it and label the tradeoff. Do not approve
   on behalf of the user.

## 13. Archive, document, push and pause

Archive the selected candidate's exact inputs/results in NE/model/:

- Admission, recipe, .osim, final unscaled .sto, model/solve/coordination/replay
  receipts and relevant optimizer logs/status.
- Coefficients, basis/layout and exact compressed initializer baseline if used;
  record the baseline hash and coefficient relationship.
- Independent forward receipt.
- Environment versions, source factory commit and geometry/profile/GLB hashes.
- Retarget receipt, Unity reference/parity, capture receipt, all-frame sheets,
  plots and native-time videos.
- README/review JSON separating candidate generation, visual approval, physical
  validation, Unity parity and production status.
- Reproduction commands and a SHA256 manifest.

Do not overwrite C47 receipts or reuse them to certify changed assets.
Keep giant intermediate tables, raw frames and disposable builds in task storage,
but preserve enough exact input in Git to reproduce/replay without that cache.
Unselected trials retain truthful status.

Update both roadmaps, central research/Moco docs and artistic direction with the
actual result. PENDING/FAIL/NOT_RUN/NOT_ATTEMPTED are valid states.
Do not scatter important parameters into unrelated ad hoc documents.

Inspect diffs, stage explicit paths, commit and push both branches without force.
Verify each remote branch SHA equals its local HEAD:

~~~bash
git -C "$W" status --short
git -C "$W" diff --check
git -C "$G" status --short
# Inspect authored diffs. Existing Unity-generated files and exact archived
# source documents may contain whitespace; do not rewrite their bytes casually.
# Explicit git add <task paths>, then commit before the following pushes:
git -C "$W" push origin HEAD:refs/heads/codex/animal-profile-housekeeping
git -C "$G" push origin HEAD:refs/heads/codex/animal-profile-housekeeping
git -C "$W" rev-parse HEAD
git -C "$W" ls-remote origin refs/heads/codex/animal-profile-housekeeping
git -C "$G" rev-parse HEAD
git -C "$G" ls-remote origin refs/heads/codex/animal-profile-housekeeping
~~~

If someone advanced a branch, inspect/integrate safely. No force push or automatic
reset. “Push all” means task code/docs/selected evidence, not unrelated files or
other worktrees.

Final checkpoint message: present actual MP4s inline where supported
(Markdown image syntax with an absolute local video path in Codex), a before/after,
what changed, important measured improvements/regressions and remaining failures.
Supply exact remote SHAs. Stop owned solve/render processes and **pause for user
feedback**.

The existing Codex goal is paused. Do not wake stopped workers or automations.
Its old wording about subagent implementors is obsolete. The incoming agent may
maintain its own continuation goal as authorized by the user.

Your first useful action is to verify both checkouts and watch C47 C.
Your next useful deliverable is a scientifically better-motivated, self-reviewed
C48 animation checkpoint, not another framework or a claim that physics is solved.
