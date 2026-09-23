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

IN PROGRESS: support fit and full Moco pilot started. No new visual approval,
full-convergence or independent-stability claim. Update this section with the
actual returned outcomes and exact artifact paths before final handoff.
