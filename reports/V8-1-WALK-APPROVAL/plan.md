# V8.1 approved walk — iteration 38 snapshot plan

## Scope

Promote the user-approved, walk-only respin-2 iteration 38 into an additive,
immutable V8.1 movement snapshot. It becomes the approved walk base for later
V8.2 work; it does **not** replace or modify `validated_result/v8.1/`, any
accepted V8.1 GLB, or quarantined prior iterations.

## Source lock

- Candidate GLB: `candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb`
  - SHA-256 `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`
- Approval MP4: `showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4`
  - SHA-256 `8ef3d2c571e2ee317a431a66f8a031fabe53936d6bf256e9c091a9071ef48a20`
- Candidate resolved profile SHA-256 `eefc0c8ef7fd571c9f298cfce346a8af51106f37ef370c17d020b073ca8998d4`.
- Candidate overlay SHA-256 `3d5a56b183abc710dc0f73518bc4d3cfbc8569a3a5248fb15f4b17406c4addff`.
- Authoritative validator status is `PASS`; accepted V8.1 source GLB and
  canonical profile hashes remain `fbb42c2edad4eadebbcf808d32028d7c73b3fbfd6172610eddd5df84990a65c7`
  and `f128bd39cca62a674855ffbcce2e88226cec3b17048bf9a830bd158238240143`.

## Intended files and ownership

The factory has no local ownership config. The governing Eonwild config assigns
reports to the task owner; the parent integration handoff explicitly authorizes
the following additive package snapshot paths.

- `reports/V8-1-WALK-APPROVAL/**` — task-owned plan, summary, and checks.
- `procedural-animation-toolkit(v8.1)/approved_snapshots/APPROVED_WALK_BASE.json`
  — package-level machine-readable selector.
- `procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/**`
  — immutable GLB, config, evidence, media, provenance, script copies, and
  snapshot verifier.
- `procedural-animation-toolkit(v8.1)/PACKAGE_MANIFEST_V8_1.json` and
  `SHA256SUMS_V8_1.txt` — regenerated only by the package's existing
  `scripts/write_package_manifest_v8_1.py` tool.

No file under `validated_result/v8.1/`, `showcase/v8.1/`, candidate history,
or any quarantined iteration is a promotion target.

## Snapshot layout

```text
approved_snapshots/
  APPROVED_WALK_BASE.json
  v8.1-walk-iteration-38/
    asset/tarbosaurus_procedural_v8_1_walk_iteration_38.glb
    config/resolved-profile-v8.1-walk-iteration-38.json
    config/profile-overlay-v8.1-walk-iteration-38.json
    evidence/{animation-manifest,generation-report,base-validation,authoritative-validation}.json
    media/{walk-relaxed-v8-1-respin-side.mp4,render-run.json}
    reproduction/{generate,validate,render}_walk_respin_2.py
    reproduction/{commands.md,verify_snapshot.py}
    APPROVAL_MANIFEST.json
```

## Acceptance checks

1. Snapshot copies hash byte-for-byte to the approved iteration-38 artifacts.
2. `APPROVAL_MANIFEST.json` records all internal files, source lineage,
   user-approval intent, 12 m reference scale, stride, speed, tool versions,
   and exact reproduction commands.
3. Snapshot verifier fail-closes on missing or mismatched files.
4. `scripts/write_package_manifest_v8_1.py` regenerates the inventory, and
   `scripts/verify_package_v8_1.sh` verifies the package sums/manifest.
5. The pre-existing `validated_result/v8.1` tree, original package files, and
   quarantined media retain their pre-promotion hashes; only the additive
   snapshot and manifest inventory files change.
6. The stored approval MP4 remains one H.264 960x540, 24 fps, 240-frame,
   10.000-second review clip.

## Assumptions

- “Approved” applies only to the relaxed walk base, not the full 47-clip V8.1
  package or unrelated power-attack findings.
- The snapshot intentionally keeps a copy of the tiny review MP4 so future
  V8.2 work does not depend on a mutable showcase path.
- Copied generator/validator/render scripts are immutable source records. Their
  exact original repo locations and hashes are included so reruns fail closed
  if future live candidate scripts diverge.

## Completion

All acceptance checks passed. The snapshot verifier checked 14 internal files
and 13 lineage paths; the authoritative validator reran against the copied GLB
with status `PASS`; package inventory verification passed at 301 entries; and
the pre-promotion 285-entry inventory comparison found zero changed or removed
pre-existing package files. No commit or push was made.
