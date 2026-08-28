# V8.2 release productization plan

## Scope

Create a lean, self-contained `procedural-animation-toolkit(v8.2)` release
from the approved V8.2 Candidate-A iteration-g artifact. The release retains
the exact approved binary and a pinned included iteration-b base so its
official-basis chest-balance solve can reproduce that binary deterministically.
It does not import any rejected iteration, cache, source package, or manual
binary patch workflow.

## Intended files and ownership

- `procedural-animation-toolkit(v8.2)/README.md` — release use, provenance,
  commands, and limitations.
- `procedural-animation-toolkit(v8.2)/config/release.json` — hashes, allowed
  chains/clips, bounded gain, and output contract.
- `procedural-animation-toolkit(v8.2)/input/*` — one pinned iteration-b GLB
  base required by the deterministic solver.
- `procedural-animation-toolkit(v8.2)/asset/*` — approved V8.2 GLB only.
- `procedural-animation-toolkit(v8.2)/scripts/*` — standalone generator and
  snapshot verifier.
- `procedural-animation-toolkit(v8.2)/evidence/*` — authoritative evaluator,
  structural/mechanical report, manifest, and release verification output.
- `procedural-animation-toolkit(v8.2)/media/*` — bounded V8.2 approval side
  video and V8.1/V8.2 comparison metadata/media.
- `reports/V8-2-RELEASE/*` — command log, inventory, and final evidence.

All paths are new release-owned paths in this clean worktree. Approved source
artifacts are read only from `/Volumes/m2-extended-disk/Repos/eonwild-factory`.

## Acceptance checks

1. Rebuild from the included base using only release config/script and require
   the approved GLB SHA-256 `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
2. Verify source/base/output hashes, GLB JSON structure, walk clip membership,
   duration/timeline equality, and that only approved rotation accessors differ
   from the included base.
3. Verify the official Candidate-A and structural/mechanical evidence reports
   are PASS and bound them by hash in the release manifest.
4. Verify media codec, dimensions, frame count, duration, hashes, and package
   inventory; reject any file over 100 MB or any cache/temp/failed candidate.
5. Test a clean-output reproduction directory, then verify the packaged output
   and manifest again. Commit locally with the configured signed `hurtener`
   identity; do not merge or push.

## Assumptions

- Iteration-b is the minimal reproducible pre-chest-solve base and is included
  solely because it is required to regenerate the approved artifact.
- V8.1 provenance is referenced by immutable path and SHA rather than copied
  into this V8.2 package.
- Blender 5.2+ with NumPy is the supported generation runtime; the release
  performs direct GLB accessor patching only under the declared allowlist.
