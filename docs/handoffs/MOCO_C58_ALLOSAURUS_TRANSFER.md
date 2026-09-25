# C58 — Allosaurus MoCo walking and running transfer

Status: CHANGES REQUESTED after user review; physical acceptance FAILING.
C57 C is deferred at the user's request, not approved. Accepted Tarbo baselines
remain preserved. Direct implementation without subagents; pause here.

## Delivered and what changed

Walk B: 16 seconds, held idle → start → walk at 1.6 m/s → stop → held idle.
Run C: 10 seconds of native-time sustained running at 3.8 m/s.
Both have side and front-quarter views, 24 fps. Every captured frame (1248 total)
was visually inspected in 52 chronological contact sheets. This is not a claim
of direct video playback analysis. No full-world scene is needed.

Uses the existing Allosaurus v21 source and Running42 semantic profile with the
shared OpenSim body/contact and inverse-dynamics initializer, not an Allosaurus
solver. C51 A Tarbo replay supplies a warm reference. Limbs are re-solved for
the new anatomy. This is reference-guided transfer, not reference-free prediction.

Shared changes:
- Normalize tail arc length when transferring bend across different lengths
  and subdivisions. Allo has ten physical links and eleven connected semantic
  skin nodes, checked against its real rig. No artificial twelve-bone mapping.
- Opt-in body seed scaling by admitted leg length before destination limb IK.
- Admit duty factors below 0.5 in the contact initializer. Restrict static
  standing-force settling to overlapping support.
- Fit the oriented admitted sole's lowest pad to the support plane without
  shifting horizontal anchors. This is task initialization, not a render fix;
  the lowest-pad envelope may still introduce sharpness.
- Optional scalar solve of the existing periodic root-height parameter to
  balance integrated vertical ground impulse. This leaves mass, contact forces,
  capacities, joint limits and acceptance unchanged. It does not balance
  instantaneous forces, horizontal impulse, angular dynamics or internal effort.

Allo inputs: 1512 kg from the engineering profile; measured rig segment lengths
0.837393 / 0.738363 / 0.409243 m. Walk uses the inherited authored
0.6-body-height step reference: 1.178726 m per step / 2.357453 m per same-foot
stride. Run uses the existing 1.7 m step / 3.4 m stride intent. These are not
fossil measurements. Segment mass fractions and actuator capacities are inherited
engineering estimates, not measured Allosaurus muscles.

Two A initializers each ran six nonlinear evaluations. Neither converged.
Final B/C reuse those coefficients on corrected task initialization and are
evaluated only; Run C also solves one vertical-impulse parameter. The finite
walk uses the existing authored contact/cadence sequence with anatomy IK and
inverse-dynamics audit. No full Moco optimal-control solve was performed.

## Results and limitations

| Metric | Walk B sequence | Run C |
| --- | ---: | ---: |
| Root residual RMS, normalized BW/BWL | 0.23719 | 1.43436 |
| Peak normalized command | 8.1296 | 153.4851 |
| Mean vertical force / BW | 0.99688 | 1.00000 |
| Peak vertical force / BW | 1.31884 | 8.41107 |
| P95 loaded surface speed | 0.03316 m/s | 0.20427 m/s |
| Minimum reopened skin floor | -9.84 mm | -39.65 mm |
| Reopened knee/ankle angle-limit violations | none | none |
| Full Moco convergence | no | no |

Running impulse was 6.041 BW before scalar initialization, 1 BW afterward;
short airborne intervals now occupy about 5.8% of sampled time below 0.05 BW.
This does not repair the excessive peak load or command. Physical errors are
substantial, not minor numerical tolerance misses. No thresholds were relaxed.

Visible knee excursion is restored (about 65° walk, 103° run), tail binding is
intact, and the walk enters/exits a held stance. Running ankle recovery remains
sharp; peak speed is about 834°/s. The finite walk also contains a left ankle
speed spike (~1757°/s), despite angle bounds passing. Arms remain held and the
tail is comparatively quiet; no new arm-life pass is claimed. Reopened skin
penetration and slip remain unresolved, especially in running.

Running start/stop is PENDING: the current finite walking sequence assumes
grounded support. Do not force airborne running through it. Turning/backward
transfer, sprinting, and hit reactions are also pending. Do not proceed before
user feedback on this first transfer. C57 C remains deferred.

