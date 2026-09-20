# Factory movement roadmap and acceptance tracker

Updated 2026-09-20. This is a living evidence tracker, not a fixed plan inherited from an earlier model. Update it at every visual checkpoint. Game-design chapters retain product authority.

Research before the next running pass: [running evidence baseline](research/RUNNING_EVIDENCE_BASELINE.md)
records measured bird motion, the published BIRDS model, and diagnostic Allo/Tarbo
extrapolations. The user requested evidence-based calibration after the C37
landing/release analysis. Checkpoint 38 adopts selected, explicitly transferred priors. Checkpoint 39 adds
whole-stride leg fitting; both-animal review is pending.


## Current animation inventory

Checkpoint 27 retained-braking-support stops are approved for both animals.
Latest full checkpoint approval is checkpoint 28. Checkpoint 32 is the user-selected running base; checkpoint 34 has changes requested; checkpoint 35 has changes requested; checkpoint 36 has changes requested; checkpoint 37 has further changes requested; checkpoint 38 C has changes requested (Tarbo substantially improved; neck needs restraint; Allo not fully convincing); checkpoint 39 B is the periodic leg-fit candidate awaiting review. **Approved means visually accepted
in the reviewed clips**, not fully certified for arbitrary gameplay. Unless a row
says otherwise, both admitted animals use the same shared engine with profile data.
Historical sections and capture-time receipts below retain earlier review states.
Checkpoint 26 is the approved walking side-hit recovery baseline; standing impacts remain checkpoint 25.

| Movement family | Allosaurus | Tarbosaurus | What remains |
|---|---|---|---|
| Grounded stance / held idle | Reviewed baseline | Reviewed baseline | Broader expressive idle behavior |
| Normal walking | Approved, iteration 14 | Approved, iteration 15 | Preserve gait while completing production contact work |
| Faster walking | Approved in sequence | Approved in sequence | Grounded fast walk; running is a separate family |
| Idle → start → normal → faster → slow → stop | Approved sequence; revised stop approved, checkpoint 27 | Approved sequence; revised stop approved, checkpoint 27 | Preserve retained braking support in connected controls; full contact parity pending |
| Heel roll, toe-off and swing recovery | Reviewed; added intermediate toe joints | Reviewed | Maintain articulation across combined behaviors |
| Walking curves / tight walking turns | Approved, checkpoint 17 | Approved, checkpoint 17 | Connect to player steering; final material contact and mass work |
| Stepping turns in place | Approved, checkpoint 12 | Approved, checkpoint 12 | Connect to other movement states; final material contact and mass work |
| Backward start, steps and stop | Approved, checkpoints 19/20 | Approved, checkpoints 19/20 | Connected controls and runtime obstacle awareness |
| Deliberate lateral balance recovery | Approved, checkpoint 21 | Approved, checkpoint 21 | Live balance detection and triggering |
| Standing / slow-walking side-hit stumble / catch / settle | Standing baseline, checkpoint 25; walking recovery approved, checkpoint 26 | Standing baseline, checkpoint 25; walking recovery approved, checkpoint 26 | Live collision transfer, full contact and force certification; native player shutdown fix |
| Running side-hit stumble / recovery | Requested; not implemented or reviewed | Requested; not implemented or reviewed | Carry running momentum, support phase and articulation into urgent catch steps and a controlled exit |
| Sprinting side-hit stumble / recovery | Requested; not implemented or reviewed | Requested; not implemented or reviewed | Sprint-specific support availability and momentum; review recoverable hits independently from knockdowns |
| Hit-induced knockdown from walking | Requested; not implemented or reviewed | Requested; not implemented or reviewed | Loss of support → descent → actual body-ground contact → displaced grounded settle |
| Hit-induced knockdown from running | Requested; not implemented or reviewed | Requested; not implemented or reviewed | Retain incoming travel through the fall; choreograph ground contact and residual slide/rotation where appropriate |
| Hit-induced knockdown from sprinting | Requested; not implemented or reviewed | Requested; not implemented or reviewed | Review sprint entry and ground arrival separately; no assumed approval from the running fall |
| Grounded aftermath / get up after a hit | Missing | Missing | Transition from actual displaced fallen pose into supported rise; exit depends on gameplay state |
| Independent gaze / neck attention | Mini-world demo and routine/exceptional glances approved | Mini-world demo and routine/exceptional glances approved | Sensory decisions, visibility/occlusion and coordinated body following |
| Arm carriage and secondary motion | Full-transition pass approved | Full-transition pass approved | Behavior-specific overrides for attacks, rest and interaction |
| Jaw relaxation / breathing-like cycle | Full-transition pass approved | Full-transition pass approved | Full-body breathing and behavior-specific mouth control |
| Expressive idle / listening / alert scanning | No complete approved family | No complete approved family | Compose meaningful attention, posture and breathing behaviors from existing layers |
| Running / sprinting | Sustained run candidate, checkpoint 38 C; pending review; sprint missing | Sustained run candidate, checkpoint 38 C; pending review; historical Run010 / Sprint006 preserved | Review release smoothness and retained tail/body motion; then entry/braking and sprinting |
| Feeding / gripping / pulling | Current approved transfer missing | Historical Feeding003 reference preserved | Current grounded support, oral contact and interaction handoff |
| Drinking / swallowing | Missing | Missing | New choreography and world interaction |
| Rest / sit / lie down / rise / sleep | Missing | Missing | New support transitions and resting behavior |
| Bite / attack / active defense | Missing complete family | Missing complete family | Offensive/action choreography and gameplay windows; received side-hit reaction already exists |
| Injury / limp / death | Missing | Missing | Injury-specific movement and terminal outcomes; hit-induced falls/get-up are tracked separately above |
| Jump / airborne landing / recovery | No reviewed behavior | No reviewed behavior | Airborne gait code is not a reviewed jump/landing family |
| Terrain adaptation / slopes / stepping over | Runtime acceptance missing | Runtime acceptance missing | Adapt contacts on uneven ground and obstacles |
| Swim / wade / enter or leave water | Missing | Missing | Water interaction and locomotion; current mini-world water is scenery |
| Social / display / vocalization | Missing | Missing | Behavior breadth and intent |
| Connected runtime movement controls | Approved, checkpoint 28 | Approved, checkpoint 28 | Forward/curves/in-place turns/reverse/stops connected; visually approved. Lateral/impact controls, terrain and full contact parity remain open |

Checkpoint 27 stopping baseline is approved and preserved. Current: checkpoint
28 connected controls, approved for both animals. Next: running/sprinting transfer;
running and sprinting side-hit recovery; hit-induced knockdowns from walking,
running and sprinting with grounded aftermath/get-up; feeding/drinking and the
remaining rest, combat/injury and behavior breadth. Each new entry gait and
outcome needs its own both-animal visual checkpoint. Running/sprinting reactions
need reviewed incoming gaits; walking knockdowns can be developed independently
once the current recovery baseline is preserved. This is a roadmap, not approval
of any unreviewed take.

Detailed impact scope: principal Eonwild `docs/SIDE_IMPACT_RECOVERY_SPEC.md`,
“Requested impact coverage” section. This is documentation guidance, not a
runtime import.


## Dynamic connected controls — checkpoint 28, approved

The player can request walking, faster walking, left/right walking turns,
in-place turns, reverse and stopping. Runtime motion uses the approved 27/17/12/19
source clips unchanged, with a shared contact/pose adapter for both rigs. Endpoints
are the actual resulting world pose and support placements. Incoming motion selects
a compatible phase, carries linear/angular velocity, and releases inherited foot
placement during recovery. Reverse stopping uses reverse choreography.

The public state-adoption entry point carries articulated pose, body position,
heading, linear/angular velocity, and world foot poses/velocities/contact flags.
Six actual-rig checks displaced and rotated each animal mid-step before adopting
walking, a curve and reverse. These checks exercise grounded adoption; the full
hit-to-run example still needs live collision handoff and the incoming run solver.

