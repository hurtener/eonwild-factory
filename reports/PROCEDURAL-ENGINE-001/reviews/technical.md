# Independent technical review

## Verdict

- Commit reviewed: `a0e88479f16a6b72d66eb9e435a35f2e49439191`
- Base: `origin/main` at `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3`
- P0: **0**
- P1: **3**
- P2: **1**
- Release recommendation: **FAIL / do not promote**

The executable V8.2 build/validation slice is deterministic and reproduces the
approved artifact, but the release gate does not validate the evidence it
claims to require. Two additional implementation acceptance checks are also
not complete: comparison has no media/contact/editorial output, and command
failures do not consistently use a validated common report envelope.

## Findings

### P1-1: promotion accepts empty validation/comparison evidence and no render evidence

`src/eonwild_motion/pipeline/promote.py:30-34` checks only that
`validation.json` and `comparison.json` exist. It never parses either file,
validates its schema/status, or binds its artifact/profile/lock hashes to the
run. `render.json` is optional at `src/eonwild_motion/pipeline/promote.py:77-80`.
The manifest then embeds a newly computed validation object rather than hashes
of the required evidence (`src/eonwild_motion/pipeline/promote.py:81-105`), so
the manifest schema cannot detect substituted evidence.

Controlled reproduction from the reviewed head:

1. Built V8.2 successfully into
   `/tmp/eonwild-engine-promo.nAnnR4/work/runs/20260828T195410Z-build-12b811400a`.
2. Replaced both `validation.json` and `comparison.json` with `{}` and left the
   run without `render.json`.
3. Supplied schema-valid, distinct technical/visual reviewer names and invoked
   `eonwild-motion promote` to a new temporary destination.
4. Promotion exited 0 and created
   `/tmp/eonwild-engine-promo.nAnnR4/promoted-with-empty-evidence`.
5. Its promoted evidence files are each three bytes (`{}\n`), no
   `evidence/render.json` exists, and its promotion run report says `PASS`.

This contradicts the promotion requirement in
`reports/PROCEDURAL-ENGINE-001/plan.md:85-87`, the fail-closed design in
`reports/PROCEDURAL-ENGINE-001/architecture.md:470-475`, and the failure
boundary in `reports/PROCEDURAL-ENGINE-001/architecture.md:704-708`.

Required closure: parse and schema-validate every required evidence document,
require `PASS`, bind it to the exact run lock/profile/artifact hashes, require
the declared render evidence, and include immutable evidence hashes in the
release manifest. Add independent negative tests for empty, malformed, failing,
cross-run, wrong-artifact, and missing-render evidence.

### P1-2: `compare` does not implement the accepted comparison contract

The acceptance check requires structural, motion, contact, artifact, and media
differences plus a browsable review page
(`reports/PROCEDURAL-ENGINE-001/plan.md:109-113`). The architecture repeats
fixed-camera media and static-page requirements
(`reports/PROCEDURAL-ENGINE-001/architecture.md:449-456`).

`src/eonwild_motion/pipeline/compare.py:12-42` produces only an animation
contract and structural/accessor/byte difference object. The CLI writes only
JSON (`src/eonwild_motion/cli.py:169-203`); it emits no contact metrics, media,
or review HTML. The handoff itself records this omission at
`reports/PROCEDURAL-ENGINE-001/summary.md:77-84`.

This is not an unmentioned future enhancement: it is acceptance check 7 for
the submitted implementation. Required closure is either to implement the
declared comparison outputs and tests or formally narrow the accepted slice
before release review.

### P1-3: the common run-report contract is neither enforced nor universal

The plan requires every command to emit the same versioned envelope
(`reports/PROCEDURAL-ENGINE-001/plan.md:77-80`). The nominal writer emits that
shape, but never validates it (`src/eonwild_motion/reports.py:14-45`). The
schema requires thirteen keys while defining constraints for only `schema` and
`status`, and permits arbitrary extra data
(`schemas/motion/run-report.v1.schema.json:1-10`).

More directly, promotion failures before run-context creation return the bare
object `{"status":"FAIL","error":...}`
(`src/eonwild_motion/cli.py:271-321`). A controlled missing-run invocation
exited 1 with that exact two-field shape, without `schema`, `runId`, `command`,
timestamps, inputs, outputs, checks, or source lock. The outer `MotionError`
handler has the same bare-object behavior at
`src/eonwild_motion/cli.py:373-380`.

