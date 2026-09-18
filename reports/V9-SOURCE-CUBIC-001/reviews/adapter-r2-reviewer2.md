# Source CUBICSPLINE Blender playback adapter — reviewer 2 R2

Reviewed exact head `f5207ca3a83718f21f0c8fb1bd25d891be6a4a8f` against
`4823fa8cc3813fa07a06e670f7b344e8321908ec`. This was a narrow review of the
R1 render-overwrite closure, truthful FBX omission, and direct-script bootstrap.

## P1

1. **The format detector rejects approved multi-clip LINEAR assets.**
   `requires_exact_cubic_playback()` calls `_source_animation()`, which
   requires exactly one glTF animation before inspecting interpolation. The
   approved V8.2 GLB contains two LINEAR clips and therefore fails before the
   renderer can select Blender's compatible stock LINEAR path. This regresses
   legacy rendering and showcase entry points that now call the detector.
   Preserve the strict single-animation requirement for the exact CUBICSPLINE
   adapter, while allowing genuine multi-clip LINEAR inputs to return false.
   Root's reproducer is
   `audits/root-blender-cubic-round2-f5207ca/legacy-multiclip-probe.json`.

## Closed R1 evidence

- The adapter detaches approximate importer actions from every CUBICSPLINE
  target owner and fails closed on active NLA strips or missing owners.
- Root's independent Blender 5.2 Cycles run reports post-render same-index skin
  errors of `2.3496518960810366e-6 m` in-place and
  `2.4421291038418187e-6 m` root-motion, restoring parity after dependency
  graph evaluation. Receipt:
  `audits/root-blender-cubic-round2-f5207ca/native-result.json`, SHA-256
  `20ef785a4af2e5e5a49731b853895dbaf4d8025b76bd07508b9052e2b424d474`.
- Cubic showcase renders omit unsupported FBX transport and label
  `UNSUPPORTED_TASK_OWNED_CUBIC_SAMPLING`; LINEAR requests retain FBX.
- The legacy direct Blender script adds the repository `src` path before
  importing the task-owned guard.
- Focused local run: 22 tests and 10 subtests passed in 0.73 s
  (`test_blender_native_playback.py`, `test_showcase_acceptance.py`,
  `test_review_connected_sequence.py`, and
  `test_review_candidate_stills.py`).

No additional P0/P1 findings in the narrow diff.
