# Procedural engine consolidation inventory

## Scope and disposition

This is a read-only migration inventory of the committed V5, V5.5, and V8.2
toolkits at branch head `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3`.
It does not propose changing any approved release binary in place. The safest
consolidation is to create one tested engine beside the immutable release
folders, reproduce each accepted artifact through adapters, and archive the
version folders only after their golden gates pass from the new entry point.

No P0 migration blocker was found. There are four P1 risks: preserving V8.2's
byte-exact output, selecting the canonical implementation from copied versions,
separating species data from algorithms, and retaining independent validation
rather than migrating implementation and oracle together.

## Repository facts

| Release | Size | Shape | Migration implication |
|---|---:|---|---|
| `procedural-animation-toolkit(v5)` | 304 MB | 501 files; V1 through V5 source, inputs, generated releases, frames, browser artifacts and reports | Historical bundle, not a source package boundary. |
| `procedural-animation-toolkit(v5.5)` | 416 MB | Full V5 clone plus a second V5.5 toolkit and V5.5 outputs | 497 of V5's 501 files are byte-identical here. Only the package records, root README and root verifier differ at the same relative paths. |
| `procedural-animation-toolkit(v8.2)` | 88 MB | 13-file lean release: three Python scripts, config, two GLBs, evidence and media | Best executable acceptance slice, but still a release capsule rather than a reusable library. |

Within `procedural-animation-toolkit(v5.5)`, `toolkit/v5.5` repeats 63 files
byte-for-byte from `toolkit/v5`. Six same-relative files differ:

- `README.md`
- `tests/test_browser_contract_v5.py`
- `scripts/eonproc_v3/gltf_io.py`
- `scripts/eonproc_v4/profile.py`
- `scripts/eonproc_v4/locomotion.py`
- `scripts/eonproc_v4/actions.py`

V5.5 adds nine paths beyond its copied V5 toolkit: `build_v5_5.py`,
`adjust_v5_5_foot_pivots.py`, `validate_v5_5_release.py`, the
`tarbosaurus-v5.5.json` profile, and the five-file `eonproc_v5_5` package.
Within that package, `jaw.py` and `polish.py` are byte-identical to their
`eonproc_v5` counterparts; only `transitions.py` is materially different.

The source GLB, edited bone map and reference walk video in V5 and V5.5 are
also exact duplicates. Their Git blob identities are respectively
`9a949d...` (44,747,660-byte GLB), `f817f0...` (11,209-byte YAML), and
`98a6d2...` (2,077,005-byte MP4).

## Reusable engine algorithms and modules

The following should move into one version-neutral Python package. Names below
describe ownership, not a mandated final spelling.

