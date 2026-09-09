# Constant skin-target law round 1 — independent reviewer 2

- Reviewed head: `07514b88e8d1624673c208a0883853c8bd1e7be5`
- Closed provider ancestor: `f847630b901d86b4aeb895fe50fd9523b13d79e6`
- Direct commits under review: `c7618ccc526a469992bfe98df3976355c98298fe` and `07514b88e8d1624673c208a0883853c8bd1e7be5`
- Scope: the new non-emitting constant skin-target law and its focused tests only.
- Decision: **CHANGES REQUIRED — three P1 authority/evidence families, two local P2 hardening items.** No additional P0/P1 was found beyond the independently reproduced families below.

## P1 — the evaluated query is not bound to the admitted request

`CanonicalConstantSkinTargetLaw.build` validates the separately supplied provider/request, then evaluates the separately supplied `SourceMotionQuery` without proving they describe the same source, semantic roles, gait/transition, complete decorated plan, axes, contact profile, or articulation profile.

Independent reproduction constructed the request/provider with the canonical default performance and passed a valid query whose plan additionally declared `pelvis_yaw_degrees=3.0`. Construction returned successfully. The law therefore labels values from a different body program as belonging to the validated request.

The fix needs one authoritative query/request binding. Revalidating only the independent request arguments does not bind the object that actually owns `context`, source, body response, rows, and evaluation.

## P1 — returned state can corrupt the law, and `AVAILABLE` is unconditional

`corrections_m` returns the law's owned arrays. `setflags(write=True)` followed by a 10 mm left vertical mutation changed later evaluations. The next loaded value still returned `AVAILABLE` with:

- residual: `0.010006475526659746 m`
- minimum gap: `0.01010647552665615 m`
- clearance flag: `true`

The law must retain a checked immutable internal calibration and return detached values. A NumPy writeable flag on an owned array is not an ownership boundary.

`_observe_at` currently returns `AVAILABLE` regardless of its observations. It does not enforce loaded material residual, unloaded clearance, solver foot-target residual, unreachable extension, or articulation-envelope violation. Construction checks only each anchor side at its own touchdown; it does not check every simultaneously loaded foot at both calibration events, so cross-foot influence is not admitted.

The corrected pointwise result should be available only when all relevant feet pass the existing pointwise constraints. A failure should be typed unavailable/rejected with its observed reason. Derivative and optimizer-branch authority must remain separately unavailable.

## P1 — reported full-cycle evidence is not bound to the claimed production inputs

The focused `_law` helper replaces the walk's authored performance with `Performance(canonical_support_anchors=True)` defaults and supplies no articulation/gaze binding. The provisional `adult-v9-full-cycle.json` was generated from the adult V8 recipe with performance v6, not the current adult V9/performance v8 package. Existing heredoc runs retain neither an executable reproducer nor complete source/recipe/code/input hashes and per-row pointwise results.

Before this stage can support the next continuity step, retain one executable exact-input scan for the actual adult V9 and the named legacy walk family, including source, recipe, plan, performance, contact, articulation, code, query/provider binding, every evaluated row, and unavailable reasons. Provisional aggregates cannot substantiate recipe-level coverage.

## Local P2 hardening

1. `value(10**10000)` leaks `OverflowError: int too large to convert to float` from `math.isfinite` instead of the public `ContractError`. Catch numeric overflow before converting the admitted time.
2. `ConstantSkinTargetValue` is only shallowly frozen: `row["feet"]["left"]["contact"]` and nested observation mappings remain caller-mutable. This did not alter future law state in the reproduction, so it is lower severity than the owned correction-array issue, but the returned diagnostic should use the existing recursive freeze/detach boundary.

Focused Ruff also reports 26 findings confined to the two new files (mostly E701/E702 one-line statements and one unused import). This is local cleanup rather than a separate behavior finding.

## Verification

```text
PYTHONPATH=src:tests uv run --frozen --group test pytest -q \
  tests/test_constant_skin_targets.py tests/test_canonical_support_anchors.py \
  --basetemp out/constant-law-r1/pytest
11 passed in 46.54s

git diff --check f847630b901d86b4aeb895fe50fd9523b13d79e6..07514b88e8d1624673c208a0883853c8bd1e7be5
PASS
```

Independent adversarial result: `out/constant-law-r1/adversarial.json`, SHA-256 `1bc9a17563d3d6cf49d1620c436b4d706feb821a7303ebf1dfaa3b6dcf26d1c1`.

Pointwise observation scan: `out/constant-law-r1/pointwise.json`, SHA-256 `2b463a97b0063890ef8ed6e3a52164249a0e04f62a8ff62ec0cecc6a80d4b9ef`.

Reviewed files:

- `src/eonwild_motion/solve/constant_skin_targets.py`: `44137dd690a353d83183ba492fe4c45194e8b4b1423e65bc4c655ee7d3b156a3`
- `tests/test_constant_skin_targets.py`: `001f740c71e43d65bfa4838a0df46a019441286b13f21bef06204edd00fd5c3c`

No source, provider, recipe, emitted asset, threshold, or approval state was changed. The closed provider stage is not reopened by this review.