Evidence lives in principal Eonwild `game/Evidence/connected-movement-study/`.
The separate native app is `game/Builds/Eonwild Connected.app`; the approved
mini-world scene and earlier checkpoints are preserved. This adapter does not
certify skin contact, joint loads or full physical inertia. Current planar travel
still needs terrain/collision reconciliation. Capability-driven straight cadence
and acceleration budgets remain open; approved straight timing is preserved.
Both native 42-second Unity recordings completed (1,008 frames each at 24 fps),
with all 2,016 frames inspected chronologically. Each sequence made 17 handoffs.
Maximum foot-joint target residual was 1.29 mm Allosaurus / 1.73 mm Tarbosaurus;
these are adapter diagnostics, not skin-contact certificates. Focused native
keyboard checks verified input/release, animal selection, pause/reset and exit.
Held-key combinations were exercised through the demo intent path; live FPS was
not measured in this pass. The player was closed after verification.

User approved both animals on 2026-09-15. Checkpoint 29 begins normal running transfer; sprinting remains a separate later review.

## Retained braking stance — checkpoint 27 revision, approved

The user identified an unnecessary half-step followed by a return toward rest in
both stopping animals, and preferred the fluid stance recovery of the approved
side-hit motion. The ordinary stop planner was releasing its earlier braking foot
after forward travel had ended, solely to bring it into a prescribed closing pose.

Shared recipe `walking-response-review.v2.json` opts into
`retain_braking_support`: retain each foot's last braking placement, suppress its
preparation for another toe-off, and let the other foot finish its committed
recovery as the body stops. Both contacts then remain planted. The ending stance
is slightly staggered (about 7.9 cm Allosaurus / 9.6 cm Tarbosaurus between planned
forward placements). The transition contract names `retained_braking_stance`;
future controls must consume that actual stance rather than assume canonical idle.
Legacy recipes retain their previous behavior. This is shared grounded-stop
choreography, not a species branch or a claim of full force simulation.

Both actual-rig GLBs are newly emitted and reopened. All sampled translations and
rotations before the stop stage match the previous straight assets exactly.
Fifty-three focused checks pass, including retained anchors, continuous landings
and the truthful exit contract. Final contact is solved on the new support plan;
new reopened measurements cover all 444 keys and their midpoints on each animal.
Existing whole-clip maxima do not increase (floor penetration 4.49/10.90 mm,
loaded-material residual 2.90/2.07 mm), and production contact passes remain false.
The preceding speed, first-step body response, profile cadence limitations and
full force/parity work remain as documented in the earlier review.

Evidence: principal game `game/Evidence/retained-support-stop-study/` and separate
runtime assets `game/Assets/Eonwild/Directional/StraightStop27/`. The earlier
checkpoint-27 replay is retained with the user's requested stop correction.
Both native Unity captures completed successfully: 438 frames per animal at
24 fps, 18.25 seconds each. All 876 frames were inspected in chronological
sheets; no additional post-stop reset was identified. Runtime secondary arm/jaw
motion remains active. User approval on 2026-09-15: “much much better! approved”.
These exact revised stops are now the visual baseline for both animals.
Capture-time receipts remain unchanged; user-review.json records the approval.
Connected controls are next, with actual final foot placements preserved.
Full force and production contact acceptance remain open.

## Earlier straight response replay — checkpoint 27, stop changes requested

This checkpoint addresses an outstanding review gap: the purposeful straight
start/stop retiming first emitted during checkpoint 16 was never separately
approved when the walking curves advanced to checkpoint 17. The original
approved connected sequence (iteration 16) is a different baseline.

The exact existing straight GLBs are preserved and replayed in fresh native-time
three-quarter recordings on both animals, alongside their original side views.
There was no new solver or motion export in the initial checkpoint-27 replay. The review isolates
first-step acceleration, sideways weight transfer, recovery through normal/faster
walking, final placement and settling. Arm and jaw secondary motion stays active.
The recordings retain the source take's on-screen label “16”; this is review
checkpoint 27 of that existing motion, not a relabeled new animation.

The authored response reaches full speed over 0.9 of one step after 0.35 s
preparation. Moving-foot articulation has its own 0.85 floor. These clips retain
the earlier gait cadence (1.23 s per step for both animals), anatomy and body
support coefficients; they do not demonstrate the newer capability-driven
cadence/acceleration differences. That integration remains work for connected
controls and must preserve the approved visual rhythm.

Both fresh captures exited successfully; all 876 frames were inspected in 30
chronological sheets. Forty-seven focused transition checks pass. The motion
hashes match the original receipts; existing reopened contact measurements still apply to the same assets:
floor penetration maxima 4.49/10.90 mm and loaded-material residual maxima
2.90/2.07 mm (Allosaurus/Tarbosaurus). Those are diagnostic results, not new
production passes. Full force balance, numeric capability acceleration budgets
and complete Unity contact parity remain pending. The initial body rise,
particularly Tarbosaurus, is explicitly left for native-speed weight judgment.

Evidence: principal game `game/Evidence/straight-response-review-checkpoint27/`.
Pause for both-animal feedback here. Do not infer approval of this response from
the approved original sequence, curves, or side-hit recoveries. After review,
resume connected controls, then the incoming run/sprint families before their
hit reactions. A requested visible correction comes before that expansion.

## Earlier catch articulation — checkpoint 26, visually approved

The first redirected walking catch previously continued the walking fold until
the knee reached its hard flexion boundary, then unfolded sharply. The shared
planner now permits an authored earlier release of that incoming articulation
objective. Recipe `stumble-recovery-review.v5.json` uses 65% of catch flight;
previous recipes retain the full-flight release. The incoming gait phase remains
continuous, with a C2 release into catch articulation before touchdown.

Both animals' C/D packages are exported and reopened. The planned body/footwork
and measured final pelvis paths match checkpoint 25 exactly. In case C, the
largest early ankle change between keys/midpoints falls from 17.79 to 11.04 degrees
for Allosaurus and 11.51 to 10.32 for Tarbosaurus; neither sampled first-catch knee
reaches the previous 65-degree corner. Case D unfolds earlier too, with a slightly
larger peak angular change; the user accepted both native-time videos.

Evidence: principal game `game/Evidence/earlier-catch-articulation-study/`.
User feedback on 2026-09-15: “i like them”. Both checkpoint-26 C/D videos are
visually approved. Preserve v5 as the current walking side-hit recovery baseline,
including the earlier articulation handover and checkpoint-25 body continuity.
Standing impact cases remain checkpoint 25. The game evidence `user-review.json`
binds the approved videos and motion hashes. Capture-time receipts retain their
historical pending state. Final contact, whole-body force certification and live
collision integration remain open; the native shutdown issue is tracked separately.

## Continuous body recovery — checkpoint 25, continuity approved

The shared impact response now carries the incoming walking articulation clock
into the shorter catch and starts the following preparation during late weight
acceptance. The currently accepting foot cannot immediately lift again.

In the first preview, the user identified sideways push-stop staircases. The
emitted trajectory confirmed that neutral support-plane accommodation cancelled
continuous body travel during single support, then released it at support
switches. During impact this geometric root preference now yields over 65 ms;
fixed foot anchors, anatomical leg solving and final material/floor correction
still run afterwards. This is authored support compliance, not full force balance.

Recipe: `stumble-recovery-review.v4.json`; canonical animal profiles are unchanged.
Both actual rigs have standing chest/hip and opposite walking-phase impact cases.
Evidence: principal game `game/Evidence/continuous-body-impact-study/`.
The body path is measured on every native 24 fps frame, alongside joint/contact
receipts and chronological image review. Checkpoint 24 remains preserved.

Implementation, actual-rig export and native Unity playback are delivered at
this checkpoint. User feedback: “Recovery feels continuous.” The sideways body
continuity is approved for both review videos; preserve this as the current
recovery baseline. Early Allosaurus ankle unfolding remains the next local polish
target. Production contact/force certification remains pending; this feedback
does not approve those gates or a new motion family.

## Side-impact recovery — checkpoint 24 positively reviewed, transition polish next

