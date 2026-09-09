# Allosaurus authored-material joint feasibility 001

## Status

The adapter-only numerical correction is frozen at `24c0651e6d815f946049c516899c2bebe8539bab` (tree `310af9feb7419a8ed5bedd3946bfef0a7936a246`), based on diagnostic-message head `ee8e0e5354736bd5afde29e3988b7c5fb03f3417`.

Root's final narrow review and the independent reviewer-two closure report P0=0, P1=0, and P2=0. The actual old-source public package compile launched from intermediate `bf6af4f32df6bb9ee4166c3a4b88af2be246f5a2` remains **RUNNING / UNACCEPTED** at this report boundary. No emitted, visual, Unity, anatomical, or production acceptance is claimed.

## Exact failure

The clean `c51b3aa` public compiler failed at `t=0.2238918918918919` for the right foot with `authored material clearance material gap is nonmonotone`. The same minimum material vertex, index 398, produced this local sequence:

| Requested height | Material gap |
|---:|---:|
| 0.014268489938549051 m | 0.013265030863688103 m |
| 0.014294463389953738 m | 0.013351248213287592 m |
| 0.014336423246479702 m | 0.013332964132288506 m |

The middle height is below the upper height while its material gap is 18.284080999 µm higher. At the middle point the right knee reached its solver clamp; target residual was 61.272528 µm, unreachable extension was 61.363103 µm, and articulation-envelope violation was zero. This is a solver/skin coupling at the active clamp, not a tolerance-only failure.

The frozen pre-fix capture tested the center, adjacent floating-point values, and ±1 µs. All five were unavailable for the same reason.

## Resolution

The ordinary shared monotone-floor implementation is unchanged. Only the acquired authored-material path handles its exact nonmonotone-floor outcome with a deterministic local upward bracket beginning at the immutable declared row height. A candidate is admitted only when the same full solve satisfies:

- requested material gap;
- target residual no greater than 1 mm;
- unreachable extension no greater than 1 mm; and
- articulation-envelope violation no greater than 0.01 degrees.

The returned height is solved again and all four conditions are checked. No safe bracket, exhausted search, or failed final combined check remains typed unavailable. The method is an engineering resolution of one observed local component. It does not claim a globally monotone solver, the global first or minimum feasible interval, continuous-time success, or a formal branch-stability certificate. Serialized package gates remain authoritative.

The adapter binding now declares `material_floor_and_local_joint_feasibility.v3`; its digest differs from the previous `minimum_material_and_bounded_reach.v2` semantics.

## Verification

- Exact final-head query at center, adjacent floating-point values, and ±1 µs: 5/5 AVAILABLE.
- Across those rows, maximum residual was about 61.274 µm, maximum extension about 61.365 µm, and articulation-envelope violation zero.
- Measured reversal, no-safe-bracket, final-combined-gate, and prior bounded-reach tests: 5 passed.
- Authored-material contact tests after the version binding: 20 passed in 18.18 seconds.
- Authored-material, source-query, and constant-target focused files: 56 passed in 74.78 seconds.
- Ruff and `git diff --check`: passed.

An earlier sparse-checkout run omitted `recipes/heavy-biped/walk.v3.json` and is classified INVALID_TEST_FIXTURE. It is not a code failure and is superseded by the 56-test run after materializing the tracked recipe directory.

## Evidence

`evidence/` contains the independent initial failure review, reviewer-two closure, exact before/after neighbor captures, and the valid focused-test log. `SHA256SUMS` binds the retained files.
