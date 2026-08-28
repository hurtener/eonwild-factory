# PROCEDURAL-ENGINE-001 — implementation summary

## Outcome

The first canonical procedural-motion vertical slice is executable. A single
installable `eonwild-motion` package now resolves schema-validated semantic
rig, family, species, motion, layer, render-set, and release-profile contracts;
builds the V8.2 compatibility profile; validates and compares its GLB; invokes
Blender for a real fixed-camera render; and promotes only an independently
approved, hash-locked build into a new destination.

The implementation does not copy an approved binary, import code from a
versioned toolkit, modify a legacy toolkit, or implement the deferred hip
layer. The V8.2 profile references the committed immutable input and approved
output by repository-relative path and SHA-256.

## Package and command surface

- Python package: `src/eonwild_motion/`
- Console script: `eonwild-motion`
- Commands: `build`, `validate`, `compare`, `render`, `promote`
- Contracts: `schemas/motion/`
- Concrete semantic data: `catalog/`
- Versioned compatibility profile: `profiles/v8.2/`
- Legacy archive classification: `legacy/catalog.json`
- Tests: `tests/`

Every non-promotion command writes only below the supplied external
`--work-root`, with a versioned `run-report.json`. Promotion additionally emits
a common run report below its external work root and writes the destination
atomically with `manifest.json` last.

## One verification command

Run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

This runs unit/contract, integration, Blender build/render, double-build,
promotion, source-cleanliness, and negative-path coverage without skips.

## Acceptance result

- 21 tests passed in 72.674 seconds with zero failures or skips.
- Two independent builds were byte-identical and each produced approved SHA
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
- Independent validation found 67 rotation channels and 245 samples in each of
  the two declared walk clips.
- glTF Validator reported 0 errors and the two pre-existing allowlisted
  warnings `MESH_PRIMITIVE_GENERATED_TANGENT_SPACE` and
  `NODE_SKINNED_MESH_NON_ROOT`.
- Structural comparison found zero byte changes outside declared accessor
  regions and JSON-equivalent GLB structure.
- The build stage binds every layer patch to the declared clip, semantic
  channel, and exact owned accessor before writing bytes.
- Blender PNG output is decoded and re-encoded as filter-0/zlib-9 RGB(A) with
  volatile metadata removed. Two independent renders are byte-identical at
  SHA-256 `0b1494dd526f4eeb8312fa28ab61310163f9a508f229c26e98c8db8a479b9202`;
  decoded-pixel SHA-256 is
  `5ca028e49545863349b16961b53bf18ca11bfcaa1d34fc4d1a19f185ad98e576`.
- The actual 640x360 canonical fixed-camera PNG is committed under the task
  report media directory for inspection.
- Comparison now emits structural, accessor, inherited-contact, fixed-media,
  and artifact facts plus a responsive static HTML page. It explicitly states
  that technical comparison is not visual approval.
- All command successes and failures—including missing-run and missing-profile
  failures before normal context creation—emit the fully constrained,
  schema-validated common envelope.
- Engine-source scan found no concrete bone, species, clip, release, approved
  hash, iteration, or legacy-toolkit literals.
- No tracked legacy-toolkit or approved GLB/media path changed.

## Promotion boundary

Promotion fails closed unless the build run passed, the run and current source
locks are clean and at the same Git head, the resolved profile lock still
matches, technical and visual reviewers are distinct from each other and the
implementer, the artifact hash is approved, all validation/comparison/render
evidence parses, validates, passes, and binds to the exact run/profile/artifact/
source lock, provenance is complete, and the destination does not exist.
The manifest is schema-validated before the temporary directory is atomically
renamed.

No real release was promoted in this task. Promotion was verified only against
temporary test destinations, so the committed V8.2 release remains untouched.

## Deferred work

- Hip balance is intentionally absent. It becomes a future registered layer
  and profile revision, followed by contact/IK revalidation.
- V5 and V5.5 remain legacy archives until each behavior has a declared
  migration and acceptance comparison.
- The browsable comparison is fixed-frame technical evidence, not multi-frame
  locomotion playback or visual approval. Video comparison remains deferred.
- The first profile retains the 45,331,840-byte GLB. Browser-size reduction is
  a later measured optimization and may not weaken exact V8.2 compatibility.