| Proposed engine area | Current committed sources | Reusable behavior | Migration note |
|---|---|---|---|
| `math/quaternion.py` | V8.2 `scripts/glb_math.py`; V3 `rig.py`/`gltf_io.py` | normalized multiply/inverse, rotation-vector conversion, sign continuity, local/world composition | Keep a NumPy-only deterministic path for V8.2. Do not silently replace it with SciPy and expect the same bytes. |
| `io/glb.py` | V5.5 `eonproc_v3/gltf_io.py`; V8.2 `Glb` | GLB chunk parsing, accessors, TRS, skins, animation reads/writes, accessor byte offsets | Consolidate behind explicit read-only and rewrite APIs. The V8.2 byte-patch writer must remain a distinct exact-output strategy. |
| `rig/semantics.py` | `eonproc_v3/rig.py`, edited bone-map YAML | semantic tags, anatomical basis, hierarchy lookup | Bone names belong in rig maps/profiles, never engine logic. |
| `rig/pose.py` | `eonproc_v3/rig.py` | FK pose state, world/local conversion, chain rotation distribution | Extract from Tarbosaurus-specific pipeline assembly. |
| `motion/curves.py` | `eonproc_v3/curves.py` | smoothstep, minimum jerk and derivatives, cyclic Gaussian, C2 pieces | Already generic and repeated across toolkit generations. |
| `motion/clip.py` | `eonproc_v4/clip.py`, `animation_reader.py` | animation clip model, normalization, sampling, baked pack reading | Define one clip schema and make release-name rewriting an adapter. |
| `motion/path.py` | `eonproc_v4/path.py` | straight, arc and eased-arc paths | Generic, independent of species. |
| `environment/terrain.py` | `eonproc_v4/terrain.py` | flat, plane and procedural height/normal surfaces | Keep scalar surface queries separate from gait policy. |
| `contact/sole.py` | `eonproc_v4/sole.py` | weighted sole-vertex selection and contact correction | Generic if semantic foot/toe chains and thresholds are injected. |
| `solve/biped.py` | `eonproc_v3/generator.py` | anatomical leg geometry, constrained IK, continuity preferences, tail dynamics | Extract solver mechanics; move every magnitude, chain and quality threshold to a family/species profile. |
| `solve/locomotion.py` | V5.5 `eonproc_v4/locomotion.py` | schedules, stance/swing phasing, contact solve, root and pelvis tracks, in-place derivation | Use the V5.5 variant as the migration source because it exports pelvis translations and contains the later recovery phasing. |
| `solve/actions.py` | V5.5 `eonproc_v4/actions.py` | fixed-foot constrained actions and action clip construction | Separate generic action envelopes from Tarbosaurus idle/eat/bite/roar recipes. |
| `post/jaw.py` | either V5.5 `eonproc_v5/jaw.py` or `eonproc_v5_5/jaw.py` | mesh-witness jaw closure calibration | These copies are identical; migrate once. |
| `post/polish.py` | either V5.5 V5/V5.5 `polish.py` | quaternion-continuous Savitzky-Golay smoothing, cyclic padding, endpoint restoration | These copies are identical; expose protected tracks and filter parameters as data. |
| `post/transitions.py` | V5.5 `eonproc_v5_5/transitions.py` | RotationSpline/Hermite transitions with exact endpoints and pelvis/root translations | Prefer V5.5 over V5; retain golden endpoint tests. |
| `rig/pivots.py` | V5.5 `eonproc_v5_5/pivots.py` | lower-foot pivot relocation while preserving toe world origins, inverse-bind consistency and rest-skinned mesh | This is a rig migration operation, not per-run gait polish. Run before animation generation and validate independently. |
| `post/balance_transfer.py` | V8.2 `release_generate.py` | bounded world-relative chest response to pelvis phase plus residual neck-chain compensation | Extract the solve from release I/O. Inject roles, basis axis, gain, residuals, clip selectors and local-delta limits. |
| `validate/package.py` | V8.2 `verify_release.py` | exact inventory, hashes, size cap, forbidden paths and `ffprobe` media facts | Generalize policy, but keep it a release-layer validator rather than a motion algorithm. |

TypeScript under V4/V5/V5.5 `runtime/` is a separate browser-runtime seam:
phase clock, action controller, event dispatcher, motion graph, terrain contact
adapter and Babylon adapter are reusable concepts, but they should not be
folded into the Python build package. Move them into a sibling runtime package
only after tests define its animation-manifest contract. The copied
`v4-viewer.js`/`v5-viewer.js` files are demo clients, not canonical runtime
source.

## Data profiles, release constants and contracts

Move these out of source code and into schema-validated data:

1. **Rig profile:** semantic role-to-node mapping, expected hierarchy, skin and
   foot/toe chain selectors, anatomical basis, joint sign/range policy. Sources:
   `inputs/tarbosaurus_bone_map.edited.yml` and V8.2 `contract.roles`,
   `expectedParents`, `spineParent`, and basis declarations.
2. **Biomechanical family profile:** large-theropod gait/contact ranges, stance
   and swing functions, solver tolerances, terrain limits, tail dynamics and
   protected track classes. Seed from `BipedV3Profile`/`BipedV4Profile`, but do
   not keep the class name or Tarbosaurus defaults as engine truth.
