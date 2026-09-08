# Final integrity review — `3219d65d66f4408e1eaf05d4eccec39409b474e1`

Reviewed against base `712708652b1035526b38d06fa7d487fe3c919117`.

## Finding

### P1 — verifier accepts a package whose own manifest falsely grants approval

`verify_package` checks the manifest schema, inventory and technical status, then
`require_metadata` checks only the manifest's recipe id and version. Neither
path requires the manifest to remain a candidate, `production_approved: false`,
or its physical/scientific/biological claims to remain false. The verifier then
returns a hard-coded `production_approved: false`, which does not detect or
correct a contradictory claim already present in the package manifest.

Trigger: copy a valid candidate package and change only `manifest.json` to set
`status` to an approved value and `production_approved` (or a claim flag) to
`true`. `manifest.json` is deliberately outside `manifest.files`, so all listed
file hashes remain valid. `verify_package` still reaches `integrity: PASS`, while
the package's manifest is now an untruthful approval artifact. A downstream
consumer that reads the manifest rather than the Python return object can accept
the false claim.

Evidence:

- The compiler emits the intended invariant at
  `src/eonwild_motion/factory/compiler.py:353-356`.
- `verify_package` only verifies schema/inventory/technical-status at
  `src/eonwild_motion/factory/compiler.py:370-386` and returns a hard-coded
  false flag at `:421-424`.
- `require_metadata` begins its manifest checks with id/version only at
  `src/eonwild_motion/factory/metadata.py:21-35`; it has no approval/status/
  claims invariant.
- `tests/test_package_metadata.py:42-75` exercises rehashed contradictory
  metadata, but does not cover these manifest approval fields.

This is reachable corruption of a candidate's user-facing provenance and breaks
the repository's no-auto-approval/fail-closed rule. Require the fixed candidate
status, false approval and false claim flags during package verification, with a
rehashed-manifest regression test.

## Checks with no additional actionable finding

- The `3219d65` FBX endpoint repair uses a power-of-two bake interval in
  `tools/preview_clock.py:51-64`; the new pinned real-Blender test covers both
  `0..295.20001220703125` and `3.5..153.75`, reopens the FBX and samples start,
  middle and endpoint poses. It passed locally: `1 passed`.
- The clock unit tests passed locally: `9 passed`.
- CI's macOS contracts job runs the complete suite with Blender and the genuine
  glTF validator (`.github/workflows/factory-baseline.yml:14-42`). Native review
  remains distinct, preserves the same recipe/view matrix, and changes only its
  timeout from 40 to 90 minutes (`:64-114`).
- `out/continuation-adult-v3-world-recovery-001/package` verified with the
  factory verifier. All 11 manifest file hashes matched; manifest SHA-256 is
  `8a6fb8ad6ae06acc2f2150804e3c7658ffea6813bc52c9e18b6b141f10ed1ff3`.
  Its recorded visual state remains `PENDING`, Unity `NOT_RUN`, and production
  approval false.
- The legacy V8.2 tree is byte-identical at base and reviewed head (identical
  recursive tree digest `0d05accfd8d51cc48d401162ad677cfda3aba1e17a8387babb6b12137e9f0251`);
  no baseline-approved-take diff was found.

## Limits retained

This review did not rerun the root agent's full suite or candidate-pair jobs.
The known blocked sprint direct joins, pending visual approval, absent Unity
parity and lack of biological approval are correctly recorded limitations, not
new defects from this review.
