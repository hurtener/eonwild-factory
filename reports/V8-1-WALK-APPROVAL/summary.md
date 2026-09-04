# V8.1 approved walk — iteration 38 promotion

Status: **COMPLETE — durable walk-only base snapshot created; no commit/push.**

The user-approved iteration-38 walk is now frozen at
`procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/`.
The package-level pointer
`approved_snapshots/APPROVED_WALK_BASE.json` declares it the V8.2 walk input.
`validated_result/v8.1/` remains a separate, untouched accepted full-package
release; this promotion does not approve unrelated clips.

## Frozen artifacts

- Walk GLB: `asset/tarbosaurus_procedural_v8_1_walk_iteration_38.glb`
  - SHA-256: `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`
- Review MP4: `media/walk-relaxed-v8-1-iteration-38-side.mp4`
  - SHA-256: `8ef3d2c571e2ee317a431a66f8a031fabe53936d6bf256e9c091a9071ef48a20`
  - H.264, 960x540, 24 fps, 240 frames, exactly 10.000 seconds.
- Frozen candidate resolved profile, phase overlay, animation manifest,
  generation report, base validator, authoritative validator, render metadata,
  and exact generator/validator/renderer source copies are listed in
  `APPROVAL_MANIFEST.json`.

## Validation and boundaries

- Snapshot hash verifier: PASS (`14` internal files, `13` external lineage
  sources).
- Authoritative validator rerun against the snapshot GLB: PASS for all six
  checks: immutable V8.1, all-key ground/support/joints, physical stride/speed,
  derived reach, bilateral causal rocker, and dense distal toe lock.
- Physical base: 12 m reference scale; stride `2.59999997 m`; speed
  `4.59999986 km/h`; hip height `2.75636 m`.
- Package inventory regenerated with the existing writer and verifier: `301`
  files pass checksum validation.
- Comparison against the pre-promotion inventory: all `285` pre-existing
  manifested contents are unchanged; no pre-existing entry was removed. The
  only additions are the `16` pointer/snapshot records.

## Exact package inventory state

- Pre-promotion package inventory SHA-256:
  `965a509f52043d37817754fa119c7fdc03223c4273b9adfaf2eb7408256d7c17`.
- Current regenerated inventory SHA-256:
  `9baab73e361b7f1cd24261593cb28849e9818e10f7f11bdc39db7ed8f79b0bcc`.
- Current checksum list SHA-256:
  `e9f3089b26828ff8ba593c4566a4e1f5a7e0eb56e8109224592395204d940e68`.
- Accepted V8.1 source GLB / canonical profile / full-release GLB retain:
  `fbb42c2edad4eadebbcf808d32028d7c73b3fbfd6172610eddd5df84990a65c7`,
  `f128bd39cca62a674855ffbcce2e88226cec3b17048bf9a830bd158238240143`, and
  `ba321da21c20fce9fc2192efbcc40ae192303b06c2ccb856e0b8d7edeba2cc8a`.

Reproduction and verification instructions are at
`approved_snapshots/v8.1-walk-iteration-38/reproduction/commands.md`.