3. **Species/motion profile:** the values in
   `toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`: cycle, stride,
   support shift, neutral posture, joint ranges, foot articulation, idle/eat/
   bite/roar controls and transition durations.
4. **Clip recipe:** clip names, cycles/duration, terrain/path, loop/root-motion
   flags, action sequences and transition graph. Today these are hard-coded in
   `TarbosaurusV4Generator.generate_all()` and `build_v5_5.py`.
5. **Post-process profile:** jaw search range/witness policy, polish windows and
   protected tracks, foot-pivot fraction, transition endpoint tolerances.
6. **Balance-transfer profile:** V8.2 clip selectors, output allowlist,
   world-relative formula, `rotationVectorAxis=2`, gain `0.3984375`, neck
   residuals `[0.89, 0.74, 0.55, 0.31, 0, 0]`, and 1.0/0.75-degree delta
   bounds.
7. **Release lock:** base/output paths and SHA-256 values, approved accessor
   delta, evidence/media paths and hashes, size limits and forbidden-path
   policy. These are release metadata and must not enter engine defaults.

Concrete constants that must leave executable source include `SAMPLE_HZ=60`,
37 clips/16 transitions/75 joints, V4/V5/V5.5 name replacements, the explicit
transition list and durations in `build_v5_5.py`, jaw phases and angles, and
all Tarbosaurus-specific action envelopes. Fixed numerical epsilons used only
for stable quaternion/linear algebra may remain documented engine constants.

## Binary, input and provenance assets

### Canonical fixtures or release-owned inputs

- V5/V5.5 `inputs/tarbosaurus_source.glb`: one deduplicated content-addressed
  fixture, not one copy per release.
- V5/V5.5 `inputs/tarbosaurus_bone_map.edited.yml`: canonical Tarbosaurus rig
  profile with provenance.
- V5/V5.5 reference walk MP4: research/reference input with provenance and
  usage constraints; it is not an engine dependency unless reference fitting
  is explicitly requested.
- V8.2 `input/tarbosaurus_v8_2_iteration_b_base.glb`: immutable release fixture
  required for exact reproduction.

### Approved outputs and evidence

- V5/V5.5 `validated_result/**` and V8.2 `asset/**` are golden release outputs,
  not engine source.
- V8.2 `evidence/**`, `media/**`, and `RELEASE_MANIFEST.json` remain with the
  V8.2 release capsule. They establish acceptance/provenance; do not import
  them as runtime configuration.
- V5/V5.5 manifests, resolved profiles, solve/render/validation reports and
  checksums remain immutable release evidence. Future runs should emit the
  equivalent records into a run directory.

### Generated and ignored in future layouts

Ignore `.venv/`, `__pycache__/`, `*.pyc`, frame directories, temporary GLBs,
montages, encoded preview intermediates, self-contained HTML builds, package
inventory refreshes and transient JSON/stdout captures. The hundreds of V5
`validated_result/v5/showcase/_frames/**` images demonstrate why generated
frames must not live in the engine tree. Approved final GLBs/media/evidence are
promoted explicitly into a release directory by hash; they are not left as
ordinary build output.

## Legacy archive boundary

Keep the following immutable until the consolidated engine proves the relevant
goldens, then move them as whole history snapshots rather than importing them:

- V1/V2/V3 source, guides and migration documents.
- The copied V3 and V4 packages nested inside V4, V5 and V5.5.
- V5's refinement-only release pipeline and browser demos.
- V5.5's copied V5 directory and release packaging shell scripts.
- V8.2's release-local scripts after the engine adapter reproduces the exact
  approved SHA and the release verifier passes.

Documentation describing rationale and quality gates is useful reference, but
versioned README text, learning labs, agent prompts and demo HTML must not
become executable engine dependencies.

## Validation and render command inventory

