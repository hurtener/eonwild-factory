# V8.2 release productization evidence

## Verdict

PASS. `procedural-animation-toolkit(v8.2)` is a lean canonical release on
`codex/v8-2-release`. It contains one required iteration-b reproduction base,
one approved V8.2 GLB, reusable configuration/solver/verifier scripts,
authoritative pass evidence, and two bounded review MP4s. No rejected
candidate, cache, duplicate rebuilt artifact, or unapproved V8.1 package is
included.

## Reproduction

The clean-output build regenerated SHA-256
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`,
exactly matching the approved artifact. The snapshot verifier passed base and
candidate hashes, GLB JSON equality, non-empty approved change set, and the
two RESPIN clips' rotation-accessor allowlist.

The reusable contract is gain `0.3984375` applied in the official
world-relative rotation-vector basis, with deterministic neck cancellation.
It preserves root, pelvis, lower-body, tail, translation, non-walk, timeline,
and GLB-structure data from the included base.

## Quality and provenance

- Official Candidate-A evidence: PASS.
- Structural/mechanical and iteration-38 inherited locomotion evidence: PASS.
- Package size: 88 MB; largest files are the 43 MB base and 43 MB approved
  GLB, each below the 100 MB cap.
- Side review: 960x540, 24 fps, 240 frames, 10.000 seconds.
- Three-quarter comparison: 1920x540, 24 fps, 240 frames, 10.000 seconds.
- V8.1 source provenance SHA:
  `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`.

Exact package paths and hashes are in
`procedural-animation-toolkit(v8.2)/RELEASE_MANIFEST.json`; commands are in
`commands.log`. No merge or push is part of this release handoff.

## P1 release-fix round

The v2 verifier now parses the release manifest, requires an exact inventory,
checks every shipped file's SHA-256 and <=100 MB size, rejects extras, and
probes both media files. The manifest intentionally excludes only itself from
its inventory; the verifier schema-checks that documented convention and the
signed commit binds the manifest bytes. The generator now validates configured
semantic roles, hierarchy, timeline/layout and basis axis, enforces measured
local-delta bounds, and avoids zero-angle NumPy division warnings.

## Final P1 closure

The v3 verifier inventories every package file except the manifest itself and
independently rejects cache, bytecode, temporary/rejected paths, and files over
100 MB even when they are not in the manifest. The shipped GLB helper now
contains only the quaternion, GLB-accessor, and hierarchy utilities used by the
generator/verifier; it has no model-name literals or legacy overlay solver.

The generator now resolves `expectedParents` through semantic role selectors
and enforces all five accessor-contract fields: component type, value type,
byte stride, common rotation timeline, and interpolation. Eleven negative
tests fail closed with exit code 1: bad parent; STEP and CUBICSPLINE; false and
mismatched common timelines; bad component type, value type, and stride; zero
local-delta bounds; a small pycache; and an oversized pyc. Exact diagnostics
are recorded in `p1-negative-tests.json` and the rerunnable harness is
`run_p1_negative_tests.py`.

With `PYTHONDONTWRITEBYTECODE=1`, Blender 5.2.0 LTS rebuilt and verified
SHA-256 `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
The approved GLB and both approved MP4 hashes remain unchanged.
