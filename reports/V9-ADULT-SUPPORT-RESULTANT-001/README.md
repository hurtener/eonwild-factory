# Adult V9 sampled support-resultant sensitivity 001

## Scope

This diagnostic evaluates the immutable adult V9 root-motion package with four explicit engineering segment models. It adds no motion control, recipe binding, emitter behavior, threshold, or approval. Code head `0e4cfa45c192b43716fc223924cfec3e021ba9b4` is based on published integration `83aa5e5391848493c902af0c6bd4ecab6228afe6`.

The calculation reuses `compute_centroidal_series` for world COM and angular momentum, then differentiates its sampled velocity and momentum. Tangential moment balance locates a single ground-force resultant on the declared plane; the unrepresented normal-axis moment remains explicit. Because the GLB uses LINEAR channels with velocity jumps at keys, these are native-sample sensitivity values, not exact runtime dynamics.

All inputs are hash-bound to the V9 package, source geometry, recipe, runtime, animal, contact profile, provisional segment profile, and prior material-envelope audit. The total mass is the published `2816.3 kg` PIN 552-1 volumetric estimate. Snively et al. also report axial-body yaw inertia `4486 kg·m²`, body-plus-swing-leg yaw inertia `4515.1 kg·m²`, and an axial-body COM location for their reconstructed model. Those values come from a connected-frustum/superellipse reconstruction with regional density assumptions; they are neither fossil measurements nor segment properties for this GLB ([Snively et al. 2019](https://doi.org/10.7717/peerj.6432), [open primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6387760/)).

The paper and its PIN-level tables do not supply a full set of segment masses, three-dimensional local COMs, or node-frame inertia tensors transferable to this rig. The diagnostic therefore labels the existing 17-segment normalized profile as engineering data. It compares joint-origin and semantic-link-midpoint local COMs, plus a conservative `±0.03` total-mass redistribution between the axial center and tail. The latter is a sensitivity bound motivated by the paper's result that changing tail depth by ±10% changed whole-body mass by no more than 3%; it is not a measured PIN tail mass.

## Actual V9 result

At the two declared sole-support midpoints, all four models require a lateral ground resultant in these ranges:

| Support | Required lateral position, root-relative | Difference from engineering central-toe proxy |
|---|---:|---:|
| Left | `-138.85` to `-129.47 mm` | `+15.03` to `+24.41 mm` |
| Right | `+89.65` to `+120.94 mm` | `-64.24` to `-32.95 mm` |

The central-toe value is the distal node of the semantic toe chain nearest the foot-root lateral center in the recovered neutral geometry, projected to the ground. It is an authored CoP proxy, not measured pressure or tooth/sole contact. All required points also lie inside the much broader near-ground material envelope; that envelope only proves geometric availability.

The normalized vertical resultant is `1.041–1.050 body weights` at the sampled double-support landmarks and `0.856–0.892 body weights` at sole-support midpoint. With the published mass assumption, that is about `28.76–29.01 kN` at double support and `23.65–24.63 kN` at sole support. Mass changes the force scale but not the normalized balance point.

The forward result is not robust. At sole support it ranges from `68.76` to `387.35 mm` root-relative, and its error from the toe proxy ranges from `-289.68` to `+28.91 mm`, depending primarily on local COM and tail-mass assumptions. The models' static-sample yaw inertias are `9332–11863 kg·m²`, more than twice the paper's `4486 kg·m²` axial-body value. The quantities are not perfectly like-for-like because the rig model includes carried limbs, but the discrepancy is large enough to reject these engineering inertias as calibrated PIN properties.

## Actionable control boundary

The robust lateral result does not support increasing lateral pelvis sway: the inferred resultant already stays close to the explicit central-toe proxy across the tested mass and local-COM alternatives. The forward uncertainty and yaw-inertia mismatch also do not support a tail-phase or trunk counterrotation change from this evidence.

The supported next comparison is one bounded, authored **double-support load-acceptance response**: add `0.01 body height` (`22.84 mm` for V9) of extra pelvis compression centered on each double-support load peak, with a matched small trunk response owned by the same support clock and zero added displacement at sole-support midpoint. Preserve root travel, contact timing, lateral carrier, tail phase, jaw, gaze, and configured limits; then source-re-solve both feet and reopen the emitted material-contact and support-resultant receipts. This is an engineering visual hypothesis tied to the phase where the sampled resultant is `~1.05 BW`, not a claim that fossils prescribe 22.84 mm or that the model predicts muscle force.

If that comparison is implemented, use one fixed trunk response rather than an amplitude sweep. A reasonable local gate is: required lateral resultant remains within the admitted semantic toe-proxy neighborhood and geometric support patch, planted material checks remain unchanged, and the sampled double-support/sole-support force ordering remains truthful. Visual review must decide whether the added load acceptance communicates mass.

## Reproduction

```sh
source /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/task-env.sh
PYTHONPATH=src python tools/diagnose_support_resultant.py \
  --output /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/audits/adult-v9-support-resultant-sensitivity.json
```

Focused verification: `70 passed in 11.39s` across `tests/test_support_resultant.py`, `tests/test_v9_dynamics_slice.py`, and `tests/test_v9_dynamics_fixtures.py`; Ruff passed for the new module, CLI, and tests. Analytic checks independently cover stationary projection, known horizontal acceleration, known pitch-momentum rate, a rotated coordinate frame, normalized-mass rejection, zero-up-axis rejection, and loss of positive normal support.

- `result.json` SHA-256 `ccf44ab5d32cca5c9e6255e6ba5ce718202a234f55fbb5ba04654d9516caa648`
- Assumption profile SHA-256 `3436202850a0488fc96076f1ee724d5c5d233f996db6519b3c867768b5def7e0`
- Diagnostic module SHA-256 `0706932a7e48a40c78aed08d7bce6e7ed0f537e919fe0949ce3a24c588673465`
- CLI SHA-256 `979673f3b3f1fafe7a2af1e7b71467e0478dbdedf809557357a34bb3c7d3a787`

This result does not establish measured CoP/load, fossil segment properties, stability certification, mass dynamics, biological validity, contact preservation after a future change, native playback, Unity parity, or production approval.
