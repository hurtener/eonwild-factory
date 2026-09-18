# Adult sagittal response v6

Status: **IMPROVED OVER V5; WHOLE-BODY POLISH REQUIRED.** Adult walk v6 is
the current bounded body-response review candidate. It preserves the recovered
v3 legs and v5 lateral support carrier, then adds a modest support-timed pelvis
pitch with opposing distributed upper-trunk, neck and tail response. This is
authored kinematic coordination. It does not simulate center of mass, contact
forces, inertia, or response from the animal's recorded mass.

The opt-in implementation is commit
`3e012cd0a011127716936d7cdf48edbe4a08d15d`; the v6 binding is
`7e90292c4bd92c35bd40906537371d072a4c2899`. Independent review found that
the initial hierarchy check did not bind the declared root to the pelvis.
Commit `4ea2ad2a9e2e73fdb7bfc2b0cd34445c044c1ae4` closes that P1, and the
narrow re-review is clean. The versioned recipe is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v6.json`, SHA-256
`6e82962e47485026a0a8129e68e2e9d934f1e88c102da27f181c9077788c3028`.

The authoritative post-fix package is retained outside Git at
`out/continuation-adult-v6-sagittal-body-postfix-001`. It contains one
2.46-second cycle and passes package integrity. Its retained validation records
the historical estimator's technical PASS; the independent exact exported-loop
check below is BLOCKED. Its principal hashes are:

- manifest: `5c745c9b15fb43ae2a12d18e37957a6fd6fe50ea73cd8dcfaf2b768ff77d3041`
- root-motion GLB: `4a2c3587d932a8c8bab002b9e536f1ed22a28388e928cbe18fe8845b553e7e7b`
- in-place GLB: `2878670fbeacfd7e99014e8a75537d5711deea5ceafc96362b5fbc545a63aa0b`
- plan: `564f28d2aa1f9246581df500c55a7e5d00582a8d15b07b46b607b73364cd9c9b`
- solver receipt: `9502763e1c1b324f66df931ffcdab1d8be8c8a33bedb978efd5961624d044d6a`
- validation: `471e28a81d45e461581fc61783a0976c5e3e8a84d9e2366a07ae406388487105`
- runtime: `a7d520bd7233d23d7a9fbed69fdf1ea08dc71a090e3cecdee1496e102cb22e42`
- input lock: `f47bb451cb9a667cf36a1e53c05e0345b0745df060a9a019f812532710a49af9`

The reopened audit found all 297 authored samples equal to v5 after excluding
compiler-owned skin-refinement offsets. Local translations and scales are
unchanged. Final full-patch interior-swing clearance is 35.214 mm left and
40.603 mm right, with no penetration or hard-articulation violation. Head
attention changes by less than 0.00001 degree. `reopened-audit.json` is the
root-reproduced quantitative record, SHA-256
`4d57a160c1749f9a0ec20fdb1b9bca130a5dafb2765695b406cbe6ce3ad2b9eb`.
The rendered pre-fix package and fixed-source package have byte-identical
motion payloads; only their source-locking metadata differs. The host
equivalence receipt has SHA-256
`d8690e9cac15eb8f39477ab017a1a2170160a8fa9cdd3ad699d1d60c94f3f2d8`.

The host inspected all 370 rendered frames across five native-time views and
completed five paired v5/v6 native-speed playbacks. The added pitch makes the
pelvis, trunk, neck and tail response less rigid without losing the recovered
leg direction, clearance, restrained lateral transfer or gaze. Constant
forward travel and body effort still read too even. `host-review.json`,
SHA-256 `f64aba1fcfe95d564efba84066c6dd7dbfbd0d8b81607e2516c070153db2b6c0`,
therefore records `WHOLE_BODY_POLISH_REQUIRED`, with Unity parity not run and
production approval false.

The exact integration head
`30f434ce914b6392f1438f0ff234718c82d2e985` passed 749 tests plus 21
subtests in 502.90 seconds with real Blender 5.2.0 and Khronos glTF Validator
2.0.0-dev.3.10. `host-validation.json` records the clean checkout, command,
toolchain, log and JUnit hashes.

The package's recorded continuity PASS is the compiler's existing quadratic
finite-difference estimator. An independent direct-accessor evaluation of the
emitted LINEAR/SLERP loop measures 1.728740 mm/s linear mismatch against the
1 mm/s limit and 3.410360 degrees/second angular mismatch against the 10
degrees/second limit in both GLBs. `host-exact-continuity-status.json`, SHA-256
`45bad61e5b3628e968b8af303f31781d4ffcc0b27c1edb0ad42735aa6da4ae53`,
therefore records current exact local-loop status **BLOCKED**. The reviewed
validator is integrated at source
`61c7ffc99ac2c5166345c5b690328c55bce2aefd`, which passed 758 tests plus
21 subtests in 211.81 seconds. `exact-head-validation.json` is that clean
real-tool receipt. The motion remains blocked; this report makes no exact
runtime C1 claim. See the
[exact tangent report](../V9-EXACT-EMITTED-TANGENT-001/README.md).