Required closure: make success and all failure paths produce the same
schema-validated envelope, fully constrain the schema's declared fields, and
add CLI negative tests asserting the envelope on pre-context failures.

### P2-1: documented tool pins are not runtime-enforced

The architecture requires Blender 5.2.0, an exact glTF Validator
version/checksum, and pinned FFmpeg/FFprobe
(`reports/PROCEDURAL-ENGINE-001/architecture.md:497-510`). The code invokes the
ambient `blender` and `gltf_validator` names
(`src/eonwild_motion/pipeline/build.py:82-107`,
`src/eonwild_motion/pipeline/render.py:11-34`, and
`src/eonwild_motion/pipeline/validate.py:225`) without checking a toolchain
lock before execution. The render integration test checks the observed Blender
version, and reports record observed versions, but production commands do not
fail closed on an unapproved executable/version/checksum.

This does not invalidate the reproduced exact GLB because its approved hash is
enforced, but render and validation reproducibility remain environment-based.

## Positive verification evidence

### Source, identity, ancestry, and hygiene

- `HEAD` was exactly the requested commit and was one direct child of the live
  `origin/main` SHA above (`git merge-base` returned the base and
  `git rev-list --count origin/main..HEAD` returned `1`).
- The commit contains an SSH signature that independently verified for
  `117486687+hurtener@users.noreply.github.com` with RSA fingerprint
  `SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`.
- Author and committer are Santiago Benvenuto using the hurtener GitHub no-reply
  identity; the global `lgads.tv` email was not used in the commit.
- `git diff --check` passed. The reviewed source was clean before this review
  report was written.
- The full diff is 63 files, 4,539 insertions and one `.gitignore` deletion.
  No implementation or binary changes exist under any legacy toolkit.
- Legacy toolkit tree objects match the base exactly:
  - V5: `dedabea120c3e2e7c82758eb351521fee8417e75`
  - V5.5: `aff45b0dc8da9dbf28343c0cc9715c9a6a0e255a`
  - V8.2: `0ef600321dfef270b5d29aa501b0a2674c9ce5f2`

### Clean-source build and tests

A detached worktree at the reviewed commit was created at
`/tmp/eonwild-engine-clean.oXjBio`. From that detached clean source, this exact
documented command passed:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Result: **19 passed, 0 skipped, 19.708 seconds**. The detached source remained
clean after the suite. The suite exercised:

