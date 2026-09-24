# C55 A — cautious backward retreat

2026-09-23. **Candidate pending user review.** Work performed directly, without
subagents. C54 B received favorable feedback ("way better") and the user chose
to proceed to backward walking. C51 A running, C52 B H walking and C53 A turning
remain the explicitly approved references. This does not certify physical
convergence for any visually approved take.

## Motion and scope

Sixteen native seconds: grounded rest, preparation, four alternating rearward
placements, then settled rest. Right/left/right/left land at 4.0, 5.8, 7.6 and
9.4 seconds. The last placement closes the stance instead of retracting a
half-finished swing. Total backward travel is 1.316 m. Head remains forward,
facing the thing the animal retreats from. Twelve admitted tail links receive
a small delayed lateral response to body transfer.

The task starts from the actual first grounded state of C52 B H. Initial
coordinate error is zero. Only this stopped-state adoption is implemented;
joining retreat from an arbitrary moving or turning state is NOT_RUN.
This first task admits exactly four placements and the admitted forward axis.
Allo, curved retreat, faster retreat, nonzero starting velocities and generalized
heading are NOT_RUN. No new species-specific solver was added.

The 0.32 normal-step ratio comes from reverse-walking-review.v2.json and remains
an authored prior. A 1.0 s swing / 1.8 s placement interval is a deliberately
cautious trial, not a measured dinosaur reverse gait. Low clearance and toe-up
release about a rear sole witness are explicit hypotheses, not universal anatomy.
The forward walking clip is not reversed and its push-off is not reused.

## Model and shared implementation

RetreatPlan owns backward placements, release and overlapping support intention.
A constant-height inverted-pendulum prior solves c - h/g * c'' = support in the
horizontal plane. Bounded whole-leg IK reconciles the actual articulated COM
and feet; inverse dynamics then audits the resulting motion. This is **not a
new converged Moco solve, a forward-stable controller, or optimized muscle gait**.

The first diagnostic exposed about 83 mm of visible sole penetration during
lateral loading. Its symmetric pads covered only part of the admitted toe spread.
The optional surface_edge_pads geometry policy now samples both transverse edges
of each admitted foot. Aggregate nominal stiffness shares stay at 5 per foot;
material friction, damping, masses, strength and joint limits stay unchanged.
Actual force response changes with this more complete layout. Previous recipes
leave the policy disabled and retain their prior contact sites.

The reduced leg has sagittal ankle/MTP hinges; sole roll is a soft preference,
not an additional lateral ankle joint. Vertical IK targets the smooth minimum
of the actual pads, followed by bounded contact compression (unchanged +/-25 mm
bracket). No render-only floor offset or limb translation hides contact errors.
Existing midline pad centers still provide the reduced support-location prior;
this is not a measured center-of-pressure controller. Lateral transfer/foot roll
and residual sliding remain especially relevant for visual and physical review.

Numerical source: d9f95f9 (including d339a3f and 2621878).
Model SHA256: 2d233dc6eea15a87a24f7246afe6557d278330003ca9cc4054394d744d77cfa8.
Emitted GLB SHA256: bbd0cf33e5d4c4da9a8c3fa640c3d76314f9d2f0c638ebc4af16b8c2b21c6b62.

## Exact final audit and limits

- 1,538/1,538 limb IK solves terminate successfully; maximum five evaluations.
- Maximum sole-height/horizontal task error: 0.304 mm.
- Maximum horizontal COM task error: 0.150 mm.
- All sampled model coordinate bounds pass; reopened skin knee/ankle limits pass.
- Reopened joint mapping error: 1.31 micrometres.
- Minimum emitted skin height: -1.98 mm.
- Root residual RMS: 0.21024 BW/BWL; peak normalized command: 2.00931.
- Minimum total modeled vertical support: 0.54586 BW; no sample below 0.05 BW.
- Loaded pad tangential speed reaches 0.266 m/s (left), 0.206 m/s (right).
- Peak backward COM speed: 0.386 m/s; lateral speed reaches 0.892 m/s.

These residuals, excess command and sliding **fail to establish physical
feasibility**. No tolerances were weakened. Successful IK is not full dynamics
convergence. The visual candidate can be reviewed separately; do not promote
it as production contact or strength validation.

Seventeen focused tests pass: reverse support/release, closing placement,
endpoint smoothness, reduced balance equation, surface geometry/stiffness,
existing path tasks and turning tests. No broad release suite was run.

## Evidence and reproduction

Factory: task worktrees/stride-hip-visual-iteration on codex/moco-c52-walk-turn.
Game: principal Eonwild on codex/moco-c52-walk-turn-review.
Task root:
 /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526
Research: task research/moco-c55-backward-retreat.
Durable evidence: game/Evidence/moco-c55-backward-retreat.
Unity asset: game/Assets/Eonwild/MocoRetreat55A/tarbo.glb.

Use execution.json for exact commands. sequence_moco_retreat.py consumes the
C52 B H finite replay, C51 support-a baseline and archived retreat-plan.json.
Replay its returned solution, retarget to the v15 12-tail-connected motion set,
then build MocoRetreat55A using MocoPrototypeReviewBuilder. Capture 384 frames
per view at 24 fps, side and front-quarter. No world demo is needed.

Visual inspection receipt is saved with each video. Pause for user feedback;
do not start another artistic iteration or a long full solve automatically.

All 768 rendered frames were inspected as 32 chronological sheets, plus enlarged
quarter frames 78, 128 and 215. No obvious ankle snap or frame discontinuity was
observed. Sole roll remains visible during lateral support, and body/neck motion
is deliberately restrained. These are the main artistic review concerns alongside
cadence. This is frame inspection, not direct video perception. The camera follows
root translation, so use foot placement and shadows to read displacement.