All six requested ideas are represented in the shared engine and exported on
both actual rigs: localized point/vector input; support-dependent braking and
absorption; available-foot selection with walking-swing redirection; changing
trunk/tail response; bounded threat attention with arms/jaw; and an explicit
displaced alert exit state. This is a reduced horizontal/yaw model with authored
regional/vertical compliance, not articulated whole-body dynamics.

Recipe: Factory `catalog/behaviors/stumble-recovery-review.v3.json`.
Canonical profiles hold optional `impactResponse` settings, with authored
provenance. Existing mass, agility, attention and semantic bindings are reused.
Earlier recipes and approved clips remain preserved. The detailed authority is
the principal game's `docs/SIDE_IMPACT_RECOVERY_SPEC.md`.

Cases A/B compare standing chest/hip hits at 1000 N s; C/D interrupt opposite
slow-walking swing phases at 1800 N s. Both walking cases carry current foot
position/velocity/phase into the catch. Allosaurus selects 3/3/5/5 placements;
Tarbosaurus 3/3/4/4. The first foot changes between C and D. Landings increase
braking authority; changing acceptance time changes subsequent body travel.

Evidence: principal game `game/Evidence/support-coupled-impact-study/`.
All eight actual-rig exports reopened; Unity build and captures completed.
Two chaptered native 1280×720, 24 fps videos contain 568 Allosaurus and 588
Tarbosaurus frames. Every frame inspected in 53 chronological sheets, with
selected full-size transition views. 53 focused tests and full video decode pass.
Implementation/generation/export/Unity playback: complete. User review: positive first-pass feedback; transition polish requested.

No sampled reach overflow. Emitted attention stays within the selected profile
caps. Standing planted patches remain stable; the moving cases retain up to
35.82/44.34 mm individual planted skin-vertex drift (Allosaurus/Tarbosaurus),
despite stable centroids. Case C has a quick ankle unfolding that remains a
specific visual review point. Full material-contact acceptance and whole-body
force balance remain pending. The evidence records final pelvis/proxy differences;
the reduced proxy must not be mistaken for measured whole-body COM.

User feedback: “they are super good starters”; overall direction is positively reviewed, with transition smoothness still needing polish. Preserve checkpoint 24 as the starting reference for that pass. This feedback does not certify production contact or forces.

Next polish target: continuous weight acceptance into the following correction,
ankle unfolding, and settling into the alert stance, while preserving urgency.
Remain paused until the next implementation request.

Live collision transfer, arbitrary runtime interruption,
unknown-threat search, connected controls, falls and other motion families are
not delivered by these baked review clips.

## Immediate curved impact — checkpoint 23, feedback received

The shared response now bends the chest sideways with head/tail lag, while a low
catch begins almost immediately. Reaction onset, first-foot release and load
transfer share one clock; unexpected hits no longer anticipate an unload. An
authored emergency cadence shortens the first catch and progressively returns
to the profile-derived base period. Recipe authority is
`catalog/behaviors/stumble-recovery-review.v2.json`; v1 and earlier assets remain.

First release occurs 33.8 / 35.6 ms after impact (Allosaurus / Tarbosaurus), with
first landing at 295.6 / 332.7 ms. These are authored timings, not biological
reflex measurements. The same 1000 / 1800 N s inputs and profile mass settings
retain checkpoint 22's planned distances and catch counts. A draft ankle snap
on Allosaurus was corrected by lowering catch clearance and vertical compression
before the final exports and captures.

Native Unity evidence: `game/Evidence/immediate-curved-impact-study` in the
principal game. Allosaurus: 127 frames / 5.291667 s; Tarbosaurus: 106 frames /
4.416667 s, both 1280×720 at 24 fps. All 233 frames inspected chronologically in
11 sheets, plus six full-size frames. A fixed elevated three-quarter camera
exposes the sideways curve. 47 focused tests, both actual-rig generations,
reopened export measurements, Unity build, captures and full video decode pass.

Maximum knee angles are 146.76 / 114.07 degrees; ankle angles 128.69 / 135.01.
Zero sampled reach overflow. Maximum planted skin-vertex drift is 7.01 / 2.13 mm;
full material contact and whole-body force balance remain pending. This remains
a baked authored recovery, without live collision transfer or fall dynamics.
Checkpoint 21 is accepted; 22 is a revision reference. The user described 23 as
better and requested development of the six improvements specified for 24. This
is positive feedback and continued refinement, not full production acceptance.
Connected controls and other motion families remain after the impact checkpoint.

## Side-hit stumble and recovery — checkpoint 22, revision requested

User feedback: checkpoint 22 is too restrained and the catch appears delayed. The next pass must bend the body sideways into a curve and begin recovery almost immediately. Checkpoint 21 remains accepted; checkpoint 22 was not approved.

Checkpoint 21 is accepted. The requested stronger version now receives an
authored side impulse before catching and recovering, with continuous torso/hip
compression, delayed head/tail response and low articulated foot release. A new
shared impact planner consumes canonical victim mass, lateral acceleration and
cadence; the approved deliberate sidestep and all older assets remain preserved.

The same two rightward received impulses (1000 / 1800 N s) are shown on both
animals. Allosaurus plans 0.401 / 1.147 m of travel and 2 / 4 catching steps;
Tarbosaurus plans 0.154 / 0.418 m and 2 / 2 steps. These are authored diagnostic
inputs and planned distances, not measurements of dinosaur collisions or final
COM travel. Head/torso yaw stays within the ordinary profile envelope.

Native Unity videos: principal game game/Evidence/stumble-recovery-study.
Allosaurus 6.208333 s / 149 frames; Tarbosaurus 5.416667 s / 130 frames, 24 fps.
All 279 frames were inspected chronologically in 13 sheets, plus six full-size
neutral/recoil/catch frames. The stronger Allosaurus response opens a larger
support area and adds another catch pair; Tarbosaurus remains more restrained.
Review the perceived urgency and weight; no user approval is inferred.

47 focused tests, actual-rig generation, final-export measurements, Unity build,
native capture and complete video decoding passed. Zero reach overflow; maximum
knee interior angles 130.28 / 110.35 degrees. Maximum planted skin-vertex drift
8.71 / 7.58 mm remains, despite near-fixed patch centroids. Full contact and
whole-body force balance are pending. This is a new authored behavior family,
not a live collision or fall solver. Hit timing is an annotation in the viewer,
not gameplay damage. Other directions are supported by semantic input and a
mirrored planner check; only rightward hits were rendered in this checkpoint.
Pause here for feedback before connected controls or additional motion families.

## Lateral balance recovery — checkpoint 21, user accepted

The shared engine now generates a controlled rightward recovery and matching
leftward recovery for both admitted animals. The travel-side foot opens support,
then the other foot follows to restore the broad stance. Low recovery, a modest
toe/metatarsal release, load-weighted hip roll and bounded attention overlap.
This is authored planned recovery; external impacts and dynamic balance detection
are not implemented.

Behavior shape and stance live in `catalog/behaviors/lateral-recovery-review.v1.json`.
Animal mass, lateral force, cadence and attention ranges come from the canonical
profiles. The new behavior planner reuses directional foot sampling, support/load
response, semantic limb IK and final material-contact correction. No animal profile
or approved locomotion asset was retuned.

Native Unity evidence: principal game `game/Evidence/lateral-recovery-study/`.
Allosaurus 5.458333 seconds / 131 frames; Tarbosaurus 6.041667 seconds / 145 frames,
both 24 fps. All 276 captured frames were inspected in 13 chronological sheets;
opening and transfer frames were also inspected at full capture resolution.
The response is deliberately restrained; review whether the catch and settling
communicate enough weight before adding stronger reactions.

38 focused tests passed; actual-rig generation, Unity build, capture and video
decode passed. Reopened source exports have zero reach overflow. Maximum planted
skin-vertex drift is 14.08 mm Allosaurus / 16.47 mm Tarbosaurus; full material
contact and whole-body force balance remain open. This is a diagnostic checkpoint,
not production acceptance. User accepted both animals on 2026-09-14: “i liked the idea! and how it looks.” Preserve Factory 0ddf799ac83fac0cae9f83c0dd9d10a2ce81b963 and game 1ee439b5df82ed53fc13f55ae874d54d5e7b5121. The immutable capture receipts retain their original pending state. The requested next checkpoint is a stronger side-impact stumble and recovery, before connected controls.