| Lane | Committed command | What it proves |
|---|---|---|
| V5 build | `./procedural-animation-toolkit(v5)/scripts/reproduce_v5.sh` | Refines the preserved V4 GLB, builds browser assets, then validates V5. |
| V5 tests | `./procedural-animation-toolkit(v5)/scripts/run_v5_tests.sh` | V5 unit tests, JS syntax, and baked release validation. |
| V5 package | `./procedural-animation-toolkit(v5)/scripts/verify_package.sh` | Presence plus fixed 37/75/16 release facts; it is not a full hash inventory. |
| V5.5 build | `PYTHON_BIN=.venv/bin/python ./procedural-animation-toolkit(v5.5)/scripts/reproduce_v5_5.sh` | Full source-to-V4.5 constrained solve, then pivot/jaw/polish/transition packaging. |
| V5.5 tests | `PYTHON_BIN=.venv/bin/python ./procedural-animation-toolkit(v5.5)/scripts/run_v5_5_tests.sh` | V5 immutability, unit tests, V5.5 structural/body-balance validation and showcase check. |
| V5.5 package | `PYTHON_BIN=.venv/bin/python ./procedural-animation-toolkit(v5.5)/scripts/verify_package.sh` | Release facts and hash plus the complete V5.5 test wrapper. |
| V4/V5 render | `render_v4_validation.py`, `render_v5_validation.py`, `render_v5_stills.py` | VTK/Pillow/ffmpeg preview evidence; expensive and distinct from solver correctness. |
| V8.2 generate | `blender --background --python-exit-code 1 --python 'procedural-animation-toolkit(v8.2)/scripts/release_generate.py' -- --config 'procedural-animation-toolkit(v8.2)/config/release.json' --output /tmp/tarbosaurus_v8_2_rebuilt.glb` | Exact regenerated GLB SHA. Blender supplies NumPy; the script does not use `bpy`. |
| V8.2 verify | `blender --background --python-exit-code 1 --python 'procedural-animation-toolkit(v8.2)/scripts/verify_release.py' -- --config 'procedural-animation-toolkit(v8.2)/config/release.json' --candidate /tmp/tarbosaurus_v8_2_rebuilt.glb --output /tmp/v8_2_verify.json` | Full package inventory/media checks plus exact GLB/accessor contract. Requires `ffprobe`. |

The consolidated engine should expose one Python CLI for build/validate, while
render remains an explicit optional command with VTK/Pillow/ffmpeg dependencies.
The minimal solver dependency set is NumPy/SciPy/PyYAML; OpenCV belongs only to
reference fitting, VTK/Pillow to evidence rendering, and `ffprobe` to release
media verification.

## Unsafe assumptions to remove or fence

- Version directories are treated as import roots via `PYTHONPATH`; imports
  such as `eonproc_v3` are implementation-history names, not stable ownership.
- V5 is a refinement of a baked V4 GLB, while V5.5 regenerates from the source
  GLB. A single ambiguous `build` command could silently select the wrong
  lineage.
- `BipedV4Profile` carries Tarbosaurus defaults. Instantiating it without a
  profile makes species-specific numbers look generic.
- Clip catalogs and transition graphs are hard-coded in generator/build scripts.
- Release validators assert Tarbosaurus facts (37 clips, 75 joints, named
  actions and bone roles) directly instead of reading a release contract.
- V8.2 assumes little-endian float32 VEC4 rotation accessors with 16-byte
  stride, LINEAR interpolation, a common timeline, preserved JSON bytes, and
  writable non-sparse GLB buffer views. Those are validated for this release,
  not universal glTF guarantees.
- V8.2 writes byte ranges into the base GLB. A general GLB rewrite can reorder
  JSON, buffer views or float operations and break the approved hash while
  remaining visually equivalent.
- `verify_release.py` validates the package directory surrounding its own
  script. Running it from a source tree with generated files intentionally
  fails; future engine outputs must be outside the release capsule.
- V5/V5.5 renderers and validators share production readers/math, creating a
  correlated-failure risk. Preserve independent hash, raw-accessor and browser
  checks.
