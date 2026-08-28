# Normative evaluator dispatch P1 plan

## Scope

Close the single bypass in `reviews/technical-final-re-review.md`: choose the
normative evaluator from an explicit resolved profile capability, never by
detecting optional evidence keys. Missing required normative fields must reach
the declared schema and fail.

## Files intended to change

- `profiles/v8.3/profile.json` and its deterministic lock/channel references;
- `src/eonwild_motion/pipeline/validate.py`;
- `src/eonwild_motion/pipeline/normative_evidence.py`;
- `tests/test_integration.py`;
- narrow task reports/review inputs.

No artifact, motion, layer, species, rig, media, stable object, stable history,
or top-level channel generation may change.

## Acceptance checks

- V8.3 explicitly declares evaluator implementation/version/schema;
- deletion of each of `artifactSha256`, `selectedScale`, `metrics`, and
  `evidence` fails independently;
- missing/malformed/unknown profile evaluator declarations fail;
- the selector-only path is reachable only for the explicit legacy
  protected-channel proof contract;
- stable remains exact; working re-locks to the same artifact;
- focused and full suites pass; signed hurtener commit; no promotion.
