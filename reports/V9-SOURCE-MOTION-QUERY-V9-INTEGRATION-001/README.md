# SourceMotionQuery and adult V9 integration

This integration combines the closed adult axial-clock and neutral-jaw V9 publication head with the closed `SourceMotionQuery` extraction. Its exact merge head is `ae25a5106b378773e991a168c8883e33e2c44ab7`, with parents `9f6e93f0ac1a06e3a3d6c121c99ef84ae4cd7830` and `b31bcf655d72883d98e899e70f86213d3cec9730`.

`SourceMotionQuery` exposes deterministic solved pose rows under the admitted source, plan and event contracts. This stage does not claim arbitrary-time evaluation, continuous source derivatives, a new emitter, new gait acceptance, native playback, Unity parity or production approval. It adds no canonical support-anchor provider.

## Closed integration review

Both narrow compatibility reviews are clean with no P0, P1 or concrete local P2 finding:

- [root review](review-root.md), SHA-256 `0df933e4a4eef95c80293a6b425910a3bac2b8739da5759963effe0989b8fb5b`
- [independent review](review-independent.md), SHA-256 `c696cec4fccb87396408e63830bcc0363edc8b58eb920016642e56d6260b532f`

The reviewers confirmed the extracted final context owns the neutral-jaw fields and one source admission, while query construction preserves detached state, source identity and mutation isolation. `solve_airborne_plan_sample` remains AST-identical to the closed adult source. The known huge-integer error-type P2 remains follow-up debt from the closed query stage.

## Adult V9 preservation

The independently generated [byte-parity receipt](adult-v9-byte-parity.json), SHA-256 `6af8bc37a724e711475dde092b476c3ebc967e2613f217402a25bea3cd0d73f7`, proves that compiling the V9 recipe/input binding with the integrated query source leaves both full GLBs, plan, solver receipt, validation and runtime metadata byte-identical to the retained `2c5dc91` V9 package. No rerender is needed. The candidate’s existing exact LINEAR loop `BLOCKED` status and native-playback `PENDING` status remain unchanged.

## Final suite

The [persisted suite receipt](full-suite-receipt.json), SHA-256 `b6671e47ad8c1055df5c464ab34ea93a47692cf601c61b407e1f1192bb2508e7`, records 907 tests plus 21 subtests, with zero failures, errors or skips in 292.68 seconds at exact union `ae25a510`. The suite used Python 3.12.10, pytest 9.1.1, Blender 5.2.0 LTS and Khronos glTF Validator 2.0.0-dev.3.10 from the paths recorded in the receipt. Raw pytest output and JUnit XML remain on external SSD at their recorded paths and hashes.

An earlier invocation executed zero tests because the newly created virtual environment lacked pytest; its wrapper then encountered zsh’s reserved `status` variable. The receipt preserves that output as an environment setup failure, not a test or code failure. After installing the lockfile-defined test dependency group, the single complete final suite above passed.