## Exceptional neck glance — checkpoint 20, user accepted

User accepted both exceptional-glance videos on 2026-09-14 (“i like both!”).
Source: Factory f5a597589e2d1716b02bad90256559fd1ca67277; game
ed6e74932ead85dcc002c4cc43c99194adb00e13. Immutable media SHA-256:
- allo-neck.mp4: d36a641ff7702efe5a4e9a8f14641cc7b18aa9df6feb65ac3bac7ea4728139c8
- tarbo-neck.mp4: e4e1404643fec1d4f9c126ef8ccbe262d12a5823da1a146251f6e8a2335d6738

The original candidate receipts remain unchanged. This is visual acceptance of
these poses and timing, not a new biological measurement or production certificate.


The user accepted checkpoint 19's ordinary-range backward footage and requested a
stronger glance. Named `exceptional` intent now selects the existing animal
envelope explicitly; no anatomy numbers or footwork were retuned. The same reverse
v2 recipe is reused with a recorded diagnostic override instead of a copied recipe.

Actual emitted head heading relative to the torso peaks at 81.424 degrees for
Allosaurus and 62.616 for Tarbosaurus. These are smoothed results of authored
85/65-degree targets, not measured biological maxima. Routine limits remain
unchanged and the measurement receipt explicitly records routine-cap exceedance
under exceptional selection.

Native Unity evidence: principal game `game/Evidence/neck-range-study/`.
All 282 captured frames were inspected chronologically; peak frames were also
inspected at full capture resolution. Allosaurus shows a more pronounced, tighter
inner-neck bend; Tarbosaurus retains a broader, stiffer silhouette. Non-attention
local channels match checkpoint 19 exactly at every source key. Twenty-four
focused tests, actual-rig generation, Unity build and full video decoding passed.
This is a neck-range study, not coordinated body following or new force balance.

The Factory embodiment contract is now the explicit ownership index. Profile
numbers are canonical; Unity exports and evidence snapshots are derived. Research
mirrors, two delivery roadmaps and legacy review tooling still exist. A unified
editor and complete migration are not claimed. The user requested the next
iteration: checkpoint 21, left/right lateral balance recovery for both animals.

## Neck baseline — checkpoint 19, user accepted

User accepted the ordinary-neck backward previews on 2026-09-14 (“this was good”).
Acceptance binds Factory source 8de1ff68b31c445090e19023db372f5577543de7,
game source f0c6173 and the immutable media in game/Evidence/neck-baseline-study.
Its original pending-review receipt remains unchanged as historical evidence.
This accepts that ordinary-range take, not exceptional poses or production certification.

The user's neck investigation is preserved with a reviewed evidence/implementation
summary in [the neck baseline](research/THEROPOD_NECK_BASELINE.md). T. rex's modeled
60-degree posture is verified; Tarbosaurus uses a comparative estimate and the
Allosaurus numeric ranges remain authored. Whole-head heading, regional curvature,
ordinary/strong/exceptional ranges and body-follow requests are distinct.

Canonical animal profiles now own ordinary/scan/strong/routine-cap/exceptional-cap
values: Allosaurus 40/55/70/80/85 degrees, Tarbosaurus 35/45/55/60/65 degrees per
side. Directional generation and Unity consume the same envelope. Ordinary reverse
recipe v2 requests 40/35 degrees; final exports reopen at 40.00001/34.99999 degrees
relative to torso. Tarbosaurus has reduced base contribution; Allosaurus distributes
bend more evenly through its two available neck controls. This is not newly measured
vertebral anatomy. Numerical envelope parity passes 60 Python/Unity cases; the
existing secondary layer retains parity across 3,000 cases.

All 282 captured frames were inspected chronologically across 13 sheets; 57 focused tests passed. Checkpoint 19 has new native front three-quarter footage in principal game
`game/Evidence/neck-baseline-study/`. Preserve checkpoint 18 and approved curves.
Exceptional poses were subsequently accepted at checkpoint 20. Coupled regional roll/pitch,
automatic body follow with grounded footwork, visibility/occlusion, and migration
of older compiler families remain pending. Neck articulation does not change the
leg contact choreography or establish new whole-body force balance. Ordinary and exceptional glances are now accepted; lateral recovery is next.

## Animal profile housekeeping

Canonical embodiment profiles now collect the approved rig bindings, explicit axes, sequence timing and consumer settings. Python reference evaluation, Unity parity vectors and Blender preview baking are documented in [the embodiment contract](ANIMAL_EMBODIMENT_CONTRACT.md). This is portability work, not a new animation family or blanket production acceptance.

## Active directional locomotion set — 2026-09-12

User requested walking turns, coordinated turns without forward travel, backward walking, and lateral balance-recovery steps. Work directly, without subagents. Preserve the approved straight gait and secondary-motion baseline.

| Checkpoint | Scope, both animals | Status |
|---|---|---|
| A — turning | Gentle walking curves, tighter low-speed turns, alternating stepping turns in place | Draft 10 accepted as a good turning baseline. Draft 11 adds numerical animal capabilities to the shared planner; both-rig Unity renders and all-frame audit complete; user accepted draft 11 as a good indie-game baseline. Draft 12 hip/contact polish visually accepted by the user. Draft 13 walking curves rejected for missing walking recovery articulation. Draft 14 restored walking recovery; user retained direction and requested timing polish. Draft 15 overlaps unloading and recovery; user requested stronger neck turning and more purposeful startup. Draft 16 received an Allosaurus walking-turn knee-overextension correction request. Draft 17 adds continuous knee flexion reserve; both native walking-turn videos visually accepted by the user ("good both", 2026-09-14). Final mass/contact remain open |
| B — reverse | Backward start, several coordinated steps, stop; its own grounded contact choreography | Checkpoint 18 remains historical. Checkpoint 19 ordinary-neck reverse and checkpoint 20 exceptional-neck reverse were visually accepted for both animals; final force/contact certification remains open |
| C — lateral recovery | Left/right recovery steps, support transfer, whole-body settling | Checkpoint 21 visually accepted on both admitted rigs; 276 native Unity frames inspected. Side-impact recovery subsequently reached checkpoint 25; final force/contact certification remains open |
| D — connected controls | Blend the reviewed directional behaviors with idle and walking; runtime root ownership and contact | After visual acceptance of A–C |

Draft 10 is the user-accepted turning reference, preserved in `game/Evidence/continuous-release-turn-study/`. Draft 11 adds profile mass/inertia, authored force/torque budgets, walking speed/cadence, braking, lateral response and attention/response timing. The shared planner consumes these values without species branches. Both actual rigs generated and were captured in Unity; all 470 captured frames were visually inspected. Current evidence: principal game `game/Evidence/capability-turn-study/`. User re-review accepted draft 11 for both animals as a good indie-game turning baseline. Draft 10 remains preserved as the preceding reference.

The user visually accepted draft 12 on 2026-09-13 as the next turning baseline. It replaces the turn's vertical pelvis pulse with a small roll that preserves the load-weighted supporting-hip height. Load acceptance is spread across touchdown/lift, and preparation time scales with height and effective lateral force/mass. The shared solver corrects planted material-patch centroid drift after body changes. Both actual rigs were generated, reopened and captured in Unity; every one of the 470 captured frames was inspected. Evidence: principal game `game/Evidence/hip-load-contact-turn-study/`.

This is a reduced authored support response, not converged whole-body force balance. Individual contact vertices still deform: maximum horizontal drift is 12.2 mm Allosaurus and 21.1 mm Tarbosaurus. Planted-interval knee travel projected onto the foot lateral axis increased from 31.6/33.8 mm in draft 11 to 38.1/55.4 mm in draft 12; this includes changing flexion and is not a joint-stress measurement, but remains a visible-polish concern, especially for Tarbosaurus. No isolated abrupt buckle was identified in the captured frame sequence; occlusion limits that observation.

