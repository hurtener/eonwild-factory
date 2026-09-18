# Root bind-pose admission review, round 1

Code/input head: 7d3945b7083c1e04dbf360e852d401e29d3e98fa. Final report head: 16aab6232698c6f641c34624c0ea246c67f1684e. Review scope is generic recovery, input validation, catalog/source claims and independent static Blender parity. The old default admission path remains unchanged. No visual walking acceptance is implied.

## Findings

- **P1: Nonfinite POSITION can be admitted with a false zero skin error.** `factory/source.py:111-138` reads positions but checks finite values only for weights. Replacing one actual source POSITION float with NaN is accepted; NumPy propagates NaN through the error reduction, then Python `max(0.0, nan)` records `maximum_reopened_skin_position_error_m: 0.0`. Require finite source positions, transformed positions, residuals and every published maximum; fail with ContractError. Add regression for NaN/Inf and arithmetic overflow as applicable.
- **P1: Malformed index metadata is coerced into valid indices.** `factory/source.py:148-157` permits Boolean/fractional skin joint values via int(), and a negative inverseBindMatrices accessor is interpreted as Python indexing. On the actual asset, JSON true in place of joint 1, a fractional joint, and inverse accessor -1 pointing to an appended duplicate valid accessor are all accepted. Validate exact non-Boolean integer type, nonnegative range, accessor semantic/component/type and joint/weight references before reads; avoid int coercion as validation. Add meaningful malformed-index tests.

The independent reviewer is assessing valid intermediary-node capability separately. These root findings do not require changing valid source geometry, motion or any tolerance.

## Evidence

`root-bind-round1-malformed.json` records the four accepted corruptions and emitted identity. Thirteen existing focused bind/catalog/admission tests passed (10+3). Root independently imported the fixed source into real Blender 5.2, inspected side/front/rear/three-quarter static views, and compared all 59169 vertices: max skin delta 3.0198903336 micrometres, RMS 0.6982234105; max semantic origin delta 1.1690565795 micrometres. The wide-open bind jaw is explicit and remains a separate behavioral calibration. Static findings support joint/skin alignment, not anatomy, mass or walking approval. Final candidate documentation accurately retains visual pending, exact-loop blocked, Unity not run and no production approval.
