# PROCEDURAL-ENGINE-001 — canonical procedural engine architecture

## 1. Decision

Create one Python distribution named `eonwild-motion` with one stable CLI,
`eonwild-motion`. Versions such as V8.2 are immutable release profiles and
manifests. Biomechanical changes such as chest balance or future hip balance
are versioned motion layers. Neither creates a package copy, a toolkit copy,
nor a branch.

The first implementation is not a framework-only scaffold. Its definition of
done is a complete V8.2 vertical slice:

```text
immutable V8.2 base GLB
  -> schema-valid resolved profile
  -> deterministic chest-balance layer
  -> exact approved GLB
  -> technical validation
  -> fixed-camera render
  -> baseline comparison
  -> approval-bound promotion
```

The existing V8.2 script is sufficiently small and deterministic to migrate
without carrying its release-folder boundary forward. Its accepted SHA and P1
negative tests become compatibility fixtures for the new engine.

## 2. Canonical root layout

```text
pyproject.toml
uv.lock
README.md

src/
  eonwild_motion/
    __init__.py
    __main__.py
    cli.py
    errors.py
    paths.py
    hashing.py
    reports.py
    contracts/
      load.py
      resolve.py
      semantic_rig.py
      family.py
      species.py
      motion.py
      layer.py
      profile.py
    glb/
      container.py
      accessors.py
      animation.py
      compare.py
    math/
      quaternion.py
      transforms.py
    layers/
      registry.py
      chest_balance_world_relative_v1.py
    pipeline/
      context.py
      build.py
      validate.py
      render.py
      compare.py
      promote.py
    blender/
      entrypoint.py
      scene.py
      render.py

schemas/
  motion/
    semantic-rig.v1.schema.json
    family.v1.schema.json
    species.v1.schema.json
    motion-spec.v1.schema.json
    motion-layer.v1.schema.json
    release-profile.v1.schema.json
    resolved-profile.v1.schema.json
    run-report.v1.schema.json
    artifact-manifest.v1.schema.json
    comparison-report.v1.schema.json
    promotion.v1.schema.json

catalog/
  rigs/
    tarbosaurus-v8.semantic-rig.json
  families/
    heavy-predatory-biped.v1.json
  species/
    tarbosaurus.v8.json
  motions/
    relaxed-walk.v8_1-respin.json
  layers/
    chest-balance-world-relative.v1.json
  render-sets/
    locomotion-review.v1.json

profiles/
  v8.2/
    profile.json
    profile.lock.json

inputs/
  sha256/
    bf/
      bfe8e833.../
        tarbosaurus_v8_2_iteration_b_base.glb
        provenance.json

releases/
  v8.2/
    manifest.json
    approvals.json
    artifacts/
      a2/
        a2cf73a3...glb
    evidence/
      official-balance.json
      structural-mechanical.json
      reproduction-verify.json
    media/
      walk-side.mp4
      comparison-three-quarter.mp4

legacy/
  catalog.json
  README.md

tests/
  unit/
  contract/
  integration/
  blender/
  negative/
  fixtures/
    tiny-rig/

reports/
  PROCEDURAL-ENGINE-001/
```

### Tracked versus generated

`src`, `schemas`, `catalog`, `profiles`, `inputs`, `releases`, `legacy`,
`tests`, and task documentation are tracked source/release records.

All ordinary command output goes to an external work root:

```text
<work-root>/
  runs/<run-id>/
    resolved-profile.json
    run-report.json
    command.log
    artifacts/
    validation/
    renders/
    comparisons/
    promotion-candidate/
  cache/sha256/
```

The default work root is the platform cache/data location, not the repository.
CI must pass an explicit temporary directory. `.eonwild/` may be supported as
an opt-in developer work root only if it is ignored and the CLI proves it is
not inside a tracked path. A normal build never writes to `inputs/`,
`releases/`, `reports/`, or any legacy folder.

`promote` is the only command allowed to write a tracked release directory. It
copies from a verified run using content addressing and refuses to overwrite
any existing path, version, hash, evidence, or approval.

## 3. Package boundaries

### `contracts`

Loads JSON, validates it against a schema version, resolves references, and
emits a fully expanded `resolved-profile.json`. No solver may read arbitrary
profile dictionaries directly. Typed domain objects are the boundary.

Contract resolution is pure: the same files and hashes yield the same lock.
All references are IDs plus expected SHA-256, never ambient relative imports.

### `glb`