Checkpoint 12 remains the accepted in-place turn. Checkpoint 17 is now the visually accepted walking-curve baseline for both animals, superseding curve drafts 13–16. Approved straight walks are preserved. Locomotion acceleration limits exclude added local pelvis accommodation. Backward start, several steps and stop is the next checkpoint for both animals; lateral balance recovery follows.

## Backward walking — checkpoint 18, review pending

The next bounded movement family is a short backward start, four alternating steps and a settled stop for both animals. The shared planner resolves a signed backward path from the animal's onboarded normal step and speed; the new reverse behavior owns its release, toe curl, recovery pitch and flank glance. It uses no reversed animation take or species branch. Existing support transfer, hip-plane accommodation, compliant pelvis roll and final material contact correction run on both rigs.

Recipe `reverse-walking-review.v1.json` uses authored fractions: 0.32 of normal step length and 0.36 of normal speed, with capability acceleration/cadence budgets. Nominal steps are 0.360 m Allosaurus / 0.439 m Tarbosaurus, with fitted step intervals 1.124 / 1.357 s. The total retreat is 1.442 / 1.754 m. These are authored reverse estimates, not paleobiological measurements. The first/last placements vary with startup and braking. Reverse stance width is 0.28 body heights; release is restrained to 4 degrees, with a low recovery arc and toes relaxed before contact.

Source durations are 5.397 / 6.328 s. Both final GLBs were reopened; maximum sampled knee angles are 133.03 / 120.12 degrees with zero source-key reach overflow. Final sampled material-vertex drift is 8.69 / 10.60 mm; stable centroids do not certify a rigid contact patch. Full force balance, continuous skin contact and complete Unity parity remain open. Native-time side and front three-quarter review evidence is in principal game `game/Evidence/backward-walking-study/`. All 564 delivered frames were inspected across 26 sheets; 41 focused tests passed. User review is pending; stop here before lateral recovery. Checkpoint 17 remains the accepted walking-turn baseline.

## Walking-turn knee flexion — checkpoint 17, visually accepted

The user identified Allosaurus knee overextension in checkpoint 16 walking turns. Reopening that candidate found a 179.15-degree knee despite zero reach overflow: geometric reach alone did not establish a credible supported leg shape. Straight checkpoint 16 motion has not received additional approval from this feedback.

Walking-curve recipe v5 adds a shared continuous flexion preference. Above the authored 155-degree knee preference, the pose cost increases smoothly and coordinates ankle articulation around the existing foot target. The shared solver retains the existing hard joint limits, recovery and contact schedule. No species branches, altered bone lengths, shortened stride or additional pelvis pulse. This is authored pose selection, not biological ROM or new force simulation.

Both actual rigs were generated, reopened and captured in Unity at native 24 fps. Maximum knee angles at all emitted keys and midpoints are 157.02 degrees Allosaurus and 155.82 degrees Tarbosaurus. Both have zero source-key reach overflow. All 691 captured frames were inspected; 35 focused tests passed. Evidence: principal game `game/Evidence/knee-flexion-walking-curve-study/`. The user accepted both native videos on 2026-09-14: "good both". The acceptance receipt binds the reviewed videos and source commits. Full material contact and whole-body forces remain open; visual acceptance is not production certification. Reverse walking is next, followed by lateral recovery.

## Purposeful walking response — checkpoint 16, correction requested

User feedback requested a little more neck turning and quicker establishment of walking rhythm, including straight starts/stops. Approved steady walks and the earlier connected sequence remain preserved.

Straight starts reach full body speed over 0.9 of one step after 0.35 s preparation. Moving-foot articulation has a separate 0.85 floor; this gain is not physical load. Stops preserve the incoming step, concentrate braking into the last 0.9-step interval, then complete placement and settling. Contact anchors and steady cadence retain the shared gait law. This is an authored response candidate: the straight sequence does not yet enforce numerical capability acceleration budgets or solve new whole-body forces.

Walking curves retain the capability-limited body path and use recovery duration from normal profile cadence: 0.76 of a normal step (0.815 s Allosaurus, 1.042 s Tarbosaurus). Extra time goes into support before and after recovery; heel preparation uses 0.40 of a normal step. Load response and foot sampling share the same contact window. The first draft delayed release too far and overextended Allosaurus; the candidate releases earlier and has zero reach overflow on both emitted rigs. Attention gain is 1.25 and neck share 0.83.

Both straight and curved motions generated and reopened on the actual rigs. Unity build and all four captures completed; 76 focused checks passed. All 1,567 captured frames were inspected across 68 sheets. Straight reopened contact remains diagnostic: floor minima -4.49/-10.90 mm and loaded-material residuals 2.90/2.07 mm (Allosaurus/Tarbosaurus). Curve planted vertices still deform up to 75.4/100.6 mm, including heel articulation. Native videos and frame inspection are saved in principal game game/Evidence/purposeful-walking-response-study/. Final contact and force acceptance remain open. **Pause for feedback; do not advance to reverse/lateral work or promote these candidates automatically.**

## Continuous walking release — checkpoint 15, response polish requested

The user retained checkpoint 14's direction but reported a brief unloading stop before recovery. The shared heel curve had reached zero velocity exactly where foot travel, lift and recovery began from zero. Recipe `walking-curve-review.v3.json` now continues heel rise through release, peaks at 10% of swing and relaxes by 40%. Recovery lift reuses the approved walk's rounded height curve, resolved from the admitted gait. Contact times, path, placements, pointing and load schedule retain checkpoint 14's settings; no species branches or changes to approved straight walks.

Both actual rigs generated, reopened and ran in Unity. Native 24 fps videos and all 691 inspected frames are saved in principal game `game/Evidence/continuous-walking-release-study/`. Thirty-five focused checks pass. Earlier lift makes early joint flexion more pronounced, especially Allosaurus; native-speed feel still requires user review. Final individual planted-vertex drift is 78.1/99.7 mm (Allosaurus/Tarbosaurus), including articulation/deformation, despite stable centroids. Reach overflow is zero at emitted keys. Whole-body forces, continuous-time contact and live steering remain open.

**Checkpoint 15 feedback requests stronger neck turning and faster establishment of walking rhythm. Checkpoint 17 resolves the requested Allosaurus knee correction and is visually accepted for both walking turns; checkpoint 12 remains accepted for in-place turns.** Reverse walking and lateral recovery stay queued.

## Articulated walking curves — checkpoint 14, timing changes requested

Checkpoint 13 was rejected: head/foot pointing was acceptable, but recovery lacked the walking articulations. The shared engine now reuses the admitted walk's metatarsal recovery, separate pad pitch and digit flexion on the curve's contact clock. It retains the curve's foot placement, pointing, heel preparation and hip-load response. Gentle/tight turns use authored articulation scales of 0.90/0.75 and clearance scales of 0.80/0.65; no species branch or changes to normal stride.

Both actual rigs generated, reopened and captured in Unity at native 24 fps. All 691 captured frames were inspected. Fifty-eight focused tests pass; 493 approved-gait samples exactly match the pre-extraction implementation. Evidence: principal game `game/Evidence/articulated-walking-curve-study/`, including videos, all-frame sheets, recipes, source/profile snapshots and measurements.

The recovery now visibly folds and reopens. Final material contact remains open: maximum individual planted-vertex drift is 82.0 mm Allosaurus / 104.9 mm Tarbosaurus, including heel-roll articulation/deformation, despite stable patch centroids. No unreachable extension at source keys; continuous-time contact, whole-body forces and live steering remain unvalidated. Initial heel preparation is not a certified idle join. **User feedback: direction is good; unloading briefly stops before recovery and needs polish. Checkpoint 15 addresses that timing above; 14 is not approved as a completed walking turn.**

## Walking curves — checkpoint 13, rejected

