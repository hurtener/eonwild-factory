# V9-EXTENSION-001 reference coverage audit plan

## Bounded task

Produce a Phase-0, read-only pose/reference and provenance deliverable for the
V9 Tarbosaurus animation extension. The audit covers all 29 animation
contracts and the 16 authored bridges, classifies each item A-E, records the
existing V5.5/V8.2/V8.3 evidence boundary, and specifies only the genuinely
missing user-generated still/video captures. This task does not implement or
modify an engine, motion program, schema, asset, or generated animation.

## Intended files

Only this report directory in the productized engine worktree is in scope:

- `reports/V9-EXTENSION-001/plan.md`
- `reports/V9-EXTENSION-001/reference-coverage.md`
- `reports/V9-EXTENSION-001/reference-coverage.json`
- `reports/V9-EXTENSION-001/commands.md`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-narrow-gauge-relaxed-walk-sheet.png`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-narrow-gauge-relaxed-walk-sheet.provenance.json`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-investigate-scent-sheet.png`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-wounded-idle-sheet.png`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-listen-reaction-sheet.png`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-faster-locomotion-sheet.png`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-body-shove-stumble-sheet.png`
- `reports/V9-EXTENSION-001/references/user-generated/tarbosaurus-v9-reference-sheets.provenance.json`

No engine or motion files will be edited. The user later supplied one generated
narrow-gauge sheet for exact-byte archival as art-direction evidence; its
incomplete generator/license metadata is recorded rather than inferred.

## Source material read

- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/README_FIRST.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/animations/ALL_29_ANIMATIONS.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/animations/01_STATES_LOCOMOTION_AND_TRANSITIONS.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/animations/02_PERCEPTION_AND_COMBAT.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/animations/03_FEEDING_DRINKING_AND_GROUND_POSTURE.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/animations/04_INJURY_CALLS_AND_DEATH.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/03A_V8_3_CLIP_RECOVERY_CATALOG.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/docs/RESEARCH_NOTES.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/motions/tarbosaurus/catalog.yaml`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/motions/tarbosaurus/power-attack.yaml`
- existing V5.5, V8.2, and V8.3 evidence paths cited by the pack and recorded in the report

## Ownership confirmation

The repository ownership map assigns `reports/**` to the task owner, with each
task restricted to its own report directory. This task writes only
`reports/V9-EXTENSION-001/**` in the productized engine worktree. An
intermediate status snapshot showed a transient untracked `uv.lock` at the
worktree root. No ownership is inferred from that snapshot; it was not edited
by this task and was absent from the final snapshot. Any pre-existing or
concurrent untracked paths outside this report directory must likewise remain
untouched.

## Acceptance checks

1. `reference-coverage.json` parses as JSON.
2. The JSON contains exactly 29 unique animation IDs and exactly 16 unique bridge IDs.
3. Every classification is one of `A`, `B`, `C`, `D`, or `E`; every requested shot ID resolves.
4. Markdown and JSON have no trailing whitespace; the report identifies all existing coverage and reconstruction-only cases.
5. `git diff --check` passes for the report files.
6. `git status` confirms that this task added files only inside this report directory; pre-existing or concurrent untracked paths remain outside the task diff and untouched by this task.

## Unresolved assumptions and boundaries

- The V9 pack is an implementation handoff; it claims no generated or approved V9/V8.3 animation artifact. V8.3 architecture documents are therefore not treated as visual coverage.
- V5.5 and V8.2 media are prior project evidence, not biological truth. Existing local reference media is cited only by repository path and observed role; no protected external source is searched or ingested.
- `E` means the action must be a provenance-labeled, bounded gameplay/engineering reconstruction rather than a visual imitation. It does not prohibit internal art-direction targets, but those targets must not be presented as paleobiological evidence.
- The grounded committed-bite contract is audited separately from the airborne branch in `power-attack.yaml`; airborne feasibility remains unresolved and must fall back to grounded execution.
- The requested fps values are capture recommendations for native-speed user references, not scientific claims about Tarbosaurus timing.
