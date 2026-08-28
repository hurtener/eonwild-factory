# V8.3 exact-head independent technical review

## Verdict

- Commit: `c2701d09420630de8634c1a55c6c1c503a7b8f5f`
- Parent/diff base: `42f5fe6eb00597b589d697b8ddf4fc2f90dd13dc`
- P0: **0**
- P1: **1**
- P2: **0**
- Recommendation: **FAIL technical acceptance until the V8.3 evaluator is executable and fail-closed**

The selected GLB is deterministic and its central motion measurements withstand
independent spot reproduction. V8.2 remains exact stable, semantic write
ownership is enforced, and the working-only channel boundary is correct. The
blocking issue is the acceptance seam: the committed validator advertises the
new balance/contact/upper-body gates but does not evaluate them. It trusts
self-authored booleans in a hash-pinned JSON document, for which no executable
producer or schema is committed.

This review was run from a detached clean checkout of the exact commit. The
active worktree contained concurrent visual-review/media work; this report did
not inspect those later uncommitted bytes as evidence for `c2701d0` and did not
modify engine or media files.

## Finding

### P1-1: the release validator trusts V8.3 PASS assertions instead of evaluating the normative gates

The revised contract says the evaluator **must** reject absent/non-finite
metrics and prove the double build, controlled pelvis progression,
final-skinned contact, rocker/passive/receiving timing, upper counterbalance,
head stability, and export seam
(`reports/PROCEDURAL-ENGINE-V8-3/evaluation/contract.md:54-60`). The profile also
advertises `v8.3-balance`, `final-skinned-contact`, and
`upper-counterbalance` as validators
(`profiles/v8.3/profile.json:18-19`).

No such evaluator is present in the committed source. The documented commands
build, validate, hash, and render, but none regenerates or evaluates
`amplitude-sweep.json`, `machine-evaluation.json`,
`final-skinned-witnesses.json`, or the normative thresholds
(`reports/PROCEDURAL-ENGINE-V8-3/commands.md:5-32`). There is likewise no JSON
Schema for any of the V8.3 evaluation/evidence envelopes under `schemas/` and
no test references any of the V8.3 hard-gate selectors.

The actual acceptance path reads the profile-bound machine-evaluation JSON and
checks only that eight configured selector values are literal `true` and one
configured count converts to zero
(`src/eonwild_motion/pipeline/validate.py:40-68`). `validate_candidate` does
perform the valuable artifact hash, structure, declared-accessor, unchanged
region, package, and glTF checks, but then delegates all V8.3 biomechanics to
that selector reader (`src/eonwild_motion/pipeline/validate.py:293-335`). It
does not check the evidence document's schema/status, candidate SHA, selected
scale, threshold identity, evidence-file hashes, metric presence/finiteness, or
the relation between metrics and thresholds.

An independent controlled negative made a copy of the bound document with:

- `status: FAIL`;
- `artifactSha256` set to 64 zeroes;
- `selectedScale: 999`;
- every entry under `metrics` replaced with `null`.

With the nine selected booleans/count left unchanged,
`contact_inheritance_facts` returned `status: PASS` and
`protectedChannelsByteExact: true`. This is precisely the correlated-validator
failure the contract was intended to prevent. Hash-pinning the document
protects it from accidental mutation after authorship; it does not establish
that its assertions were derived correctly, nor let a clean checkout reproduce
them.

Required closure: commit a deterministic evaluator (and evidence schemas) that
derives the sweep selection and every advertised V8.3 gate from the bound
source/profile/thresholds and final exported GLBs; bind all input and output
hashes in its report; invoke it from validation or validate an independently
produced immutable report with equivalent provenance; and add negative tests
for FAIL status, candidate/threshold/cross-file mismatch, missing/non-finite
metrics, false strongest-pass selection, and tampered final-skinned evidence.

## Independently passing evidence

### Exact build and strongest-output sweep

