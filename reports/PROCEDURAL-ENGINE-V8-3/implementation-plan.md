# PROCEDURAL-ENGINE-V8-3 — executable balance transfer

## Objective

Implement V8.3 as three registered semantic motion layers in the canonical
`eonwild-motion` package, using the immutable approved V8.2 GLB as input and
leaving the stable channel unchanged. The working profile will resolve the
selected deterministic V8.3 artifact only after the prescribed amplitude
sweep passes every machine gate.

Required execution order:

1. `pelvis_balance_pre_ik@1`
2. `leg_contact_resolve@1`
3. `chest_tail_head_stabilization@1`

## Intended changes

- package implementation under `src/eonwild_motion/` for generic animation
  channels, hierarchy transforms, semantic balance layers, sweep evaluation,
  and deterministic build/report integration;
- semantic rig, family, motion, layer, render-set, V8.3 release-profile, and
  working-channel documents under `catalog/` and `profiles/`;
- contract schemas under `schemas/motion/` only where the executable profile
  requires new version-neutral fields;
- focused fixtures and tests under `tests/`;
- the selected content-addressed V8.3 artifact under `assets/sha256/` if its
  size remains within the repository gate;
- V8.3 evidence, commands, metrics, deterministic media, review page, and
  provenance under `reports/PROCEDURAL-ENGINE-V8-3/`.

The approved V8.2 artifact/profile, stable channel pointer/history, legacy
toolkits, and primary checkout are read-only.

## Implementation design

- Add a deterministic zero-mean pelvis translation/roll signal from the
  declared support phase. Sagittal translation and pelvis pitch/yaw remain
  untouched.
- After that edit, numerically re-solve each semantic leg chain per sample so
  its foot world transform matches the approved V8.2 target. Foot pivot
  translation is bounded by the evaluator contract. Toe local tracks remain
  untouched, preserving the accepted rocker, passive lag, receiving, and
  distal trajectories through the restored parent transform.
- Preserve V8.2 chest and tail local accessors exactly. Apply bounded neck/head
  compensation only after contact resolution to keep world stabilization
  within the declared envelope.
- Sweep `[0.5, 0.625, 0.75, 0.875, 1.0]`, independently decode every exported
  candidate, and select the strongest all-hard-gates PASS using the evaluator's
  exact tie-break order.

## Acceptance checks

## Review-page direction

- Visual thesis: a restrained dark field-report surface where the textured animal is the dominant evidence and warm amber is used only for orientation and PASS state.
- Content plan: full-bleed synchronized side hero, machine-gate proof, alternate front/three-quarter views, nine full-body/foot phase diagnostics, and an explicit pending-approval boundary.
- Interaction thesis: one shared playback clock across views, quiet scroll reveals, and a full-body/feet diagnostic switch with no decorative motion.
1. Stable resolves to the exact approved V8.2 artifact SHA and its state/history
   bytes do not change.
2. Working resolves only to the selected V8.3 profile/artifact and records its
   channel revision in every run lock/report.
3. Layer registry and resolved profile prove the exact required order and use
   semantic roles only; engine code contains no concrete bone/species/clip
   names.
4. Root, timeline, non-walk animations, mesh/skin/rest/inverse binds, stride,
   speed, pelvis sagittal/pitch/yaw, and V8.2 chest/tail local tracks meet the
   evaluator's exact/frozen gates.
5. Final exported/final-skinned bilateral contact, trajectory, rocker, passive,
   receiving, upper-body, seam, and continuity gates pass at 120 common phases.
6. The exact prescribed sweep and selection policy are captured in machine
   evidence; two independent selected builds are byte-identical.
7. Full unit/contract/integration/negative tests pass without writing generated
   work into source.
8. Fixed side/front/three-quarter 10-second, 24-fps, 240-frame synchronized
   comparisons, required phase crops, and a static review page are produced
   after machine PASS. They are technical evidence only, not self-approval.

## Ownership and assumptions

The root integration task explicitly grants this worktree and the canonical
engine/profile/catalog/schema/test/report surfaces for V8.3. Concrete rig and
motion identifiers belong only in catalog/profile data. Existing reviewer and
evaluator documents will be retained verbatim and included in the signed
handoff. If the declared contact or balance envelope cannot be met without
weakening a gate or modifying frozen V8.2 data, work stops with captured
candidate evidence rather than changing the contract.

## Verification entry point

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The evidence bundle will additionally record the exact sweep, double build,
independent validation, Blender render commands, media hashes, and source/tool
versions.