Generated both animals directly from the shared solver using a separate `walking-curve-review.v1.json` recipe. Each performs a four-step 35-degree gentle curve, settles, then makes a four-step 65-degree turn in the opposite direction at a shorter step setting. These are two movements separated by settling, not continuous S steering. The curve recipe uses 70% and 42% of each profile's documented normal step respectively; normal step/stride values and approved straight-walk assets are preserved. Explicit authored reductions replace the earlier fixed short pivot-step distance for this walking study.

The shared planner integrates a smooth speed ramp into continuous arc travel and begins heel preparation before foot release. It carries forward checkpoint 12 hip-load response, support planes, attention and final material-centroid correction. Capability budgets set different durations: Allosaurus 13.154 seconds, Tarbosaurus 15.597 seconds. This is numerical profile behavior, not a biological claim that size determines speed.

Both emitted rigs reopened, the Unity build and native captures completed, and all 691 captured frames were inspected chronologically (316 Allosaurus, 375 Tarbosaurus; 24 fps). Twenty-seven focused tests pass. Fixed-camera videos, every-frame sheets, source/profile snapshots and receipts are in principal game `game/Evidence/walking-curve-study/`. No isolated abrupt joint buckle was identified in the visible frames; far-leg occlusion and the wider framing limit this observation.

Open technical limits: individual planted material vertices move up to 43.4 mm Allosaurus and 34.7 mm Tarbosaurus, despite stable patch centroids. That includes articulation/deformation and does not establish rigid patch contact. Source-key floor samples and reach are acceptable for this diagnostic, but continuous interpolation, whole-body forces, joint loading and live gameplay steering are not certified. Checkpoint 12 remains the accepted turn baseline. **User rejected checkpoint 13: preserve head/foot pointing, restore articulated walking recovery in the combined walking-turn behavior. Checkpoints 14 and 15 are recorded above; do not advance to reverse or lateral recovery before review.**

## Current limitations

- Saved sequence contact residuals: Allosaurus 0.131 mm; Tarbosaurus 0.230 mm at loaded material anchors.
- Brief interpolation floor dips: Allosaurus 0.703 mm; Tarbosaurus 5.646 mm at first toe-off. Production contact acceptance remains open; these do not block visual iteration.
- Body controls are approved engineering responses, not newly converged dynamics solutions.
- Focused Unity landmark and secondary-layer parity were verified in housekeeping. Full material contact, arbitrary terrain and worst-case device performance remain open.

## Completed mini-world and portability checkpoints

The user approved the mini-world, its FPS improvement, attention demonstration and full-transition arm/jaw life. The source walk remains preserved. The game tracker records native Unity captures, import parity, focused secondary-contact checks and measured M4 performance. Canonical embodiment profiles, explicit axes, Python/Unity secondary-motion parity and Blender preview imports were implemented in the housekeeping checkpoint. These are focused validations, not full production contact or terrain acceptance.

Unity remains the approved validation consumer; shipping platform decisions are separate. Directional and impact checkpoints are tracked in the current inventory above.

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

User review: ACCEPTED as a good indie-game turning baseline, with further choreography polish still open. The deliberate reversal settling remains visible. Maximum planted-interval knee displacement along the foot lateral axis is 31.6 mm for Allosaurus and 33.8 mm for Tarbosaurus, close to draft 10's 31.9/32.5 mm. This is a positional diagnostic, not proof of joint loading. Locomotion-path acceleration limits exclude additional local pelvis support accommodation; final mass/contact correction is still open. Evidence and the next work are tracked in the current checkpoint above.


## Normal running transfer — checkpoint 29 D, awaiting review

Checkpoint 28 connected controls are approved for both animals. The next bounded
review adds normal running with the existing airborne-family planner and the
current source rigs. The normal walk and historical Run010/Sprint006 are preserved.
Sprinting and their impact reactions are later checkpoints.

Canonical `locomotion.run` inputs declare moderate authored target speed, one-step
distance and complete same-foot stride. Allosaurus uses 3.8 m/s, 1.70 m per step
and 3.40 m per stride; Tarbosaurus uses 3.4 m/s, 2.02 m and 4.04 m. These are game
animation calibration values, not fossil measurements, maximum speeds or a claim
of which species was biologically faster. The shared resolver derives cadence
from distance/speed, never from species names.

The candidate preserves current toe-chain topology, outward leg/foot orientation,
heel release and distal-pad recovery. Loading, launch and catch share a continuous
body carrier with restrained chest/head/tail response. The Unity adapter accepts
running intent using the same actual-pose/velocity/contact handoff state. The
review sequence is walk → run → walk → retained-support stop. Full force balance,
terrain contact, running steering and collision-triggered hit → escape are open.

Evidence will be recorded in `game/Evidence/running-study/` in principal Eonwild.
Both-animal visual approval is pending.

Checkpoint 29 uses a plain animation stage at the user’s request; ordinary
animation iteration returns embedded videos instead of launching the demo world.
The supplied running/sprinting examples were inspected at all 145 frames each.
The reference-led revision raises running compression/flight excursion and tail
response. Both newly emitted GLBs were reopened; 24 focused checks pass. Two
actual-rig displaced-state adoption checks also pass in Unity. These are diagnostic
checks, not final force/contact certification. Allosaurus has up to 8.86 mm of
requested foot overreach during late flight, with bone lengths preserved.


Checkpoint 29 articulation review (2026-09-15): the early Allosaurus preview
received feedback on deep knee gathering, ankle motion and heel rise. Actual-rig
analysis confirms prolonged recovery at the configured ankle limit on both rigs.
The stronger internal C bounce also creates a late-flight Allosaurus straight-knee
lock. Running is not approved. Next: coordinated hip/knee/foot trajectories and
contact, then both-animal plain-stage videos. See principal Eonwild
`game/Evidence/running-study/JOINT_REVIEW.md`; sprinting remains pending.


Checkpoint 29 D correction: reduced heel roll, shallower support compression and
recovery, and touchdown at 40% of one step ahead of the root preserve the declared
step/stride and cadence. Removed the additional world-metatarsal recovery target.
Both rigs were re-emitted and reopened: zero sampled reach excess, no recovery
keys at the former 90-degree ankle limit, no straight-knee lock. Both 20-second
plain-stage videos were recorded, all 960 frames inspected, and the candidate is
paused for user feedback. Contact-centroid/floor corrections are included; full
material contact and physical force balance remain uncertified. This is running
only; approved walks and historical Run010/Sprint006 were not regenerated.

### Running correction — checkpoint 29 F

D was not accepted: the user identified unfinished foot/ankle recovery and
Tarbosaurus raised-toe support during its walking-derived slowdown. The creative
Allosaurus turning example supplies qualitative short-step/continuous-intent
reference, not biological measurements. F adds a shared short entry and a
retained-support braking catch with left/right entry variants. Running no longer
needs walking-stop choreography to finish. The returning pad/digits open before
landing; the running-owned pitch curve avoids the extra late-swing fold.

Both current rigs were generated and reopened. No sampled reach excess or
reported articulation-envelope violations; no keys at the old 90-degree ankle
limit. Twenty-seven focused checks pass. Unity source import/build and two
actual-state adoption checks pass. Native videos and feedback are the next gate.
The current straight pass does not claim running reversals, hit-to-run, physical
braking forces, terrain or final material-contact certification. Approved walking,
turning and historical Run010/Sprint006 remain unchanged. Principal evidence is
`game/Evidence/running-study/`; stop for review before more choreography.

### Sustained running coordination — checkpoint 30

The user identifies the stumble as the most credible current motion and asks to
rebuild sustained running using its continuous support/response principles.
Running support now owns a smooth prescribed load pulse. Its integral supplies
vertical velocity and body-proxy displacement; each flight interval has zero
support and constant downward acceleration. Bounded horizontal speed yielding,
hip recovery preference, toe/heel release and regional lag follow that cycle.
The canonical impact response times are reused for regional compliance. Profile
speed/stride, admitted geometry and approved walking/impact assets are preserved.