## Files and reproduction

Factory worktree:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration`

Research:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c58-allosaurus-transfer`

Durable game evidence:
`/Volumes/m2-extended-disk/Repos/eonwild/game/Evidence/moco-c58-allosaurus-transfer`

Evidence contains `execution.json`, source patch/launch snapshots, model and
solve receipts, coefficients, unscaled solution.sto, compressed replay.json,
admissions, recipes, retarget audits, all frame sheets, logs and saved MP4s.
`comparison.json` contains the complete final measured values.
`reproduce-final.sh` reconstructs selected candidates from archived A
coefficients; it is documented reproduction, not a second run performed here.
Decompress replay.json.gz before tools that expect plain JSON.

Source geometry SHA256:
`b605b9934a5585a6387361dffd054467af0d1a1d7b9ed2c46b442b7744687e9a`.
Source profile SHA256:
`c4fdb476571b6dacad6a39bcb3086394b1ceef5031a66c61f27f6cf0a92295b3`.

Canonical checkpoint recipes:
`catalog/behaviors/moco-c58-allosaurus-walk.v1.json` and
`catalog/behaviors/moco-c58-allosaurus-run.v1.json`.
Source motion set: `catalog/motion-sets/allosaurus-engineering-native-walk.v21.json`.

Game assets: `game/Assets/Eonwild/MocoAllo58Walk` and `MocoAllo58Run`.
Review builder accepts `-moco-animal allo`; default remains tarbo.
Player captures label via `-animal-label ALLOSAURUS`, and `-alternate` selects
running. These only select assets/labels; playback adds no motion corrections.

Verification: 18 focused tests passed, Unity standalone review build succeeded,
four captures encoded and all frames inspected. Reopened skin audits passed
knee/ankle angle bounds but failed contact/effort acceptance. Full runtime
integration/parity and production acceptance are not claimed.


## User review and code diagnosis — 2026-09-25

Status: CHANGES REQUESTED. User reports a frozen straight idle tail, excessive
mouth opening, unrelaxed walking metatarsus, running ankle reversals and a knee
that reads constrained. No new motion has been generated for this diagnosis.

Confirmed by source and reopened emitted C58 GLBs:
- Idle is constructed from the cycle mean and motion gain is zero at rest.
  Proximal tail coordinate variation is effectively zero in the initial hold.
  There is no independent standing/living posture task in this sequence.
- Allo neutral calibration v7 has close_degrees=0. The retargeter gates all jaw
  animation on a nonzero neutral closure. The configured 0.8–2.3 degree walking
  and 0.8–3.8 degree running breathing is therefore skipped. Jaw local rotation
  is constant in both saved clips (sampled first 1.5 seconds).
- The skin is faithfully following the solved leg landmarks (maximum error
  about 2.9 micrometres walk, 1.4 micrometres run). Retargeting has not frozen
  the knee. Actual three-landmark interior knee angle in the running skin spans
  66.44–169.93 degrees. It spends much of the cycle bent, with rapid extension
  late in recovery; full-cycle range alone hid the timing problem.
- The walking MTP coordinate is active (~55 degrees total excursion), but that
  does not establish relaxed unloading or correct metatarsal carriage.
- Shared model knee limits are [-2.0,-0.16] rad and ankle limits [0.15,2.25] rad,
  identical to the Tarbo prototype. They are inherited engineering limits,
  not limits extracted from the Allo bind-pose knee angle.
- The contact initializer strongly fits toe orientation and position independently
  per sample, with only a weak joint-reference cost. This can redistribute a
  prescribed foot trajectory into an undesirable knee/ankle/MTP combination.
  Final B/C were reinitialized/evaluated rather than fully coordinated to
  convergence. Cause attribution to one cost alone remains a hypothesis.

Next correction scope: C58 B, not more behaviors. Separate living standing
posture from bind pose and gait mean; fix jaw binding/neutral/breathing separation;
solve continuous knee-ankle-metatarsus coordination and support reception,
including relaxed unloaded foot carriage, with the same shared mechanics.
Keep physical limits and source geometry intact. Do not widen knee ROM merely
because it reads stiff; do not claim that removing rest-pose influence alone
will cure force/ankle problems. Reopen final skin/contact after any posture change.
