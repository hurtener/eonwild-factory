# Adult recovered-bind geometry diagnostic V8

Status: **CANDIDATE / TECHNICAL BLOCKED / VISUAL PENDING / UNITY NOT RUN / NOT PRODUCTION APPROVED**

This bounded candidate tests one geometry-admission change. It recovers the original skin-aligned joint worlds from `W_mesh * inverse(inverseBindMatrix)`, projects each parent-relative transform to bounded TRS, reopens the emitted source, and verifies both joint worlds and every weighted skin vertex. It then runs the unchanged V7 gait, timing, performance, articulation limits, contact thresholds, and root authority on that newly admitted geometry. It does not adjust gait amplitudes to imitate V7.

## Frozen identities

- Base: `cc7b3d9e199d1679d28bbcbefb61bcea5407b129`
- Recovery implementation and focused production-shaped tests: `0a6ca91`
- Frozen source, calibration, contact binding, recipe, and catalog tests: `7d3945b7083c1e04dbf360e852d401e29d3e98fa`
- Input source: `044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6`
- Recovered source: `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`
- Immutable package: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/out/continuation-adult-v8-bind-pose-001`
- Package manifest SHA-256: `a8b5b1d82b98d6e3579e4aec2e2ac15eec3f0baa9c0cb42ea4ff734dc15b88d3`

The original binary buffer and inverse-bind accessor bytes are preserved. Animation tracks are not read and the admitted output contains zero animations. The generic API requires an explicit skin index and explicit orthogonal forward/up axes; it does not infer a species or bone convention.

## Admission and static source evidence

The adult input stays within all strict projection and reopened-reconstruction limits:

| Measure | Result | Limit |
|---|---:|---:|
| Input normalized orthogonality | `2.27805e-7` | `1e-6` |
| Parent-local TRS projection | `1.26457e-7` | `1e-6` |
| Reopened world-matrix element error | `5.27842e-7` | `2e-6` |
| Reopened weighted-skin position | `1.13533e-6 m` | `3e-6 m` |

The independent source inspection measured all 59,169 vertices, a maximum bilateral semantic-leg landmark residual of `0.445053 µm`, and explicit `+Z` forward evidence from the bilateral X plane and rostral head-tail geometry. Its independent Blender 5.2 import found `3.01989 µm` maximum and `0.698223 µm` RMS same-index skin difference from factory FK/LBS. All four static views were inspected: the skeleton remains inside the body/leg silhouettes with no obvious rupture or inversion. This is static import evidence; walking deformation remains pending.

The recovered bind jaw is visibly wide open. Its world rotation differs from the historical animation-free snapshot by `51.666°`; the unchanged performance profile adds no jaw delta. This is an explicit visual finding, not a recovery failure. A behavior-owned jaw closure would be a separate calibration and is absent here.

The contact v10 ground is the measured recovered-source skin floor `8.663434924195463e-8 m`, scaled with the locked animal geometry to `7.44670325699803e-8 m` before solving. Mask and threshold values are unchanged from v9. This is source calibration, not a post-solve floor adjustment.

## Candidate comparison

Correcting the neutral geometry changes body-height-derived world quantities even though every dimensionless gait/performance value remains unchanged:

| Measure | V7 historical package | V8 recovered-bind |
|---|---:|---:|
| Derived body height | `2.270663282 m` | `2.284175584 m` |
| Step length | `1.362397969 m` | `1.370505350 m` |
| Mean root speed | `1.107640625 m/s` | `1.114231992 m/s` |
| Same-foot cycle travel | `2.724795938 m` | `2.741010701 m` |
| Planned swing clearance | `0.499545922 m` | `0.502518628 m` |
| Pelvis vertical velocity range | `±0.092760797 m/s` | `±0.093312800 m/s` |
| Neutral rostral elevation | `-25.252391°` | `-30.766081°` |
| Locked/scaled ground | `-0.010315559 m` | `0.000000074 m` |

The requested gaze offset remains `+3°`. Reopened V8 checks pass for both exports: contact (`0` penetration; maximum stance gap `0.130629 mm`), solver feasibility (maximum foot-target residual `0.481333 µm`; no unreachable extension), articulation (zero hard-envelope violation), swing-clearance refinement (zero recorded error), and planted distal material velocity (`0.054303 mm/s`). Maximum solved foot-pitch rate is `284.906°/s` under the unchanged `600°/s` engineering limit.

The published mass (`2816.3 kg`), hindlimb length (`2.415 m`), and study hip-height proxy (`1.932 m`) remain declared inputs with their original citations. Their correspondence to this recovered mesh is explicitly unvalidated. The output is not a COM, force, tissue-density, mass-distribution, or biological validation.

## Honest blocker

The current exact serialized local-channel evaluator rejects both V8 modes on the unchanged `1 mm/s` linear tangent limit: `3.231012 mm/s` at `Bone_001`. Angular closure is `2.240155°/s`, below `10°/s`. All other current package gates pass. The historical V7 package recorded `TECHNICAL PASS` before this exact evaluator existed; its current companion evaluation is also blocked (`3.211645 mm/s` linear). The statuses are not directly interchangeable.

## Verification

- `13 passed`: bind recovery, adult catalog binding, and factory admission focused tests.
- Ruff and `git diff --check`: pass.
- Package verifier: integrity `PASS`; technical `BLOCKED`; visual `PENDING`; Unity `NOT_RUN`; production approval `false`.
- Static Blender import review: complete; native walking review remains pending with the host.

Evidence files:

- `admission.json` SHA-256 `3f50f1de1021c08229e0b611d692779208aaaddf4eeebdbc2c76382bc3154007`
- `source-inspection.json` SHA-256 `223406b27be2010e0eed6193dad9dd19b04c543f1e3feecec20bf0b71f862e1a`
- `host-static-import-review.json` SHA-256 `4e4463661c0e249307b1861df900f2a363a5225d635192dd1e45c8934041c2ce`
- `comparison.json` SHA-256 `f699b26e7f3441f44f86ce9229c92f5bc6643e103c7ce08484efab80d8f94e92`
- `v7-host-exact-continuity-status.json` SHA-256 `1e2e7bc13746b0af232a764c00cd905c90aa09791ff71ae9ea270e3b663483be`
