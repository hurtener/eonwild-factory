# V9 adult axial clock and neutral jaw candidate

This candidate combines two closed, opt-in behavior stages on the recovered V8 bind geometry. `support_timed_axial_carrier` coordinates pelvis yaw, chest counteryaw and centered-tail yaw from declared grounded support events. The neutral-jaw calibration applies a constant authored closure in the admitted jaw-local hinge frame and composes the existing breathing motion exactly once. The V9 binding preserves V8 gait, legs, contacts, articulation, root travel and configured amplitudes.

These are authored kinematics. They are not a COM, mass, inertia, force, work, muscle-effort or biological model. The `50.03933635803102 degree` jaw closure and `0.0015` body-height surface-gap target are engineering calibration, not tooth contact. The factory remains V9; the recipe version is `tarbosaurus-pin-552-1-adult-walk.v9`.

## Frozen source and inputs

The reviewed integration source is `2c5dc911d15e60b4a37a0d6b9248fa547168672b`.

- recipe SHA-256: `f55da91847dc63489f9655cfc3641bee665bf8ce6122755a61748d98fabf3ccd`
- performance SHA-256: `e133819dddf19bd224ddec7419687208e01abf8f3906fa147837813710dc2dfc`
- recovered source geometry SHA-256: `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`
- package manifest SHA-256: `1b89ef55a89be040e12eb714ee391f31c5fca8f4b896bbe722e1eb26d5872b83`
- root-motion GLB SHA-256: `db5b2123e156fa218cc426cf8774972a8c02f9cfce7eea9c80fcf91a8c129ebe`
- in-place GLB SHA-256: `5a16382521ebf06e73662b37d53151048df5c7f430b776fb7950d2c480abec51`

The immutable package remains outside Git at `out/continuation-adult-v9-axial-jaw-001`. This report does not duplicate GLBs, frames or videos.

## Verification

Both binding reviews are clean with no P0, P1 or P2 finding: [root review](review-binding-root.md), SHA-256 `e30875a7dd9ceaf74ba7f5121223ed028ccdc6c31db233eb790df571ff53483e`, and [independent review](review-binding-independent.md), SHA-256 `484d36c77bd5bb5cc48cece3f6bfb0b94fe8d551c1c0d74c0ac3ce3da0230491`.

The persisted [full-suite receipt](full-suite-receipt.json), SHA-256 `a7bf61a02d1f1207d1713dd79a5f021dc8c0713bfece0da92ffbd1badc751838`, records 896 tests plus 21 subtests, with zero failures, errors or skips in 385.56 seconds at exact source `2c5dc91`. The raw external pytest log and JUnit XML are retained at the paths and hashes in that receipt. A prior 896-test observation took 449.48 seconds but had no persisted log and is classified only as observed tool output.

Real Blender 5.2 was exercised by the suite. The reopened Khronos glTF Validator 2.0.0-dev.3.10 reports contain zero errors and four existing warnings for both [root motion](gltf-validator-root-motion.json), SHA-256 `f8efdc4d79d7cc9c9fd82ee2db9c220793d0958789eafbbaf5f135cbde49d832`, and [in place](gltf-validator-in-place.json), SHA-256 `2635f49656fbc5ed22682df6da41d9a55e4c511e1517c80b3c7359312275f695`.

The reopened [technical summary](technical-summary.json), SHA-256 `ad3b469c3fd8b039fa9a4c4e20662d9270c765a0b73e3400088f4b85d7a4e701`, confirms contact, articulation, output and rotation-rate gates pass in both modes. Exact serialized local-channel cyclic continuity remains **BLOCKED**: LINEAR translation mismatch is `0.00323101227406632 m/s` against the unchanged `0.001 m/s` limit. Angular mismatch is `2.2502600720859265 deg/s` against `10 deg/s`. No threshold changed.

The [emitted jaw audit](emitted-jaw-audit.json), SHA-256 `12e9fa8c27663a751cadb4b90bb3f19b5bf427915c7a7794f0a8bf9748730e13`, reopens all 297 keys in both modes. Every non-jaw local channel and key time is byte-identical to the closed body-only diagnostic. All 72 bound jaw vertices retain at least `3.426269 mm` of head-carried clearance. A world-up bin gap may become negative under head pitch and is retained as a descriptive value, not treated as a collision metric.

The [axial body measurements](axial-body-measurements.json), SHA-256 `40b8f4b41f54a642acbe9d54b411eff607e16c31d99c24cdfb10b46739538f7a`, and [body still review](axial-body-still-review.json), SHA-256 `aad91627466da0e09ee5aecc572fa62b5389662552200b00c44906ff80914141`, preserve the body-only lateral diagnostics. Their surface and volume summaries are geometry proxies, not mass distribution, balance or force evidence.

## Visual boundary

The host [frame review](host-frame-review.json), SHA-256 `e97fdad9c24623802ca0429e47b6bbac4f2bbbe6ceb38fc10b15bd4179caf4c0`, covers all 370 rendered frames across five locked cameras, 25 contact sheets and five full-resolution critical frames. The [render audit](render-audit.json), SHA-256 `5ba764afbfd6d0ed198e4a6395a2023a6bb19ade042b56608035d0e5bf6b4d81`, binds that media to this package. The review found the bilateral recovery and support-timed chest carriage visible, with no gross mesh rupture, limb collapse or adjacent-frame body jump.

The external V8/V9 [comparison page receipt](comparison-index-receipt.json), SHA-256 `e5861a024a7ecc3a5c976acf940edb0a423d8b9202a1fa9e1bab42c15098e801`, records ten HTTP-verified films, real render times, locked camera identity, paired playback and frame stepping.

Native-speed playback remains `PENDING_MAC_UI_LOCK`, so perceived weight is not accepted. Unity import validation is `NOT_RUN`. This candidate has no production or biological approval.
