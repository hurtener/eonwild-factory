# V8.1 deep-rework plan

## Task

Create an immutable-from-V8 Tarbosaurus procedural-animation V8.1 release that keeps V8 walk/contact behavior, ports the accepted V5.5 neutral posture and asymmetric idle support, repairs the jaw hinge under head turns, and separates the existing grounded bite from a new airborne power attack with explicit landing/arrest/feeding continuity.

## Baseline and preservation

- Source package: `procedural-animation-toolkit(v8)/`
- Initial raw-tree observation: `f7d59366a82c98e50401ddbada3889a9b9cb75d8026a25f28194cde873e713f7`. This raw hash is not a stable preservation oracle because read-only Python imports regenerated `__pycache__/*.pyc` files inside the imported package.
- Canonical preservation hash excluding `.DS_Store`, `__pycache__`, and `*.pyc`: `1eb9d5856873bf77e318bb301d2aacdc8930581761ad58c458e5a13222a9ad65`.
- Editable duplicate: `procedural-animation-toolkit(v8.1)/`
- Existing untracked V5-to-V5.5 transfer-guide material is user-owned and will be updated in place only where the mistaken V7/V7.1 labels must become V8/V8.1.

## Intended files

- `procedural-animation-toolkit(v8.1)/**`
- `docs/V5_TO_V5_5_CHANGES_AND_V8_1_TRANSFER_GUIDE.md` (corrected successor name; preserve material)
- `reports/V5-V5-5-TRANSFER-GUIDE/plan.md` (content correction only)
- `reports/V8-1-DEEP-REWORK/**`
- `showcase/v8.1/**`

No file below `procedural-animation-toolkit(v8)/` may change.

## Acceptance checks

1. Recompute the cache-excluding canonical V8 tree hash and inventory non-cache mtimes. Do not claim raw-tree equality or delete regenerated caches.
2. Require an explicit canonical `tarbosaurus-v8.1.json` profile and record its SHA-256.
3. Require the V8.1 walk samples/contact diagnostics to match V8 exactly except for release metadata and any explicitly isolated neutral-pose initialization.
4. Verify V5.5 neutral-chain and asymmetric idle values in generated clip diagnostics.
5. If the lower-foot pivot correction is ported, prove identical source rig, only two inverse-bind entries changed, fixed toe roots, and unchanged undeformed mesh.
6. Verify separate normal-attack and power-attack catalog entries, mirrored variants, semantic events, and transition endpoints.
7. Verify power attack has one-foot launch, bounded both-feet-clear interval, root vertical apex, ordered landing/catch, no ground penetration, persistent forward delivery, bounded landing velocity/acceleration, and feeding-ready settle.
8. Verify jaw centering geometrically across symmetric head yaw/roll and jaw closure at bite contact/clamp.
9. Run V8.1 unit, fixture, baked-ground, browser-contract, and release validators.
10. Reproduce from the canonical profile and compare hashes.
11. Render full-body side/three-quarter/front evidence and an offline comparison page for V5.5, V8, and V8.1.

## Ownership

The factory repository does not provide a narrower `config/ownership.yml`; this task is scoped to the new V8.1 copy, its evidence, and the explicitly requested transfer-guide correction. V8 remains read-only.

## Assumptions

- V8.1 is a new release and does not overwrite V8.
- The current V8 power-labeled grounded bite becomes the normal attack without changing its motion curves.
- The new power attack is additive and has its own transition/event contract.
- V5.5 posture values are accepted starting measurements; walking motion is not retuned.
- The power-attack reference is motion inspiration/provenance only and is not redistributed beyond the already supplied package input.

## Completion

All eleven acceptance checks passed at final GLB SHA-256 `ba321da21c20fce9fc2192efbcc40ae192303b06c2ccb856e0b8d7edeba2cc8a`. The clean reproduction produced the identical GLB, animation manifest, and resolved profile. See `summary.md` for exact metrics, commands, authored file inventory, artifact paths, and the remaining perceptual-review boundary.
