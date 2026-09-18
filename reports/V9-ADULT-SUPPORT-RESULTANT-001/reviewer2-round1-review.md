# Independent support-resultant diagnostic round 1

Reviewed exact head `2a985f36f987cd6c5dc07fcb053b230c60e5e31f`
(implementation `0e4cfa45c192b43716fc223924cfec3e021ba9b4`), relative to
published `83aa5e5391848493c902af0c6bd4ecab6228afe6`.

Decision: **CHANGES REQUIRED**. Two P1 families are independently reproduced.
The standalone moment equation and declared-frame signs have no finding.

## P1 — consumed biomechanics data is outside the asserted source binding

`tools/diagnose_support_resultant.py` consumes package `biomechanics.json`
for both `geometry.uniform_scale` and
`geometry.actual_semantic_pelvis_to_toe_plane_m`, but neither the file nor
either value appears in `expected`/`actual` source identity. The README's
claim that all inputs are hash-bound is therefore false.

I reran the frozen CLI against the root proof package whose only owned payload
change raises the semantic height by 20%. It completed successfully, retained
the same reported source identities, and reproduced result SHA-256
`6dbce46b8ac81ec7ed339f81290c7c50d9c409e6f346b07393cf309f0d0ab361`.
The changed height alters inertia scaling and required resultant points; this is
not a receipt-only defect.

Fix: bind and validate the exact consumed biomechanics payload through the
existing package identity contract before computation, and retain its hash in
the result. A mutation of either consumed field must fail before output.

## P1 — declared model alternatives do not govern computation

The receipt copies
`engineering_model.contact_load_alternatives` and
`local_com_alternatives`, but the CLI independently hardcodes:
`single_support_1.0`, equal 50/50, leading 60/trailing 40, and all four
joint-origin/link-midpoint/tail variants.

Two independent executions demonstrate the divergence:

- Declaring leading 90/trailing 10 still emits only
  `leading_0.6_trailing_0.4`; output SHA-256
  `e5853d26ce61bd9bac382ca193eb61c70db51023f951f87ed7dd74a0c3292b3b`.
- Declaring only `semantic_joint_origin` still emits the link-midpoint and
  tail-heavy/tail-light models; input SHA-256
  `e5de7e3981c7e7d57219aac01dfeec9bb2a98bf945ef3a5bf8a52a10580f05ee`,
  output SHA-256
  `8edf939c3d3ee63dea5957fab1a8133cb76084d83fa918f4ad21f553e88ad045`.

Fix: make validated profile values build the evaluated alternatives, or reject
anything other than the exact supported values. Tests must exercise the CLI
boundary and verify the evaluated model keys/weights, rather than only the
standalone moment equation.

## Local P2 reporting and portability fixes

- The lateral conclusion is conditional on one authored central-toe node proxy.
  At sole support the proxy is inside each axis-aligned near-ground material
  range, and the inferred lateral point differs by 15.03–64.24 mm across the
  four assumed mass/COM models. No pressure distribution or measured CoP
  establishes that proxy, and independent forward/lateral ranges do not prove
  membership in the material patch's convex hull. Replace “robust” and the
  undefined “admitted semantic toe-proxy neighborhood” gate with the measured
  distances and an explicit conditional statement. This evidence can say it
  does not motivate a sway increase under the chosen proxy; it cannot rule one
  out generally.
- The `±0.03` redistribution is an authored sensitivity, not a paper-derived
  tail-mass bound. Snively et al. varied tail geometry and reported its effect
  on whole-model properties; transferring 3% of total mass between central and
  tail segments while holding mass fixed is a different counterfactual. Remove
  “conservative bound” language while retaining the existing honest
  engineering label. Primary source:
  <https://doi.org/10.7717/peerj.6432>.
- `SUPPORT_AUDIT` and the default package are hardcoded to one task-specific
  SSD path. Add explicit path arguments or retain the small audit with a
  documented package-relative invocation. This is local diagnostic portability,
  not runtime architecture.

## Verification

`tests/test_support_resultant.py`: **5 passed in 0.67 s** under the frozen
head and external SSD `--basetemp`. The tests independently cover static
projection, horizontal-acceleration sign, angular-momentum-rate sign, a rotated
frame, and fail-closed mass/support/axis cases.

Reviewed SHA-256:

- module `0706932a7e48a40c78aed08d7bce6e7ed0f537e919fe0949ce3a24c588673465`
- CLI `979673f3b3f1fafe7a2af1e7b71467e0478dbdedf809557357a34bb3c7d3a787`
- tests `6778d0bace3c71015b3a64b5c321926576d8450aa412e20961e74f0ca44e73be`
- assumptions `3436202850a0488fc96076f1ee724d5c5d233f996db6519b3c867768b5def7e0`
- README `f1731aed206b8c78776cfd6e321598d57dfa1f5d06d8561a3975405c97145b45`
- result `ccf44ab5d32cca5c9e6255e6ba5ce718202a234f55fbb5ba04654d9516caa648`

No runtime recipe, generated package, motion threshold, or approval state was
changed.