Owns GLB container parsing, accessor layout/timeline inspection, bounded
in-place binary edits, and byte/semantic comparisons. It knows glTF node
indices and names only through the resolved semantic-rig mapping. It does not
know Tarbosaurus, V8.2, chest balance, or hip balance.

The first slice preserves the proven direct-accessor strategy because exact
V8.2 binary parity is required. A later Blender-native animation writer may be
added behind the same artifact contract only after measured equivalence.

### `math`

Contains dependency-light quaternion and transform operations. Functions are
unit tested independently and contain no rig, family, species, or profile
logic.

### `layers`

Contains the registered procedural algorithms. Each implementation accepts:

- an immutable animation/pose view;
- resolved semantic roles;
- validated parameters;
- declared read/write channel capabilities;
- deterministic execution context.

It returns a patch set and metrics; it does not write a GLB or select files.
The registry maps a versioned implementation ID, such as
`chest_balance_world_relative@1`, to code. Unknown versions fail closed.

### `pipeline`

Orchestrates commands, stage ordering, immutable input reads, external work
directories, manifests, validation, evidence, and promotion. It is the only
layer allowed to perform production filesystem mutations.

### `blender`

Is an internal committed Blender entrypoint, invoked as:

```text
blender --background --python-exit-code 1 --python <entrypoint> -- <request>
```

The host CLI writes a schema-valid request into the run directory. Blender
reads it and writes a schema-valid stage report. Host Python never imports
`bpy`; Blender modules do not become a second package or CLI. Inline MCP
Python is not a production path.

## 4. Contract model

Schemas are authoritative. Each document has `schema`, `id`, `version`, and
content hash fields. Unknown fields fail unless a schema explicitly declares
an extension object.

### Semantic rig

Maps reusable anatomy/control roles to concrete GLB nodes and declares:

- coordinate system, handedness, forward/up axes, units, and rest basis;
- unique node mapping for root, pelvis, spine, chest, neck, head, jaw, tail,
  limb segments, feet, digit roots, and optional controls;
- required parent relationships expressed through semantic selectors;
- rest-transform and inverse-bind expectations;
- mirrored limb pairs;
- channel/accessor requirements;
- supported contact anchors and deformation witnesses;
- skeleton/family compatibility version.

Engine code asks for `roles.pelvis` or `roles.foot.left`, never a model bone
name. Concrete names remain data in the rig mapping.

### Biomechanical family

Declares the reusable engineering archetype:

- compatible semantic-rig contract and required roles;
- morphology bounds and explicit proposal-required outcomes;
- locomotion grammar and required motion semantics;
- contact model, default layer capabilities, and stage ordering constraints;
- allowed family-level parameters and safety bounds;
- capability hooks, LOD/bone policy, and provenance.

`heavy-predatory-biped.v1` is initially `provisional`. One Tarbosaurus release
proves an engine slice, not family reuse. Acceptance requires a second,
meaningfully different compatible morphology without a species branch.

### Species

Composes, rather than subclasses:

- taxon/morphology references and their provenance;
- selected family version;
- concrete semantic-rig mapping;
- source model/input hashes;
- evidence-backed species overrides;
- presentation and material references;
- uncertainties and gameplay-tuning disclosures.

It contains no algorithm implementation and cannot expand a layer's channel
permissions.

### Motion specification

Defines the semantic animation product:

- required clip semantic IDs and concrete clip bindings;
- loop, duration, sample/timeline, and interpolation contracts;
- root-motion policy and nominal speed/stride;
- contact phases/events and action windows;
- required tracks, invariants, render shots, and comparison metrics;
- provenance and family compatibility.

For V8.2, one motion specification binds relaxed-walk root-motion and in-place
clips without embedding those concrete clip strings in engine code.

### Motion layer

Defines a deterministic transformation:

- implementation ID and version;
- stage: source, pre-IK, IK/contact, post-IK, stabilization, or export;
- declared semantic-role/channel reads and writes;
- parameter schema and bounds;
- ordering dependencies and conflicts;
- required invariants before and after;
- metrics and evidence emitted;
- determinism class and tool requirements.

A layer cannot write a channel merely because it can find it in the GLB.
Pipeline patch application rejects undeclared writes, duplicate writers, and
changes outside the resolved allowlist.

### Release profile

Selects immutable inputs and composes exact versions of rig, family, species,
motion specifications, layers, render sets, validators, expected outputs, and
promotion gates. A profile is declarative; it contains no Python path or
inline expression.

Profiles may reuse catalog documents by hash, but inheritance never remains
implicit at execution time. `profile.lock.json` is the fully resolved,
hash-bound execution record. Changing any referenced document produces a new
lock and therefore a new run identity.