The first internal candidate brought the swing foot forward too early and
straightened Tarbosaurus's knee. Using the shared smooth velocity transport
retains travel into the catch; reopened B maximum knee interior angles are
152.9 degrees Allosaurus and 157.3 Tarbosaurus. These are rig diagnostics.
Thirty-three focused checks pass. Both source GLBs were generated and reopened;
the Unity build succeeds. Both 12-second native-time side/front-quarter videos
are ready; all 576 captured frames were inspected. User visual review is pending.

Recipe: catalog/behaviors/running-review.v2.json. Shared planner:
src/eonwild_motion/planning/running_support.py. This is prescribed reduced
vertical support, not articulated inverse dynamics or reconstructed muscle force.
Mass cancels for the normalized vertical load; it does not introduce an agility
ranking. Entry, braking, running turns, sprinting and impacts remain separate
checkpoints after this cycle is reviewed. Principal evidence:
game/Evidence/running-support-study/. Pause for user feedback.

### Propulsion and tail correction — checkpoint 31

Checkpoint 30 B was not approved. The user found a rigid tail/base, walking-like
steps with added flight, unconvincing lower-leg motion and turnout distortion.
The next candidate is C of checkpoint 31, still awaiting visual review.

The shared running planner now integrates a rounded support impulse, with a
stronger loading/drive contrast. Running owns continuous knee/ankle preferences
through compression, drive, release and recovery. The articulated solve uses a
common admitted heading for the knee plane, hock and foot; it retains the source
ankle hinge branch and discourages inverted running hock attitudes. Two early
internal candidates exposed conflicting joint preferences; they are not offered
for approval. Tail response now reaches the base and propagates with delay along
the semantic chain. Profile speed/stride and hard articulation limits are kept.

Recipe: catalog/behaviors/running-review.v3.json. Both rigs were emitted/reopened;
39 focused tests pass. Candidate C has no sampled reach excess or reported joint-
envelope violation. Native side/front-quarter evidence is in principal Eonwild
game/Evidence/running-propulsion-study/. This remains a reduced prescribed-load
animation model, not a muscle/force simulation. Pause at this visual checkpoint.


## Running rear-fold recovery and damped tail — checkpoint 32, pending review

Checkpoint 31 requires changes after the user confirmed the Tarbo reference
comparison: propulsion/recovery remain weak and the tail rebounds like a spring.
Its previous capture-time manifest is historical; user-review.json records the
feedback. Approved walking, turns, stopping, impacts and connected controls remain
unchanged.

Shared recipe `running-review.v4.json` changes the free-foot spatial arc: gather
behind the hip, sweep forward with continuing clearance, and open for contact.
The metatarsal orientation preference releases with the free-leg fold while hard
rig articulation constraints remain authoritative. The standing-relative body
height and load/release preferences accompany that changed arc. Flight duration,
profile speed and step/stride intent are preserved. Tail curvature uses two
non-resonant lag stages driven by body displacement, with a restrained base and
delayed response distributed down the chain. No species branch is introduced.

Both current rigs are emitted and reopened. Evidence and review state live in
principal Eonwild `game/Evidence/running-recovery-study/`. This is a sustained
running visual checkpoint, not an approved gait or a full-force solution.
Run entry, braking, sprinting, terrain and hit-to-run handoffs remain open.
Pause for user feedback here.

Checkpoint 32 C capture completed: both native-time videos contain 216 frames
(side plus front quarter), with all 432 frames inspected and two leg-detail
sheets. The 47 focused checks and Unity build pass; both final source rigs are
reopened with zero sampled reach excess/reported articulation violation.
Visual approval, full material contact and force certification remain pending.


## Previous checkpoint — 33 A: responsive running trunk and tail, refinement requested

The user selected checkpoint 32 as the improved base, requesting more body/tail
response, lateral motion and life through the chest immediately before the neck.
This accepts the direction for refinement, not production running certification.
Checkpoint 32 source, recipe and media remain preserved.

Shared recipe `running-review.v5.json` retains the complete checkpoint 32 leg
cycle. It distributes loading pitch through the semantic spine/chest chain,
adds support-driven roll/yaw, partial neck/head stabilization, a subtle authored
breathing-like thoracic pitch, and delayed lateral tail curvature. Tail pitch
retains two non-resonant lag stages with greater distributed response. The motion
is authored from support and profile response times, not solved muscle forces or
measured respiratory biomechanics. All body changes precede contact solving.

Both source rigs were generated and reopened. Their emitted leg joint positions
are identical to checkpoint 32 at every source key. No reported reach or admitted
articulation violations occur. Fifty-nine focused checks, the native Unity build,
four captures and complete MP4 decoding pass. All 432 captured frames were
inspected in chronological sheets. Source-key contact diagnostics remain separate
from full material-contact, interpolation and articulated-force acceptance.

Evidence: principal Eonwild `game/Evidence/running-body-response-study/`.
Each native-time video has six seconds side view and three seconds front quarter.
The cut joins separate views; it is not an animation handoff. Pause for feedback
on torso flexibility and tail follow-through. Sustained running remains under
review; reconnecting entry/braking, sprinting and airborne impacts are later work.

## Previous checkpoint — 34 A: proximal tail candidate, changes requested

The user requested movement through the first three/four tail segments and
supplied Rexy's Allosaurus Run Cycle Animation as an artistic target. Shared
recipe `running-review.v6.json` biases lateral rotation toward the tail base and
reduces pitch, retaining C33 torso/neck and C32 legs. Both rigs are generated and
native plain-stage videos are captured. Actual exported tail paths are graphed
for discussion; they are not measured traces from the reference.

Sixty-seven focused checks pass. All 432 captured frames were inspected in 18
chronological sheets. All four captures and full MP4 decoding pass. Both source
assets were reopened with zero sampled reach excess/reported articulation
violation; named non-tail joint positions match C33 at 121 sampled times.
Earlier connected clips/segments and their hashes remain unchanged.

The user reviewed Allosaurus during this checkpoint and requested stronger rear
propulsion, a foot that remains flexed through recovery, and a longer-looking
running stroke. They also see a figure-eight-like tail path in the reference,
with much more motion beginning at the hip and tail base. This candidate is
not approved. Tarbosaurus's new video is supplied for context, not assumed approved.

The configured running stride is already longer: Allosaurus 3.40 m vs walking
2.253 m; Tarbosaurus 4.04 m vs 2.741 m (same-foot strides). However, the analytical
running plan's shorter support interval produces less backward planted-foot sweep
relative to body travel: Allosaurus 1.223 m vs nominal walking 1.397 m; Tarbosaurus
1.454 m vs 1.699 m. These are authored intent/plan comparisons, not measured
reference biomechanics or skin paths. Increasing stride alone is insufficient.

Next coordinated pass: more visible rearward drive within joint limits, a longer
collected foot recovery followed by purposeful opening/catch, fore/aft neck shape
that steadies the head, and pelvis-led proximal tail curvature. Evaluate the
reference's flattened figure-eight quality through coupled timing and phase delay,
without bringing back the vertical spring. Preserve flight and yielding landings.
Keep the central artistic direction authoritative and pause at this checkpoint.

Evidence: principal Eonwild `game/Evidence/proximal-tail-running-study/`.
Full contact/force certification, run entry/braking, sprinting and airborne
impacts remain open. Existing approved movement remains preserved.


## Previous checkpoint — 35 A: propulsive running and pelvis-led tail loops, changes requested

Shared recipe `running-review.v7.json` combines a closer landing placement with
more rearward drive, stronger toe-off, and foot flexion retained through the
moving recovery arc. The planned rearward release reach increases about 46%
(Allosaurus 0.543 to 0.796 m; Tarbosaurus 0.646 to 0.945 m). Authored same-foot
stride and average speed remain unchanged. Flight remains present: about 98 ms
per Allosaurus step and 131 ms per Tarbosaurus step.

Pelvis yaw/roll and proximal tail curvature share the stride phase, with
profile-driven response delay and restrained vertical lobes. Actual exported
fourth-segment trajectories show a flattened figure eight for both animals.
The neck also changes shape fore/aft while partially stabilizing head bearing.
Tarbosaurus's canonical run profile lifts front-body pitch by seven degrees
(from +7 to 0), raising chest and head together. The shared planner consumes
this opt-in profile field; older recipes keep their original posture.

