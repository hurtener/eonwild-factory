# CUBICSPLINE B1 interval-math review, reviewer 2

Reviewed head: `d18de689a10f81e8f1a1cb0fd3cd2c8c5fa5431f`

Base: `76219543f5bc5982a77df1435fe1668e39de821a`

Scope: the three-file B1 diff only. This is pure source-side interval math and
pipeline design; it does not emit CUBICSPLINE channels or alter technical
admission.

## Findings

### P1: the fixed rounding allowance does not establish the advertised conservative bounds

`src/eonwild_motion/glb/cubic_bounds.py:16-17,42-56,152-199` uses one
`64 * ulp(1)` plus eight-ULP scale allowance around already rounded controls.
The control values are then subdivided as many as 40 times and differenced over
a leaf duration `h / 2**depth` to derive the quaternion rate bound. The code
does not carry a bound for error accumulated by control construction and each
de Casteljau split.

If a leaf control has inherited uncertainty `delta_c`, differencing adjacent
controls and converting to per-second rate contributes error on the order of
`6 * 2**depth * delta_c / h`. Reapplying a fixed source-scale allowance after
the differencing is not a derivation that the returned value encloses that
error for all binary64 inputs, cancellation patterns and subdivision depths.
No numerical under-bound was reproduced in the existing dense tests, but those
tests cannot supply the missing universal rounding proof. The author separately
agreed this envelope cannot be presented as rigorous interval authority.

This is P1 because a later rate gate would consume the result specifically as a
conservative upper/lower certificate. The bounded fix is directed binary64
interval arithmetic for control construction and subdivision, plus a global
quadratic derivative-control hull so derivative uncertainty is never rebuilt
from rounded leaf controls. The current full CUBICSPLINE technical block must
remain until that proof and the export/contact stages exist.

### P1: large integer inputs escape the fail-closed contract

`src/eonwild_motion/glb/cubic_bounds.py:20-26` accepts Python integers and calls
`float(value)` outside an exception boundary. Finite but nonrepresentable
integers therefore raise raw `OverflowError`, rather than the module's declared
`ContractError`.

Reproduction at the reviewed head:

```python
cubic_vector_bounds((10**10000,), (0,), (0,), (0,), 1)
cubic_vector_bounds((0,), (0,), (1,), (0,), 10**10000)
cubic_quaternion_bounds(
    (0, 0, 0, 1), (0, 0, 0, 0),
    (0, 0, 0, 1), (0, 0, 0, 0), 1,
    minimum_raw_norm=10**10000,
)
```

All three raise `OverflowError: int too large to convert to float`; none is a
`ContractError`. Catch conversion overflow in the numeric boundary and reject
it as contract input. The directed-interval implementation must likewise map
arithmetic overflow to `ContractError`.

No P0 or separate reachable P2 was found. The source-pipeline document is
appropriately explicit that arbitrary-phase solve/tangent construction,
float32 export binding, contact/FK/LBS interval authority and emitter support
are later stages.

## Checks

- `15 passed in 0.03s` for `tests/test_cubic_interval_bounds.py`
- Ruff passes for the new source and test file.
- `git diff --check` passes for the exact three-file range.
- Direct malformed-input reproduction confirms the three uncaught
  `OverflowError` cases above.

Verdict: **P1 OPEN.** Consolidate the rounding authority and conversion
fail-closed corrections in one bounded fix, then perform one narrow diff-only
closure review. Do not integrate B1 at this head.
