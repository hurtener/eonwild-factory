# C54 A — central neck profile and backward planning

2026-09-23. C53 A is explicitly **visually approved**. C54 A is **PENDING user
review**, not a replacement approved baseline. Work was direct, without agents.
Preserve C51 A running and C52 B H walking. Pause at this visual checkpoint.

## Changes and limits

The shared finite turn now accepts `--attention-profile`. It uses the existing
`resolve_attention`, `attention_intent` and `bound_attention` functions, drawing
the scan target and cumulative heading envelope from the canonical embodiment.
The Tarbo scan intent is 45 degrees; it remains an authored reconstruction value
with the evidence distinctions in `docs/research/THEROPOD_NECK_BASELINE.md`.

Regional weights are aggregated across admitted semantic roles: neck.0–1 into
the lower region, neck.2–4 into the upper, plus the head. Preferred weights are
0.1328/0.6972/0.17. A smooth bounded allocation solves actual projected skull
heading relative to trunk, compensating pitch/roll coupling. When the upper
region approaches its existing 20.05-degree limit, the other regions share the
remaining turn. Thus preferred ratios are not rigid constraints. Unfulfilled
heading and body-follow requests are reported; neither silently turns the root.
No species branch or per-animal solver was added.

This integration covers yaw target, cumulative yaw envelope and regional yaw
preferences. It does not certify biological anatomy, import every pitch or rate
setting, or supply active muscles. Path look-ahead and its normalization to the
named scan target remain authored steering intent. The unchanged C53 chest
anticipation, path, steps, tail delay, joint bounds and physical model are used.
Attention is solved before limb placement/contact correction and asset export;
there is no runtime head correction. Runtime samples the GLB.

## Measured comparison

| Measure | Approved C53 A | Candidate C54 A |
|---|---:|---:|
| Maximum skull heading relative to trunk | 38.41 deg | 45.00 deg |
| Maximum projected heading speed | 34.80 deg/s | 15.00 deg/s |
| Lower neck yaw maximum | 16.46 deg | 11.68 deg |
| Upper neck yaw maximum | 16.88 deg | 20.02 deg |
| Head yaw maximum | 8.41 deg | 13.89 deg |
| Peak normalized command | 4.5534 | 3.7980 |
| Root residual RMS BW/BWL | 0.10887 | 0.10864 |

All sampled knee/ankle ranges and peak rates match C53; the small vertical contact
settling is recomputed for the altered body mass pose. Model SHA256 is identical:
`2d03ef9fa341d292b2dafdaf55a95359d6e0c94dc2b6e08d63da66176a158ff8`.
All 1,538 limb IK solves succeed (maximum 46 evaluations). No sampled coordinate
bound violations; no reopened knee/ankle violations. Mapping error is 2.96 µm;
minimum emitted skin height is −5.51 mm. Sixteen focused tests pass. These checks
do not establish production contact, force balance or forward stability.

Both side and quarter captures contain 384 frames at 24 fps / 16 native seconds.
All 768 frames were inspected chronologically, plus enlarged quarter frame 150
and side frames 90/290. No obvious new pop, renewed ankle overextension or tail
discontinuity was seen. This is frame inspection, not direct video perception.
The camera translates with the pelvis and retains its world orientation, so the
side view becomes a rear view. These views are not fixed-world foot-slip proof.

## Correction: why the neck effort was so high

The earlier C53 audit read the **original recipe spring coefficient**, missing
`calibrate_bracing`'s overwrite. Total inverse-dynamics demand and assigned
capacity were correct, but the 1.874 kNm spring attribution was wrong.

Using coefficients from the exact serialized model at C53's lower-neck peak:

- Spring resistance: **8.843 kNm**, not 1.874.
- Gravity contribution: **−0.121 kNm**, independently calculated from each
  body's potential-energy gradient.
- Sum: **8.722 kNm**, matching static inverse dynamics within 1e-7 Nm.
- Full saved demand: **9.661 kNm**, versus **2.134 kNm** assigned capacity.

The bracing calibration sets lower-neck yaw stiffness to 31,472.54 Nm/rad,
with its rest angle fixed at zero. The neck is spending most of this modeled
holding effort resisting that strong centering spring. This is an engineering
engagement assumption, not evidence that the animal cannot turn its neck.
The corrected C53/C54 audits and source are saved together. Old C53 audit files
remain historical and superseded; do not reuse their spring/damping attribution.

C54 improves distribution, but lower-neck demand still peaks near 7.964 kNm and
upper-neck demand rises to 4.918 kNm as it takes more bend. **No full Moco solve
or physical convergence is claimed.** Mass, spring, strength and acceptance
thresholds were not modified. A later mechanical pass should distinguish passive
tissue resistance from task-dependent active engagement and account for its
torque/work; moving a spring rest angle cannot be treated as free muscle force.
Do not simply increase capacity or disable the brace to turn this audit green.

OpenSim's inverse-dynamics API includes model forces in its residual calculation:
[official implementation](https://github.com/opensim-org/opensim-core/blob/main/OpenSim/Simulation/InverseDynamicsSolver.cpp).
The numerical decomposition above is a direct local-model experiment, not an
inference from that documentation or a paleobiological torque measurement.

## Reproduction and preservation

Numerical source commit: `f11e53f`, factory branch `codex/moco-c52-walk-turn`.
Game branch: `codex/moco-c52-walk-turn-review`.
Task root: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526`.
Research: task-root `research/moco-c54-neck-profile-turn`.
Worktree: task-root `worktrees/stride-hip-visual-iteration`.
Durable evidence: principal `game/Evidence/moco-c54-neck-profile-turn`.
Unity asset: principal `game/Assets/Eonwild/MocoTurn54A/tarbo.glb`.

Use `execution.json` for exact commands and source hashes. Generation is C53's
documented procedure with the C54 turn plan and added
`--attention-profile catalog/embodiment/tarbo.v1.json`. Input walking replay stays
C52 `walk-h`; baseline is C51 `support-a/replay.json`. Their durable compressed
copies remain in C53 and C52 evidence. Unpack into a fresh research directory if
needed; never overwrite approved archives. Retarget using the v15 tail12-connected
motion set and C50 source profile, then build plain-stage `MocoTurn54A`.
Neither GLB nor callbacks from an incomplete full solve are used as physics input.

The backward deliverable in this turn is **planning only**, in
[MOCO_BACKWARD_PLAN.md](MOCO_BACKWARD_PLAN.md). The roadmap distinguishes legacy
approved reverse from not-yet-implemented Moco reverse. Review C54 before starting
another animation or silently expanding into backward turns/terrain/combat joins.
