# B body counterroll review — 2026-09-08

Scope: narrow read-only mechanics and contract review of
`c6330655d30a8ce0b551bb5dd90f697f0802821c..329b150566d08c2a2ca19153aa844f8ae054855f`
in `/Volumes/m2-extended-disk/Repos/eonwild-factory-candidate-claims-fix`.
Reviewed head: `329b150566d08c2a2ca19153aa844f8ae054855f` (implementation commit
`02adf3831e5d308b2b0cf906c45b0fc83f52c82d`). This is review round 2 for the
bounded body feature, not a historical or whole-branch review.

## Result

No P0, P1, or P2 finding.

`upper_trunk_counterroll_degrees` is opt-in, finite, constrained to 0..3°, and
requires the existing support-directed carrier. Its application rejects a
missing, duplicate, or disconnected semantic spine/chest chain. On the actual
rig the chain is contiguous: `Bone_001` pelvis → `Bone_007` → `Bone_006` →
`Bone_005` → `Bone_004` → `Bone_003` → `Bone_002` chest.

The carrier uses the existing grounded, semantic-hip-derived signed support
pulse. World-forward quaternion deltas distribute +0.9° across the five spine
roles plus chest with normalized increasing weights; it counteracts the
support-directed pelvis roll rather than changing its sign. Focused actual-rig
and serialized-output tests check the resulting monotonic 1.5° pelvis to 0.6°
chest world-roll profile at support, malformed inputs, topology failure, and an
attempted airborne-plan bypass.

The v5 recipe retains exact v4 source, rig, animal, program, contact, and
articulation input locks. The program/contact/articulation hashes are,
respectively, `271ccb833a8913d3dc6bd8281e798e54b9c7bebad2080136245cb7b5e5afa725`,
`fef6279c1e7653ae6c7c485c3f934fd647410a726acb59393312b72af754a89f`, and
`c1206143387ad4d1084a413ee031018f5a61a8e0539ef8256c6bba74a0f4bc6a`.
Only the profile's authored body values change: sway 0.006→0.018 BH, roll
0.6→1.5°, and a 0.9° counterroll. The final solver can alter solved leg targets
after body-origin movement; this review makes no claim that serialized leg poses
remain byte-identical.

## Evidence

- `uv run --frozen python -m pytest tests/test_motion_performance.py tests/test_adult_body_weight_transfer_catalog.py -q --tb=short`: **45 passed**.
- B package: `out/continuation-adult-v5-body-counterroll-001/package`.
  Validation records technical `PASS`, visual `PENDING`, Unity `NOT_RUN`, and
  `production_approved: false`.
- B root-motion SHA-256:
  `6f7c6fb7ee79055c66f0f76be150a5c72cbe919fa9514c11ffb64915ee8fecf4`.
  B in-place SHA-256:
  `8dff0f9d4c92e73cda477e05ad554e536967b2c46a3df89748538fe0bfe4d086`.
- `git diff --check` for the reviewed delta passed. The review worktree was
  clean.

This is a mechanics and narrow-contract result only. Native visual review and
Unity parity remain the owning host's decision.
