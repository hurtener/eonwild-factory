# C59 B: living intent across the movement batch

Status: **GENERATED AND FRAME-INSPECTED — USER REVIEW PENDING**. No user approval inferred. Full Moco convergence remains false.

The user found C59 too robotic and requested natural behavior in tail, body and
head across the batch. B retains the same four contact tasks on both animals:
stepping pivot, lateral steps, short retreat and planted alert. All eight take
12 seconds at native time. It does not replace approved walking or running.

## What changes

Shared `LivingIntent` adds irregular attention adjustments, gentle inspection
pitch, chest breathing, restrained torso follow-through, and a delayed wave of
tail curvature. Retreat keeps smaller glances toward the threat. Tail motion is
distributed over actual admitted arc length (Tarbo 12 links, Allo 10), rather
than assuming a common bone count. Existing semantic profiles allocate the
neck/head turn and define small arm/wrist responses. Jaw breathing shares the
body breathing period. Arms and jaw remain cosmetic retarget behavior, not
independently simulated muscle systems.

Intent enters **before contact IK and finite whole-body coordination**. The
shared solver can adjust the body and limbs together; torso/tail movement is
included in the exact-model inverse-dynamics replay. This is reproducible,
authored animal behavior, not a spontaneous game AI or reconstructed physiology.
The event timings and amplitudes are artistic choices. No species solver,
anatomical range expansion, force-capacity change or animation time warp.

An exploratory B crossed the tail-base lower bound by 0.000882 rad, then its
clipped initialization produced a rapid interpolation correction. The resulting
Tarbo pivot command reached 45.63. That take was rejected. Living offsets now
enter the shared smooth bounded coordinate space before interpolation, so they
approach an existing stop without clipping. A focused near-limit derivative
check covers this failure. Revised trajectories are regenerated and replayed;
this is not a cosmetic repair to the video.

## Media and review

Saved media are under principal repository
`game/Evidence/moco-c59b-living-batch/`. Dual-view reel order:

| Interval | Animal | Movement |
| --- | --- | --- |
| 00–12 s | Tarbo | Pivot |
| 12–24 s | Allo | Pivot |
| 24–36 s | Tarbo | Lateral steps |
| 36–48 s | Allo | Lateral steps |
| 48–60 s | Tarbo | Retreat |
| 60–72 s | Allo | Retreat |
| 72–84 s | Tarbo | Alert / look-around |
| 84–96 s | Allo | Alert / look-around |

Left is side view, right is quarter view. Lateral tasks use a fixed camera.
The Unity review viewer holds the initial pose for 12 lighting warm-up frames
before saving frame zero; no motion time is skipped or stretched.

## Reproduce and continue

Factory: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration`.
Research: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c59b-living-final`.
Game: `/Volumes/m2-extended-disk/Repos/eonwild`.

Base factory commit: `52f4ad1e41a6f83397ea6d78ffd78ee8ef8edc7c`.
Base game commit: `a2d7067efadbfa9241f7db45139c3eb113d4b792`.
Review branches remain `codex/moco-c52-walk-turn` and
`codex/moco-c52-walk-turn-review`. Accepted main stays unchanged.

Canonical behavior policy: `catalog/behaviors/moco-c59-batch.v2.json`.
Archived `batch.json` identifies the exact source rest states, motion sets,
profiles and expanded plans. `source/pins.json` hashes generation code and
policy. Use archived `generate.py <take-id>` in a **new output directory**;
it invokes sequence generation, physical replay and actual-rig retarget with
commands and exits recorded. `review-ready.py` waits for exports and serializes
Unity builds while recording both camera views; `compact-sheets.py` lays out
all 288 frames per view. `assemble.py` creates eight dual-view clips and one
96-second reel. `archive.py` preserves compressed replays, models, receipts,
source inputs, videos and inspection sheets. Raw PNGs stay on the external SSD.

The prior C59 handoff contains runtime paths and additional task/mechanics
boundaries. Keep finite optimizer status, physical acceptance, exported skin,
visual review and gameplay integration separate. None implies another.
Stop after this B batch for feedback. Missing sprint, impacts/stumbles,
knockdown/get-up, feeding/drinking/rest and robust moving-state joins remain
outside this pass.

