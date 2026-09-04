# V8.2 Candidate-A iteration-g technical review

## Verdict

**PASS with P2 evidence-hardening debt. P0 = 0, P1 = 0, P2 = 2.**

This review is pinned to the filesystem release candidate at SHA-256
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
The candidate reproduced byte-for-byte from the recorded iteration-b input and
gain, the official Candidate-A gate passed with enforcement enabled, and the
structural/mechanical validator reproduced its checked-in report exactly.

## Exact release identity and reproduction

- Approved V8.1 snapshot GLB:
  `procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/asset/tarbosaurus_procedural_v8_1_walk_iteration_38.glb`
  - actual and declared SHA-256:
    `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`
- Iteration-b input:
  `candidates/v8.2-balance-transfer/generated/iteration-b/tarbosaurus_procedural_v8_2_balance_transfer.glb`
  - actual and recorded SHA-256:
    `bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2`
- Iteration-g candidate:
  `candidates/v8.2-balance-transfer/generated/iteration-g-official-chest-solver/tarbosaurus_v8_2_balance_transfer.glb`
  - actual and recorded SHA-256:
    `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`

Independent reproduction used Blender 5.2's Python runtime and
`apply_official_chest_solver.py` with gain `0.3984375`, writing only to a
temporary directory. The reproduced GLB was byte-identical to the release
candidate (`cmp` exit 0 and the same SHA-256). The independently regenerated
`official-balance.json` and `structural-mechanical.json` were also byte-identical
to the checked-in evidence.

## Official Candidate-A gate

The evaluator was rerun with both
`--gate-mode candidate-a-upper-only` and `--enforce-gate`; it exited 0.

- Frozen baseline reproduction: PASS.
  - maximum absolute metric delta: `7.272973832073149e-07`
  - tolerance: `2e-05`
- Candidate-A gate: PASS; every named check is true.
  - pelvis exact to approved
  - protected lower-leg envelope exact
  - chest roll safe improvement and counterphase
  - chest pitch/yaw preservation bounds
  - head world caps
  - tail yaw improvement and monotonic base-to-tip phase
  - exact seam
- Official candidate measurements:
  - chest pitch/yaw/roll P2P: `4.081644890 / 2.647963386 / 5.617932749` degrees
  - head world pitch/yaw/roll P2P: `2.580076144 / 1.528822058 / 0.966136994` degrees
  - tail base/mid/tip yaw P2P: `5.587140000 / 18.718185630 / 22.991999383` degrees
  - loop seam: `0 m` translation and `2.414836539e-06` degrees rotation

Authority: `reports/V8-2-BALANCE-TRANSFER/implementation/iteration-g-official-chest-solver/official-balance.json`.

## Structural and mechanical freeze

The independently rerun validator exited 0 and reproduced the recorded report
exactly.

- JSON chunk: exact to the approved snapshot.
- Changed binary bytes: `101758`, all inside allowlisted rotation accessor
  ranges.
- Walk channel membership, time accessors, interpolation, and protected output
  accessors: exact for both relaxed-walk clips.
- Non-walk animations: byte-exact by animation JSON and every corresponding
  input/output accessor.
- Lower-body world origins: maximum drift `0.0 m`.
- Lower-body world rotations: maximum difference
  `1.5007281413370531e-15` degrees.
- Root, pelvis, lower-body, foot-pivot, toe, timing, and translation tracks are
  therefore unchanged at exported keys; identical inputs and interpolation
  preserve the same dense between-key lower-body result.
- Root-motion and in-place upper allowed arrays are identical to one another.

The changed-accessor set relative to the approved snapshot is exactly 42
rotation channels: the same 21 bones in each of the two relaxed-walk clips:

- spine/chest: `Bone_002..Bone_007`
- neck/head: `Bone_036..Bone_041`
- tail: `Bone_016..Bone_024`

