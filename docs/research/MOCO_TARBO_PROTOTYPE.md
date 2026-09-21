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
