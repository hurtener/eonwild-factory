# C58B — Allosaurus shared-engine polish

Status: DIAGNOSTIC_READY_FOR_USER_REVIEW; no user approval and no full Moco convergence claimed.
C58 required changes. C57 C remains deferred. Accepted Tarbo baselines remain unchanged.

## Scope

1. Separate living standing intent from bind geometry and the mean gait pose.
2. Separate jaw binding, neutral closure and breathing. A valid zero closure no longer disables breathing.
3. Coordinate knee, ankle and metatarsus across physical time. Swing tasks can relax; support retains the existing contact law and anatomical bounds.
4. Apply gentle idle body/tail motion before contact solving and mechanics replay.
5. Reproduce Tarbo's approved C51 A skin and mechanics as a regression.

Direct implementation, no subagents. Plain-stage native-time videos, not the full world. Stop at visual review.

## Shared changes and provenance

Source geometry, segment lengths, joint bounds, contact law, capacity estimates
and acceptance tolerances are unchanged. No animal-name branches were added.
Recipes opt into periodic temporal contact initialization, physical-time limb
acceleration cost, relaxed swing tasks and finite transition coordination.
Allo standing data lives in `catalog/calibration/allosaurus-moco-living-standing.v1.json`.

Standing curvature, subtle idle motion and 14-degree jaw-neutral closure are
authored intent, not reconstructed physiology. Closure uses the existing
secondary jaw rest setting and is checked on the rendered skin. Bind transforms
are preserved. Tail bend is distributed by normalized physical arc length over
the actual ten-link Allosaurus tail.

The periodic seed uses existing OpenSim whole-sole contact forces and an
authored impulse-normalized support goal. It remains a kinematic seed.
Reduced-coordinate refinement uses inverse dynamics; neither stage is full
Moco optimal-control convergence. Failed seeds remain labeled as failures.

Finite transition coordination solves neighboring limb configurations together,
retains world foot targets and the planned root path, then settles contact.
A first free-root trial generated a negative vertical-load requirement and
was rejected. No failure is hidden by widening limits or relaxing acceptance.

## Reproduction and evidence

Research: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c58b-allosaurus-polish`.

Evidence destination: `/Volumes/m2-extended-disk/Repos/eonwild/game/Evidence/moco-c58b-allosaurus-polish`.

Recipes: `catalog/behaviors/moco-c58b-allosaurus-{walk,run}.v1.json`.
Exact launched recipes and source snapshots are retained; canonical recipes
also record provenance and the final finite-transition settings.
Walk: 1.6 m/s and 1.178726 m per step. Run: 3.8 m/s and 1.7 m per step.
These are inherited engineering intent, not new fossil measurements.

Tarbo regression: GLB SHA256
`451c8068d07107a29081e2f83bd4bfa16bb225b1cc6ef984cfda56e9863a9c60`,
byte-identical to approved C51 A. Peak control is unchanged at
1.2019968505752292; root residual differs by 6.94e-18 from
0.013702534932960617. This protects the baseline, not general transfer.

Final native-time media, reopened export measurements, every-frame review and
source/process receipts are preserved with this checkpoint.


## Walking result (rendered)

16 seconds, idle → start → 1.6 m/s walk → stop → living idle. Both side and
front-quarter renders contain 384 frames at native 24 fps. All 768 frames were
inspected in 32 chronological contact sheets, not direct video perception.
Jaw rests almost closed; tail remains quietly active; the prior start ankle
kick is no longer evident in sampled frames. Arms remain held (outside this pass).

| Metric | C58 | C58B walk |
| --- | ---: | ---: |
| Peak left ankle speed | 1757.28 deg/s | 162.30 deg/s |
| Lowest reopened foot skin | -9.84 mm | -3.98 mm |
| Root residual RMS BW/BWL | 0.23719 | 0.14381 |
| Peak normalized command | 8.1296 | 6.2343 |
| P95 loaded surface speed | 0.03316 m/s | 0.09098 m/s |
| Peak vertical ground force | 1.31884 BW | 2.68584 BW |

The smoother transition trades some foot slip and a higher peak load for less
ankle sharpness. Physical acceptance is FAILING, not improved in every metric.
Sampled joint bounds and reopened knee/ankle bounds pass. Retarget joint error
is under 3 micrometres. No source geometry, contact, mass, capacity or anatomical
limit changed. Idle tail tip lateral range is 24.2 cm over the initial two seconds.

Two broad running refinements are rejected: one lets the head wander; the
other produces severe dense-sample force spikes. A narrower leg/contact pass
retains the coherent moving axial reference (not the static bind pose). This
limits the current search scope; independent predictive axial motion remains
future work. That pass was rejected too; the selected contact polish is described below.


## Final running selection

The broader run-b, run-c and run-e searches and run-seed-d are rejected.
Run-f/run-g contact trials were also rejected for unrestrained unloaded contact.
The selected run-h applies the same temporal contact coordinator used by walking
to the existing C58 periodic physical trajectory. Periodic neighbors are coupled; whole-sole force targets prevent unloaded penetration.
Root/body/tail motion and world foot targets are retained, and anatomical limits
are enforced continuously by the shared bounded spline. This is a local polish
of a saved physical trajectory, not an independent gait prediction. The reusable
tool is tools/polish_moco_contacts.py. No animal-name branch or authored knee curve.

Peak left ankle speed: 656.70 deg/s
(C58: 834.02). Root residual RMS: 1.29772 BW/BWL.
Peak normalized command: 153.4659. Mean vertical contact:
0.9990 BW, range [-0.006242952779463088, 8.359406222614727].
P95 loaded surface speed: 0.14619 m/s.
Reopened skin floor: -39.665 mm.
Full Moco convergence remains false. These are diagnostic results, not a physical pass.
Residual running recovery sharpness and skin penetration remain. This is an
incremental polish, not a complete running fix. Flight occupies 5.81 percent
of sampled time; this remains below the authored 14 percent task intent.

## Review media and reproduction

- c58b-allo-walk-side.mp4 / c58b-allo-walk-quarter.mp4: 16 s, 384 frames/view.
- c58b-allo-run-side.mp4 / c58b-allo-run-quarter.mp4: 10 s, 240 frames/view.
- All 1248 frames inspected in chronological sheets. Frame review cannot replace
  the user's direct native-time video judgment. Approval remains pending.
- comparison.json, joint-comparison.png, visual-review.json and sha256.json record
  metrics, observations and file identity.
- Process directories preserve commands, elapsed time and unsuccessful trials.
  source-final plus source-provenance.json identify the exact source.
- Walk reproduction: walk-refine-process command, then finish-exports.sh walking
  commands. Its run-b commands are historical and rejected.
- Run reproduction: run-force-process command then finish-final-run.sh.
  The source is archived C58 run-c, not a callback or scaled iteration file.
- Rendering uses MocoPrototypeReviewBuilder.Build with MocoAllo58BWalk and
  MocoAllo58BRun; 24 fps native-time side and front-quarter capture.

All five requested areas are represented. Remaining work includes contact/force
feasibility, sustained running judgment and flight-aware running transitions.
Held arms are outside this pass. Accepted main and Tarbo C51 A remain unchanged.
Pause here; do not infer approval or proceed to another animation.
