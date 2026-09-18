# Bind-pose admission V8 — independent round-1 review

Status: **P1 findings; source is not ready to integrate.**

## Scope and frozen identities

- Review worktree: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-bind-pose-admission-v8`
- Implementation: `0a6ca91af6e03d10f86c5124b5366ceef8f7581b`
- Source/input binding: `7d3945b7083c1e04dbf360e852d401e29d3e98fa`
- Documentation-only head inspected: `16aab6232698c6f641c34624c0ea246c67f1684e`
- Base: `cc7b3d9e199d1679d28bbcbefb61bcea5407b129`
- Recovered source: `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`
- Animal V2: `53ffeba22e24a87504d3dcc310bedacf6db94d60a25ffe56ad028b03f41e849d`
- Contact V10: `61e0351fe9f7170ddce7f0b83a8f0379d119349d3c392ffec43e544adb115db5`
- Adult V8 recipe: `cda9fd36aa7130596d2c8f5610fb84991a968db96c58f088687a2365b876128a`
- Package manifest: `a8b5b1d82b98d6e3579e4aec2e2ac15eec3f0baa9c0cb42ea4ff734dc15b88d3`
- Root-motion GLB: `d0ca24b7738517804f525c7261d5dcbc0790b94479915ba1251250cd76433d37`
- In-place GLB: `b9f8f18f2508132bf3a78c900d6f4c8addc380f4d65c0c81751fd5a3016a3579`

The reviewed input preserves V7 program, performance, articulation and rig bindings. The new source has no animation, and admission declares explicit +Z forward/+Y up. The package verifier reports integrity `PASS`, technical `BLOCKED`, visual `PENDING`, Unity `NOT_RUN`, and production approval `false`. The technical block is the separately documented exact serialized local linear tangent mismatch; this review does not reinterpret it.

## Findings

### [P1] Nonfinite mesh positions make the reopened skin proof fail open

`_skin_reconstruction_error` converts `POSITION` at `source.py:109` but never requires the values to be finite. A NaN or infinity propagates through `expected`, `actual`, and the norm. At `source.py:137`, `max(0.0, nan)` remains `0.0`, so admission succeeds and records an exact zero reconstruction error.

Reproduction against the original source:

1. Replace only the first float of primitive 0's `POSITION` accessor with `NaN` (and separately with `+Inf`).
2. Run `admit_geometry(..., recover_bind_pose=True, skin_index=0)`.
3. Both malformed sources are accepted. Both receipts claim `maximum_reopened_skin_position_error_m: 0.0`; the infinity case also emits a NumPy invalid-subtract warning.

This invalidates the core fail-closed reopened-skin proof for malformed inputs. Require finite positions before homogeneous transformation and require every expected position, reconstructed position, residual vector, norm, and final maximum to be finite before comparing the tolerance. Add NaN and infinity mutation regressions.

### [P1] glTF index fields are coerced instead of strictly validated

At `source.py:154`, `skin.joints` entries are converted with `int(value)`. The reopened verifier repeats coercion at lines 91-92 and for mesh/accessor references at lines 99 and 109-111. The initial inverse-bind check accepts any Python `int`, including `bool`, and does not reject negative indices.

Concrete accepted malformed documents:

- Replacing the skin joint whose valid node is `1` with JSON `true` is accepted and produces the normal recovered result.
- Replacing valid joint `74` with `74.5` is accepted and produces the normal recovered result.
- Appending a duplicate of the valid inverse-bind accessor and setting `inverseBindMatrices` to `-1` is accepted through Python negative indexing and produces the normal recovered result.

These are invalid glTF index encodings that cross the public admission boundary and are reported as successfully recovered geometry. Validate every index as `type(value) is int`, nonnegative, and within the referenced collection before lookup. Apply the same rule to skin joints, inverse-bind accessor, selected mesh/skin fields, mesh index, and primitive attribute accessors. Tests should cover boolean, fractional, negative, and out-of-range values without relying on Python indexing behavior.

### [P2] Valid non-skin hierarchy nodes are not handled or declared unsupported

The joint solve at `source.py:211` chooses either a desired selected-joint parent world or the original input parent world. It does not propagate the recovered output world through an unselected intermediary.

Two valid-hierarchy probes expose the limitation:

- Inserting an identity non-skin node between selected joints `Bone_043` and `Bone_042` leaves input joint worlds and inverse binds unchanged, but recovery rejects with `reopened bind-pose FK exceeds tolerance`.
- Reparenting the selected-skin mesh under `Bone_043` while compensating its local TRS to preserve the same input mesh world rejects with `reopened bind-pose skin reconstruction exceeds tolerance`; the recovered ancestor moves the output mesh world while the mesh local stays stale.

This is a generic capability/diagnostic gap rather than unsafe acceptance on the admitted Tarbosaurus source. Either reconstruct all node worlds topologically while retaining non-skin locals and explicitly preserving the mesh world, or reject these ancestry forms early with a precise documented contract. Add identity and transformed non-skin intermediary tests, plus a mesh-descendant case.

## Checks and evidence

- Independent focused tests: `10 passed in 4.45s` for `tests/test_bind_pose_recovery.py` and `tests/test_adult_bind_pose_catalog.py`.
- Author report records `13 passed` including its factory-admission selection.
- Ruff on the two changed source files and two new test files: pass.
- `git diff --check cc7b3d9..16aab623`: pass.
- Correct negative cases observed: singular and reflected inverse binds reject; shear rejects; source nonuniform scale and negative scale reject; zero quaternion rejects.
- Production bind recovery remains deterministic in the focused tests, preserves the binary buffer, ignores animation tracks, and reopens 59,169 weighted vertices under its declared finite input.
- Root's independent Blender 5.2 static comparison receipt is internally consistent: SHA-256 `4e4463661c0e249307b1861df900f2a363a5225d635192dd1e45c8934041c2ce`, all 59,169 vertices, maximum same-index skin delta `3.01989033355766e-6 m`, and four static views. The wide-open jaw remains explicitly unresolved and no motion, biological, Unity, or production approval is claimed.

No old assets, package contents, source files, or input bindings were modified during this review.
