# Contact and mass visual checkpoint — 2026-09-10

Contact correction and the first mass-derived body correction are applied to
both Allosaurus and Tarbosaurus in the shared engine. Pause here for visual
feedback. These are diagnostic candidates, not a production dynamics pass.
The user liked the preceding Tarbosaurus contact-only video; preserve it.

Artifacts are under:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/outputs/visual-iteration-14`.

- `allo-contact-mass-side-front.mp4` and `tarbo-contact-mass-side-front.mp4`:
  normal-speed side/front review videos.
- `{allo,tarbo}-mass-first-preview/`: actual emitted GLBs, bound source mass
  profiles, frozen contact-law receipts, optimizer coefficients and reopened
  serialized-contact measurements. All 296 source keys passed contact checks.
- `checkpoint-source.tar.gz`: implementation, recipes, tests and both admitted
  source GLBs. `engine-source-sha256.json` records the exact implementation.
- `APPROVALS.md`: precise visual feedback boundary.

## What changed

The previous static support subset selected heel skin while toe-off deliberately
raised that skin. The anchor provider also omitted the walk's outward foot,
knee-plane and rolling carrier settings. It now uses the same frame settings
as the source query. A reusable source-derived rolling plan freezes each
material point during its own support interval and transfers support to the
next point at acquisition. The actual complete sole/toe skin remains measured.

Allosaurus retains the additional intermediate deformation joint in each of
its six pedal digits from iteration 13. Toe endpoint shape preferences are
reported separately from hard rolling skin contact; no leg or toe is stretched.
Species and source differences remain semantic rig and body data.

The existing mass coordinator now runs against corrected contact. Its surface
mass proxy validates local scale through the complete ancestor hierarchy;
world-space Gram matrices were incorrectly rejecting valid rotations beneath
small nonuniform source scales. Mass trials use owned pose batches. The world
transform arithmetic is batched with scalar-reference parity at roundoff.
Optimization probes use a smaller exact-geometry grid; production acceptance
still requires the original full source resolution and unchanged thresholds.

The first nonzero accepted optimizer iterate was exported for each animal.
Further optimization was stopped at this visual checkpoint. These corrections
are smooth periodic pelvis translations and rotations driven by the fixed
neutral-area full-LBS mass proxy, not authored species-specific offsets.

## Actual verification and limits

- 35 focused mass, contact-control and toe tests passed; anchor tests: 9 passed.
- Body-support bridge/adapter: 20 passed. Motion and new batch checks: 119
  passed, with one pre-existing expected planner hash mismatch in the unchanged
  planning code. Factory/coarse-acceptance, rolling binding and transform parity:
  8 passed. No whole-suite, hosted CI or independent-agent review is claimed.
- The reopened GLBs were measured at 120 Hz, all keys and every key midpoint.
  Allosaurus: maximum loaded-material residual 0.185 mm; minimum full-mesh
  gap -0.0039 mm. Tarbosaurus: residual 0.083 mm; minimum gap -0.0863 mm.
  These tiny interpolation residuals do not block this requested visual review.
  The unchanged strict production floor-margin gate is not passed.
- Full force/moment convergence is NOT achieved. First-iterate normalized
  force/moment residuals are 0.1142/0.1166 (Allo), 0.1526/0.1770 (Tarbo), versus
  the production threshold 0.0001. The optimizer accepted an aggregate objective
  improvement, not a proof that every individual residual improved.
- Serialized dynamics parity, native user approval of these mass candidates,
  Unity parity and production acceptance remain pending. No merge or push.
- Root implemented this pass personally. All jobs started for this checkpoint
  have ended. Do not wake older stopped workers or tasks.

Next: review side/front mass motion against the preserved contact baseline.
Use the feedback to choose the next visible correction before further optimizer
or release-validation work. Do not treat this checkpoint as a completed goal.
