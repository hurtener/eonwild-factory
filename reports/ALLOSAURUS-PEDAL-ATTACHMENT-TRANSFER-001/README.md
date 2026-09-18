# Allosaurus pedal attachment transfer 001

This checkpoint records an opt-in, non-promoted Allosaurus source-preparation
operator. Reviewed implementation head
`f9337f7a6d084de2ed42f1d2a88c09dbc512f826` (tree
`49cedaac877f645b59e5c6130cc8910438a5c3f5`) was integrated without source
changes as `dbc1e295f43ca9a0e16ad1e8690af533ce008b50`.

The operator transfers only an upstream attachment joint's existing weight to
already weighted descendants of a declared pedal root. The declaration binds
the immutable raw source, complete physical skin rows, selector frame,
topology, and destinations. It rejects unsupported aliases, overlapping
selectors, missing ownership, invalid topology, and unnormalized results.
Positions, normals, texture coordinates, triangles, nodes, skins, and inverse
binds remain unchanged.

The immutable input source is
`91d9816b6bbaeb1037f3e9cbf253261799d8a4121efd91e0e2185f76908a6bf7`.
The prepared candidate is
`06f44c2f2f0702bb6db93faa3315ce5ef27d37b911bcd7af5f64c9191634790a`;
the separately geometry-admitted candidate is
`975a4bc626bc8d79537939ab3a0796473f54aa2c5fadc541f8561b13e442e6c6`.
Legacy V3 regeneration remains byte-identical at
`3613b67c9513c4ed5b88665c7606e0c15791bb922b01a72e7223aa112546ec89`.

Root independently regenerated the exact prepared output, checked structural
preservation, and passed 41 focused tests in 18.85 seconds. Reviewer 2 passed
12 focused attachment tests in 5.72 seconds. Both reviews report P0=0 and
P1=0.

One local P2 remains in terminology. Each coordinate-axis falloff is a quintic
C2 curve, while their minimum-composed spatial field has derivative creases on
interior equal-gain surfaces and is not globally C2. The retained deformation
probe did not establish a mesh failure, so this checkpoint records the precise
boundary without changing the reviewed output.

This is prepared-source evidence only. It does not establish whole-cycle
contact, clearance, ROM, rate, visual, Unity, anatomical, biological, or
production acceptance. The current Allosaurus gait remains blocked, and hand,
jaw, independent digit, and broader onboarding work remain unfinished.

Exact compact receipts and the reviewer probe are under `evidence/` and bound
by `SHA256SUMS`.
