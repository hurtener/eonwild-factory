# V5.5 body-balance and posture correction

## Task

Create an independent V5.5 lane by duplicating the complete V5 toolkit, then revise the Tarbosaurus posture and selected motion relationships without changing V5. The pass targets body balance rather than general polish: higher-chest neutral/idle, a cohesive and bounded walk support chain, rear-loaded attack mechanics, and supported eating posture.

## Intended files

- `procedural-animation-toolkit(v5.5)/**` — complete V5 copy plus V5.5-only code, tests, documentation, inputs, and generated results.
- `showcase/v5.5/**` — deterministic Blender renderer, site validator, evidence writer, and generated review page/media.
- `reports/V5-5-BALANCE-001/**` — plan, reference analysis, commands/results, metrics, provenance, limitations, rendered evidence, and summary.

No file beneath `procedural-animation-toolkit(v5)/**` is allowed to change. The canonical tracked-entry digest is `c4f4905f2974aa751a7fe0485a44d194898ead71280992c34d0129dc81362119`; final verification must reproduce it and show no Git status entries in that path.

## Ownership assessment

The factory repository does not contain `config/ownership.yml`. The applicable parent Eonwild constitution assigns this work to deterministic Blender/GLB factory outputs and requires canonical scripts, provenance, reproducibility, and visual evidence. This branch is an isolated implementation lane created for this task. The V5 lane is treated as frozen reference material; all authored changes are constrained to the new V5.5 and task-report paths above.

## Acceptance checks

1. Fail-closed V5 immutability: full-tree SHA-256 digest and Git status match the recorded baseline.
2. Complete-copy check: every V5 path existed at duplication time in V5.5 before version-specific additions/changes; record a copy manifest.
3. Deterministic V5.5 build produces a valid GLB and manifest while retaining the existing clip catalog and V5 jaw behavior.
4. Automated posture metrics cover neutral chest/head attitude, walk contact/rear reach/toe-off and chain continuity, attack rear-load before drive, and eating support/counterbalance.
5. Existing structural, jaw, transition, and browser-player contract tests pass in the independent V5.5 lane.
6. Blender renders use the actual GLB/materials and include full-body fixed-camera evidence for idle, walk, attack, and eat.
7. The local review page passes its checker and is visually verified at desktop and mobile widths.
8. Generated artifacts include provenance, tool versions, commands, measurements, known limitations, and honest perceptual/scientific-evidence boundaries.

## Assumptions

- Motion observations from the supplied side-walk and attack/eat videos are visual hypotheses and timing references, not scientific proof.
- The existing rig topology, meshes, textures, 37-clip catalog, and runtime contracts remain fixed for this pass.
- Corrections require a deterministic full constrained solve from the source GLB before the V5 jaw, polish, and transition layers; no source-mesh or armature restructuring is authorized.
- Idle/walk/attack/eat receive direct correction. Other clips retain V5 output unless shared neutral posture or exact transition reconstruction requires a bounded update.
- Browser rendering remains WebGL2-compatible; Blender evidence is the texture/fidelity review source.

## Known risks

- A post-bake rotation correction can preserve contacts structurally while still looking mechanically disconnected; full-body rendered review is required.
- Raising the chest without coordinated neck, pelvis, legs, and tail changes can create a cosmetic pose rather than convincing balance.
- The source videos provide image-space evidence without calibrated camera or force-plate data, so inferred joint relationships must remain explicitly labeled as hypotheses.
