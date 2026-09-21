# C42 companion — offline Moco mechanics prototype

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