- V5.5 foot-pivot correction changes rest-node translations and two inverse
  bind slots while preserving toe origins and the rest-skinned mesh. Treating
  it as ordinary animation-track polish would corrupt rig semantics.
- Current shell wrappers mix system `python3`, optional `.venv` Python,
  Blender-bundled Python, Node, ffmpeg/ffprobe and VTK. Tool versions and
  capability checks need one environment report.
- Reference-video analysis is a provenance-sensitive optional input, not a
  deterministic requirement for every build.

## Exact minimal executable V8.2 vertical slice

There are two useful meanings of “minimal” and they must not be conflated.

### Generator-only slice — four files

1. `procedural-animation-toolkit(v8.2)/scripts/glb_math.py`
2. `procedural-animation-toolkit(v8.2)/scripts/release_generate.py`
3. `procedural-animation-toolkit(v8.2)/config/release.json`
4. `procedural-animation-toolkit(v8.2)/input/tarbosaurus_v8_2_iteration_b_base.glb`

With Blender 5.2's NumPy, these regenerate a candidate and fail unless its SHA
is exactly `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
This is the first migration target: preserve the four-file behavior through an
engine adapter and golden byte comparison.

### Release-accepted slice — all 13 V8.2 files

The current verifier intentionally requires the complete manifest inventory.
Therefore the smallest slice that can pass the committed package gate is the
entire V8.2 capsule: the four generator files above, approved output GLB,
`verify_release.py`, `README.md`, `RELEASE_MANIFEST.json`, three evidence JSON
files and two MP4s. It additionally requires `ffprobe`. Removing any inventoried
file must fail; the manifest alone is excluded from its own hash inventory and
is bound by the signed Git commit.

## Recommended migration order

1. Freeze golden commands/hashes for V5, V5.5 and V8.2; keep existing folders
   immutable.
2. Create the version-neutral package with quaternion math, GLB read/write,
   semantic rig, clip and profile schemas; add unit tests before moving solvers.
3. Port the four-file V8.2 generator behind a release adapter and require the
   exact approved SHA. Do not generalize its writer in this step.
4. Port V5.5's canonical V3/V4 solver stack once, followed by jaw, polish,
   transitions and pivot modules. Re-run V5.5 structural/body-balance gates.
5. Convert Tarbosaurus constants and clip recipes into validated data profiles;
   add negative schema/semantic tests.
6. Move package validation and evidence rendering into separate commands with
   distinct dependency groups.
7. Only after exact V8.2 and accepted V5.5 outputs reproduce, mark copied source
   trees legacy and stop editing them. Preserve approved release capsules by
   hash.

## Migration risks

### P0

None found. All required source, inputs and accepted V8.2 reproduction material
are committed.

### P1

1. **Exact-output regression:** replacing V8.2's NumPy quaternion math or
   byte-offset patching with SciPy/general GLB serialization can change floats
   or layout and lose the approved SHA. Gate the first adapter byte-for-byte.
2. **Wrong canonical copy:** mechanical deduplication may select V5 code over
   the six corrected V5.5 files, or keep both V5 and V5.5 jaw/polish copies.
   Migrate from an explicit source map and assert no duplicate module owners.
3. **Species leakage:** Tarbosaurus bone names, clip names, support/action
   values and fixed release counts are embedded in code. A nominally reusable
   engine would still be one-species software unless schemas make these data.
4. **Correlated validation loss:** migrating validators onto the same new
   parser/math as production could let the same defect pass twice. Retain
   release hashes, raw binary/accessor invariance, negative contract tests and
   browser/visual evidence as independent gates.

### P2 follow-up debt

- Deduplicate large identical fixtures through content-addressed storage or
  Git LFS only after repository policy is agreed; path moves alone are not a
  correctness requirement.
- Move browser runtime TypeScript after its manifest contract is formalized.
- Preserve media/render provenance as release metadata while reducing tracked
  intermediate frames.
