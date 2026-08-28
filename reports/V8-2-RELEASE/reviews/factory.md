# Adversarial factory/productization review — V8.2 release

**Reviewed release:** `ae69233d4014bb0bd795730cf07edc0b87e064db`

## Verdict

**`P0=0`, `P1=2`, `P2=1` — NOT PASS.**  The package is an exact,
reproducible release of this one approved Tarbosaurus snapshot, and its visual
media/evidence are correctly pinned.  It is not yet an auditable, portable
factory for a compatible heavy-predatory-biped contract.  Per review scope,
no implementation change or review commit was made.

## What passes

### Exact deterministic snapshot reproduction

I ran the documented generator and verifier in a fresh `/tmp` output directory
with Blender 5.2.0 LTS and `--python-exit-code 1`:

```sh
blender --background --python-exit-code 1 --python \
  'procedural-animation-toolkit(v8.2)/scripts/release_generate.py' -- \
  --config 'procedural-animation-toolkit(v8.2)/config/release.json' \
  --output /tmp/.../rebuilt.glb

blender --background --python-exit-code 1 --python \
  'procedural-animation-toolkit(v8.2)/scripts/verify_release.py' -- \
  --config 'procedural-animation-toolkit(v8.2)/config/release.json' \
  --candidate /tmp/.../rebuilt.glb --output /tmp/.../verify.json
```

Both exited successfully.  The rebuilt SHA-256 was exactly
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
The verifier reported JSON byte equivalence, the pinned base/candidate hashes,
and exactly the 12 permitted rotation accessors (seven declared nodes across
the two declared RESPIN clips).  This is substantive evidence that the
release is not a manual edit of the shipped GLB.

### Evidence and media are pinned

Every hash explicitly pinned by `RELEASE_MANIFEST.json` matched the packaged
file:

- approved asset: `a2cf…500b5`; included base: `bfe8…f4bc2`;
- official balance evidence: `6a78…7219`; structural/mechanical evidence:
  `b5a0…239ed`;
- side review: `a29a…8bac`, H.264, 960x540, 24 fps, 240 frames, 10.000 s;
- fixed three-quarter comparison: `5e11…5d10`, H.264, 1920x540, 24 fps,
  240 frames, 10.000 s.

The official and structural evidence retained their recorded passing results.
The three-quarter asset is therefore the reviewed V8.2 approval evidence, not
an unpinned editorial substitution.

## P1 findings

### P1-1 — the claimed portable contract is not implemented or enforced

`config/release.json` is parameterized for this asset's names, but it is not a
defined compatible-biped contract.  It declares only `Bone_001`, `Bone_002`,
and the six `Bone_041..036` names; it does not declare or validate their parent
chain, rest-frame/anatomical axes, rotation-accessor type, common timeline,
coordinate convention, or clip semantics.  `release_generate.py` then assumes
all of those facts: it indexes `tracks[n]`, indexes the world rotation-vector's
literal component `[2]`, and writes fixed VEC4 float32 accessor spans (lines
18–30 and 42–45).

The output is therefore portable only to an effectively identical V8.1-derived
GLB with the same node names, hierarchy, axes, timelines, and binary layout.
That is a valid snapshot reproducer, but it is not safe portability across a
compatible heavy-predatory-biped bone contract.  A same-anatomy asset with a
semantic mapping or a different rest basis could either raise an incidental
key/layout error or receive the wrong anatomical roll without an explicit
contract failure.

### P1-2 — declared bounds are documentary, not a fail-closed generation gate

The config declares `maxChestLocalDeltaDegrees: 1.0` and
`maxNeckLocalDeltaDegrees: 0.75` (lines 16–17), but the generator never reads
either field.  I copied the config outside the repository, changed both to
zero, and re-ran the generator.  It still exited `PASS` and emitted the same
approved SHA.  Thus the release cannot honestly call the solve *bounded by
config*; the fixed expected output hash protects this one frozen artifact, but
does not protect a legitimate adapted configuration whose output hash changes.

