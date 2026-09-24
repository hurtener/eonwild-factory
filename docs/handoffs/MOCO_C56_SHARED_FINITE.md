# C56 — shared finite whole-body coordination

Returned candidate; all final capture frames inspected; user review PENDING. User authorized integration after identifying that
C55 B held the torso and prescribed the tail independently. C55 B has changes
requested: retain distal toe contact until release and restore body coordination.
Preserve approved running/walking/turning outputs and both main branches.

## Architecture boundary

`RetreatPlan` owns four footholds, release/landing times, distal-contact peel and
initial/final state intent. It does not own torso or tail animation.
`FiniteCoordination` in `src/eonwild_motion/solve/moco_finite_coordination.py`
consumes a boundary trajectory, foot-pose task and solver settings. It optimizes
all admitted coordinates together, using the same `Coordination.mechanics`,
OpenSim model, passive forces, contact forces and inverse dynamics as periodic
coordination. Periodic and finite paths call the same capacity/effort and
CF-inspired torque-coupling cost functions.

Quintic B-spline decision variables are local in time and have zero position,
velocity and acceleration corrections at both boundaries. Anatomical joint
limits remain enforced continuously through the existing latent bounded map.
Root envelopes and task/contact requirements remain soft objectives, with
violations measured rather than hidden. Numerical coefficient bounds constrain
the search neighborhood; they are not biological ranges or acceptance limits.

Root force/moment residuals now influence the chosen motion, along with internal
effort, estimated capacity, contact slip, material clearance, gaze, body posture,
neck-height envelopes, tail curvature and motion continuity. Whole-body angular
balance is represented by the exact model's root moment residual; the old
approximate trunk/tail-only angular-momentum objective is not substituted for it.
The prescribed tail response to the reduced COM reference is disabled. Each
admitted tail link's pitch/yaw is a decision variable. There is no torso sway
oscillator, changed mass, increased strength, or playback correction.

This is a shared **finite trajectory optimizer**, not a new backward-specific
physical engine. The backward adapter still builds an IK seed from its task.
It still adopts the C52 grounded start state; canonical stance admission and
nonzero-velocity adoption remain separate work. Previously approved periodic
clips are not regenerated or automatically claimed migrated. Forward finite
transitions and turns can use this interface, but transfer is NOT_RUN here.

## Contact intent

The new explicit `release_contact: distal` option uses the front material pad
as the final anchor. The proximal foot rises while the digit counter-flexes to
keep its segment's initial orientation. Recovery then lifts and moves the foot
backward. Both the release pivot and support-center reference use that contact.
The old rear pivot remains reproducible for earlier candidates. This ordering
is user-directed motion intent, not measured extinct-animal biology.

## Physical classification

The model uses effective stiffness/damping, torque capacities and soft mechanical
coupling estimates, not reconstructed anatomical muscle activations. Numerical
minimization of these residuals is not full Moco convergence, independent forward
stability, or validated physical acceptance. Report final dense mechanics and
skin/contact results separately from optimizer termination and visual review.
Do not claim full simulation from an improved video.

## Execution and checkpoint

