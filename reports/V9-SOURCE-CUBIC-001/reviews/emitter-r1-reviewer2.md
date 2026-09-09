# Source-derived CUBICSPLINE emitter — reviewer 2 round one

Reviewed exact head `67a675686475e18c28e3900e519272fbb6f65320` against base `c48e746166b1accc81f71a7ab0bbce834f2122c5`, read-only. The tracked worktree remained unchanged; its pre-existing `.venv` symlink is untracked. Scope was the eleven changed emitter, compiler, quality, constant-law and test files. Closed source-query, constant-target, exact-tangent and interval-bound stages were not reopened.

Disposition: **CHANGES REQUIRED — two P1 verifier findings, no P0**.

## P1 — The verifier trusts the runtime interpolation label instead of the serialized GLBs

`src/eonwild_motion/factory/compiler.py:616-660` derives `is_cubic` only from `runtime.json`. It never binds that declaration to the animation samplers in `root_motion.glb` and `in_place.glb`. On the retained real walk Stage 2 package, I left both GLBs byte-for-byte CUBICSPLINE, removed `runtime.interpolation`, `inputs.lock.emission`, and the midpoint-plan inventory entry, refreshed the affected manifest hashes, and ran `verify_package`. It returned both `integrity: PASS` and `technical_status: PASS`, treating the actual cubic outputs as legacy LINEAR.

The verifier must inspect every serialized TRS sampler in both exports and require a single supported interpolation mode that agrees with runtime and lock metadata. A CUBICSPLINE sampler must require the cubic evidence inventory; a genuine legacy LINEAR package must retain omission compatibility. Both movement modes must agree.

## P1 — A failed cubic midpoint contact result can retain technical PASS

`src/eonwild_motion/factory/compiler.py:654-658` checks only that `cubic_midpoint_skinned_contact` is a mapping with `root_motion` and `in_place` keys. On the same real package, I changed the root-motion midpoint verdict to `FAIL` and maximum penetration to `1.0 m`, kept the declared technical status `PASS`, refreshed the manifest hash, and ran `verify_package`. It again returned `integrity: PASS` and `technical_status: PASS`.

The verifier must validate the supported per-mode midpoint result shape and reject a manifest/validation technical PASS whenever either midpoint contact verdict fails. Recomputing from reopened output where the bound inputs are available is stronger, but at minimum the verifier must enforce the compiler's new technical conjunction rather than accepting contradictory packaged evidence. This finding is limited to the newly added cubic midpoint gate.

## Evidence and boundaries

The independent mutation receipt is `audits/source-cubic-round1-reviewer2-probes.json`, SHA-256 `24c549c78b424c7fe9a480c1b3c583d7847d1e11459024ad6a052bfc277f7045`. Its source package is `out/source-cubic-walk-v3-c48-stage2`, restored and verified at exact manifest SHA-256 `03c0edb00b53abe5d68094480f2558d657f076e4099c85650ac293bb901a277c`. During the first probe attempt, hard-linked scratch JSON accidentally changed four retained metadata files; I reconstructed them in a normal-copy scratch package, obtained the previously recorded exact manifest hash, copied those exact bytes back, changed the probe to normal copies, and reran both reproductions. The GLBs were never modified.

Focused tests covering source cubic emission, exact emitted tangents, factory packaging, articulation profiles and constant skin targets passed: **86 passed in 127.33 s**. `git diff --check` passes. Ruff passes for the changed implementation and dedicated/new test files; including the whole historical `tests/test_factory.py` reports its eight pre-existing E701 one-line `with` statements, unrelated to this delta.

I found no additional P0/P1 in the bounded diff. The batch source-time evaluation, typed UNAVAILABLE handling, quaternion sign alignment and tangent projection, midpoint timeline construction, and conservative serialized rotation-rate path are covered by the focused gates. This review does not claim arbitrary-time source-law continuity, global C1 motion, native Blender parity, Unity parity, visual approval, or biological/physical validity. The already assigned native Blender adapter discrepancy is outside this review.
