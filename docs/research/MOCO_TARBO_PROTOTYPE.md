# C42 companion — offline Moco mechanics prototype

Latest continuation: [C50 D connected-tail repair](../handoffs/MOCO_C50_TAIL_REPAIR.md),
pending visual review. The following sections retain historical context.

This is the implementation record following the
[OpenSim feasibility audit](OPENSIM_DINOSAUR_FEASIBILITY.md).
The alternate model is an independently written **planar torque-driven
prototype**, not a converted T. rex muscle model or a production game animation.
Review evidence is in principal Eonwild `game/Evidence/moco-tarbo-prototype/`.
Candidate status, convergence, replay errors and file hashes belong to that
evidence package; a solver success is not visual or biological approval.

## Shared architecture

`tools/admit_moco_prototype.py` reads the normal admitted source and semantic
bindings before motion is generated. It verifies profile/source identity and
units, exports joint centers in meters relative to the bilateral hip midpoint,
and retains body-mass and movement-task provenance. It does not read an earlier
animation. This uses the existing diagnostic compiler admission seam; a dedicated
public admission API remains future housekeeping.

`src/eonwild_motion/solve/moco_prototype.py` builds the same mechanical topology
for compatible semantic bipeds. `catalog/behaviors/moco-stride-prototype.v1.json`
contains experimental mass fractions, strength, contact and optimization priors.
Tarbo supplies its anatomy and body mass, not a separate solver branch. Transfer
of this prototype to another actual species has not been demonstrated.

The current model has 12 moving bodies, 14 generalized coordinates and 11 internal
joint actuators. The trunk has free forward/vertical translation and pitch.
Each leg has hip, knee, ankle and MTP articulation; neck/head and two tail regions
move independently. Joint torques have bounded excitation and a 35 ms first-order
activation response. **There is no root actuator or reserve.** Gravity and four
compliant foot contacts supply external forces.
This statement applies within the modeled sagittal plane. The planar joint
constrains lateral translation, roll and yaw; their constraint reactions are
not a solution of three-dimensional balance.

The study optimizes a half-stride with left/right periodic symmetry, a 2.02 m
root advance in 0.5941176 s (3.4 m/s), joint/state limits and actual toe/tail
clearance. It minimizes normalized actuator effort and vertical contact-force
squared cost. Contact forces arise from sphere/half-space deformation and
velocity; neither their time history nor a flight fraction is prescribed.
The initial guess uses an analytic foot path solely to initialize optimization.
No knee timetable or existing gait is tracked in the objective.

## What is sourced, what is estimated

| Quantity | Current source / interpretation |
|---|---|
| Total mass | 2816.3 kg, the existing PIN 552-1 profile's published volumetric estimate; original citation retained |
| Leg lengths and axial attachment points | Fresh admitted artist-rig geometry; not fossil measurements |
| Target speed and step length | Existing profile's authored moderate-run task; not maximum speed or inferred fossil gait |
| Segment mass split | Explicit engineering prior: trunk 50%, neck/head 9%, tail 21.8%, two limbs totaling 19.2% |
| Inertias and COMs | Cylinder/rod approximations and documented center fractions, scaled from admitted geometry; not measured tissues |
| Strength and activation time | Engineering torque capacities normalized by body weight × leg length; no identified muscle architecture |
| Foot contact | Two compliant spheres on each simplified articulated toe segment; estimated radius, modulus, damping and friction |
| Joint bounds | Broad engineering bounds for this planar model, not a complete anatomical ROM calibration |
| Clearance | Toe articulations, toe tips and both tail regions must remain above ground; contact spheres alone leave geometric loopholes |

