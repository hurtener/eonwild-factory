# V8.3 normative evidence P1 fix plan

## Scope

Close `reviews/technical-final.md` P1-1 without modifying motion, artifacts,
catalog, profiles, or channels. Replace selector-only trust for the working
candidate with a schema-validated, fail-closed evaluator that cross-checks the
profile-bound report against the actual candidate/baseline identities, layer
parameters and ownership, the complete sweep, normative thresholds,
final-skinned witnesses, and media/report bindings.

## Files intended to change

- `src/eonwild_motion/pipeline/normative_evidence.py`
- `src/eonwild_motion/pipeline/validate.py`
- `schemas/motion/normative-evaluation.v1.schema.json`
- `schemas/motion/amplitude-sweep.v1.schema.json`
- `schemas/motion/final-skinned-comparison.v1.schema.json`
- `schemas/motion/balance-thresholds.v1.schema.json`
- `tests/test_integration.py`
- evidence documentation owned by this task

## Acceptance checks

- the exact reviewer corruption (`FAIL`, zero artifact SHA, scale 999, null
  metrics with true selectors) fails;
- missing/non-finite metrics, wrong threshold baseline/path, false sweep
  status, wrong selected winner, and tampered final-skinned evidence fail;
- correct evidence emits candidate, baseline, threshold, sweep, witness,
  ownership, and media bindings;
- full suite passes; V8.2 legacy evidence remains supported;
- artifact/profile/channel hashes remain byte-identical.

## Assumptions

- Existing hash-pinned legacy profiles retain their selector-based compatibility
  path; the normative evaluator is selected structurally by the richer evidence
  envelope, not by a release/species literal.
- Blender-derived witness positions remain independently generated evidence;
  this validator verifies their schema, identities, sample counts, finite
  values, threshold bounds, and cross-document equality.
