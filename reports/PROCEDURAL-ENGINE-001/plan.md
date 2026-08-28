# PROCEDURAL-ENGINE-001 — canonical procedural engine plan

## Objective

Replace the folder-per-version development pattern with one executable,
schema-driven procedural animation engine. The first vertical slice must build,
validate, render, compare, and promote the existing approved V8.2 Tarbosaurus
walk through one Python package and one CLI without changing the approved
artifact bytes.

This task is an architecture gate only. It writes the plan and architecture
before any package, schema, profile, fixture, artifact, or command is
implemented.

## Current-state decision

- Branch `codex/procedural-engine` is the only implementation branch for this
  work. No version-specific branch or worktree will be created.
- `procedural-animation-toolkit(v8.2)` is the source for the first migration,
  not the permanent package boundary.
- `procedural-animation-toolkit(v5)`,
  `procedural-animation-toolkit(v5.5)`, their validated results, and the
  corresponding showcase/reports remain read-only legacy archives until a
  migration reproduces their accepted behavior.
- Generated run directories, temporary GLBs, renders, comparisons, and raw
  reports must be outside tracked source. Only an explicit promotion may add
  immutable release records to the repository.
- The superseded V8.3 hip experiment is not implemented in this stage. A
  future hip-balance solve will be a declared motion layer selected by a
  profile, followed by contact/IK revalidation, rather than another engine
  copy.

## Files changed by this architecture gate

- `reports/PROCEDURAL-ENGINE-001/plan.md`
- `reports/PROCEDURAL-ENGINE-001/architecture.md`

No engine code, legacy toolkit, approved GLB, media, configuration, main
checkout, or release manifest is modified.

## Ownership

The upstream Eonwild ownership contract assigns each task its own
`reports/<task-id>/**` directory, so both files are inside the task-owned
report scope. The future implementation spans architecture contracts, Blender
factory logic, biomechanical-family data, and validation. Before implementation
those paths require an explicit integration-owner handoff covering WS00, WS03,
WS07, and WS08 responsibilities; this document does not silently grant those
cross-workstream writes.

## Architecture inputs read

- Eonwild operational constitution.
- Deterministic asset-factory RFC.
- Biomechanics/species composition direction.
- Animation and locomotion quality RFC.
- Repository command contract and demo quality bar.
- Research/IP/provenance policy.
- WS03, WS07, and WS08 boundaries.
- The approved V8.2 release configuration, generator, verifier, manifest, and
  final P1 evidence.

## Implementation stages

1. **Freeze contracts and legacy inventory**
   - Add the package skeleton, schemas, command envelope, and a hash-bound
     legacy catalog.
   - Do not move or import legacy directories.
   - Pin Python, Blender, glTF Validator, and FFmpeg versions.
2. **Make V8.2 the vertical slice**
   - Migrate the minimal quaternion/GLB code and official chest-balance solve
     into package modules.
   - Express the rig, family, species, motion, layer, and V8.2 release profile
     as schema-valid data.
   - Build into an external run directory and require the approved SHA-256
     `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
3. **Close the command loop**
   - Implement `build`, `validate`, `render`, `compare`, and `promote`.
   - Make every command emit the same versioned run-report envelope.
   - Add fixed-camera evidence and fail-closed technical comparisons.
4. **Prove immutability and failure behavior**
   - Add tiny synthetic GLB fixtures and negative contract fixtures.
   - Prove source-tree cleanliness, deterministic reruns, no overwrite on
     promotion, and no undeclared channel writes.
5. **Promote V8.2 through the engine**
   - Create a release record only after exact artifact parity, manifest
     verification, render evidence, and independent review.
   - Keep the original V8.2 directory as a legacy reference until the promoted
     release has been accepted.
6. **Migrate older behavior incrementally**
   - Inventory V5 and V5.5 behavior into candidate profiles/layers.
   - Migrate only a behavior with a named parity or intentional-difference
     report. Never copy the old engine wholesale.

## Acceptance checks for the implementation

1. `eonwild-motion build --profile v8.2` succeeds from a clean checkout and
   emits the exact approved GLB SHA.
2. A second build with the same lock and inputs produces the same artifact,
   manifest, and semantic report (excluding explicitly declared timestamps and
   run paths).
3. `validate` passes the V8.2 artifact and fails every retained V8.2 P1
   negative case: hierarchy, accessor component/type/stride, interpolation,
   common timeline, bounds, cache/temp paths, and oversized files.
4. Semantic-role tests prove engine code contains no Tarbosaurus bone names or
   species-ID branches.
5. Layer ownership tests prove a layer cannot read or write undeclared
   channels and that untouched GLB regions remain byte-identical.
6. `render` produces the declared fixed-camera, fixed-duration evidence with
   pinned Blender/FFmpeg facts.
7. `compare` produces machine-readable structural, motion, contact, artifact,
   and media differences and a browsable review page; it cannot reduce a
   failure to image-only approval.
8. `promote` refuses missing approvals, dirty/unlocked runs, hash mismatches,
   version overwrite, incomplete provenance, or a source-tree path as its
   work root.
9. Successful promotion creates a new immutable release manifest and
   content-addressed artifact without altering an existing release.
10. The tracked source tree is unchanged after non-promotion commands; no
    cache, bytecode, temporary render, or run report appears under source.
11. The approved V8.2 GLB and media are unchanged during migration.
12. Unit, contract, integration, Blender smoke, and negative tests run locally
    through one documented verification command with no skips.

## Evidence required at implementation handoff

- Tool and dependency versions plus license notes.
- Exact commands and exit codes.
- Unit/contract/integration/negative test reports.
- Input, resolved-profile, artifact, media, and manifest hashes.
- GLB structural/accessor comparison and unchanged-region proof.
- Fixed-camera render metadata and review outputs.
- Source-tree cleanliness and promotion immutability evidence.
- Known limitations, especially V8.2's current 43 MB artifact versus the
  longer-term browser package target.
- Independent technical and visual review; the implementer does not approve
  its own release.

## Non-goals

- Rewriting V5 or V5.5.
- Implementing the hip-balance layer.
- Changing the approved V8.2 animation or media.
- Building the game runtime.
- Creating a generic plugin framework without the V8.2 executable path.
- Claiming the heavy-predatory-biped family is generally accepted from one
  species. It remains provisional until a second meaningfully different
  morphology passes the family contract.

## Unresolved assumptions

- The implementation owner will receive explicit WS00/WS03/WS07/WS08 path
  authority before adding canonical schemas/package/configuration.
- Blender 5.2.0 LTS remains available for exact V8.2 parity; changing Blender
  is a separate measured migration.
- Promoted release binaries remain Git-compatible for the first slice. If
  repository size policy rejects them, an ADR must define an immutable
  artifact store before promotion; the engine must not silently fall back to
  an untracked local file.
- V8.2 is the first release profile, not a claim that V8.2 contains the final
  family locomotion grammar.