The official [OpenSim 2D walking model](https://github.com/opensim-org/opensim-core/blob/4.6/OpenSim/Examples/Moco/example2DWalking/2D_gait.osim)
was inspected for contact implementation: it uses the same smooth force family,
a 62 kg model, 3.067776 MPa modulus and 0.035 m sphere radius. Those example values
are not dinosaur tissue measurements and are not copied as a calibrated Tarbo
contact. Our current contact settings remain explicit estimates. The example's
human tracking/prediction run has not been reproduced at this checkpoint.

## Runtime and verification

Native arm64 Python 3.12.10, OpenSim 4.6 and NumPy 2.5.3 run on this Mac.
Installing the missing GNU Fortran runtime resolved IPOPT loading. The official
sliding-mass problem then solved at 0.4000269 s, versus its analytical 0.4 s
solution. Environment, example solution and hashes accompany the prototype.

Five actual OpenSim witnesses check total mass/internal-only actuation,
geometry/inertia scaling, free fall under gravity, upward floor reaction and
stationary seed support while the root advances. These tests check implementation
mechanics, not dinosaur realism. Final state replay measures support, penetration,
loaded surface speed, knee opening and the dense force-balance discrepancy.

The first coarse converged solution exposed sharp between-node force impulses
and a tail penetrating the floor. Later visual inspection exposed another
loophole: toe contact spheres could bear load while the MTP bone sank below the
floor. Explicit bone clearance addresses that physical-envelope error. Refining
the numerical mesh remains necessary; a coarse successful IPOPT status alone
does not establish a dynamically faithful continuous motion.

## Reproduction and outputs

Use a separate Python 3.12 environment with `opensim==4.6` and `numpy==2.5.3`.
Rendering additionally needs Matplotlib and ffmpeg; it can use the existing
factory scientific environment. On this Mac OpenSim's wheel also needs Homebrew
GCC's `libgfortran.5.dylib`. Moco remains an optional offline dependency; normal
factory and Unity imports do not require it.

1. Run `tools/admit_moco_prototype.py` in the factory checkout with the Tarbo v15
   motion set and the preserved Running41 profile. Save its JSON in task storage.
2. Run `tools/build_moco_prototype.py --admission ADMISSION --output NEW_DIRECTORY`.
   Keep each numerical candidate in a new directory. `--mesh` controls time
   discretization; `--warm-start` may use a recorded prior Moco solution.
3. Run `tools/replay_moco_prototype.py DIRECTORY` using the Moco interpreter.
   It loads the exact saved `.osim`, states and controls. Native OpenSim body
   transforms supply the renderer, not interpreted Euler angles.
4. Run `tools/render_moco_prototype.py DIRECTORY`. The saved 24 fps movie repeats
   the half-stride with leg symmetry, follows root travel, and displays computed
   ground-force arrows. Dense Moco interpolation is state replay, not forward
   integration or a Unity retarget.

The evidence package retains `.osim`, `.omoco`, `.sto`, admission, recipe,
environment, logs, receipts, mechanical video and plots. Reproducing another
optimizer run can reach another local solution; exact saved-state replay is the
reproducible visual reference.

## Remaining work before promoting the alternate path

Review the mechanics first. Then calibrate foot geometry/padding, segment masses,
COMs and strength with uncertainty ranges; compare initial guesses and mesh
refinement, and forward-integrate the saved controls. Planar movement cannot
establish lateral balance or our desired figure-eight tail. Muscles, tendons,
caudofemoral coupling and bone stress need additional data and modeling.

Production promotion still requires semantic retargeting, reopened skin contact
and Unity parity after physical calibration. A periodic stride is not an
arbitrary-transition gameplay controller. C42's shared-engine animations and
all previously accepted walks remain separate preserved evidence.

## Requested skinned diagnostic — candidate I

The user subsequently requested the actual Tarbo rendered through this prototype.
`tools/retarget_moco_prototype.py` now maps the saved candidate I body directions
to a freshly admitted rig with the same source/profile hashes. It preserves
artist limb lengths, maps one Moco neck and two tail regions while retaining
their rest curvature, and repeats the half-stride with bilateral symmetry.
There are no species branches, new optimization, running-solver overlays,
time warps, IK/contact correction or hidden root support. Extra artist toe
joints retain their rest shape inside Moco's single toe region; this is a
diagnostic simplification, not articulated toe contact certification.

Principal game `game/Evidence/moco-tarbo-skin/` contains the 9-second native-time
side/quarter movie, all 216 frames in chronological sheets, source receipts,
reproduction scripts and Unity parity. Leg-center error against saved Moco is
below 0.001 mm; 492 Unity landmark comparisons pass the unchanged 2 mm gate
(maximum 0.00131 mm). These checks certify this kinematic mapping, not the physics.

Skin contact **FAILS**: maximum measured foot-region penetration is 144.4 mm.
The simplified sphere padding and the artist foot/sole geometry do not coincide;
the original Moco floor and body trajectory are deliberately retained in this
diagnostic. Low shuffling recovery, low tail, quiet trunk and neutral open jaw
are visible. No breathing or attention overlays are applied. The mechanical
solution's force/scuffing limitations remain unchanged. Before another physical
solve, calibrate the actual sole/toe geometry in the model rather than hiding
this discrepancy with a visual root lift. User review is pending; pause here.


## C43: calibrated contact and coordinated recovery

The first skinned prototype was rejected as too raw to justify replacing the
established animation. This pass changes the physical problem before another
render. The same generic builder consumes semantic anatomy; it contains no
Tarbo-only joint choreography or per-species solver branch.

- Fresh admission now measures the artist sole envelope and intermediate toe
  joint. Five compliant contact spheres per foot replace two coarse pads. The
  model gains a distal toe articulation so the heel can peel while the front
  pads remain in contact. Sphere compliance remains an engineering estimate.
- The body has a separate chest segment and internal spring/damper torques at
  chest, neck and both tail regions. Total mass is conserved. Springs cannot
  support the free root: the whole model still accelerates downward at gravity
  when airborne without contact. These are mechanical approximations, not
  identified ligaments or reconstructed muscles.
- Soft world-space tasks coordinate toe support, heel release, recovery
  clearance and a forward catch. Heel angular velocity continues through
  release. The knee has bounds and dynamics but no tracked angle timetable.
  Broad posture is a soft target, including actual sole depth in hip height.
- Distal-body angular acceleration receives a small explicit regularization
  cost to discourage sharp ankle/toe motion. Activation dynamics and bounded
  internal actuators remain. There is no root force, root lift or runtime IK.
- Semantic retargeting now carries chest and distal toe motion into the real
  rig. Its admitted static jaw-neutral calibration is applied; breathing,
  attention and lateral motion are not invented on top of the physical result.

This is **guided dynamic optimization**, not unconstrained gait prediction or
measured dinosaur motion. The 0.43 duty target is a labeled extant-bird transfer;
it is soft and does not enforce an airborne percentage. Recovery clearance,
forward catch, posture, stiffness and actuator capacity remain explicit priors.
Optimization may depart from the task to satisfy its discretized dynamics.

The optional recipe is `catalog/behaviors/moco-stride-prototype.v2.json`.
Contact/task construction lives in `src/eonwild_motion/solve/moco_tasks.py`.
Use `--recipe` with a fresh calibrated admission; older admissions without sole
geometry fail explicitly. Keep every saved solve immutable. A warm start must
be a saved solution with valid monotonically increasing timestamps, not Moco's
intermediate debug export. Reference tables accompany the saved study.

The principal game evidence location is
`game/Evidence/moco-calibrated-stride-study/`. It will hold the selected solve,
plain-stage native-time side/quarter video, C39 comparison in the same renderer,
reopened skin measurements and Unity import parity. Review status remains
PENDING; the exact numerical/visual outcome is recorded with that evidence.

Remaining scope is unchanged: mesh sensitivity, forward integration, calibrated
inertia and strength, muscles/tendons, three-dimensional balance and arbitrary
transitions are not established by this periodic planar experiment. In
particular it cannot generate the desired lateral figure-eight tail. Preserve
C39, C42 and the original Moco I package for direct comparison.


C43 result: candidate P is saved for review, not converged (158 iterations,
agent-requested diagnostic stop). The 60-interval O diagnostic was also stopped;
mesh convergence is not established. All 216 native P frames were inspected.
Recovery and posture improve visibly over Moco I, but support still briefly
unloads/reloads and the torso lacks C39 lateral life. Skin penetration falls
from 144.4 to 34.8 mm and remains a contact failure. Seven focused physics
checks and 902 Unity landmark comparisons pass. Independent forward replay
of controls drifts up to 0.280 m in root height over the half-stride, so the
improved saved-state video is not physically validated. C39 remains the preferred
baseline. The roadmap and evidence retain these separate outcomes. Pause here
for user feedback; no further unseen polishing or automatic promotion.

When deserializing an OpenSim 4.6 study, register the constraint type first with
`opensim.OpenSimObject.registerType(opensim.MocoOutputConstraint())`. Otherwise
this build of OpenSim logs unrecognized output constraints and silently omits
them. The portable candidate study was checked after registration: all six
clearance constraints and 48 states survive; relative task references load.
Do not run a deserialized study that has dropped its path constraints.


## Checkpoint 44 — contact comparison ready; 3D coordination unfinished

The user requested contact/force consistency plus physical 3D body coordination,
then a native-time visual checkpoint. This is a **partial checkpoint**:
contact candidate D is available for review; no usable 3D solution was obtained.
Allosaurus transfer and muscles/tendons have not begun. Work was done directly,
without subagents. C43 and the approved animation library remain preserved.

The shared optional Moco builder adds a soft single-lobe support-force prior,
reduced foot-path tracking, internal limb damping and linear control interpolation.
These are declared engineering priors, not measured dinosaur forces or external
forces applied to the animal. The knee is not following a tracked angle schedule.

| Evidence | C43 P | C44 D contact |
|---|---:|---:|
| Independent pelvis-height drift over 0.594 s | 279.74 mm | 10.72 mm |
| Dense planar force-balance RMS | 1.722% body weight | 0.609% body weight |
| p95 loaded contact-surface speed | 0.157 m/s | 0.115 m/s |
| Maximum skin penetration | 34.8 mm | 23.87 mm |
| Optimizer convergence | No | No |

Body replay is substantially closer, but the left toe-base joint still diverges
by 5.58 rad in independent integration. Skin contact still fails the unchanged
0.5 mm threshold. D has 176 iterations and an agent-requested diagnostic stop.
Its video replays the saved state trajectory; it is not a recording of successful
independent forward simulation. Neither numerical improvement nor accurate Unity
import establishes physical or biological validation.

All 216 new D frames and 144 rejected 3D G frames were inspected chronologically.
D has clearer stance compression/extension but more body rise than C43; a force
shoulder and abrupt unloading remain. It is still planar. The 3D G diagnostic
has floating feet, a crouched posture and a dipping head; its forces do not
support its saved motion, so it is rejected before user candidate selection.
Later K/L attempts also failed to produce usable motion. G is not a render of L.

The unfinished spatial model has a free six-coordinate root, hip pitch/yaw/roll,
chest coupling, two neck regions, an independent head and four tail regions.
There are no root actuators. Mass fractions, inertia, stiffness, damping and
motor capacity are estimates. Later experiments add divided stiffness for
transverse pads, axial torque reserve from static demand, equivalent optimizer
mass units and a temporary sagittal continuation goal. They did not establish
3D feasibility. Nine actual-rig poses verify unit-equivalent acceleration within
3.28e-11; that is a units check, not a motion pass.

Primary evidence: principal Eonwild
`game/Evidence/moco-spatial-study/README.md`. The selected planar model, native
side/quarter videos, C43 comparison, rejected G diagnostic and unfinished L model
are preserved separately with source recipes, solutions and receipts.
Eleven focused checks pass; 726 Unity landmarks per rendered model pass.
Production contact and 3D coordination remain unfinished. Pause for user review;
do not promote D, advance to Allosaurus or start muscle/tendon work unseen.


## Checkpoint 45 — focused pursuit and spatial tail, pending review

The new Tarbo candidate J keeps the nose steady while the chest and two neck
regions compensate for running. Four tail regions now bend laterally with the
pelvis. Jaw breathing is a separate, explicitly authored 0.8–3.8 degree cycle.
The actual emitted rig has 24.41 mm vertical nose travel per stride, versus
289.19 mm in C44 D, while pelvis travel remains 259.23 mm. Tail-tip lateral
travel is 1.914 m. These are animation measurements, not biological findings.

J is a **spatial inverse-dynamics initializer**, not a converged Moco solution.
It optimizes smooth periodic corrections using the existing OpenSim contacts,
gravity, passive forces and internal motor estimates. The six-coordinate root
has no actuators. There is no head/tail overlay after the physics trajectory;
only the jaw cycle is added in retargeting. The shared semantic builder remains
animal-independent; Allosaurus transfer is still unattempted.

All 216 native-time side/quarter frames were inspected. Fourteen focused tests,
source bone lengths, loop closure and 558 Unity landmark comparisons pass.
Skin contact still fails: 30.09 mm maximum penetration, versus 23.87 mm in C44.
Independent forward replay loses 357.87 mm of pelvis height over 0.594 s and
shows major joint divergence. A small control-bound excess and a 0.685 mm
violation of the tail's existing safety margin also remain. The tail is above
the actual floor. Do not describe the saved-state video as validated dynamics.

Evidence: principal Eonwild `game/Evidence/moco-focused-coordination-study/`.
It includes native videos, a C44 comparison, a nose/tail path chart, exact model,
initializer coefficients, source recipes, trial records and failing checks.
The separate Moco refinement is recorded as an unselected experiment; it is not
the source of the J video. Preserve C39/C42/C43/C44 and the approved library.
Pause here for user review. Next work is contact/control/forward consistency
for the spatial result, then Allosaurus transfer and muscles/tendons after review.


## C46 — engaged body support and the admitted tail chain

C45's nose-only improvement did not pass whole-body review: the user rejected
the excessive vertical body reaction and compliant chest/neck. C46 uses the
same shared model builder, driven by the new optional
`catalog/behaviors/moco-supported-stride.v1.json` recipe. The old catalog recipes
remain unchanged. There are no species-name branches.

The actual Tarbo source contains nine tail nodes/eight links, not twelve. Every
admitted link now has a physical body, pitch/yaw coordinates and internal
torques. Total tail mass remains 21.8% of the admitted body mass; a smooth
volume-based taper redistributes it over the links. Angular stiffness uses
EI/link length, avoiding a direct doubling of bending stiffness just because
the chain has more links. The transverse soft-tissue taper is an engineering
prior, not a measured tissue section or a validated continuum reconstruction.
This yields 23 moving bodies, 45 coordinates and 39 internal motors, with the
same six free root coordinates and no root actuator.

Loaded-pose inverse statics establish gravity support at the desired carriage.
Chest/neck stiffness is derived from the model's reflected inertia and estimated
response frequencies. Damping uses estimated damping ratios. Tail preload
supplies 90% of the reference holding torque; remaining static and dynamic
work comes from bounded motors. This is **constant effective tonic engagement**:
it is not a muscle recruitment model, nor phase-dependent co-contraction.
The neck remains more compliant than the trunk so it can compensate without
turning the whole torso into a compliant hinge. Joint limits also have physical
smooth stops, preventing the unrestricted distal-joint revolutions observed
in earlier independent replays. OpenSim uses degree-based angular damping
units for these forces; an actual torque witness checks the conversion.

The periodic initializer adds a soft body envelope, carried-tail endpoint
envelope, adjacent-link curvature regularization and normalized positive
motor-power/vertical-COM-speed penalties. These task choices guide an estimate;
none is evidence of the animal's real motion. Every altered posture is passed
through actual contact and inverse dynamics. No corrective root lift or
render-only head/tail oscillator is applied. A short numerical IK step preserves
world foot poses only while constructing the starting guess; optimization then
frees all coordinates.

The physical rationale comes from the previously reviewed
[Coelophysis simulations](https://pmc.ncbi.nlm.nih.gov/articles/PMC8457660/)
and [tyrannosaur tail study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8059583/).
They support investigating axial rigidity and loaded tail support; they do not
provide the Tarbo running stiffness, strength or damping values used here.
The [OpenSim limit-force API](https://opensim-org.github.io/opensim-moco-site/docs/1.3.0/html_user/classOpenSim_1_1CoordinateLimitForce.html)
defines the force units. Exact priors, neutral angles and generated mechanics
are archived with the checkpoint.

C46 D is the body-motion diagnostic. It reduces modeled chest pitch range from
8.72 to 0.57 degrees and torso pitch from 11.20 to 6.31 degrees. The emitted
pelvis range decreases from 25.92 to 13.44 cm. Tail-tip minimum model height
rises from 0.531 to 1.515 m, with 2.249 m emitted lateral range. Nose vertical
range increases from 2.44 to 4.77 cm; this tradeoff is recorded, not hidden by
the quieter torso. The model COM and rig pelvis are different landmarks.

D is still an initializer, not a converged Moco solution. Maximum normalized
control is 1.135, loaded-surface p95 speed 0.489 m/s and skin penetration 47.75 mm.
Independent replay completes the half-stride but loses 245.29 mm of root height
and more than a radian at a hip. Those results fail physical acceptance, despite
better body shape and intact joint ranges. The Moco E continuation evaluates
whether the same supported model can close the dynamics discrepancy; its final
status belongs in the evidence package.

Eighteen focused OpenSim tests pass. New witnesses cover a different admitted
tail count, conserved mass/free COM fall despite internal support, calibrated
loaded torque, rotational stop damping and optimizer mass-unit invariance.
These checks establish implementation behavior, not biological truth or a
second-species production transfer. Native review and current candidate status:
principal Eonwild `game/Evidence/moco-supported-body-study/`.

### C46 F — middle-neck correction, pending review

The user identified excessive bounce at the middle of the neck in D. Its nose
was relatively quiet, but the emitted middle-neck landmark moved 27.51 cm.
F adds shared, leg-length-normalized world-height task envelopes for the neck
base and middle, together with modestly increased upper-neck effective
stiffness/damping. The solver chooses the coordinated joint angles; there is no
render-only neck clamp or species branch. Corresponding Moco output-tracking
goals are wired and their study builds, but a full F Moco refinement is NOT_RUN.
The archived generation recipe and the continuation recipe distinguish those
settings explicitly.

F starts from E's returned physical trajectory and reoptimizes all coordinates.
Emitted middle-neck travel is 7.58 cm (72.4% less than D); neck-base travel is
16.93 cm versus 25.91 cm. Skull-nose vertical travel is 5.44 cm versus 4.77 cm,
and lateral travel is 3.04 cm. Whole-body pitch range is 3.30 degrees and
relative chest pitch 0.94 degrees. The pelvis tradeoff is explicit: emitted
vertical range grows from D's 13.44 to 18.86 cm, still below C45's 25.92 cm.
Actual model COM vertical range is 11.97 cm. Raised tail carriage remains:
minimum model tip height 1.510 m and emitted lateral range 2.813 m.

F remains diagnostic. Maximum command is 1.0585, loaded-surface p95 speed
0.274 m/s, skin penetration 43.27 mm and independent half-stride root-height
divergence -235.65 mm. Eighteen focused OpenSim tests pass; actual source
lengths, loop closure and 558 Unity landmarks pass (max error 0.00173 mm).
All 216 captured native-time frames were inspected in chronological sheets;
the neck comparison and full videos are saved without retiming. These checks
do not confer physical or user approval. Pause for visual feedback.

The separate E continuation used the same supported-body mechanics as D and
40 collocation intervals. It was bounded by the assistant after approximately
15 minutes; the returned status is User_Requested_Stop at iteration 45, not
convergence. An earlier iteration had small primal residual, but the returned
iteration's primal infeasibility was 0.0362. Independent root-height divergence
remained -218.50 mm over the half-stride. It is preserved as an unselected
experiment, not a validated improvement or the source of the displayed F video.
OpenSim 4.6 variable-scaled intermediate callback files were rejected because
their times were degenerate and states still scaled; only the returned,
unscaled MocoSolution was used. See the experiment receipt.

### C47 C — material contact and ankle audit

The shared optional builder now adds measured lower-envelope foot samples as
clearance witnesses on the two reduced toe segments. Moco constrains their
world height; the initializer penalizes violations. Existing physical contact
pads remain the only source of ground reaction. Their effective stiffness is
five times C46's as an explicit engineering contact experiment. It is not a
measured tissue property. Actual skinned digits retain a separate floor check.

C47 C reduces maximum emitted skin penetration from 43.27 to 6.91 mm. Neck-middle
travel is 7.20 cm, neck-base 15.29 cm and nose vertical travel 3.76 cm. Lateral
nose travel rises from 3.04 to 4.35 cm; emitted pelvis travel is 18.23 cm versus
18.86 cm. These measured tradeoffs accompany the native-time C46 comparison.

The ankle's estimated 8.59–128.92° flexion bound was not enlarged. C spans
8.43–122.70°, with 0.16° soft-bound overrun; the distal toe overruns by 0.08°.
The toe-base motor reaches 0.981 of estimated capacity while the ankle reaches
0.593. Their full traces and loading are preserved; ankle speed increased from
525 to 572°/s, so contact improvement is not proof of resolved ankle sharpness.
The [research review](LOCOMOTION_CONFIGURATION_REVIEW.md) explains why published
walking angles and another species' reconstructed mobility are not universal ROM.

C is an initializer, not a converged physical solution. Maximum motor command
remains 1.110, loaded-pad p95 slip 0.272 m/s and independent half-stride root-height
divergence −272.65 mm. Final contact still fails the unchanged 0.5 mm threshold.
Nineteen focused tests, actual-rig lengths/closure and 558 Unity landmarks pass;
maximum Unity landmark error is 0.00242 mm. The model and solution reproduce
byte-for-byte. All 216 saved native-time frames were inspected chronologically.

Separate B/D full Moco refinements have archived outcomes in principal Eonwild
`game/Evidence/moco-contact-support-study/experiments.json`. They are not the
source of the C video and cannot be cited as its physical acceptance. The
selected visual candidate is under `candidate-c/`; user review is pending.
The user-supplied workbook/JSON and four papers are referenced centrally with
input hashes. Their five new-animal proposals remain uncalibrated and disabled.