### Artifact and run manifests

Every command emits the common pipeline envelope required by the asset-factory
RFC:

- run ID and command;
- engine/package/tool versions;
- resolved-profile hash;
- all input/output paths, kinds, sizes, and SHA-256 values;
- stage status and timing;
- metrics, warnings, and errors;
- provenance and approval references;
- deterministic-equivalence class;
- dirty-source and work-root checks.

Console output is a convenience, never the only success record.

## 5. V8.2 profile composition

The first profile resolves to:

```text
profile: v8.2
input:
  bfe8e833...  # included iteration-b base
rig:
  tarbosaurus-v8 semantic mapping
family:
  heavy-predatory-biped.v1 (provisional)
species:
  tarbosaurus.v8 engineering profile
motion:
  relaxed-walk.v8_1-respin
layers:
  - chest_balance_world_relative@1
output:
  a2cf73a3...
render-set:
  locomotion-review.v1
validators:
  - contract
  - hierarchy
  - accessor
  - timeline
  - quaternion
  - local-delta-bound
  - unchanged-region
  - artifact-inventory
  - media-facts
```

The migrated layer reads pelvis/chest/neck/head rotations through semantic
roles, writes only the declared chest/neck/head rotation channels, and carries
the current gain, residual fractions, basis, and local-delta bounds as profile
parameters. Exact V8.2 output SHA is a compatibility gate, not hard-coded
inside the algorithm.

## 6. CLI contract

All commands accept `--profile`, `--work-root`, and `--json-output` where
applicable. They return 0 only when every required gate passes and always emit
a run report, including on failure.

### Build

```sh
eonwild-motion build \
  --profile profiles/v8.2/profile.json \
  --work-root /tmp/eonwild-motion \
  --json-output /tmp/eonwild-motion/build.json
```

Resolves and locks contracts, verifies immutable input hashes, executes the
layer DAG, applies allowlisted patches, writes a candidate artifact, and
validates the declared output hash/equivalence. It never writes a release.

### Validate

```sh
eonwild-motion validate \
  --profile profiles/v8.2/profile.json \
  --artifact /tmp/eonwild-motion/runs/<run>/artifacts/candidate.glb
```

Runs schemas, hierarchy, accessors, timelines, transforms, bounds, unchanged
regions, provenance, inventory, external glTF Validator, and profile-specific
gates. Validation of a release additionally checks its immutable manifest,
approval chain, and media facts.

### Render

```sh
eonwild-motion render \
  --profile profiles/v8.2/profile.json \
  --artifact <candidate.glb> \
  --view-set locomotion-review.v1
```

Invokes the committed Blender entrypoint with fixed engine, lighting, cameras,
frame range, FPS, resolution, background, and color-management settings. It
emits frame/media hashes plus FFprobe facts. Render evidence supplements but
never replaces technical validation.

### Compare

```sh
eonwild-motion compare \
  --baseline release:v8.2 \
  --candidate run:<run-id> \
  --motion relaxed-walk
```

Produces:

- GLB JSON and buffer-region differences;
- per-node/channel/timeline differences;
- root/stride/contact/toe/loop metrics declared by the motion spec;
- fixed-camera side-by-side media;
- a static browsable review page;
- a machine-readable comparison verdict.

Thresholds come from the profile/motion contract. The command does not decide
visual approval.

### Promote

```sh
eonwild-motion promote \
  --run <run-id> \
  --release v8.2 \
  --approvals <independent-approvals.json>
```

Revalidates the run from hashes, requires technical and independent visual
approvals, copies the artifact/evidence into a new content-addressed release,
and writes the manifest last. It fails if the release/version/path already
exists, the repository is dirty outside the promotion set, the run used
unlocked inputs, or any report is absent/failing. Promotion is never implicit
in `build`.

### Supporting commands

`eonwild-motion doctor` records tool versions/capabilities.
`eonwild-motion resolve` emits a lock without building.
`eonwild-motion verify-release` replays manifest verification from a clean
checkout. These support the five primary commands but do not create a second
entry surface.

## 7. Execution and dependency strategy

### Host environment

- Python version pinned in `pyproject.toml` and lockfile.
- `jsonschema` is the only planned runtime Python dependency for complete,
  standard contract validation; JSON is used for canonical contracts to avoid
  a YAML runtime dependency.
- Packaging/build tooling and test tooling are development-only and locked.
- Tests use the standard library where practical; no dependency is added for
  convenience alone.

### Blender environment

