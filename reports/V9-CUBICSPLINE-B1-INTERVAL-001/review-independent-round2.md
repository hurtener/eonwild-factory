# CUBICSPLINE B1 postfix review, reviewer 2

Reviewed head: `50aa941b016566945455e7dccd229e35570ba44f`

Parent: `d18de689a10f81e8f1a1cb0fd3cd2c8c5fa5431f`

Scope: final bounded review of the three-file B1 primitive, tests and source
pipeline document. No emitter, recipe, profile, admission or gate change is in
scope.

## Verdict

**CLEAN.** The two reviewer-2 round-one P1 findings are closed. No new P0/P1
or reachable local P2 was found.

## Rounding-authority closure

The fixed `64 epsilon` heuristic and leaf-duration derivative rescaling are
gone. Hermite-to-Bezier controls, global derivative controls and de Casteljau
subdivision now propagate closed binary64 intervals. Every arithmetic operation
rounds its lower endpoint toward negative infinity and upper endpoint toward
positive infinity with `nextafter`; non-finite results and divisors spanning
zero reject.

The vector value and derivative bounds use convex hulls of interval controls.
The quaternion nonzero proof subdivides only the value controls and accepts a
leaf only when one component interval stays at least the requested distance
from zero. This supplies a valid lower bound on the raw quaternion norm. The
global derivative hull supplies the raw derivative upper bound, avoiding the
round-one `2**depth / h` amplification of uncertain leaf controls. One upward
step after `math.hypot` covers its documented less-than-one-ULP error. The
final `2 * |qdot| / |q|` calculation itself uses directed interval multiply and
divide.

Underflow is enclosed by the directed successor/predecessor around signed zero.
Overflow rejects. A subnormal duration that cannot produce a finite derivative
bound rejects. Depth and node exhaustion remain explicit `ContractError`s.
The returned nominal Bezier controls are labeled diagnostic; interval endpoints
remain the authority.

Independent exact-rational checks used binary64 inputs as exact fractions:

- 3,000 random vector cases across dimensions 1–4, scales `2**-500` through
  `2**500`, and durations `2**-40` through `2**20`; every exact Bezier and
  derivative control remained inside the reported component bounds, and the
  speed upper bound enclosed the exact derivative-control hull.
- 600 random quaternion cases with 33 exact dyadic samples each; every sampled
  exact raw norm exceeded the returned lower bound and every exact normalized
  angular speed remained below the returned upper bound.

These randomized checks are corroboration, while the directed-interval and
convex-hull construction supplies the proof.

## Fail-closed conversion closure

Numeric conversion now catches `OverflowError` and `ValueError` and maps them to
`ContractError`. The three round-one counterexamples all close:

- a `10**10000` vector value;
- a `10**10000` duration;
- a `10**10000` minimum quaternion norm.

Each now rejects through the module contract rather than leaking a Python
conversion exception.

## Checks

- `41 passed in 2.83s` for the interval-bound and exact-emitted-tangent modules.
- The author reports 47 focused tests passing on the frozen head.
- Ruff passes for the modified source and focused test file.
- `git diff --check` passes for the exact parent-to-head range.
- The three huge-number counterexamples reject with `ContractError`.

The source-pipeline document remains honest: B1 supplies source-side binary64
math only. Exact float32 export binding, continuous source pose/tangent
generation, FK/LBS and contact interval authority, and the emitter remain later
work. The existing full CUBICSPLINE technical block must remain in place.
