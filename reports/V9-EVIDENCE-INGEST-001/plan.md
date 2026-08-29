# V9 evidence ingest remediation plan

Task: `V9-EVIDENCE-INGEST-001` (rights-gated remediation)

## Bounded scope

Remove the ten duplicate MP4s previously copied into this productized
worktree. Retain their exact source paths, SHA-256 hashes, byte sizes, ffprobe
facts, 24 fps limitation, and filename-derived candidate mappings in the
receipt manifest, but mark the files as externally received and unavailable
for engine/reference use until project ownership or reuse rights are confirmed.
This remediation does not inspect or adjudicate choreography, establish
biological truth, modify engine or motion code, modify GLBs, re-encode media,
alter source files, or commit changes.

## Ownership and intended files

The remediation owns only these productized-worktree paths:

- `assets/examples/tarbosaurus/v9_evidence/` — remove only the ten named
  duplicate MP4s; do not remove or modify the external source files.
- `reports/V9-EVIDENCE-INGEST-001/plan.md` — this remediation plan.
- `reports/V9-EVIDENCE-INGEST-001/audit.md` — rights-gated receipt audit.
- `reports/V9-EVIDENCE-INGEST-001/audit.json` — receipt/provenance manifest;
  every file keeps source facts while `stored_path` becomes `null`.
- `reports/V9-EVIDENCE-INGEST-001/commands.md` — reproducible removal and
  validation commands.
- `reports/V9-EXTENSION-001/reference-coverage.md` and
  `reports/V9-EXTENSION-001/reference-coverage.json` — external-receipt
  coverage and remaining-gap bookkeeping only.
- `reports/V9-EVIDENCE-INGEST-001/narrow-gauge-contract.json` — remove this
  unneeded duplicate report-level copy; the canonical contract remains under
  `reports/V9-GAIT-FOOT-AUDIT-001/` and is untouched.

No files under engine, motion, procedural-animation-toolkit, GLB, source
research packages, or the external source checkout are in scope. Existing
unrelated worktree changes must remain untouched.

## Exact source and duplicate set

Source root (preserved):
`/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence`

Productized duplicate root (removal target):
`assets/examples/tarbosaurus/v9_evidence`

The exact basenames are:

1. `BITE MISS + RECOVERY — front three-quarter.mp4`
2. `BODY SHOVE → SMALL STUMBLE → RECOVERY.mp4`
3. `FEEDING + TEAR:PULL — fixed side.mp4`
4. `GROUNDED COMMITTED BITE — fixed side.mp4`
5. `LISTEN REACTION — front three-quarter.mp4`
6. `RUN START-RUN-RUN STOP.mp4`
7. `running-sustained-left.mp4`
8. `sprint-left.mp4`
9. `walking-back-gauge.mp4`
10. `walking-front-gauge.mp4`

The prior ingest observed productized HEAD
`85de1f2ceaa75427f74090a47d2b6a1ca3c6022a`; the V8.3 audit pin
`195a8b4707997b3309f86f8821217ed1d7e9c22a` is its ancestor. This remediation
does not move, reset, or commit that worktree.

## Checks

1. Confirm the external source still contains exactly these ten regular MP4s;
   re-hash every source and preserve the existing ffprobe facts.
2. Resolve the productized removal targets explicitly, confirm each is a
   regular file, then remove only those ten duplicates after this plan update.
   Confirm the source files remain present and byte-identical to their recorded
   hashes.
3. Parse the updated manifest and coverage JSON. Require all ten rows to have
   `stored_path: null`, `stored_path_absolute: null`, `copied: false`,
   `committed: false`, `usable_as_motion_input: false`, and unresolved rights;
   retain basename, source path, SHA-256, byte size, codec, dimensions, fps,
   frame count, duration, audio, and candidate mappings.
4. Confirm the duplicate narrow-gauge report is absent and the canonical
   narrow-gauge contract remains present and unchanged.
5. Check touched text files for trailing whitespace, run `git diff --check`,
   parse every JSON file, and inspect scoped status. Leave all changes
   uncommitted.

## Assumptions and evidence boundaries

- The ten MP4s are user-supplied art-direction/choreography evidence, not
  scientific evidence or measured animal performance.
- The external source directory is the byte authority. Generator/tool,
  original source, prompt/seed, creator, and license/commercial-use fields
  remain unresolved; no rights are inferred from filenames or receipt.
- Filename/package mappings remain candidate bookkeeping only. This task does
  not inspect or adjudicate pictured choreography, contacts, gait, stance,
  biological posture, or motion quality.
- All recorded primary video streams are 24 fps rather than the requested
  60 fps. Receipt therefore remains insufficient for native-speed/sub-frame
  timing validation.
- “Externally received” means technical metadata was observed in the source
  checkout; it does not authorize storing, using, or distributing the media.