- two independent Blender builds with byte-identical output;
- exact approved GLB SHA-256
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`;
- validate and compare commands;
- a real Blender 5.2.0 LTS fixed-camera render;
- dirty-source, existing-destination, and tampered-artifact promotion refusal;
- hierarchy, accessor type/component/stride, interpolation, timeline, bounds,
  cache/temporary-path, oversized-file, and undeclared-channel negatives;
- source cleanliness after non-promotion commands.

The resolved V8.2 lock SHA was
`d73e46ce80d4357e93b27e1dd008bb331fbbd5ac354d28ef4cdeba393862411d`.

### Contracts, neutrality, provenance, and dependency hygiene

- All ten committed motion schemas passed Draft 2020-12 metaschema validation.
- Profile resolution schema-validated all seven active profile/catalog
  documents and reproduced the committed lock.
- Package imports contain no imports from V5, V5.5, V8.2, or other legacy
  version folders.
- A source scan found no concrete `Bone_`, `PROC_`, Tarbosaurus, approved-hash,
  V8.2, iteration, or legacy-toolkit literal in `src/eonwild_motion`.
- No test is skipped and no `TODO` placeholder exists in the engine/tests.
- No cache or bytecode file was present in the reviewed package source; no new
  engine/catalog/profile/schema file approaches the binary fixture budget.
- The Python package declares Python `>=3.12`, `jsonschema==4.26.0`, and build
  dependency `setuptools==80.9.0`. The build/render paths use Blender-provided
  `bpy`, `mathutils`, and NumPy. License notes cover Python (PSF), Blender
  (GPL), jsonschema/setuptools (MIT), and glTF Validator (Apache-2.0); no new
  third-party model, texture, animation, or media was added.

## Review disposition

No implementation or media was modified. Because P1 is nonzero, this review
report is intentionally left uncommitted for the implementation owner and
integration gatekeeper to consume.

---

## Round-2 exact-head re-pin — 2026-08-28

### Verdict

- Fix commit reviewed: `8f9fc4538454492d695059172b96e8bd6e192eb6`
- Diff reviewed: `a0e88479f16a6b72d66eb9e435a35f2e49439191..8f9fc4538454492d695059172b96e8bd6e192eb6`
- P0: **0**
- P1: **0**
- P2: **1 retained** (the previously recorded ambient toolchain pinning debt;
  it did not reopen this narrow P1 remediation review)
- Release recommendation for the remediated P1 scope: **PASS**

This section supersedes the first-round release disposition for the three P1
findings. The remediation commit is the direct signed child of the reviewed
implementation commit. It does not alter any legacy toolkit tree.

### P1-1 closure: evidence-bound promotion now fails closed

`src/eonwild_motion/pipeline/promote.py:30-80` requires, parses, and
schema-validates validation, comparison, candidate-render, and baseline-render
evidence, then binds each document to the exact build run, profile lock, and
source commit. Lines 88-188 additionally bind the artifact, baseline, render
set, clip, frame, dimensions, camera, contact/static/media PASS facts, media
files, review HTML, and declared build outputs. Lines 196-265 copy the verified
bytes and record evidence/media hashes in the schema-validated manifest.

Independent controlled attempts against a clean exact-head build all exited 1
without creating their requested release destination:

- `validation.json = {}`: rejected as an unknown evidence schema;
- missing `render.json`: rejected as missing required evidence;
- comparison from another run ID: rejected by run binding;
- validation carrying a stale source SHA: rejected by source binding;
- render carrying a different artifact SHA: rejected by artifact binding.

The committed suite additionally covers malformed evidence, an evidence
document whose status is changed to FAIL, and stripped contact facts. All were
rejected. Conversely, a valid temporary promotion exited 0 and produced the
approved artifact plus all four evidence JSON files, both PNGs, and relative,
browsable `evidence/review.html`. The manifest's four evidence SHA-256 values
matched the copied files byte-for-byte; its candidate/baseline/review media
hashes and dimensions matched the copied media.

### P1-2 closure: comparison contract is executable and bound

The clean build and standalone compare command produced schema-valid
`eonwild.motion.comparison-report.v1` evidence with:

- structural and accessor PASS facts;
- contact PASS facts inherited through byte-exact protected-channel evidence;
- canonical fixed-camera 640x360 baseline and candidate PNGs;
- file and decoded-pixel SHA-256 values for both images;
- a responsive static review page using relative `media/baseline.png` and
  `media/candidate.png` references;
- explicit `visualApproval: false` and page text stating that technical
  evidence does not grant visual approval;
- exact run ID, profile SHA, profile-lock SHA, source commit, baseline SHA, and
  candidate SHA bindings.

The candidate PNG reproduced SHA-256
`0b1494dd526f4eeb8312fa28ab61310163f9a508f229c26e98c8db8a479b9202`;
decoded pixels reproduced
`5ca028e49545863349b16961b53bf18ca11bfcaa1d34fc4d1a19f185ad98e576`.

### P1-3 closure: all command reports use the constrained envelope

`schemas/motion/run-report.v1.schema.json` now closes additional properties and
constrains command, status, inputs, outputs, checks, source, profile,
tool-version, and timestamp fields. `src/eonwild_motion/reports.py:14-64`
validates reports before writing whenever a repository is known, while the
pre-context fallback emits the same complete shape. All five command success
reports, promotion rejection reports, missing-profile failures, missing-run
promotion failures, and the outer failure path were exercised.

An independent Draft 2020-12 validation pass accepted all 15 material reports
from the manual build/validate/compare/render/promote and five tamper cases.
The separate pre-context missing-run invocation also emitted a complete
schema-conforming `promote`/`FAIL` envelope with nullable unknown source and
profile fields rather than the former bare two-field object.

### Exact-head reproduction and invariance

From detached clean worktree `/tmp/eonwild-round2.ncuFze`, the documented
command completed with **21 passed, 0 skipped in 55.893 seconds**:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

An additional clean manual build reproduced approved V8.2 GLB SHA-256
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`
and resolved lock SHA-256
`eba6d05608e5b34c408dfeed5f9440ac85444b441d380c9279688e76d5c280ec`.
The V5, V5.5, and V8.2 legacy toolkit tree IDs remained respectively:

- `dedabea120c3e2e7c82758eb351521fee8417e75`
- `aff45b0dc8da9dbf28343c0cc9715c9a6a0e255a`
- `0ef600321dfef270b5d29aa501b0a2674c9ce5f2`

The fix commit has a valid SSH signature for
`117486687+hurtener@users.noreply.github.com` using RSA fingerprint
`SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`. `git diff --check` passed.
No implementation or media was modified by this reviewer.
