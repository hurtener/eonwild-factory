# PROCEDURAL-ENGINE-V8-3 — channel P1 closure

## Result

Both technical-review P1s are closed in the stable-promotion boundary.

Stable advancement now accepts only an installed `manifest.json` below the
repository's `releases/` area. It schema-validates that manifest, binds its
engine, release, profile, working-channel lock, artifact path, and artifact
hash, and derives the next stable profile/release/artifact references from
those installed bytes. A promoted stable selector resolves to that exact
content-addressed artifact. The legacy initial stable capsule remains a
read-only compatibility source until the first approved promotion.

History and channel state are now staged as fsynced sibling files. Their
installation is guarded by exact prior-state and no-overwrite preflight checks;
any exception restores the prior state bytes, removes only the history record
created by the attempted transition, removes temporary files/directories, and
allows the identical transition to retry. Promotion additionally removes the
new release destination if this state transition fails.

## Verification

- Focused channel suite: 6/6 PASS.
- Controlled promotion/immutability checks: 2/2 PASS.
- Full suite: 27/27 PASS in 44.272 seconds, no skips.
- Injected failures after history staging, state staging, history installation,
  and state installation each restored exact state, left no history record,
  and accepted a retry.
- Promotion-level failure after history installation left no destination,
  state mutation, or history directory; identical retry passed.
- A deliberately distinct promoted destination became the exact stable
  manifest/artifact path and resolved successfully.
- No `releases/` test residue remained.
- Canonical channel state, V8.2 profile, V8.2 artifact, and V8.2 release
  manifest hashes remained unchanged.

## Boundaries

No motion, hip-balance behavior, profile, GLB, legacy tree, review report, or
evaluation report was changed. No real release was promoted.
