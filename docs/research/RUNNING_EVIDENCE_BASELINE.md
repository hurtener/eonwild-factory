# Running evidence baseline

Researched 2026-09-20. Status: research baseline and diagnostic extrapolation;
partly adopted in checkpoint 38 C, reviewed with changes requested.
Checkpoint 39 B was reviewed: Tarbo remains good; Allo still looks restrained.
Checkpoint 40 D adds bilateral floating-body dynamics and awaits morning review.
C37 has landing/release changes requested. The user's approval of the analysis/chart
does not approve a new animation. Implementation remains direct, without agents,
and pauses at the next both-animal video checkpoint.

## Source roles

| ID | Primary source and locator | What it supplies | Transfer boundary |
| --- | --- | --- | --- |
| RUN-BIRDS-2018 | [Bishop et al., PLOS ONE, doi:10.1371/journal.pone.0192172](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0192172), Table 3 and S1 Code | Regression-based contact timing, stride and ground-force profiles from 12 bird species, 0.045–80 kg; supplied MATLAB implementation | Predictive prior for theropods, not measured dinosaur gait. COM location and extrapolation beyond the sampled masses matter. |
| RUN-OSTRICH-2007 | [Rubenson et al., JEB, doi:10.1242/jeb.02792](https://journals.biologists.com/jeb/article/210/14/2548/16933/Running-in-ostriches-Struthio-camelus-three), Results and Figs 8–10 | Measured joint curves at 3.29 ± 0.30 m/s: duty factor 0.43 ± 0.04; support 0.30 ± 0.02 s; swing 0.40 ± 0.04 s; same-foot stride 2.32 ± 0.25 m | Speed- and anatomy-specific observations, not dinosaur presets. Ankle motion during stance was small; substantial compliance occurred at the toe-base joint. |
| RUN-TOES-2017 | [Zhang et al., PeerJ, doi:10.7717/peerj.2857](https://peerj.com/articles/2857/), Table 2 and Fig 4 | Separate toe-joint trajectories and uncertainty bands. At 2.77 ± 0.28 m/s: duty factor 0.45 ± 0.03, support 0.34 ± 0.03 s, swing 0.42 ± 0.02 s | Two ostriches; their two-toed foot is not a direct geometry match to a three-toed theropod. |
| RUN-OSTRICH-DATA | [Rankin, Rubenson & Hutchinson, Dryad, doi:10.5061/dryad.fh3h6](https://datadryad.org/dataset/doi:10.5061/dryad.fh3h6), Models and Motion Data.zip | Published musculoskeletal model and motion files, linked to the 2016 optimization study | Listing verified; archive/README retrieval returned HTTP 403 in this pass. Files and coordinate definitions have not been inspected. Muscle forces are inferred, not direct measurements. |
| RUN-EMU-2024 | [van Bijlert et al., doi:10.1126/sciadv.ado0936](https://research-portal.uu.nl/en/publications/muscle-controlled-physics-simulations-of-bird-locomotion-resolve-/), [author project](https://simtk.org/projects/emily_project) | Emu predictive simulation work on posture, muscle function and grounded running; useful for future transitions | Simulation evidence in an extant species; project download was not verified. Do not treat model outputs as measured Allo/Tarbo motion. |
| RUN-TAIL-2021 | [Bishop et al., doi:10.1126/sciadv.abi7348](https://pmc.ncbi.nlm.nih.gov/articles/PMC8457660/), supplementary data and movies | Predictive bipedal dinosaur simulations with a dynamic tail role | Comparative simulation reference; supplementary files not inspected in this pass. It does not supply a measured Allo/Tarbo figure-eight amplitude. |

Reported ± values are study standard deviations, not confidence intervals for dinosaurs.

## Correct the previous interpretation before tuning

The C37 chart's flat trace was **world-space metatarsus orientation**. That is
not the same quantity as anatomical ankle flexion. A flat portion is not, by
itself, proof that an animal should have more ankle motion. The sharp
post-release reversals are still measurable defects, but the proposed solution
must distribute motion between knee, ankle, toe base and toe segments using
mapped definitions. Do not remove an orientation preference merely because
the chart is flat.

A joint's axis orientation, joint flexion angle and world segment heading are
three different quantities. Published externally oriented knee/ankle axes must
not be pasted into hip yaw controls. Establish semantic anatomical axes and
angle zero conventions first.

## Diagnostic BIRDS calculation for our current animals

Inputs use the existing profile mass proxies and the sum of the three admitted
hip-to-toe-base segments, measured in the preserved C37 source rig. The model
estimates hip height from leg length; this is not a measurement of the artistic
mesh's COM or a replacement for its standing admission.

| Input | Allo | Tarbo |
| --- | ---: | ---: |
| Existing mass proxy, kg | 1512 | 2816.3 |
| Rig leg length, m | 1.985 | 2.415 |
| Current run speed, m/s | 3.8 | 3.4 |
| Model-estimated hip height, m | 1.890 | 2.313 |

These are approximate engineering inputs. The profile already flags correspondence
between the published mass models and artist geometry as unverified.

| Result | Allo C37 | Allo extrapolation | Tarbo C37 | Tarbo extrapolation |
| --- | ---: | ---: | ---: | ---: |
| Per-foot duty factor | 0.39 | 0.55 | 0.39 | 0.60 |
| Contact duration, s | 0.349 | 0.421 | 0.463 | 0.553 |
| Same-foot stride, m | 3.40 | 2.95 | 4.04 | 3.13 |
| Peak vertical support / body weight | 2.56 | 1.45 | 2.56 | 1.29 |
| Peak timing, % of support | 50 | 30 | 50 | 29 |

Duty factor is one foot's contact duration divided by its complete same-foot
cycle. For symmetric alternating steps, values above 0.5 imply overlap of
support; values below 0.5 allow flight. The model's approximate crossing speeds
are 5.0 m/s for Allo and 5.5 m/s for Tarbo with these inputs. These are
extrapolated gait-transition estimates, **not maximum speeds or biological
thresholds**.

C37's values describe its prescribed body-support proxy, not independently
solved muscle forces. The comparison plot normalizes support time; durations
and overlap also differ. A lower force curve cannot simply be substituted
while preserving C37's flight and timing.

The independent regressions for stride, duty factor and stance time are not
perfectly algebraically identical. A future resolver must reconcile
speed = stride / cycle time and exact impulse consistency rather than enforce
all fitted central values as hard constraints.

## How to use this in the shared engine

Integration policy (the bounded C38 implementation is recorded below):

1. Curate phase curves and scalar priors with source, measurement definition,
   animal/sample size, speed, uncertainty and evidence class. Keep measured
   extant data separate from derived dinosaur predictions and authored choices.
2. Use body mass, actual leg geometry, crouch and dimensionless speed
   v/sqrt(g*h) to select or derive a compatible gait. Normalize lengths by leg
   or hip height as defined in the source, forces by body weight, and time by
   the characteristic time sqrt(h/g). This does not rank agility from size.
3. Resolve contact duration, cadence, stride, flight/overlap and force impulse
   together. Preserve existing researched stride as intent; expose conflicts
   instead of silently shortening it to match a regression.
4. Coordinate foot approach, toe-base yielding, grounded drive and departure
   against that support trajectory. Fit compatible phase and velocity across
   the joints rather than adding independent smoothing knobs.
5. Keep skeletal reach and admitted ROM authoritative. Fit measured curve
   shapes within each rig's geometry; avoid copying absolute ostrich angles.
6. Generate one shared candidate for both animals, compare the result to the
   selected evidence bands and show native-time videos. Do not turn this into
   an OpenSim/physics-engine migration or an extended validation project.

The user wants an aerial running and sprinting family. Preserve that artistic
intent explicitly. A future pass can choose a coherent aerial speed/regime or
label a deliberately more aerial moderate-speed gait as authored. Research
does not silently revoke approved movement or select a new gait for the user.

## Reproducibility

The research artifact directory is:

`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/outputs/directional-checkpoint/running-research-2026-09-20`

It contains the downloaded S1 code, a small analysis-only transcription,
`comparison.json` and `empirical-support-comparison.png`. S1 source SHA-256:

`97f0a25a159e6f60ca6075c402ac782a6bc2742d5ef8fb4c1faee799a64ea9c0`

The transcription reproduces the paper's 8000 kg, 3.1 m leg, 5 m/s example:
duty 0.543, contact 0.427 s, stride 4.083 m and peak 1.491 body weights at
30.56% support, consistent with its published rounded values. That is a narrow
calculation check, not animation validation. That statement described the research-only pass. C38 now adopts selected priors
as recorded below; canonical animal speed/stride inputs remain unchanged.


## Applied candidate — checkpoint 38 C

The shared engine now evaluates BIRDS priors from the admitted bilateral mean
leg length, sourced profile mass proxy and declared running speed. It records
all predictions alongside the applied gait in each exported receipt. The code
lives in src/eonwild_motion/planning/running_evidence.py; recipe authority is
catalog/behaviors/running-review.v10.json.

The selected aerial duty factor is **0.43**, transferred from RUN-OSTRICH-2007's
measured mean, also within RUN-TOES-2017's reported variation. This is explicitly
an extant-transfer choice. The model's predicted 0.55/0.60 grounded duty remains
visible as a conflict. The result is **not** the unchanged BIRDS-predicted gait.
Dinosaur speed and full-stride intent remain 3.8 m/s / 3.4 m Allo and
3.4 m/s / 4.04 m Tarbo; exact cadence follows those inputs.

BIRDS' speed-conditioned vertical force shape is renormalized to the selected
contact time. Its analytic integral balances weight over every step and produces
a periodic height/velocity trajectory, with gravity-only flight. Both actual
inputs give upward velocity at release and downward velocity at landing.
This is a body-support proxy, not articulated muscle/ground force certification.
Fore-aft body yielding remains authored; no horizontal inverse dynamics were added.

Joint angles, foot placement, recovery clearance and toe roll remain an authored
fit inside admitted rig limits. The landing is farther forward, heel rock peaks
while grounded, and the stance hock preference eases during unloading. Lower
recovery clearance avoids an ankle solution switch found in the first draft.
No absolute ostrich angle, joint-axis orientation or toe anatomy was transplanted.
Tail figure-eight and stabilized gaze retain their authored regional controls.

| Applied quantity | Allo C38 | Tarbo C38 |
| --- | ---: | ---: |
| Per-foot contact fraction | 0.43 | 0.43 |
| Flight per alternating step | 0.063 s | 0.083 s |
| Sampled peak support / body weight | 1.86 | 1.78 |
| Foot base ahead of hip at catch | 0.677 m | 0.792 m |
| Maximum sampled early post-release knee opening | 6.21° | 4.02° |

Remaining limitation: Allo's release opening increased from C37's 5.25° despite
smaller maximum adjacent knee changes. Some ankle corners remain. This candidate
establishes a source-backed calibration path; it does not complete smoothness or
prove dinosaur biomechanics. Checkpoint media and full comparisons are in the
principal game's game/Evidence/empirical-running-study/. Pause for review.


## Whole-stride articulation experiment — checkpoint 39 B

C38 feedback: the user finds Tarbo substantially improved, but its neck too
laterally active; Allo is not fully convincing. C39 is an explicitly bounded
experiment before more detailed modeling. No new gait approval is inferred.

Implemented in `src/eonwild_motion/solve/running_stride_fit.py`, opt-in through
`catalog/behaviors/running-review.v11.json`. This extends the existing engine.
Both actual animals use identical code/recipe, with admitted geometry and profile
mass, stride and speed supplying the differences. The normal per-frame solver
remains unchanged for recipes without the opt-in.

### Mathematical scope

The body path, toe choreography, contact times and foot trajectories remain
prescribed. For each leg, 64 periodic phase samples explore its remaining
metatarsal-pitch redundancy while maintaining hip-to-foot reach. Anatomical hinge
branch and admitted hard joint limits define feasible intervals. A periodic fit
chooses all samples together. It returns a periodic cubic pitch function to the
rotation-only source solver, before final material/floor correction. Emitted
poses and material patches are reopened and measured afterward.

This is a whole-stride **leg articulation fit**, not a whole-body optimal-control
solution. Hip, knee and ankle are geometrically coupled through the one remaining
variable; root, feet and toes are not independent optimization variables yet.

Reduced sagittal joint moments use Newton-Euler inverse dynamics. At each joint
j, sum over distal segments i:

    tau_j = sum((c_i - p_j) cross m_i * (a_i - g) + I_i * alpha_i)
            - (p_contact - p_j) cross F_ground

Segment centers are midpoints; rod inertia is m*length^2/12. The pelvis reaction
is not constrained. Ground force is applied at the toe-base proxy, not a solved
pressure center. Vertical force comes from the existing BIRDS transfer. Fore-aft
force follows the authored body travel acceleration during support. Free legs
have no ground force. Constant forward travel is removed before cyclic
differentiation so the loop boundary does not invent an impulse.

The objective combines a soft reference to the freshly generated source plan,
angular acceleration/jerk, normalized joint moment and rate of joint moment.
Angles are radians; derivatives use physical seconds. Moment is normalized by
body mass * gravity * admitted leg length. Derivative costs are scaled by stride
frequency. This is an effort proxy, not metabolic cost or measured muscle force.

The reference is current admitted geometry + recipe evaluated during this build.
No C38 GLB, historical source animation or prior curve drives generation.

### Explicit engineering assumptions

Per-leg mass fractions for thigh/shank/metatarsus are 0.035/0.018/0.006 of body
mass. These and midpoint/rod inertias are low-confidence engineering estimates;
no dinosaur segment measurements or strength limits are claimed. They are
versioned in the recipe and copied into the receipt with actual kilogram values.
Objective weights are engineering regularization, not biological measurements.
The contact proxy omits toe inertia, changing pressure center, tendon elasticity,
actuator limits and whole-body/lateral angular-momentum balance.

The method is informed by motion-tracking optimal control, described by
[Dembia et al. 2020, OpenSim Moco](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008493).
C39 uses a reduced in-engine fit rather than adopting an OpenSim muscle model.
Reference movement/mechanics remain those cataloged above. No new measured joint
curve dataset has been admitted in this checkpoint.

### Results and boundaries

All four leg fits converged in 11-14 residual evaluations. On the reduced fit
model, angular-acceleration RMS falls approximately 23-35%, and estimated joint
moment RMS approximately 4-6%, relative to its fresh seed. These are model-space
metrics, not a certificate of equal improvement in every emitted joint.

Reopened source-key measurements reduce early post-release knee opening from
6.21 to 5.84 degrees (Allo) and 4.02 to 3.48 (Tarbo). Maximum knee angle is 146.25
and 143.83 degrees. The largest Tarbo adjacent source-key knee change increases
from 10.15 to 10.82 degrees; keys are not uniformly spaced. Allo ankle local
sharpness also remains. Preserve regressions; do not certify universal smoothness.
Both source candidates have zero reported sampled reach excess and hard-ROM
violations after final correction. Skin and Unity full continuous parity remain
separate from these sampled checks.

The neck adjustment is separately authored: anterior trunk yaw falls from 8 to
2 degrees while pelvic yaw and the proximal tail eight are retained. This is
not a dynamically predicted neck solution.

### Conditional continuation

After positive visual feedback, admit paired extant kinematic/force trials with
axis/zero conventions; add pressure-center/toe compliance and allow body/foot
trajectories to co-adapt; improve segment mass, joint capacity and elastic priors.
Validate against an extant trial/speed withheld from fitting, then report dinosaur
extrapolation uncertainty. Only subsequently revisit approved walking and other
movement families. Do not deepen the model before the current videos are reviewed.


## Checkpoint 40 D: free swing tasks and a coupled reduced body

The user's review identifies restricted articulation, especially in Allosaurus.
C39 only optimized metatarsal redundancy against prescribed body/foot paths;
its strong pose reference could retain that restriction. C40 weakens the pose
reference and optimizes three sagittal segment angles per leg, torso pitch and
mean COM placement together over 64 periodic samples. The same algorithm and
recipe serve both animals; admitted geometry, body measurements, semantic ROM,
speed and stride supply their differences. No prior animated clip is a fit input.

For each sample, local segment centers r_i and mass fractions f_i determine the
bilateral hip-center position B = C - sum(f_i r_i). C is the COM path integrated
from the existing support impulse. This makes limb swing produce body recoil
and exactly reconstructs COM **within this reduced model**. The remaining mass
is a torso at the hip center. Three uniform rods per leg have I = m L² / 12;
torso gyration is estimated at 0.55 times leg length. Per-leg mass fractions
[0.035, 0.018, 0.006] and that gyration are engineering priors, not measurements.

The fit minimizes a weighted sum of squared residuals for weak pose tracking,
joint acceleration/jerk, inverse-dynamic torque and torque rate, actuator power,
foot tasks, material clearance, ROM margins, body displacement and angular
momentum balance. H includes limb orbital momentum, rod spin, torso orbital
momentum and torso pitch inertia. dH/dt is compared with ground-force moment
about reduced COM. Contact and angular balance are finite-weight objectives;
their residuals are reported. These are not equality-constrained certified
forward dynamics. Absolute mass scales Nm demand but cancels from normalized
shape costs when geometry/timing are held equal: heavier alone does not produce
slower motion here. Strength scaling and muscle capacity remain future work.

Grounded toe-base tasks stay strongly constrained; swing tasks can move. A
first fresh full-rig solve measures the toe material envelope so the optimizer
does not lower a curled foot into the floor and leave final contact correction
to force the ankle out of range. Full-rig IK and material correction still follow
the planar fit; final emitted motion is checked separately. Source-key reach and
hard ROM violations are zero for both selected candidates. Intermediate A/B
failed to protect Tarbo's material envelope and were not selected.

### Scientific basis and limits

[Dembia et al. 2020, OpenSim Moco](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1008493)
provides the useful distinction between tracking motion and predicting it through
musculoskeletal optimal control. This implementation uses SciPy nonlinear least
squares and a reduced model, not Moco, muscles, tendons or a reproduced published
animal simulation. [Rubenson et al. 2007](https://journals.biologists.com/jeb/article/210/14/2548/16933/Running-in-ostriches-Struthio-camelus-three)
supports retaining explicit joint coordinate conventions: 3D axes cannot be
replaced by unqualified planar angles or transplanted into these rigs.

Support timing/force shape, toe choreography and tail/neck artistic motion remain
prescribed. Torso COM at the hip is a major approximation for these animals;
there is no distributed torso/tail inertia or moving pressure center. The reduced
fit is not a whole-rig force certificate or proof of biological dinosaur running.

### What changed in the emitted motion

Estimated model torque RMS falls from 4279.9 to 3281.4 Nm for Allo and 8478.3 to
6997.9 Nm for Tarbo relative to the fresh unfit seed. Normalized angular-momentum
residual RMS is 0.00700 / 0.00320 bodyweight × leg length. Maximum fitted support
position residual is 0.205 / 0.208 mm. These are model measurements, not muscle
forces or final-rig metrics.

Allo's source-key knee minimum decreases from 78.69 to 72.72 degrees, giving more
gathering. Early post-release knee reopening falls from 5.84 to 2.50 degrees;
Tarbo from 3.48 to 0 degrees in the sampled first 0.2-step window. Tarbo's maximum
knee extension increases from 143.83 to 153.31 degrees and needs fresh review.
Adjacent source-key increments increase; irregular sample spacing means this is
not angular speed and does not certify smoothness either way.

C40 C and D use identical solved key poses. D changes emission from LINEAR to
CUBICSPLINE, with sign-aligned quaternion keys and projected quaternion tangents.
The same reduced COM proxy measured from final GLBs on a 128-sample periodic grid
has vertical force residual RMS/BW of:

| Animal | C39 linear | C40 C linear | C40 D cubic |
| --- | ---: | ---: | ---: |
| Allo | 0.629 | 0.698 | 0.093 |
| Tarbo | 0.425 | 0.474 | 0.091 |

This ablation attributes most of that improvement to serialization continuity,
not solely to the deeper fit. Finite-difference residuals depend on sampling and
our assumed mass model. Cubic interpolation does not preserve every constraint
between keys: reopened loaded floor gaps at keys/midpoints range from -1.021 to
+0.637 mm (Allo), -0.530 to +0.432 mm (Tarbo). No continuous-contact certificate.

Native Unity video evidence, every-frame sheets, scripts, source hashes and the
remaining consumer checks are in principal Eonwild
`game/Evidence/floating-body-running-study/`. Unity landmark comparison currently
fails the unchanged 2 mm criterion (Allo 6.76 mm, Tarbo 6.51 mm). Do not transfer
source measurements into a claim of verified Unity parity. One complete Tarbo
capture exited 255 in Metal/CVDisplayLink after saving its frames; the failure is
preserved. Videos are diagnostic candidates pending the user's morning review.

Next, conditional on the visual direction: resolve cubic consumer parity;
introduce better distributed mass/COM and contact pressure/toe compliance;
calibrate strength/capacity and paired extant kinematics/forces. Keep running
entry/braking, sprinting and eventual walking migration separate checkpoints.