## Final evidence and limitations

All eight actual-rig takes are rendered in both views: **4608 frames inspected**
in chronological sheets, including every frame of each 12-second capture.
This is frame inspection, not a claim of direct video perception. The combined
reel is 96 seconds, 2304 frames, native 24 fps, 2560×720. The individual dual-view
clips are 12 seconds each. Source views are also preserved.

The added life reads most clearly in head follow-up looks, chest/neck breathing
and delayed tail settling. Arms remain subtle. No gross new limb inversion,
body jump or tail-base snap was seen. A brief brightness change remains during
the first roughly 0.33 seconds of the captures despite the warm-up; motion
frames were neither dropped nor retimed. Small interpenetrations and subjective
fluidity still require user review.

All sampled admitted coordinate bounds passed. Seventeen focused tests passed,
including segmentation-independent tail amplitude, deterministic boundary
adoption and a near-joint-limit acceleration regression. All eight generation,
physical replay, retarget and Unity capture processes completed successfully.

**Physical acceptance is NOT CERTIFIED. Full Moco convergence is false.**
The finite optimizer reaches its six-evaluation budget; this is not convergence.
Normalized command above 1 still exceeds an actuator estimate. Root force
residuals and contact/slip limitations remain in the archived receipts.

| Take | Root residual RMS | Peak normalized command | Min skin floor (mm) |
| --- | ---: | ---: | ---: |
| tarbo-lateral | 0.05310 | 1.940 | 4.52 |
| tarbo-retreat | 0.05148 | 1.339 | 4.29 |
| tarbo-pivot | 0.12584 | 3.953 | 4.93 |
| tarbo-alert | 0.03716 | 2.102 | 9.12 |
| allo-lateral | 0.08246 | 1.421 | 8.21 |
| allo-retreat | 0.08012 | 1.421 | 7.86 |
| allo-pivot | 0.08800 | 1.422 | 10.88 |
| allo-alert | 0.06990 | 1.421 | 12.22 |

The final Tarbo pivot's tail-base acceleration is 10.24 degrees/s², compared
with approximately 2390 in the rejected exploratory B. Peak command is 3.953
(A: 4.014), and peak ankle speed is 158.05 degrees/s (A: 381.4). The rejected
B is never displayed as the review candidate.

Model masses, segment properties, joint ranges and actuator capacities match
the source. Contact pads match C59 A. They differ from the forward gait source
because C59 A admitted medial/lateral support-edge pads; the audit's
physical_parameters_unchanged.contacts=false refers to that earlier difference,
not a new B relaxation. See prior C59 handoff for the contact model boundary.

Media in the principal game repository:
- [Complete B review reel](../../game/Evidence/moco-c59b-living-batch/c59b-review-all.mp4)
- [Tarbo pivot](../../game/Evidence/moco-c59b-living-batch/tarbo-pivot-review.mp4)
- [Allo pivot](../../game/Evidence/moco-c59b-living-batch/allo-pivot-review.mp4)
- [Tarbo lateral](../../game/Evidence/moco-c59b-living-batch/tarbo-lateral-review.mp4)
- [Allo lateral](../../game/Evidence/moco-c59b-living-batch/allo-lateral-review.mp4)
- [Tarbo retreat](../../game/Evidence/moco-c59b-living-batch/tarbo-retreat-review.mp4)
- [Allo retreat](../../game/Evidence/moco-c59b-living-batch/allo-retreat-review.mp4)
- [Tarbo alert](../../game/Evidence/moco-c59b-living-batch/tarbo-alert-review.mp4)
- [Allo alert](../../game/Evidence/moco-c59b-living-batch/allo-alert-review.mp4)

These relative media links resolve in the principal game repository; from the
factory use the principal path above. Evidence includes source hashes, exact
commands, replays, models, task recipes, retarget receipts, review observations
and comparison metrics. Gameplay integration remains NOT RUN.
