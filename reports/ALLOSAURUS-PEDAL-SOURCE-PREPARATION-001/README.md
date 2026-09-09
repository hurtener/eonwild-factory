# Allosaurus pedal source preparation 001

This checkpoint adds a **non-promoted, provisional engineering** Allosaurus
pedal rig to the shared factory. It is source preparation for a real
second-animal transfer test, not a finished walk, anatomical reconstruction,
Unity production asset, or catalog selection.

## Exact integration

The reviewed changes were generated as `4eee1ba4d35d2a5fd767e7d14e9adf20a57b96cd`,
`db0adb6518898ae651eb999f1003590f97ee3b20`, and
`f0a08c8c481bb27e5f00080d5b46dba39e3a20f3`. They were replayed without
conflict onto published `f24297da9f3ef3a5db28cfd30860fa15760bb50d` as
`3811430`, `9b956f8`, and `fca59c7`.

The immutable prepared source is
`assets/sha256/3613b67c9513c4ed5b88665c7606e0c15791bb922b01a72e7223aa112546ec89.glb`.
The separately admitted geometry is
`assets/sha256/6b588e9ffa1ebdb167f1619593d8107779b1dfd943fe9dc0c02830572a953d8c.glb`.
The public v2 animal, contact, and neutral-pose inputs bind the admitted hash;
the rig-preparation config binds the preserved incoming/source identity.
Regeneration retained the exact `3613b67c…` bytes.

The declarative preparer adds three independently weighted pedal deformation
branches per side and the semantic articulation mapping drives all branches.
They are mesh-informed engineering proxies for the three visible lobes, not a
complete fossil phalange reconstruction. The original artist pivots and segment
lengths were placeholders; this checkpoint does not claim that the provisional
replacement pivots are corrected anatomy. Neutral full-weight skin is
preserved within the tested tolerance, weights remain normalized, and the
closeup receipt records neutral and bilateral ±8 degree deformation views.

## Review closure

Round 1 found two P1 families: ambiguous repeated physical skin rows could be
mutated more than once, and public inputs bound the raw prepared asset rather
than admitted geometry. The postfix binds raw and admitted identities
separately, validates all public v2 inputs, deduplicates identical physical
accessor layouts, and rejects partially overlapping physical byte layouts.

A first accessor-index fix was insufficient because duplicate accessor
descriptors could address the same bytes. The exceptional narrow closure keys
physical layout by byte start, count, stride, item size, component/type and
normalization. Root and reviewer 2 both reproduced zero changed vertices for
the duplicate-descriptor case and confirmed the exact raw regeneration.

On the published-base integration, 67 focused rig-preparation, Allosaurus, and
shared motion-set tests passed in 37.84 seconds. The changed preparer/tests pass
Ruff and `git diff --check`. The published base `f24297d` separately has hosted
contracts 1,123 tests plus 21 subtests PASS in 648.92 seconds and source-evidence
PASS; this focused integration run is not a replacement full suite.

## Motion boundary

The retained public shared-engine preflight is still **BLOCKED**. Its first
observed loaded-foot failure was a 4.630359 mm material residual with a
-2.608252 mm minimum gap. Subsequent audit-only source diagnostics distinguish
plantar weight ownership from a later whole-cycle reach problem, but neither
counterfactual is included here.

Hands remain unbranched placeholder chains. The existing jaw hinge still needs
soft-tissue and full-head deformation work. The three pedal branches do not
provide complete independent digit anatomy. An actual Allosaurus walk/fast-walk
package, full native review, continuous Unity runtime parity, mass physics, and
production promotion remain pending.

The tracked Unity receipt covers four source samples with full influence
consumption and a maximum 0.202939 mm source error. It does not establish
Animator/runtime, continuous-cycle, or Allosaurus parity.
