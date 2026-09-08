# Adult fast-walk recovery v3

Status: **RECOVERY IMPROVED; WHOLE-BODY POLISH REQUIRED.** This candidate
preserves the 1.6-second cycle, 0.6-body-height stride, duty factor, clearance,
world-metatarsus target and adult articulation guardrails. It selects an opt-in
rate-limited C2 recovery carrier after release-only timing moved the foot-pitch
rate witness between the onset and return branches.

The reusable implementation is
`f53782e060d38554879cbd25a65d0d62c72d44f4`; test-only cleanup is
`0955fc867fcf70383613d67f984baf4a92c4d6e0`. Both independent bounded
reviews are clean. The recipe is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-fast-walk-recovery.v3.json`,
SHA-256 `809ad959c7cd335daaecb7990099d9a4f0d503e77448a49cd1c383ecd9012f5c`.

The frozen package at
`out/tarbosaurus-adult-fast-walk-recovery-v3-f53782e` passes package integrity.
Its retained validation records the historical estimator's technical PASS; the
independent exact exported-loop check below is BLOCKED. Its principal hashes are:

- manifest: `4d3eca7ef8933661baed623ffef59119d9348c740cb8906bd31e6efb3784b900`
- root-motion GLB: `4416c91ea3629f638949139c5c7a9c1d1e0ed062b518822d024dbd313670e2a7`
- in-place GLB: `0215d73f22f45e1897afa8d6336caea8bd2072a57679e63e05ce735fe32717cf`
- plan: `675a303e10421ed9f8ee0d69df0898c8c40d0ad36726b0308ed1f3433b93c206`
- solver receipt: `16dd97bc8ca656ab13ac02a9956525fa76d7c677a47ca4bf3d56bc7889762d6a`
- validation: `6c68095a2056a15b074d1580b33bc8132f583b3d1e48d73afbbe70318695dd0c`
- runtime: `ee3cc22c438114c72e3fa0ae356df42ce6a8008cbd4667d0a324f2e6a7f118d2`
- input lock: `a93636f2e4a96bdfef562e9716a3c71409eb9f27df4b38c8d7567154e6268199`

Solved foot pitch peaks at 575.599 degrees/second under the unchanged 600
limit; global serialized rotation peaks at 972.710 degrees/second under the
unchanged 1200 limit. Extension and hard-articulation violations are zero, and
final skinned contact passes.

The host inspected all 192 frames across four native-time views and completed
all four native-speed playbacks. Recovery keeps the intended extended distal
direction and coordinated pad/toe motion without the earlier pinched ankle,
mid-recovery floor skim or lateral crossing. The older body profile remains
level and even, so `host-review.json`, SHA-256
`3b2f3adc4d998315d733d9efbce2ee07357780675b032a96910a42298282ab46`,
records `WHOLE_BODY_POLISH_REQUIRED`. It does not grant biological, Unity or
production approval.

The combined exact integration head
`30f434ce914b6392f1438f0ff234718c82d2e985` passed 749 tests plus 21
subtests in 502.90 seconds with the pinned real tools. Its recorded continuity
status uses the quadratic finite-difference estimator. An independent
direct-accessor evaluation of the emitted LINEAR/SLERP loop measures 5.406219
mm/s linear mismatch against the 1 mm/s limit and 6.683922 degrees/second
angular mismatch against the 10 degrees/second limit in both GLBs.
`host-exact-continuity-status.json`, SHA-256
`b7b63c3e4849d9ed0f880b309d4b2a57eb4cc7df559f8b5844464d9faaf49f74`,
therefore records current exact local-loop status **BLOCKED**. The reviewed
evaluator correction is not included in this head.
