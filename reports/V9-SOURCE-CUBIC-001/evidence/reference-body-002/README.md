# Adult V10 reference-body phase audit 002

Status: **corrected bounded image-space evidence; no motion or camera change**.

This supersedes `adult-v10-reference-body-001` for reference-tail measurements. The first audit added fixed color thresholds to `uint8` channels, allowing wraparound. Audit 002 promotes RGB channels to signed `int16` before thresholding, retains all 55 audited frames from 60 through 114, and reports extrema over that complete interval. The original driver and result remain preserved.

## Frozen identities

- Source head: `94c81e7e3bb00e2e6057fd1babb183adb70ff9e3`.
- Authored reference: `assets/examples/tarbosaurus/Tarbosaurus#walk_side_v02.mp4`, SHA-256 `7f981e34a38955b44df799069693c57a5b5c881083ae4cbd62419e5cdc7d3ea5`.
- V9 manifest/root-motion GLB: `1b89ef55a89be040e12eb714ee391f31c5fca8f4b896bbe722e1eb26d5872b83` / `db5b2123e156fa218cc426cf8774972a8c02f9cfce7eea9c80fcf91a8c129ebe`.
- V10 manifest/root-motion GLB: `e3e9923526ced4e2fd08b5f4ffaa455edb78ce66020c3c3f369e6336d5f0aff7` / `32048baac7ab944cf954bf80aba51c9582c465d6c965a24cf3fb006a3f0a6212`.
- Corrected driver: `analyze.py`, SHA-256 `3252e2e79fcb1ff66482ac7c413dfa064ebdf0708e9bb1fd858eb31ad405775e`.
- Corrected result: `result.json`, SHA-256 `31d72d012d09147fbb631e0ba7ce2c61d37ea4baf2a3b49fbcce40f845c720a3`.
- Superseded result: SHA-256 `628f2bdf1f197e6b4b5f7ffb7a2de93f5afce76cc6d6d122e10e790fd609ce0d`.

## Correction outcome

The corrected mask changes distal-tail points at frames 68, 75, 88, 93, 96, 98, 105 and 106. None of the nine previously selected landmark frames changes, but frame 80's 25-pixel image-down displacement is only the largest selected-landmark value. Across all 55 frames, the corrected distal-tail silhouette maximum is 39 pixels image-down at frame 76 (3.1667 s); its minimum is 20 pixels image-up at frame 66 (2.7500 s).

The full surface traces refine the phase interpretation:

- Chest reaches its 13-pixel image-down plateau over frames 69–73, spanning late apparent load acceptance into early labelled midstance.
- Proximal tail reaches its 14-pixel image-down plateau over frames 69–71.
- Distal-tail silhouette reaches its 39-pixel image-down maximum at frame 76, three frames after the chest plateau ends and five after the proximal-tail plateau ends.
- Pelvis surface reaches its separate 12-pixel image-down plateau at frames 89–91. Its non-monotonic projected trace does not support assigning the factory pelvis carrier an exact phase from this clip.

The delayed distal silhouette is consistent with qualitative tail lag, but it is not a measured joint phase. Surface texture motion, silhouette curl, perspective, and manual event labels limit the timing precision. Pixels are not metres, surface landmarks are not anatomical joints, and neither pelvis nor image-space motion is a center-of-mass, force, or stability measurement.

## Decision

The correction does not justify another amplitude sweep or a new tail/body law. It weakens the earlier prose from a simple whole-torso yield/recovery claim to a bounded observation: chest and proximal-tail surfaces descend around apparent load acceptance, the distal-tail silhouette peaks later, and the pelvis surface has a later secondary maximum. V9/V10 emitted timing remains directionally compatible with part of that sequence, while exact reference-to-factory phase alignment remains unresolved.

The shallow 3.5-degree V9/V10 review media remain unchanged. Root inspected all 148 frames and retained the visible floor/support relationship. Live control verification of that new page is `NOT_RUN_POLICY_BLOCKED` because the authorized Chrome surface was closed and the subsequent loopback tab was denied by enforced browser policy; no alternate browser route was attempted. Existing original-page controls had been verified previously.
