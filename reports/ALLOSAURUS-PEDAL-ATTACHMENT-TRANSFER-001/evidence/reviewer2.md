# Allosaurus pedal attachment transfer — independent round-one review

Reviewed immutable head `f9337f7a6d084de2ed42f1d2a88c09dbc512f826`, tree `49cedaac877f645b59e5c6130cc8910438a5c3f5`, against base `9a7e20983b8bce4bfcc3fbbf2ae34c3e92280f82` in `ARC/worktrees/eonwild-pedal-attachment-transfer`.

## Verdict

- P0: 0
- P1: 0
- Local P2: 1

The opt-in declaration is fail-closed around source/config identity, topology, destination ownership, physical skin-row aliasing, normalized rows, and selector overlap. The retained evidence distinguishes prepared/admitted source identities and preserves positions, triangles, nodes, skin joints, inverse binds, neutral skin, and contact membership. I found no concrete release-blocking defect in those boundaries.

## Local P2 — the composed box field is not globally C2

`src/eonwild_motion/factory/rig_preparation.py:116-122` constructs three individually C2 quintic axis gains and returns their minimum. At interior surfaces where two nonconstant gains are equal, `min` has a first-derivative crease. The included exact-head probe uses a corner-taper point where the lateral and forward gains are both 0.5. Across that point, the measured one-sided lateral derivatives are approximately `9.375` and `1.1e-9` per metre, so the composed field is not C1 there and therefore is not globally C2.

This does not establish an observed mesh deformation failure: the retained 15-degree diagnostic reports substantially better boundary-triangle and weight-jump measurements than the rejected hard selector. It is therefore a local claim/documentation issue rather than P1. Describe the implementation as quintic C2 falloff on each axis with a minimum-composed spatial field. A later output-changing product composition would require regenerated evidence and should not be taken solely to improve terminology.

## Checks

- `git diff --check 9a7e209..f9337f7a6d084de2ed42f1d2a88c09dbc512f826`: PASS.
- `PYTHONPATH=src /Volumes/m2-extended-disk/Repos/eonwild-factory/.venv/bin/python -m pytest -q tests/test_rig_preparation.py -k pedal_attachment`: 12 passed, 26 deselected in 5.72 seconds.
- `focused-tests.log` SHA-256: `79ff968ed4a5c3c9975a3d349c096701ea94e76800f141537cf6844672569e0c`.
- `probe_c2.py` SHA-256: `fbf12eb760e8e1589592db0f8abb7e282fccc5f836fffe3ef1b826c7b845f8ab`.
- `probe-c2-result.json` SHA-256: `4f097cdf0cd4319d13545a7d321f6b3168f142da8d0d1687e8d1c7ce7d2e90f0`.

## Limits

This review does not promote the prepared source and does not establish full-cycle contact, clearance, ROM, rate, visual, Unity, biological, or production acceptance. Those remain correctly pending in the implementation evidence.