Both rigs were emitted, reopened, imported and captured in the native Unity
player. Seventy-six focused checks and the build pass. All 432 captured frames
were inspected chronologically; both nine-second MP4s decode completely.
No admitted articulation violation is reported. Allosaurus has no sampled reach
excess. Tarbosaurus has a maximum 18.3 mm target shortfall at 12 flight samples;
loaded samples are unaffected. This remains an explicit flight-recovery tuning
item, not a changed joint limit or a production contact pass.

Evidence: principal Eonwild `game/Evidence/propulsive-loop-running-study/`,
including source receipts, recipe, hashes, full-frame sheets and actual tail-path
graph/data. Earlier approved connected clips and segments remain byte-identical.
The videos show six seconds from the side plus a separate three-second front
quarter view. Candidate 35 A has user changes requested; checkpoint 34 retains changes
requested. Full material contact/force certification, run entry/braking,
sprinting and airborne impacts remain open. Pause for user feedback here.


## Previous checkpoint — 36 D: quieter gaze and cleaner leg recovery, changes requested

The user liked C35's direction and requested less head yaw while retaining the
pelvis/tail momentum, plus cleanup of repeated leg reversals. C35 now has changes
requested. Shared recipe `running-review.v8.json` and the opt-in solver refinement
apply identically to both animals; canonical species profiles are unchanged.

The pitch search previously missed a narrow feasible interval between coarse
grid points and selected a distant ankle configuration. Refining each coarse
objective valley under the same hard constraints removes the large Tarbosaurus
ankle switches. Forward swing transport starts earlier, with no initial backward
free-foot loop. Less extreme gathered pad/knee/ankle preferences avoid crowding
the articulation boundary. Running stride, speed, flight, rear release geometry,
Tarbosaurus's raised carriage, and the pelvis/proximal-tail law are preserved.

Measured emitted head-yaw excursion falls from 11.95 to 1.22 degrees in Allosaurus
and 12.96 to 1.63 degrees in Tarbosaurus. The fourth tail point relative to its
base matches C35 exactly at the sampled source keys. Tarbosaurus's largest
adjacent ankle change falls from about 61 to 13 degrees; its former 18.3 mm
flight reach shortfall is gone. Both source receipts report zero reach excess
and zero admitted articulation violation. These are source-key diagnostics,
not a full velocity, material-contact or articulated-force certificate.

Remaining polish is explicit: release/folding still has sharpness. Peak adjacent
knee changes do not uniformly improve (Tarbosaurus right 24.39 to 25.68 degrees;
Allosaurus left 13.71 to 18.47 degrees). Do not describe this as all artifacts
resolved. See the complete bilateral measurements and actual emitted-motion plot.

Eighty-four focused checks pass. The native Unity build and four captures pass;
both nine-second videos decode completely. All 432 frames were inspected in 18
chronological sheets. Earlier connected clips, segments and hashes are unchanged.
Evidence: principal Eonwild `game/Evidence/continuous-running-study/`.
Each video has six seconds side view and three seconds front quarter; the camera
cut is not an animation transition. Candidate D is the saved review result;
internal variants A/B/C/E are not promoted. Pause for feedback at this checkpoint.
Run entry/braking, sprinting, airborne impacts and full production acceptance
remain open.


## Current checkpoint — 37 A: continuous heel departure and flexion reserve, pending review

The user identified Tarbosaurus knee overextension and Allosaurus extending
after the foot had left the ground. Checkpoint 36 has changes requested. Both
animals still use the same shared planner, articulated solver and versioned
running recipe. No species branch, new animal-specific solver or profile change
is introduced.

Shared recipe v9 raises the authored heel-rock amplitude from 18 to 32 degrees
and carries a single curve through toe departure. The heel is still moving when
contact ends, instead of stopping and handing off to a delayed lift. Clearance
develops earlier, with a broader recovery fold; the common solver reserves knee
flexion using the existing extension-preference cost under a generic field.
Contact and admitted hard joint limits retain authority. The requested 150-degree
preference is an authored coordination choice, not a new anatomical hard limit.

Actual emitted source keys show maximum knee angles of 138.96 degrees Allosaurus
and 142.86 degrees Tarbosaurus, versus 151.51 and 175.20 in C36. Maximum adjacent
knee changes are 15.48 and 13.69 degrees, versus 18.47 and 25.68. These are
sample-spacing-dependent diagnostics, not a velocity certificate. Post-release
extension is reduced but not eliminated: maximum extra opening during the first
0.2 step after toe-off is 5.25 degrees Allosaurus and 4.60 Tarbosaurus, versus
8.01 and 17.44. Some ankle/hock sharpness remains; neither animal is auto-approved.

Both final GLBs were reopened: source receipts report zero reach excess and
articulation violation. Head yaw and the fourth tail point relative to base
match C36 at every source key. Stride, speed, contact/flight timing, body response
and Tarbosaurus's raised carriage are preserved. All earlier connected clips
and segments remain unchanged with matching asset hashes.

Ninety-three focused checks, the native Unity build, four captures and complete
decoding of both videos pass. All 432 captured frames were inspected in 18
chronological sheets. Each video is six seconds side plus three seconds front
quarter; the view cut is not a gait transition. Evidence and complete bilateral
measurements: principal Eonwild game/Evidence/grounded-push-running-study/.
Pause for user feedback. Full material-contact/force certification, connected
run entry/braking, sprinting and airborne impacts remain open.

## Evidence-informed sustained run — checkpoint 38 C, pending review

The user approved implementing the scientific calibration approach. Both animals
use the same BIRDS prior evaluator and analytic support integrator, with their
admitted leg lengths, profile mass estimates, speed and stride. Applied aerial
duty is 0.43, transferred from measured ostrich running; the regression's grounded
prediction at these dinosaur inputs is retained as an explicit conflict. This
preserves the requested small flight phase without claiming measured dinosaur gait.

The candidate moves the catch forward, advances weight acceptance, reduces body
bounce, and eases the hock preference before toe-off. Recovery clearance was fitted
to avoid a Tarbo ankle configuration switch. Canonical animal speed/stride and the
approved connected/walking clips are preserved. No species-specific solver exists.

97 focused checks passed. Native Unity plain-stage videos and source-key
comparisons live in game/Evidence/empirical-running-study/ in the principal game.
Sampled reach excess and hard articulation violations are zero. These diagnostics
do not certify skin contact, muscle forces or arbitrary gameplay transitions.
Allo still has up to 6.21° early post-release knee opening (C37: 5.25°); Tarbo 4.02°
(C37: 4.60°). Smaller maximum adjacent knee changes do not establish full smoothness.

Next: user review of the evidence-informed catch/loading rhythm; then targeted
release polish, running entry/braking and the separate sprinting family. Preserve
checkpoint 32 as the user-selected running base until a new candidate is approved.


## Checkpoint 39 — whole-stride leg fit

A single shared periodic fitter now coordinates each leg across an entire stride, using reduced sagittal inverse dynamics and temporal costs. It consumes newly admitted geometry and a fresh source-plan seed, never a previous animated take. Candidate B uses recipe `catalog/behaviors/running-review.v11.json`; both-animal saved videos are in principal Eonwild `game/Evidence/coupled-stride-running-study/`.

This first bounded stage optimizes the leg's remaining articulation degree of freedom with prescribed body motion, foot paths and contact timing. It is not full-body optimal control or muscle simulation. See the appended mathematical scope and assumptions in [running evidence baseline](research/RUNNING_EVIDENCE_BASELINE.md). Anterior trunk yaw is also reduced for quieter neck motion; the hip/tail eight remains.

C38 feedback: Tarbo is substantially improved with neck changes requested; Allo is not fully convincing. C39 B is pending, not automatically approved by objective reduction. Further detail is conditional on this review: paired measured extant trajectories, contact pressure/toe compliance, body/foot trajectory co-optimization, better segment mass and strength priors. Walking may be revisited after running demonstrates the method; preserve approved walking now.
