# Round-1 review fixes

This record closes the four P1 findings and the related local P2 findings for
the bounded stationary-support slice. It does not widen the slice into support
polygon/friction dynamics, multi-family support, GLB motion, or CLI wiring.

## P1 findings and fixes

- Absolute dynamics are admitted only when the body schema and semantic loader
  see `absolute_policy: fixture_absolute_allowed` together with
  `status: fixture`, `kind: synthetic_fixture`, and `scientific_claims: false`.
  The plan schema/loader carries and rechecks the same provenance boundary.
  A Tarbosaurus profile whose mass fields are changed to absolute while its
  provisional provenance remains unchanged is rejected by the negative test.
- Recursive `ensure_finite` checks run before and after schema admission and
  before every V9 canonical hash. JSON decimal parsing rejects exponent
  overflow, including `1e999`; report writing uses `allow_nan=false`. Focused
  coverage exercises contact, body, embedded-plan evidence, and direct hashes.
- Segment COM fields are now `com_body_m` under the declared
  `segment_com_frame: body`. The loader validates unique IDs, one root,
  existing parents, no self-parent, and no cycles. The planner documents and
  consumes already-resolved common body-frame points only; it does not perform
  hierarchy or world transforms.
- The synthetic profile follows the handoff fixture's materially different
  dimensions and mass distribution, with authored deterministic body-frame COM
  points and fixture provenance. Tests compare segment payload/hash and output
  COM while asserting the planner contains no Tarbosaurus branch.

## P2 findings and fixes

- Evidence now requires named `intent`, `program`, and `body` inputs plus at
  least two uniquely named `contact_*` entries. Every entry contains a path and
  source SHA-256; the loader resolves paths inside the repository, recomputes
  each hash, loads every source through its expected V9 schema, and binds IDs,
  contact states/effectors/IDs, and contact payloads to the embedded plan.
  Empty, stale, or substituted manifests are rejected by focused tests.
- Canonical gravity `[0.0, -9.81, 0.0]` is required for the stationary slice.
  Support and feasibility fields explicitly say `bookkeeping_only` and
  `physics_evaluated: false`; contact centroid output is not a support proof.
- Segment inertia remains in `SegmentMassProperties` and in the strict body
  schema, even though this static planner does not consume it.

## Verification after fixes

- Focused V9 suite: 23 tests passed.
- Existing repository suite: 52 tests passed in the final regression run.
- Final emitted Tarbosaurus report hashes, reloaded through the strict evidence
  schema, are: plan `828f59439732de0de8b287b688284afdb0ab4d60ee5caae45c755f2178866629`,
  evidence `9120adbbfa66330c909de0402fb48c9cedb235ee6f5bc233501ab638713ed8d0`,
  and canonical report `ad3b687e0888676c6ea400f5390f3709885454d34acb26c2af3beb4c09832f6a`.