This is particularly material to the portability claim: the output SHA is an
excellent snapshot lock, not a substitute for geometric/local-delta gates when
the recipe is reused.

## P2 findings

### P2-1 — clean reproduction emits a NumPy runtime warning

The clean generation succeeds but emits
`RuntimeWarning: invalid value encountered in divide` from
`scripts/glb_math.py:41`.  It arises because `np.where` evaluates
`sin(half) / angle` at zero even though the alternate small-angle branch is
selected.  The emitted GLB is deterministic and hash-correct, so this is not a
release blocker by itself; it should nevertheless be removed before presenting
the generator as warning-clean production tooling.

## Provenance note

The release's own plan requires a locally signed `hurtener` commit
(`reports/V8-2-RELEASE/plan.md`, acceptance check 5), but
`git show -s --format='%G?' ae69233…` returns `N` (no signature).  This is a
recorded acceptance/provenance discrepancy.  I have not counted it separately
from the two factory P1s above, but it must be corrected or explicitly waived
before presenting the release as a signed provenance chain.

## Required disposition

Do not promote this as a cross-rig factory yet.  It may be described accurately
as a **pinned, reproducible V8.2 Tarbosaurus balance-transfer release**.  To
close P1, define and validate the compatible rig contract (including semantic
mapping/hierarchy/basis/timeline checks), enforce the declared local-delta
bounds, then rebuild and re-pin the artifact/evidence.  Recreate the release
commit with the required signature or record a deliberate exception.

## Round-2 exact-head re-pin — `51bd9823cc1e9f19922062da8fba7c60b2955489`

**Narrow verdict: `P0=0`, `P1=1`, `P2=1` — NOT PASS; no review commit.**

### P1 closures confirmed

- A clean Blender 5.2 replay rebuilt the exact approved SHA and the v2
  verifier passed manifest inventory, every inventory hash/size, media facts,
  base/candidate hashes, GLB JSON, and the declared accessor delta.  The
  former package-inventory P1 is closed.
- The config now supplies semantic roles, a parent chain, and the phase/basis
  axis.  The active generator consumes the role names and configured rotation
  vector axis, validates required animated roles, direct parent relationships,
  VEC4 shape, and common rotation timeline before it writes an output.
- The declared local-delta limits are now active.  A temporary config that set
  both limits to zero failed cleanly with
  `local delta bound exceeded Bone_002: 0.965347702150647`; it did not write a
  passing replacement artifact.
- The zero-angle NumPy warning is gone in a clean replay.
- I correct the earlier signature note: raw commit objects for both the
  original release and this fix contain `gpgsig` SSH signatures.  This host's
  `%G? = N` is a local allowed-signers verification limitation, not proof of an
  absent signature.  The manifest's documented signed-commit binding is
  therefore present.

### Remaining P1 — shipped code still violates the no-`Bone_*`-literal and full config-contract requirement

The active `release_generate.py` no longer has a `Bone_*` literal.  However,
the shipped/imported `scripts/glb_math.py` still contains seven such literals
in its retained legacy overlay implementation (for example lines 190, 198,
222, 242, 290, and 336).  That code is not on the current release-generator
path, but it is still distributable executable code in the factory and carries
the original rig's hard-coded roles.  The requested exact-head condition was
**no `Bone_*` literals in code**, not merely none on the currently exercised
path, so this requirement is not met.

There is a related contract inconsistency: `expectedParents` and
`accessorContract` are declared in `config/release.json` but are never read.
The implementation reconstructs the parent expectation from other keys, and
the GLB helper enforces float/VEC4/stride where writing changed accessors, but
the declared `LINEAR` interpolation contract is not validated.  A
compatible-named CUBICSPLINE or STEP rotation clip is therefore not rejected
by the declared interpolation rule before its sampled values are treated as
ordinary per-frame rotations.  This keeps portability partially implicit rather
than fully config-governed.