Direct work, no subagents. Task root:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526`.
Research: `research/moco-c56-shared-finite`.
Factory: `worktrees/stride-hip-visual-iteration`, branch
`codex/moco-c52-walk-turn`.
Game: `/Volumes/m2-extended-disk/Repos/eonwild`, branch
`codex/moco-c52-walk-turn-review`.

First bounded solve: 99 sample times over 2–9 s, 14 spline intervals,
maximum 12 optimizer evaluations. Sixteen-second output preserves rest before
and after the four placements. All coordinates participate. No full Moco
optimization was launched. Focused basis, force-cost and material-release tests
pass (20 total with existing contact/path/turn checks).

Completed: replayed the exact returned trajectory, retargeted, rendered native
16-second side/quarter videos, and inspected all 384 frames in each view.
Source, recipes, hashes and evidence are preserved for the visual checkpoint.
No user approval is inferred.

## First internal solve — rejected after rendering

This first result is NOT the delivered video. It lifted the tail excessively because the finite objective omitted the existing carried-tail term.

Numerical generation source: `21b965e` (metadata wording subsequently clarified
without changing trajectory bytes). The optimizer reached its explicit limit
of 12 function evaluations, **not convergence**. Squared objective reduced from
32,424.5 to 10,586.3. All 53 coordinates participate through 689 temporal
coefficients. Dense exported-state replay gives the following comparison:

| Measure | C55 B | C56 |
|---|---:|---:|
| Root force/moment residual RMS BW/BWL | 0.06499 | 0.04482 |
| Peak normalized actuator command | 1.7064 | 1.0800 |
| Maximum loaded pad tangential speed | 0.1788 m/s | 0.0677 m/s |
| Peak loaded sole roll | 0.376 deg | 0.648 deg |
| Lateral COM span | 0.0211 m | 0.1643 m |
| Chest yaw excursion | 0 deg | 7.546 deg |
| Root roll excursion | 0 deg | 1.494 deg |
| Tail-base yaw excursion | 1.770 deg prescribed | 11.333 deg optimized |

The increased lateral COM response is intentional freedom for coordination,
not a target amplitude or a claim of user acceptance. The supporting feet stay
nearly level. Some actual pad slip persists, and the 8% peak command excess is
still a physical failure. Residual support is not supplied by hidden actuators.

During the four peel intervals the rear pad rises 35.2–37.0 mm while the distal
pad center moves at most 3.91 mm on any axis. Toe articulation participates in
keeping the distal segment steady. There is no claim of perfect anchoring.
All sampled anatomical joint bounds and reopened knee/ankle limits pass.
Minimum final skin height is +5.01 mm; no skin penetration, but not exact
skin-to-floor contact everywhere. Model-to-skin mapping error is 1.64 micrometres.
The initial coordinate state is preserved. Minimum total support is 0.7458 BW
(including unchanged boundary-state mechanics); no flight interval is introduced.

The exact final GLB SHA256 is
`d7ffbb5959d80c9db4d76d0531d0682674ed435e945e5e03862eadd55f9846c2`.
Render target is the separate `game/Assets/Eonwild/MocoFinite56` Unity folder.
All prior review assets remain intact.

## Final checkpoint candidate — shared carriage restored

The correction uses numerical source `081b447` and the same model/physical limits.
The inherited tail-carriage cost is restored. Effort, CF-inspired coupling and
carriage are now centralized for periodic and finite modes in
`moco_coordination_costs.py` (formula-preserving refactor `b6a6ef6`). This avoids
adding a separate backward tail rule. Twenty-one focused checks pass.

A bounded eight-evaluation refinement starts from the first solve's saved
coefficients. It reaches its evaluation limit, not convergence. Squared
objective with the restored carriage term falls from 71,316.7 to 10,676.6.
The final tail-tip height relative to the root spans -0.828 to -0.429 m instead
of -0.938 to +1.452 m. A residual ~4 cm violation of the soft carriage envelope
at some intermediate links remains; this is not a hard posture-constraint pass.

| Measure | C55 B | Final C56 |
|---|---:|---:|
| Root force/moment residual RMS BW/BWL | 0.06499 | 0.04491 |
| Peak normalized actuator command | 1.7064 | 1.2503 |
| Maximum loaded pad tangential speed | 0.1788 m/s | 0.1325 m/s |
| Peak loaded sole roll | 0.376 deg | 0.686 deg |
| Lateral COM span | 0.0211 m | 0.1644 m |
| Chest yaw excursion | 0 deg | 7.555 deg |
| Root roll excursion | 0 deg | 3.061 deg |
| Tail-base yaw excursion | 1.770 deg prescribed | 11.841 deg optimized |

The final force/command figures supersede the first internal comparison above.
Restoring tail carriage raises the peak command relative to that rejected solve;
25% command excess and nonzero root residual/slip remain physical limitations.
No threshold or strength has been altered to call them acceptable. The final
rear-pad peel rises 35.6–36.8 mm with at most 5.59 mm distal-center motion on any
axis. The toes stay approximately anchored through peel, not perfectly fixed.
All sampled joint bounds and reopened knee/ankle bounds pass. Final minimum skin
floor height is +4.98 mm and mapping error 1.52 micrometres. Initial state is
preserved. No new independent forward-stability or other-animal claim is made.

Final GLB SHA256:
`c1d7db4c86cf6fac602c8056408fdb779e7a363fdd771ecda610e931fe8dd15f`.
The `MocoFinite56` Unity folder holds this final candidate. The first internal
trajectory/coefficients and one rejected frame are preserved as evidence.
Use `execution.json` in `game/Evidence/moco-c56-shared-finite` for exact commands,
source commits, input hashes and warm-start reproduction. Saved native-time
side/quarter movies live in `review-side` and `review-quarter` there.

## Final visual review and pause

All 768 final frames were inspected in sequential contact sheets, with enlarged
release/contact views. This is frame inspection, not direct video perception.
No obvious ankle snap or pose discontinuity was identified. The chest/pelvis
and tail participate, supporting soles remain nearly level, and the rejected
large tail lift is absent. Side-view motion remains restrained. Native-time
fluidity and artistic acceptance remain for the user to judge. Pause here; do
not generate another iteration or migrate approved clips without direction.