- Clean full suite:
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v`
  — **27 tests, 0 skipped, PASS** in 72.721 seconds.
- Two additional clean CLI builds, one through `working` and one through the
  explicit V8.3 profile, both emitted exact SHA-256
  `b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`;
  the working candidate also passed the documented validator.
- An independent Blender sweep regenerated all five serialized candidates from
  the committed layers. Their hashes exactly matched the committed sweep:
  `0.5=b5fc582e...`, `0.625=e1394f73...`, `0.75=7366d681...`,
  `0.875=bb755f19...`, and `1.0=9a6868b0...`.
- Both additional builds regenerated `layer-metrics.json` byte-for-data
  identically. This confirms the layer output and its local metrics are
  deterministic. The classification of `0.5` as the only/strongest all-gates
  PASS still depends on the uncommitted evaluator described in P1-1.

### Independent final-skinned/head facts

Using Blender 5.2.0 LTS directly on the committed V8.2 and V8.3 root-motion
actions, the six declared witness vertices were evaluated after skinning at all
977 samples. The independent maxima exactly reproduced
`final-skinned-witnesses.json`:

- axis maxima: X `0.00004601478576660156 m`,
  Y `0.00010395050048828125 m`, Z `0.0000912761315703392 m`;
- Euclidean maximum: `0.00011930971920265128 m`;
- vertex count: `59169` in both inputs; action range:
  `0.0..97.66957092285156` in both inputs.

Those values clear the normative `0.0005 m` worst-axis and `0.002 m`
Euclidean gates. A separate 120-phase Blender evaluation measured maximum
candidate-vs-baseline head-world rotation delta `0.0382166 degrees` and a
candidate head seam of `0.0 degrees`, within the declared `0.1 degree`
head-world delta cap. These independent checks support the artifact; they do
not repair the missing executable acceptance path.

### Ownership, invariance, and preservation

- Artifact inspection found 65 changed walk accessors across the two declared
  walk clips. Every change was within the 33 `(semantic node, property)`
  channels expanded from the three layers; zero bytes changed outside declared
  accessor regions. The build path separately rejects undeclared layer writes,
  wrong clip sets, wrong accessor ownership, and non-packed float patches
  (`src/eonwild_motion/pipeline/build.py:17-58`).
- Root/timeline/JSON structure and all nondeclared tracks remain byte-exact by
  `artifact_difference`; no non-walk motion file or engine literal was added.
  Independent scanning found none of `Bone_`, `PROC_`, `Tarbosaurus`,
  `tarbosaurus`, `v8.2`, `v8.3`, `v8_3`, or either approved SHA in
  `src/eonwild_motion/**/*.py`.
- The stable object and top-level generation in
  `profiles/channels/state.json` are byte-for-data identical to the parent;
  only working advanced from V8.2 iteration 0/revision 1 to V8.3 iteration
  1/revision 2. An ordinary working build left channel-state SHA
  `a44153a9ef45d9a1e5c734c9f9423945746333987e81ccce824bea256cc6e3a8`
  unchanged.
- V8.2 profile, lock, release manifest, and approved GLB are byte-identical to
  the parent. V8.2 remains SHA-256
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`;
  its release manifest remains
  `51f493aaae13fe46d8b6d3600ec1a8de117c2ee39beb6e05159398cacb21fada`.

### Media/report binding and identity

- All three video hashes match the media manifest. `ffprobe` independently
  reports H.264/YUV420p, 960x540, 24 fps, 240 frames, and 10.000 seconds for
  each. The 18 PNGs have the declared 9 full-body/9 foot split, dimensions
  960x540 and 960x320 respectively, and the standard sorted `shasum -a 256`
  lines digest exactly matches
  `a6caa7c7c70dbdaaf6ffe32831c8e5a24cb3915af0cf9b163faca7b0fc140391`.
- The review page SHA-256 matches its manifest binding:
  `aaf3ec4f45ad16ff187e3936b8df23e8547be022596102c3dcd24b99454f3156`.
  The manifest truthfully leaves visual approval pending.
- `c2701d0` is a direct child of `42f5fe6`, descends from `origin/main`, and has
  a valid SSH signature for
  `117486687+hurtener@users.noreply.github.com`, key fingerprint
  `SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`. Author and committer are
  `Santiago Benvenuto <117486687+hurtener@users.noreply.github.com>`.

No implementation, catalog, profile, asset, evidence, or media file was
changed by this reviewer. Per instruction, this report is not committed.