This equals the configured Candidate-A upper-body/tail allowlist. Relative to
iteration-b, deterministic regeneration changes only `Bone_002` and
`Bone_036..Bone_041` in both walk clips; the tail and remaining spine channels
are iteration-b-identical.

Authority: `reports/V8-2-BALANCE-TRANSFER/implementation/iteration-g-official-chest-solver/structural-mechanical.json` and
`reports/V8-2-BALANCE-TRANSFER/implementation/iteration-g-official-chest-solver/generation.json`.

## Approved V8.1 snapshot immutability

The snapshot verifier was rerun directly and exited 0:

- 14 internal snapshot files checked against `APPROVAL_MANIFEST.json`
- 13 external lineage/source files checked
- failures: none
- pointer, manifest, asset, approval media, authoritative validation, profiles,
  and reproduction scripts all match their declared hashes

The approved asset SHA also matches `APPROVED_WALK_BASE.json`, the snapshot
manifest, the V8.2 overlay config, the official evaluator report, and the
structural validator report.

## Review-media provenance

Both files decode as H.264 at the reported geometry, rate, frame count, and
duration.

| Artifact | Verified properties | Actual SHA-256 |
| --- | --- | --- |
| `showcase/v8.2-balance-transfer/iteration-g/side/walk-relaxed-v8-1-respin-side.mp4` | 960x540, 24 fps, 240 frames, 10.000 s | `a29a14dcbcab3b6963c03966755e274419acb43704f26a71da2b055f0eaa8bac` |
| `showcase/v8.2-balance-transfer/iteration-g/comparison/v8-1-approved-vs-v8-2-balance-transfer-side-by-side.mp4` | 1920x540, 24 fps, 240 frames, 10.000 s | `76910cd426c11d00e66a5bba98ba05a9a9f555638142fff48587825a4d2be5d2` |

The side render record binds the candidate GLB hash, clip, Blender version,
accepted read-only renderer, approved snapshot manifest, locked render
properties, and no-animation-edit policy. The comparison record binds the
candidate input and output hashes and identifies the approved left input. That
approved input independently matches the snapshot manifest at SHA-256
`8ef3d2c571e2ee317a431a66f8a031fabe53936d6bf256e9c091a9071ef48a20`.
No temporary render frames remain under the iteration-g showcase directory.

## Findings

### P2 — The structural validator's `sourceSnapshotReadOnly` field is tautological

`candidates/v8.2-balance-transfer/scripts/validate_balance_overlay.py:139`
compares `source_path.read_bytes()` with another read of the exact same path.
That field cannot detect mutation and should not independently be cited as an
immutability proof. This release is not blocked because the separate approved
snapshot verifier checks all 14 internal and 13 external files by pinned hash
and passed in this review. A later cleanup should remove the tautological field
or compare against a separately stored digest/manifest value.

### P2 — The release head is content-addressed but not Git-addressed

The candidate, iteration-g evidence/media, and approved-snapshot package are
currently untracked in the `main` checkout. Their internal hashes and
reproduction are consistent, but there is no commit SHA that permanently binds
the scripts, config, candidate, evidence, and media as one immutable release
head. Before promotion, add them coherently and create the intended signed
commit; until then, use the candidate SHA above rather than repository HEAD
`e04c6a36fbea2b135d5f0c6b3ca1b04c6ebea04d` to identify this review target.

## Commands rerun

- approved snapshot `verify_snapshot.py`
- `apply_official_chest_solver.py --gain 0.3984375` to a temporary GLB
- `evaluate_balance.py --gate-mode candidate-a-upper-only --enforce-gate`
- `validate_balance_overlay.py` to a temporary report
- `cmp` and `shasum -a 256` for candidate/reproduced outputs
- `ffprobe` for both iteration-g videos and the approved comparison input
- manifest-wide SHA-256 and byte-size verification for all 14 snapshot files

No implementation, candidate GLB, approved snapshot, or media file was modified
by this review.