- Blender 5.2.0 LTS is pinned for V8.2 compatibility.
- NumPy is consumed only from Blender's bundled Python for transform math.
- Host code shells out to Blender; it does not attempt to install or mock
  `bpy`.
- Blender version changes require a new toolchain lock plus artifact and
  visual comparison evidence.

### External tools

- Khronos glTF Validator is mandatory for promotion and pinned by exact
  version/checksum.
- FFmpeg/FFprobe is mandatory for encoded render evidence and pinned.
- No network is required for build/validate/render/compare/promote.
- Optional acceleration is introduced only behind measured, deterministic
  equivalence; MPS is not assumed by the contract.

### Path and process safety

- Inputs are opened read-only and verified before parsing.
- Work roots are canonicalized and rejected if they overlap tracked immutable
  inputs/releases or legacy archives.
- Subprocess arguments are arrays, never interpolated shell commands.
- Runs use atomic writes and manifest-last completion.
- Cache hits require the full key: engine version, resolved-profile hash,
  input hashes, toolchain lock, and command parameters.

## 8. Layer graph and conflict rules

The profile resolves a directed acyclic graph. A valid graph has one writer per
channel per stage unless a later layer explicitly consumes the earlier layer's
named output. The resolver rejects cycles, implicit order, unknown
implementations, undeclared role access, incompatible root-motion policies,
and overlapping writes without a declared composition rule.

For every layer the pipeline snapshots:

- bytes/accessors before application;
- declared input channels;
- proposed patch channels;
- bounds/invariants;
- bytes/accessors after application.

It then proves that all undeclared GLB regions are unchanged.

## 9. Future hip balance without an engine copy

Hip balance is introduced as catalog/profile data plus one reusable layer
implementation:

```text
pelvis_balance_pre_ik@1
  reads:
    pelvis phase, root motion, leg chain state, contact schedule
  writes:
    declared pelvis rotation/translation targets
  emits:
    load-side, lateral shift, vertical shift, roll, bound metrics

leg_contact_resolve@1
  consumes:
    pelvis targets and approved foot/contact constraints
  writes:
    declared leg/foot solve channels
  proves:
    stride, world-contact, toe rocker, loop and extension invariants
```

A candidate profile selects these layers after the existing V8.2 balance layer
and binds conservative parameter ranges. The resolved order is explicit:

```text
source locomotion
  -> approved upper-body balance
  -> pelvis balance target
  -> leg/contact re-solve
  -> approved toe-rocker/contact reapplication
  -> stabilization
  -> validation
```

The first hip profile is an experiment, not a release. It builds in a new run
directory and compares against immutable V8.2. If rejected, its run/evidence
remains outside source and no engine code is duplicated. If accepted, promotion
creates a new profile/release manifest on the same branch after review.

The profile must carry exact lower-body invariants from the accepted baseline:
root stride, foot/toe world witnesses, loop closure, channel ownership, and
contact timing. Pelvis motion may move descendants, so “unchanged local leg
channels” is not sufficient; the contact resolver must prove world-space
equivalence or an explicitly approved bounded improvement.

## 10. Legacy migration

### Freeze first

`legacy/catalog.json` records each current legacy root, Git provenance,
inventory hash, accepted outputs, known status, and whether it is frozen,
migrating, migrated, or rejected. Engine imports from legacy paths are
forbidden.

Initially catalog, but do not move:

- `procedural-animation-toolkit(v5)`
- `procedural-animation-toolkit(v5.5)`
- `procedural-animation-toolkit(v8.2)`
- legacy showcases and their release reports

This avoids rewriting history or pretending old packages already satisfy the
new contracts.

### V8.2 first

1. Hash and register the included iteration-b input and approved artifact.
2. Extract semantic rig mapping, provisional family, species engineering
   profile, relaxed-walk motion spec, and chest-balance layer descriptor.
3. Port only the minimal proven math/GLB/solver logic into package ownership.
4. Re-run the complete P1 negative matrix.
5. Require exact approved SHA, fixed-camera evidence, and independent review.
6. Promote V8.2; mark its legacy entry `migrated` only after acceptance.

### V5 and V5.5 later

1. Inventory accepted clips, inputs, rig mappings, pivots, posture parameters,
   and reports without executing legacy code through the new engine.
2. Classify each behavior as reusable family data, species override, motion
   spec, procedural layer, validator, or obsolete experiment.
3. Implement the smallest missing generic layer.
4. Build a candidate profile and compare against its historical evidence.
5. Record exact parity or an intentional, reviewed difference.
6. Promote only accepted results; otherwise retain the archive unchanged.

