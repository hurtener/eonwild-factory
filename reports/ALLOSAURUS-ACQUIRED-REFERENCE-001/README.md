# Allosaurus acquired-reference factory checkpoint 001

## Status

The reusable acquired-reference input and provenance seam is implemented and reviewed at source commit `c51b3aa86bfac51df0d30785303f698fc1f6c3a3` (tree `87331ea7435bff8b93df443442f5f498873c6ee6`). It is a single net commit on reviewed authored-material reach head `41e8ef4ea11f6cef400ae2e21f6625f3857b7873`; its reachable history never contains the private licensed FBX or derived motion capsule.

The actual Allosaurus public `compile-set` attempt is **BLOCKED**. It emitted no accepted package. The final source query failed at `t=0.2238918918918919` with `right authored material clearance material gap is nonmonotone`. Technical implementation acceptance does not imply motion, native visual, Unity, anatomical, or production acceptance.

## Ownership and replay

- The shared animal baseline owns target source/rig/body configuration and the authored-material clearance policy. The policy is `0.125` body heights and is explicitly classified `source_backed_engineering_candidate`; it is not a biological measurement.
- The motion intent owns the acquired reference descriptor: publisher identity, raw-source SHA-256, measured-capsule SHA-256, adapter model/version, and phase-preserving retime policy.
- Raw licensed input and the derived capsule remain under ignored `local/acquired/` paths. The tracked descriptor binds their bytes. Synthetic fixtures test contracts without redistributing those inputs.
- Compile-set captures and packages detached descriptor/source/capsule/policy payloads, verifies their hashes before solving, and reconstructs the original pre-emission query plan for replay. Direct recipes and transition programs reject the acquired reference rather than silently dropping it.
- The tracked admitted target GLB is `975a4bc626bc8d79537939ab3a0796473f54aa2c5fadc541f8561b13e442e6c6`. It remains a diagnostic target whose proximal-thigh visual issue is open.

Private inputs used for the retained diagnostic were raw source `c052e81297737f2f2a3b9e7ce3c8a79e4f0950ef1b4a9b16558f8e4f0ca649cb` and capsule `21363f7f7dc5787d2f0a6a20aa08bbcdc5d3e76e4d36004ded032b44d8296051`.

## Verification

- Clean integration: 80 focused tests passed in 25.16 seconds; Ruff passed.
- Complete clean-head suite: 1,184 tests plus 21 subtests passed in 373.32 seconds. This is local validation; broader hosted catalog CI is not claimed green.
- Root final review of `c51b3aa`: P0=0, P1=0.
- Independent descriptor-authority review of `f51431a`: P0=0, P1=0. Its finite-number P2 was closed in the clean net commit with a regression.
- The amplitude and reach-plateau changes received independent narrow review. The retained dense plateau probe had 133/133 available samples, but this did not establish continuous-time export feasibility.

## Actual public compile

The command was:

```bash
PYTHONPATH=src python -m eonwild_motion.factory compile-set \
  --root . \
  --motion-set catalog/motion-sets/allosaurus-engineering-acquired-walk.v3.json \
  --motions walk \
  --interpolation CUBICSPLINE \
  --output "$ARC/out/allosaurus-acquired-reference-walk-003"
```

The retained diagnostic replay found one unavailable query:

```text
time_s: 0.2238918918918919
reason: right authored material clearance material gap is nonmonotone
right target offset: [-1.4155343563970745e-16, 0.00012038048120269108, -7.549516567451064e-16]
```

This is the current mechanical blocker. It must be resolved without weakening contact, reach, articulation, or interpolation gates before the package can be reopened and sent to native visual review.

## Evidence

`evidence/` retains the root and independent code reviews, focused and full-suite receipts, amplitude and plateau reviews, the public compile log, and the exact unavailable-row diagnostic. `SHA256SUMS` binds every retained file.
