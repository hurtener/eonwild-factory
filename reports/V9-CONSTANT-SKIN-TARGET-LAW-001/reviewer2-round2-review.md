# Constant skin-target law final round 2 — reviewer 2

- Final reviewed head: `990aef08c18d2cb8cc5dbaaf5c268f1b290a7cdc`
- Frozen source head: `a6253053b2592ad0dffeb37ca41c2a2f5b3ab783`
- Closed provider ancestor: `f847630b901d86b4aeb895fe50fd9523b13d79e6`
- Decision: **PASS — no P0 or P1 findings.**

## Round-one closure

The actual retained `SourceMotionQuery` now supplies the provider request used
for admission. Its source/current uniform scale, semantic roles, solver and
locomotion gait, transition, complete decorated plan, coordinate frame,
contact profile, articulation profile, source clip, and overlay mode enter a
checked binding. The explicit compile request and actual query must both match
the sealed provider. Mutating the current source scale after construction
fails closed.

The law owns immutable copies of both calibrated vectors, hashes them, checks
their integrity before every value, and returns detached arrays. Returned pose,
row, and nested diagnostic mutation cannot alter a later evaluation.

Pointwise admission now evaluates both semantic feet after applying both
constants. Loaded residual over `0.2 mm`, unloaded clearance under `0.1 mm`,
foot-target residual or unreachable extension over the established `1 mm`
solver limits, articulation violation over the established `0.01 degrees`, or
non-finite evidence returns typed `UNAVAILABLE`. Both feet are jointly checked
at both canonical touchdown events after calibration, closing the cross-foot
case. Derivative, optimizer-branch, branch-stability, and global-C1 authority
remain explicitly unavailable.

The earlier local findings are also closed: extreme integers become public
`ContractError`, nested returned data are recursively frozen, and Ruff passes.

## Independent checks

Twelve selected adversarial regressions passed in `55.56 s`, covering actual
query/request mismatch, current-source mutation, returned-state isolation,
six typed pointwise failure modes, cross-foot touchdown admission, transition
versus steady calibration, constructor/refinement bypass, extreme time, and a
renamed/root-rotated provider fixture. JUnit and logs are retained under
`audits/constant-skin-law-round2-reviewer2/`:

- `focused-tests.log` SHA-256 `38c3eea7aed170d62d8212d0e4f9cdf2f0a6b3e10e8a81239d4c94fabdf57096`
- `focused-junit.xml` SHA-256 `a3fb5d38afb0c8840d3e240580194ffc79938cfb7e91bee9d8a22ad96049ceb2`
- `ruff.log` SHA-256 `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`
- independent manifest check SHA-256 `e2055477f9737b41ac374b8bd200a4c08de1205539860b364da6709f0c53312e`

The manifest, every input path, recipe, changed code file, row order, status,
and output size/hash were independently rehashed. They identify published
input head `83aa5e5391848493c902af0c6bd4ecab6228afe6` and the genuine recipes:

- `walk.v3`: recipe SHA-256
  `0e9c04f6e38d5d523cd354577ed82650846cf4edae3d1cddfacf76906530c783`,
  authored performance SHA-256
  `ade6d37243d4b9597c9d2c15a86a667b5528654aca3998315abe7f2f06a968be`,
  305/305 `AVAILABLE` native rows.
- adult V9: recipe SHA-256
  `f55da91847dc63489f9655cfc3641bee665bf8ce6122755a61748d98fabf3ccd`,
  authored performance SHA-256
  `e133819dddf19bd224ddec7419687208e01abf8f3906fa147837813710dc2dfc`,
  297/297 `AVAILABLE` native rows.

The retained full-cycle files bind actual source, rig, contact, gait,
performance, animal and articulation inputs where present, effective plan,
gaze calibration, provider/query/calibration identities, per-row source and
checked rows, poses, constants, and pointwise observations. Both cover exactly
one 2.46-second same-foot cycle. This re-review did not rerun those cycles
because source head `a6253053` is unchanged by the final report-only commit.

No recipe, emitter, default behavior, accepted asset, or threshold is activated
by this diagnostic. The result grants pointwise source-geometry evidence only;
it does not establish derivatives, branch stability, global C1 continuity,
emitted interpolation behavior, visual acceptance, Unity parity, or production
approval.
