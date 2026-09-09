# Allosaurus acquired-reference public failure review

Status: **confirmed source-query mechanical rejection; no package emitted**

## Bound execution

- Generator source: `c51b3aa86bfac51df0d30785303f698fc1f6c3a3`, tree `87331ea7435bff8b93df443442f5f498873c6ee6`
- Motion set: `catalog/motion-sets/allosaurus-engineering-acquired-walk.v3.json`, SHA-256 `a760ce366ff6021e8d03993a3b99b585105d006d8ea1363b25292618a05c7cbe`
- Adapter/query binding: `74b07b8182c69e93634a5d8a6c2f9cb243d1ff4ce5c95dd635976e38f14bfdf1`
- Exact failing source time: `0.2238918918918919 s`
- Public diagnostic result: `constant skin target source value is unavailable`; underlying reason `right authored material clearance material gap is nonmonotone`

The retained public replay constructed the production compiler/query from the locked motion set, descriptor, capsule, source, calibration, and material-clearance policy. The tracing driver intercepts that exact query immediately before source-cubic emission and calls `evaluate_with_target_offsets` only at the recorded failing time. This rules out an output wrapper or package replay drift as the cause.

## Measured failure

The right material-floor solve targets a `0.013291004300055361 m` gap. Its current lower and upper bracket samples were:

| requested height | solved material gap | min skin vertex |
|---:|---:|---:|
| `0.014268489938549051 m` | `0.013265030863688103 m` | `398` |
| `0.014336423246479702 m` | `0.013332964132288506 m` | `398` |

The next secant sample requested the intermediate height `0.014294463389953738 m`, but produced the larger gap `0.013351248213287592 m`, which is `18.284080999086266 um` above the current upper gap. The monotonic tolerance is `0.01 um`, so the departure is about `1828.4x` the numerical guard. Vertex `398` remains the minimum throughout this local bracket, excluding a minimum-vertex identity switch.

The full pose trace also changes the right solved pitch from `56.62187337875366 deg` at the upper sample to `56.633944511413574 deg` at the intermediate sample. Target residual rises from `0.176836008 um` to `61.272527805 um`; unreachable extension rises from `0` to `61.363103086 um`. These remain below the established `1 mm` hard gates, but the coupled IK/reach-clamp solve makes the material response locally nonmonotone. This is a real response of the current deterministic solver, not evidence of biological or force behavior.

The left solve passes. Its seven sampled gaps remain ordered for the same query. The failure is therefore localized to the right source pose and authored-material clearance solve at this time.

## Smallest implementation requirement

Keep the ordinary monotone-floor path unchanged. For the authored-material adapter only, replace the assumption of a monotone scalar gap with a deterministic, bounded joint-feasibility bracket over the same requested-height domain. Each candidate must be admitted jointly by:

- measured material gap at or above the bound target,
- target residual and unreachable extension within the existing limits,
- articulation/envelope constraints within the existing limits,
- preservation of the selected solver branch/component where that authority exists.

The chosen candidate must be re-solved by the full production query and pass the same checks before becoming available. If no connected admitted interval is established, return `UNAVAILABLE`; do not accept a convenient sample, weaken the monotonic tolerance, or claim a global minimum from this local search.

## Evidence

- `nonmonotone-trace-002.json` SHA-256 `f9efdc15a81bb3802e4b3819812f825f7ec403a1e004805893232ae130a11930`
- `trace-nonmonotone-002.py` SHA-256 `ac03b17895603e780e67977489001ee299ec9a63b9154b2c7c957b338d7213a7`
- `unavailable-002.json` SHA-256 `beb119a1399b828598cf39d737efaabdca13250bf319ddfd9896f8a290d2da69`
- `diagnose-unavailable.py` SHA-256 `2c597d97a1f10e87ac24c8aff2b999cf9d976bd2dcb77f5663a2ca4e2bc8170a`
- `diagnose-002.log` SHA-256 `33cce4cb86c167af79de974d21a5b91a5add327aebec6241cde315cddace9b33`
- `compile.log` SHA-256 `3b812c371cbf256c325a2f521da73e8ba26cd4f376876e69a8b15599d30445cd`

This diagnosis is non-emitting. Candidate technical validation, emitted replay, visual review, and Unity validation remain **NOT RUN**.
