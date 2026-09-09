# Root B1 round-one review

Frozen source: d18de689a10f81e8f1a1cb0fd3cd2c8c5fa5431f, parent 76219543f5bc5982a77df1435fe1668e39de821a.

Scope: three added files only, pure Hermite interval primitives and tests/source-pipeline documentation. No emitter, recipe, source geometry, CUBIC admission, threshold or final acceptance change.

No reproduced P0/P1 functional finding. The Hermite-to-Bezier control conversion, derivative time units, quaternion component-based nonzero lower bound, recursive subdivision and fail-closed budgets are coherent. The angular bound deliberately overestimates radial motion and does not mislabel normalized Hermite as constant-speed SLERP. Source tangent and skin-refinement continuity limitations are explicit and keep later emission blocked.

Focused tests: 42 passed in 1.68 seconds. Independent diagnostic root-cubic-b1-round1-d18de68.json checks 3000 exact-rational vector control/derivative hull cases, 300 quaternion curves at 17 exact-rational sampled norm/angular-rate values, and a nonzero curve requiring depth 30. All passed. Finite test samples do not prove every floating-point interval.

P2 / authority prerequisite: the 64-epsilon plus 8-ULP rounding envelope has no operation-count derivation for 40 subdivision levels and derivative amplification. Before this helper can support a technical-admission proof, justify that envelope against inherited rounding and all permitted depths, or propagate outward intervals through the arithmetic. No numerical underbound was reproduced; this is a proof gap, and the unchanged full CUBIC rejection currently contains its impact. The author is preparing a bounded response while the independent reviewer inspects the frozen head.

This review does not approve CUBIC emission, whole-contact interval authority, motion quality, or production use.