No migration copies `toolkit/v1` through `toolkit/v5.5` into `src`. Historical
guides remain evidence, not executable ownership.

## 11. Test architecture

### Unit

- Quaternion normalization, inverse, multiplication, rotation vectors, and
  transform hierarchy.
- Content hashing, path containment, atomic writes, and cache keys.
- Role selector and parent resolution.
- Layer DAG ordering/conflict detection.

### Contract

- One positive fixture for every schema.
- Missing/unknown versions and fields.
- Invalid semantic parents, duplicate roles, incompatible family/species
  bounds, undeclared layer channels, cycles, and hash drift.

### GLB fixture

A tiny original/licensed synthetic biped GLB covers SCALAR/VEC4 accessors,
shared and split timelines, LINEAR/STEP/CUBICSPLINE samplers, hierarchy,
rotation patches, and byte-region equivalence. It stays within the configured
fixture budget and carries provenance.

### V8.2 compatibility

- Exact clean rebuild SHA.
- Existing bad-parent, interpolation, timeline, component/type/stride, zero
  bound, cache, temp/rejected, and oversized-file negatives.
- Exact changed-accessor allowlist and unchanged GLB JSON/regions.
- Both root-motion and in-place clips.

### Command integration

- Every command writes a valid pass/fail run report.
- Failure reports retain raw diagnostics.
- Build/validate/render/compare leave tracked source clean.
- Interrupted runs never appear complete.
- Promote is manifest-last, no-overwrite, approval-bound, and idempotently
  refuses the same release.

### Visual and runtime evidence

- Fixed side, front/rear, and three-quarter views for V8.2 relaxed walk.
- Encoded duration/frame/resolution/hash checks.
- Existing side and comparison media remain hash-identical during migration.
- Babylon/WebGL2 loading belongs to the broader factory release gate; the CLI
  records and consumes its external report rather than embedding renderer code
  in the Python package.

## 12. Promotion and version policy

- Package/engine version tracks code compatibility.
- Contract schema versions track data shape.
- Layer implementation versions track algorithm semantics.
- Catalog family/species/motion versions track domain data.
- Release profile versions identify a locked composition.
- Artifact hashes identify bytes.

These versions are independent. A parameter change creates a new profile lock,
not a package copy. A bug fix that intentionally preserves output may bump the
engine and retain artifact compatibility evidence. A changed accepted artifact
requires a new immutable release version; an existing version is never
rewritten.

Git branches are work coordination, not release storage. `main` contains all
accepted profiles and engine versions. Experiments are run IDs and candidate
profiles; rejected experiments never require permanent engine forks.

## 13. Failure and rollback boundaries

- Contract resolution failure: no Blender invocation.
- Input/hash failure: no parsing or cache reuse.
- Layer failure: no patch application beyond the disposable run.
- Validation/render/compare failure: no promotion candidate.
- Approval failure: no release write.
- Promotion failure before manifest: incomplete target is removed or
  quarantined; existing releases remain untouched.
- Post-promotion rollback: deprecate through a new signed record; never mutate
  or delete the released bytes/manifest.

Legacy archives remain the fallback evidence until each migration is accepted.
The first implementation may be abandoned without changing V5, V5.5, V8.2,
their showcases, or main.

## 14. Exact implementation handoff

The implementation owner should take the following bounded slice:

1. Obtain explicit WS00/WS03/WS07/WS08 path authority for the proposed package,
   schemas, catalogs, profiles, validation, and task evidence.
2. Add the root package/configuration skeleton exactly once; do not create
   versioned package directories.
3. Implement schema loading/resolution and the shared run-report envelope.
4. Implement minimal quaternion/GLB modules by porting only code used by the
   accepted V8.2 generator/verifier.
5. Implement `chest_balance_world_relative@1` behind semantic roles and layer
   channel permissions.
6. Add the V8.2 contracts/profile/lock and content-addressed input registration.
7. Implement `build` and `validate`; require exact V8.2 SHA plus the complete
   negative matrix before proceeding.
8. Implement Blender request/report boundary and `render`.
9. Implement structural/motion/media `compare` and its static review page.
10. Implement approval-bound, no-overwrite `promote`.
11. Run clean-checkout verification and independent technical/visual review.
12. Promote V8.2 only after all gates pass; leave V5/V5.5 and hip balance
    untouched.

Stop and return to architecture if implementation requires weakening a gate,
embedding concrete bone/species names in code, writing generated work under
source, mutating an existing release, introducing an unlicensed reference, or
changing a canonical upstream schema without the integration owner.
