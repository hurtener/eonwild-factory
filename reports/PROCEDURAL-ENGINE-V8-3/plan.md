# PROCEDURAL-ENGINE-V8-3 — permanent channel and iteration model

## Objective

Add one repository-owned, schema-validated channel state so engine development
continues on one branch and one engine package while profiles carry release and
iteration identity. The initial state binds engine `0.1.0`, immutable `stable`
V8.2, and a mutable `working` pointer initially targeting the same V8.2
profile. This task does not add V8.3 motion or modify V8.2 bytes.

## Files intended to change

- `profiles/channels/state.json`
- `profiles/channels/history/*.json` when promotion records are exercised by
  temporary tests; no synthetic tracked promotion is created here
- `schemas/motion/channel-state.v1.schema.json`
- `src/eonwild_motion/contracts/models.py`
- `src/eonwild_motion/contracts/load.py`
- `src/eonwild_motion/contracts/resolve.py`
- `src/eonwild_motion/cli.py`
- `src/eonwild_motion/pipeline/promote.py`
- focused tests under `tests/`
- task evidence under `reports/PROCEDURAL-ENGINE-V8-3/`
- existing procedural-engine summary/evidence only if required to accurately
  describe the new command contract

No legacy toolkit, approved GLB, existing review report, main checkout, or
motion layer is in scope.

## Contract design

- Explicit paths continue to resolve exactly as before.
- `--profile stable` and `--profile working` resolve through
  `profiles/channels/state.json`.
- Each channel pointer binds profile path and SHA-256. `stable` additionally
  binds the immutable approved release/artifact SHA-256.
- `working` carries monotonically meaningful `iteration` and `revision`
  metadata. It is mutable only through an explicit future profile-update
  operation; ordinary build, validate, render, and compare commands are
  read-only.
- The resolved channel document and its SHA-256 become part of the resolved
  profile lock identity and every run-report profile binding.
- Promotion may update `stable` only after all existing approval/evidence
  gates pass. The update writes an immutable history record first, refuses
  overwrite, and atomically replaces channel state. Tests use temporary
  channel fixtures and destinations rather than the committed V8.2 state.

## Acceptance checks

1. `stable`, `working`, and explicit profile path resolution all succeed and
   produce deterministic lock/run bindings.
2. Missing, schema-invalid, hash-stale, and engine-version-mismatched channel
   states fail closed.
3. Mutating channel iteration/revision changes the resolved lock even when the
   target profile is unchanged.
4. Ordinary commands leave channel state and history byte-identical.
5. Stable state cannot be overwritten or changed by a non-promotion path.
6. A temporary approved promotion updates a temporary stable pointer, retains
   immutable prior state in history, and refuses history overwrite.
7. Source contains no hidden branch-name, V8.3, species, bone, clip, or
   per-version engine assumptions.
8. Existing exact V8.2 double-build, canonical-render, validation, comparison,
   promotion, and negative tests remain green.

## Verification command

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Assumptions and boundaries

- The initial working pointer intentionally targets V8.2. Its iteration label
  describes engine work state, not a new motion artifact.
- Git history is not the channel history mechanism; immutable JSON history
  records are required for stable changes.
- No channel operation creates a Git branch or copies a versioned engine
  directory.
- Hip balance and V8.3 motion remain explicitly deferred.
