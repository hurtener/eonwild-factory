# C51 — relaxed recovery and physical feasibility

2026-09-23. The user accepted C50 D's repaired tail and overall fluidity, requested
less ankle excursion/angular speed in recovery, and authorized validation stages
1–2 overnight. Work directly without subagents. Poll a running optimization **no
more often than once every ten minutes**. Stop at the next visible checkpoint;
C51 is not pre-approved. Preserve the conventional solver baselines independently.

## Preserved baseline

C50 and the accumulated source/evidence are pushed to both remote main branches:
factory `9868716ae029a43d4c16715f8c06a1e6f10d7451`, game
`9b16390cf5ef9c9a6e08d681ffaa9189b7893bcd`. The factory main CI was queued when
checked; local focused checks are separate from hosted CI. Failed historical
C50 tail sources are explicitly quarantined, not new source admissions.

Continue in the active factory worktree specified in
[the C50 source/rig handoff](MOCO_C50_TAIL_REPAIR.md). Current branches are
`codex/moco-c51-support-feasibility` (factory) and
`codex/moco-c51-support-review` (game). The main factory checkout is stale.

## Stage 1: support and ankle recovery

The saved C50 physical replay has firm-support foot centers about 0.66 m on each
side of the ground centerline (roughly 1.32 m full track). The legacy
`foot_track_hip_width_ratio: 0.5` is an initialization preference, **not an
assertion that the current result retains that narrow track**. Under firm load,
the left ground lane varies about 15 mm while pelvis-relative displacement is
much larger. Do not erase legitimate pelvis transfer by pulling planted feet
inward. Loaded pad surface speed remains a separate contact/slip diagnostic.

C50 right ankle unloaded peak is 118.26 degrees and 603.09 degrees/second. These
are reduced model coordinates, not published anatomical angles. The C51 recipe
adds continuous load-gated soft penalties above 1.8 rad and 7.5 rad/s, and an
unloaded acceleration penalty. These are **authored comfort targets**, not
biological limits. The unchanged joint bounds, exact OpenSim ground forces,
finite motor capacities, and root balance remain active. Tail/neck/chest
reference weights preserve the accepted character while the legs adapt.

The support task uses a world-lane envelope centered on the observed support
track. It does not prescribe a pelvis-relative stance, clamp exported joints,
add root assistance or change playback time. `tools/audit_moco_support.py`
reports both world and pelvis-frame measurements. The Unity plain-stage player
now accepts `-front` as well as `-front-quarter` and default side.

## Stage 2: bounded full Moco attempt

A separate C50-seeded pilot uses 25 collocation intervals and a 90-minute cap.
This is distinct from the Fourier/inverse-dynamics initializer used for the
visual candidate. The supervisor writes durable command/PID/timing/status to
`process.json` and enforces the timeout without frequent polling.

The initial audit found small ankle/roll bound violations and a larger proximal
tail violation (~0.027 rad). Projecting just these values into the existing
bounds increased maximum inverse-dynamics residual in the scaled model from
3.32 to 16.99 model force/torque units. This demonstrates a warm-start mismatch;
it does not prove that clipping explains every optimizer issue. Prepare any
refined seed inside the existing bounds through optimization, not a rendered
pose clamp. An optional initializer interior margin is a stricter search target,
not wider model limits or changed production thresholds.

Never render scaled iteration callback files. Only a returned unscaled
`solution.sto` can be replayed. Successful optimizer termination, physical replay,
mesh refinement, independent forward stability, and user approval are distinct.
Stages 3–4 are not authorized in this pass. Do not claim a physically validated
Moco gait merely because this diagnostic clip is fluid.

## Files and reproduction