This is a real factory P1, not a reason to alter the approved GLB or media:
remove or isolate the legacy hard-coded implementation, make every declared
contract field authoritative (or delete it), and fail closed on interpolation
as well as the existing hierarchy/layout/timeline checks.

### P2 retained — media input/render provenance

The manifest now hashes the final MP4s and verifies their dimensions, duration,
and frame count.  It still ships no render/input record connecting each media
artifact to the approved/candidate GLB hashes, source clip, camera/bounds, or
comparison left/right inputs.  Final-media integrity is therefore good, but
self-contained render provenance remains a follow-up rather than a new P1.

## Exceptional P1-only re-pin — `0ba8b90c1091940c06a9b83d3ea77a5480c24571`

**Verdict: `P0=0`, `P1=1`; not accepted and no review commit was made.**
P2 provenance was intentionally not reopened.

The positive release replay remains clean: generator and verifier both passed,
no warning was emitted, and the rebuilt approved GLB remained exactly
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
The included base also remains exactly
`bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2`.
Zero chest/neck bounds still fail closed as intended.

### Remaining P1 — required semantic/accessor contract fields are still inert

The requested exact-head gate requires that `expectedParents` and the *full*
`accessorContract` be actually enforced.  They are not:

- There are no code reads of `expectedParents`, `interpolation`, or
  `commonTimeline` in the shipped scripts.
- I changed each field separately in a temporary config and re-ran the
  generator: an invalid chest `expectedParents` value, `interpolation: STEP`,
  and `commonTimeline: false` all exited `0` and reported `PASS` with the
  approved SHA.  Only the independent zero-bound negative correctly failed.

The direct hierarchy, VEC4, component-type, and stride checks are useful, but
they do not make an unread configuration field authoritative.  In particular,
the generator still has no sampler interpolation check, so the declared
`LINEAR` contract cannot reject a STEP/CUBICSPLINE compatible-named source.

The literal requirement is also not met as written: `rg 'Bone_[0-9]+'` still
finds `Bone_002` and `Bone_036` in `scripts/glb_math.py`; the same legacy block
reconstructs additional hard-coded names with `"Bone" + "_001"` / `_002` /
`_036`.  This is not a semantic/config-driven factory simply because the
literal was split to avoid the pattern.

Required closure remains: delete or isolate the legacy hard-coded block, drive
the hierarchy from `expectedParents`, and validate the configured
`interpolation` and `commonTimeline` values against each affected sampler and
timeline.  Re-run these four exact negative cases before another re-pin.

## Final P1-only re-pin — `e69f42838b2b887cca54db75d3159fcc60762813`

**Final narrow verdict: `P0=0`, `P1=0`.**  Prior P2 render-provenance scope was
not reopened.  This release now passes the requested factory P1 gate.

- Shipped `procedural-animation-toolkit(v8.2)/scripts/` has zero matches for
  both `Bone_[0-9]+` and the former split-name construction pattern.  The
  legacy rig-specific overlay code was removed; generation obtains semantic
  nodes only through `contract.roles`.
- `expectedParents` is now consumed through the configured selector mapping,
  rather than reconstructed from fixed parent logic.  The complete
  `accessorContract` is consumed and validated: `componentType`, `type`,
  `byteStride`, `commonTimeline`, and `interpolation`.
- I independently ran the supplied negative matrix in a temporary copied
  package.  All 11 cases exited non-zero: wrong parent; STEP and CUBICSPLINE;
  false and mismatched common timelines; wrong component type, accessor type,
  and stride; zero local-delta bounds; and small/oversized bytecode caches.
- A clean `PYTHONDONTWRITEBYTECODE=1` Blender 5.2 generation and v3 package
  verification both passed with no warning.  The rebuilt approved SHA remains
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`; the
  included base remains
  `bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2`.

This re-pin modifies only this review report.  It is ready for the coordinated
signed review-only commit with the independently owned technical review.
