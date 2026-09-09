# Allosaurus anatomical onboarding 001

Status: **NON-PROMOTED; WALK SOLVE REJECTED**

Implementation checkpoint `292da2e6a535ef7928e26c054090670b5b2c0c96`
(tree `5ad4f7ef9e1549d4aefd79962d1b0954d3f4576c`) adds a reusable
rig-preparation endpoint operation, bounded near-unit scale normalization, and
complete one-to-three skin-influence-set admission. It also adds one source-bound
Allosaurus engineering rig and an unselected shared walking configuration. It
does not select a catalog baseline, change an existing motion, or add an
Allosaurus-specific solver branch.

## Geometry and evidence boundary

The preserved incoming source is SHA-256
`91d9816b6bbaeb1037f3e9cbf253261799d8a4121efd91e0e2185f76908a6bf7`.
The prepared source is `c611bb493813006d8b6a549124a021ff2c91930371f558f2f11434106b866c8b`;
admission adds only the geometry contract and produces the checked-in source
`a403679deb968ec88f7b8b89e3e399cc0881e9cc602e765a6e55934c28ad3826`.
The reopened neutral full-weight skin error is 0.375 micrometres. Eleven local
scales with float32 noise were normalized under an explicit 10 micrometre-per-
metre bound; the largest reopened world-matrix component difference is
6.973e-6. That mixed translation/linear-matrix metric is not a skin-distance
measurement.

The source's straight parallel legs and all original joint positions and
lengths were authored as drift-control placeholders. The new hip, knee, ankle,
and MTP points are provisional engineering centers fitted to declared surface
slabs; existing skin weights only localize a side and limb region. The hip is
especially uncertain because the visible proximal surface includes muscle bulk.
The knee and ankle land within visible contour changes and the MTP within the
pedal base in the independent opaque overlays. That supports deformation tests,
not anatomical approval. Added terminal nodes are non-skinned effector
landmarks for the existing topology and do not claim independent digit anatomy.

White et al. 2013 UUVP 6000r lengths are used only as a post-fit proportion
comparison ([primary source](https://pmc.ncbi.nlm.nih.gov/articles/PMC3722220/)).
The 1512 kg / 1.985 m hindlimb composite is an unverified configuration option,
not a measurement of this artist mesh ([Dececchi et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7220109/)).
Foster and Chure 2006 show ontogenetic proportion changes; their table/caption
metatarsal identity and one MOR 693 femur value are internally inconsistent, so
those values were not used to fit a pivot.

## Deformation probe

The retained full-weight probe applies isolated +/-8 degree rotations at each
provisional hip, knee, ankle, and MTP. All 16 probes remain finite and produce
zero local triangle-orientation reversals. The one-percent area-ratio quantile
is at least 0.885; the minimum individual ratio is 0.394 at the right hip. These
are small stress probes rather than a gait or anatomical-range claim. They do
not establish self-collision safety. Their negative foot-floor deltas also show
that a final gait must re-solve contacts after articulation.

The contact reader now binds POSITION, the selected skin, and every paired
`JOINTS_n`/`WEIGHTS_n` attribute to the declared primitive. The actual
three-set Tarbosaurus profile is unchanged; shortened two- and one-set profiles
reject. The actual two-set Allosaurus source constructs an eight-influence
`SkinRig` over all 40,105 vertices.

## Actual transfer result

The unmodified shared walk reaches canonical constant-skin-target calibration
and rejects before output with `constant skin target exceeded body-normalized
correction envelope`. The first production-rejected row is left touchdown at
0.0 s. Body height is 2.106182073 m, so the existing 0.06-body-height limit is
0.126370924 m. Iteration four proposes a 0.156723218 m constant, including
-0.150206057 m vertically, while the material patch still has a 34.306 mm gap
and the skeletal foot target residual/unreachable extension is 169.648 mm. The
mirrored right side is similar.

The initial material gap is about 39.15 mm; after 121.13 mm of accumulated
downward target offset it is still about 34.31 mm. Foot-root motion saturates at
about 36.3 mm upward and 813.3 mm forward from neutral while unreachable
extension grows from 44.99 to 169.65 mm. The same sole minimum remains vertex
27217, weighted 56.49% to the fitted MTP node and 43.51% to the ankle; the same
toe minimum remains vertex 27198, weighted only to the existing distal foot
chain. This excludes fixed upstream skin contamination as the immediate cause.

The first observed blocker is kinematic incompatibility between the copied
0.6-body-height Tarbosaurus walk intent and the scaled provisional Allosaurus
limb/foot geometry at canonical touchdown. This does not establish whether the
surface-fitted pivots, the body-height normalization, or the copied stride intent
is the incorrect assumption. The completed source-bound reach audit finds a
44.993 mm initial touchdown deficit, compared with a 154.203 mm margin in the
Tarbosaurus working baseline. The next step is a shared morphology-aware intent
resolver using declared animal support posture and family gait rules;
individually tuned animal clips would not establish reusable transfer.
The correction guard, contact thresholds, and articulation limits remain
unchanged.

## Verification

- 48 focused contact and rig-preparation tests pass in 37.67 s.
- The motion-set resolution test passes; the actual compile rejection is retained.
- Ruff passes for the changed contact/rig-preparation source and new rig tests;
  `F` checks pass for other touched source. `git diff --check` passes.
- Candidate generation is deterministic: the final prepared/admitted hashes
  equal the earlier bounded run after the normalization condition was tightened.

The checked-in report contains compact receipts only. Native overlay images,
scripts, the preserved source, and failed diagnostic scratch remain under
`ARC/audits` and `ARC/out` on external storage.

## Round-one postfix

Two independently reproduced compatibility gaps are closed at implementation
checkpoint `a26e106`. When scale normalization is omitted, rig preparation again
uses the historical exact target propagation: the unchanged v1 Allosaurus input
reproduces retained source `c56772d...` byte-for-byte. The explicit normalized v2
path still reproduces `c611bb49...` byte-for-byte. The exact emitted-tangent skin
reader now invokes the same complete primitive binding as contact and solve paths;
the real two-set Allosaurus geometry admits all 40,105 vertices and a one-set
omission rejects before tangent measurement. Eighty-nine focused tests pass.
The external reach-envelope audit remains diagnostic evidence for a future shared
morphology resolver and does not alter this rejected walk or its limits.

## Combined integration gate

The clean combined head `215588c75c5e64f5ce9f9dbbe3fa5fcfdfca03a4` passed
**1,078 tests plus 21 subtests in 632.05 seconds**, with no exclusions. Both
reviewers closed the two reproduced compatibility findings in a narrow postfix
review. Root independently reran the actual preserved source through both
preparation configurations and reproduced `c56772d...` and `c611bb49...` exactly.
The original-to-admitted full-weight surface comparison at the preceding
implementation remains below 0.525 micrometres; unchanged output bytes preserve
that result. Compact source, review, reach and test evidence is retained in
[integration/receipt.json](integration/receipt.json). This is a source-preparation
gate, not acceptance of Allosaurus motion or anatomy.
