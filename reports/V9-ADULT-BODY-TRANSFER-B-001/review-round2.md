# Body counter-roll final bounded review — `329b150`

## Review range

- Base: `c6330655d30a8ce0b551bb5dd90f697f0802821c`
- Head: `329b150566d08c2a2ca19153aa844f8ae054855f`
- Scope: the two-commit B delta only (`02adf383` implementation and
  `329b150` v5 inputs/tests).

## Findings

### [P1] The new hierarchy check accepts a leg as the upper trunk

Location: `src/eonwild_motion/solve/performance.py:186-196`

The predicate verifies only that the supplied `spine + chest` names are unique,
exist, and form *some* direct chain starting at the pelvis. It does not require
a non-empty spine or prohibit overlap with either leg/contact chain. Because
`chest` is always appended, `not names` cannot reject an empty spine.

A forged but hash-bound semantic rig can therefore set:

```python
roles["spine"] = []
roles["chest"] = roles["legs"]["left"]["contactChain"][0]
```

The new check accepts that binding and applies the advertised upper-trunk
counter-roll to the left hip. A direct real-source reproduction completed
`solve_airborne_gait` and emitted a 45,489,284-byte GLB with receipt status
`PROVISIONAL_REQUIRES_SKINNED_AND_VISUAL_GATE`; it did not reject the semantic
misbinding. Separately, `roles["spine"] = None` raises raw `TypeError` at line
186 rather than the project `ContractError`, because the rig snapshot is loaded
as JSON roles without semantic schema validation at
`factory/compiler.py:209`.

This is reachable through the versioned rig input boundary after recomputing
its authorized hash, and it silently targets a locomotion limb instead of an
upper-body chain. That violates the feature's stated semantic-hierarchy guard
and the factory rule that incompatible topology must reject rather than reuse
an unrelated chain.

Fix by validating the complete semantic rig document before compilation, or at
minimum require `spine` to be a non-empty sequence of unique node-name strings,
require `spine + chest` to be disjoint from pelvis/root, bilateral contact and
toe chains, tail, neck, and head roles, and translate malformed shapes to
`ContractError`. Add negative tests for `null`, empty spine, and a complete
pelvis-child leg chain masquerading as `spine + chest`; the current test at
`tests/test_motion_performance.py:395-411` exercises only the duplicate-chest
case despite its name mentioning disconnected roles.

## Validation evidence

- `git diff --check` passed for the exact B range.
- All v5 recipe source/profile hashes matched their committed bytes; version 5
  correctly supersedes v4 and retains the v4 gait plus unchanged source, rig,
  animal, contact, articulation, and coordinate bindings.
- Targeted B tests passed: `45 passed in 9.84s` for
  `tests/test_motion_performance.py` and
  `tests/test_adult_body_weight_transfer_catalog.py`.
- `factory verify out/continuation-adult-v5-body-counterroll-001/package`
  returned integrity `PASS`, technical `PASS`, visual `PENDING`, Unity
  `NOT_RUN`, and production approval `false`. Output, skinned-contact, cyclic
  continuity, rotation-rate, solver, and articulation checks are all `PASS`
  for the committed valid rig.
- Default legacy serialization remains compatible: the optional field defaults
  to `None` and is omitted from the performance plan unless selected.

## Verdict

One P1 finding. No P0 or additional P2 findings. Native visual quality remains
outside this review and with the root reviewer.