Task storage (large temporary data stays on the external disk):
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c51-support-feasibility/`.

- `support-recipe.json`, `support-process/`, `support-a/`: visual initializer.
- `pilot-recipe.json`, `pilot-process/`, `moco-pilot/`: bounded full Moco pilot.
- `baseline-audit/`, `initialization-audit.json`: actual baseline diagnostics.
- Factory recipe: `catalog/behaviors/moco-c51-support-recovery.v1.json`.

Use the C50 handoff's exact admission, replay, retarget and Unity build commands
with new output directories and the C51 recipe. Retain the admitted twelve-link
source and matching profile. Inspect every saved frame in chronological sheets,
measure the reopened GLB and preserve native-time side/quarter/front videos.
Receipts and source snapshots must identify the actual trajectory shown; an
unsuccessful full solve must never be substituted silently for the visual fit.

## Checkpoint status

C51 A is rendered and pending user review. All 144 side, 72 quarter and 72 front
frames were inspected in chronological sheets, with enlarged recovery/contact
frames. No disconnected tail or new discontinuous pose was seen; this is not a
claim of direct native-video temporal perception.

| Measurement | C50 D | C51 A |
|---|---:|---:|
| Swing peak ankle angle | 118.26 deg | 90.85 deg |
| Swing peak ankle speed | 603.09 deg/s | 436.57 deg/s |
| Reopened skin floor intrusion | 7.19 mm | 6.11 mm |
| Initializer six-axis balance residual RMS | 0.01305 BW/BWL | 0.01370 BW/BWL |
| Dense replay 3D force-balance RMS | 0.01399 BW | 0.01562 BW |
| Loaded contact surface speed p95 | 0.417 m/s | 0.233 m/s |
| Maximum command magnitude | 1.210 | 1.202 |
| Firm-support left world-lane range | 14.9 mm | 19.7 mm |
| Contact samples below 0.05 BW | 1.2% | 0.0% |

The contact load remains nonzero throughout the new sample (minimum 0.0984 BW).
Thus this pass is not proof of an airborne running gait. The skin-contact and
motor-command failures remain explicit. Do not promote the candidate to physical
acceptance because the ankle metrics improved.

Evidence: principal game `game/Evidence/moco-c51-support-feasibility/candidate-a/`.
Asset: `game/Assets/Eonwild/MocoSupport51A/`. The exact initializer source is
factory commit `3827ce7`; the additional audit/interior-seed helpers are `58c25aa`.
Full Moco pilot is still running separately. A second initializer prepares the
C51 motion inside unchanged model bounds, using a 0.0005 coordinate-unit interior
target and stronger range/command penalties; it is not selected for display.
Update final solver status when the bounded experiments return.


### Overnight continuation, 06:31 UTC

The interior initializer finished in 585 seconds / 40 evaluations. Dense replay
has no sampled joint-angle bound violations, including the proximal tail. The
15-interval Moco initial guess also has no such violations; projecting its
angles into the same bounds changes maximum inverse-dynamics residual by zero
(3.410 before and after, scaled model units), versus C50's 3.324 -> 16.989.
This improves bound consistency, not every feasibility measure: initializer
six-axis residual rises to 0.01604 BW/BWL and peak command to 1.2933. Dense replay
3D force-balance RMS is 0.01816 BW. Contact penetration is 5.94 mm and loaded-pad
p95 speed 0.237 m/s. These are not physical acceptance results.

The single additional full Moco attempt is now launched in `moco-interior/`,
supervised by `interior-process/`, with a 60-minute cap ending about 07:31 UTC.
The original pilot remains bounded at 07:15 UTC; its last observed primal
infeasibility was 43.0 at iteration 49, not convergence. **No further full-solve
retries are authorized in this checkpoint.** Consult `monitor.json` before any
poll and preserve a 600-second interval per active solver. Numerical
`ipopt.opt` sets initial bound distance to 1e-6; verify the option-use listing at
the next eligible poll. C51 A remains the sole displayed candidate.

Metric clarification: the earlier table mixed the baseline dense force-only
RMS with the candidate six-axis initializer RMS. The corrected table above
labels both metrics separately and makes the modest balance regression explicit.


### Pilot terminated, 07:16 UTC check

The original 25-interval pilot exhausted its 90-minute budget. The supervisor
sent SIGINT and, after its 30-second grace, SIGTERM; exit code -15. No returned
unscaled `solution.sto` or solve receipt exists. Last logged iteration 92 had
primal infeasibility 86.5. Archived under game evidence `experiments/pilot/`;
scaled callbacks are compressed and explicitly ineligible for replay/rendering.
This failure does not prove the physical problem has no feasible solution.

The interior run is still active; its latest observed iteration 63 had primal
infeasibility 0.0817, not convergence. Ipopt explicitly reported both requested
initial bound settings as used. To preserve its final unscaled iterate, a
single-use helper will remove only its exact OpenSim stop sentinel at 07:29:21
UTC, two minutes before the existing hard deadline. The plan/helper are archived
under `experiments/interior-full-moco/`. No deadline extension or new solve was
introduced. At the next eligible check, consult `monitor.json`; do not duplicate
the graceful-stop helper or re-read active progress inside ten minutes.
