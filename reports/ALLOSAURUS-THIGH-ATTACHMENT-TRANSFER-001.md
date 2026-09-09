# Allosaurus thigh attachment transfer 001

Status: **prepared engineering candidate; technical source-query evidence passed; emitted, visual, biological, and Unity approval pending**.

The Allosaurus walk showed a posterior upper-thigh hook during recovery. The bound semantic rig identifies the left and right hip roots as `Bone_023` and `Bone_029`; an earlier diagnostic receipt reversed those side labels, though its numeric measurements remain valid. The accepted counterfactual transfers only the existing hip-root share of vertices already co-owned by the tail-base attachment `Bone_014`, using the generic, config-owned rule `1 - (1 - destination_weight)^2`. It does not change gait timing, joint motion, topology, UVs, contact masks, or foot weights.

The final reviewed implementation is `947d9593efc837f2586806045054d0290e5ac87e` (tree `7d2a435c44c8a3f1969ba6b98f92ecbd616827b6`): implementation commit `4bdb5f15a315f27c6443a755ccb47ce42a8ac3fe` plus a config-only commit that reuses the existing v3 acquired-walk intent instead of cloning movement intent for a source revision. Both independent reviews report P0/P1/P2 zero. The integrated release candidate is `19b1e9cd6cb5ea4bb5ec009b16eee9a08dd6b7e4`.

The immutable prepared source is `25fb1dcad1d5f9b4c2fc57450c60b1f2c3d111886022b1f7a128a50605cb92b5`; the admitted source is `f1ac3ddebc2b8471af1a55439d0631ed0d350a750e59edaa661a9cd76ced4684`. Relative to the prior admitted source, only weight accessors 5 and 6 differ. Exactly 3,685 vertices change, confined to `Bone_023`, `Bone_029`, and `Bone_014`. Nodes, meshes, skins, positions, normals, UVs, indices, joints, and inverse bind matrices remain equal. Reopened neutral skin differs by at most `0.374943 µm`; raw weight-row sum drift is at most `4.25812e-8`.

The actual v4 shared motion-set entry evaluated 133 dense and event-neighborhood rows: 133 AVAILABLE, maximum target residual `0.999941 mm`, maximum extension `0.999867 mm`, and articulation envelope violation `0°`. Contact flags, touchdown/swing metadata, and solved local translations and rotations are exactly equal to the prior-source query across all 133 rows. The normalized finite sampled local rotation rate is `847.378°/s`, below the existing `1200°/s` limit; this is sampled source-query evidence, not a serialized CUBICSPLINE rate claim.

Renderers must keep two calibrated planes distinct: the query context toe-bone plane is `0.024153685443853573 m`, while the authoritative weighted-material ground is `0.00004167575454303952 m`. Five retained representative samples independently reproduce the query's calibrated worlds and normalized full-weight skin within `3.80e-15 m`.

Evidence:

- Counterfactual visual gate: `ARC/audits/allosaurus-thigh-attachment-counterfactual-41e8ef4-001/root-hip-only-review.json`, SHA-256 `6bacbb0bf520da60238228e489f9bc4271ef0b6fa0d2b8cc3ccd071234535cf8`.
- Root binary review: `ARC/audits/thigh-attachment-root-4bdb5f1/binary-review.json`, SHA-256 `51e0f85486fff8400df4fed5a96febf248757ba0a6f9b401ec0db649dc0e0634`.
- Independent reviewer 2: `ARC/audits/allosaurus-thigh-attachment-reviewer2-947d959/README.md`, SHA-256 `c610ff64f0b6f23ff023be1a7a1ca059204e2cf1c3cfe1864d63c1abe32e3983`.
- Query result: `ARC/audits/allosaurus-thigh-attachment-transfer-947d959-001/result.json`, SHA-256 `b6d161128cc582dd233fc18643930346ed924155f2964abc086ec5cd6b6615cf`.
- Independent FK/full-weight LBS check: `ARC/audits/thigh-attachment-root-4bdb5f1/reopened-query-947d959.json`, SHA-256 `a0df286663acb39f2c0d7a90ec63d82a0f98594d9c61bcdb070d02bfac25ccdd`.
- Plane authority supplement: `ARC/audits/allosaurus-thigh-attachment-transfer-947d959-004/receipt.json`, SHA-256 `0b5b32d787a48d321ce786123817b7f0edcd4b29a57be03dd4d54073ea9a876b`.
- Finite sampled-rate receipt: `ARC/audits/allosaurus-thigh-attachment-transfer-947d959-006/receipt.json`, SHA-256 `aef1af0f375b584016613c4767ccc2cdcf1005ce1478bebb56f01f0ec0241a7a`.

Evidence handling correction: the in-process `947d959-001/manifest.json` is **not valid as a whole** because it hashed `run.log` before the outer `tee` appended the final callback summary. Its other eight entries match. The immutable correction is `ARC/audits/allosaurus-thigh-attachment-transfer-947d959-integrity-correction-001/receipt.json`, SHA-256 `4cd4ef8a0557ea518bd19cd267e057e167fe0289887b8e9485097988806cc42d`. A separate `947d959-002` run completed all 133 evaluations and wrote its pose series, then failed receipt serialization on a `MappingProxy`; it is retained as partial evidence and is not presented as a successful run.

## Integrated release gate

The combined `19b1e9cd6cb5ea4bb5ec009b16eee9a08dd6b7e4` source passed 1,199 tests plus 21 subtests in 401.05 seconds (`ARC/audits/contracts-19b1e9c-root/receipt.json`, SHA-256 `e90717f61def016c39b087852fe414c37ac21610d5995e047873dfb2e084f07e`). Its actual public Allosaurus compile remains **BLOCKED** at `1.3942162162162162 s`: the left material floor did not converge. The exact trace is `ARC/audits/allosaurus-acquired-reference-release-19b1e9c-002/late-cycle-floor-trace-19b1e9c.json`, SHA-256 `fbb6629d8b946abe6a7c9f268b2dab902a969e6069b571a8a004acf6e81cb2a9`. This supersedes the earlier `.2239` exploratory blocker. Passing 133 direct source-query samples therefore remains narrower than complete export acceptance.
