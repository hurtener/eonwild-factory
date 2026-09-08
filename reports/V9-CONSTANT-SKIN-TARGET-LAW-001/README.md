# Canonical constant skin-target law 001

## Scope and authority

Code head `a6253053b2592ad0dffeb37ca41c2a2f5b3ab783` adds a non-emitting,
pointwise diagnostic law. It calibrates one constant vector per semantic foot
from the provider's sustained canonical source touchdowns, applies the same
two vectors at every requested source time through `SourceMotionQuery` and the
existing row solver, and jointly checks both feet. It changes no recipe,
emitter, default, quality gate, or approved asset.

An `AVAILABLE` value retains the checked row, pose, detached constant vectors,
loaded target residual or unloaded clearance, foot-target residual,
unreachable extension, and articulation-envelope violation. A failed
pointwise criterion returns typed `UNAVAILABLE` with its reason and measured
observations. Derivative, optimizer-branch, branch-stability, and global-C1
authority remain explicitly unavailable because the existing row solver does
not expose them; they are not prerequisites for a checked pointwise value.

The law binds the actual query's owned source/current uniform scale, semantic
roles, solver and locomotion gait, transition, complete decorated plan,
coordinate frame, contact profile, articulation profile, source clip, and
overlay mode to the validated provider request. The binding and internal
calibration hashes are checked before every value. Returned arrays and nested
diagnostics are detached, and direct construction cannot bypass validated
calibration.

Transition consumers calibrate from an owned `SourceMotionQuery` over the
provider's existing sustained plan. The focused regression proves a walk-start
consumer and steady walk receive identical per-side constants rather than
calibrating from the transition's standing first row.

## Established criteria

- constant-target gap: `0.0001 m`
- constant-target residual tolerance: `0.0002 m`
- calibration damping: `0.85`
- correction envelope: `0.06 body height`
- existing row-solver foot-target and unreachable-extension limits: `0.001 m`
- existing row-solver articulation-envelope limit: `0.01 degrees`

The last three solver limits are the existing `factory.quality.solver_checks`
criteria. A provisional scan exposed that the earlier `1e-9` postfix cutoff
would reject ordinary microdegree numerical residue; the final head uses the
established limits and reran both complete cycles from scratch.

## Exact-input native cycles

Both runs used the actual authored performance, gaze/rostral calibration,
articulation profile when present, animal uniform scale, scaled contact
profile, and neutral-jaw calibration when present. The sole diagnostic input
override was `canonical_support_anchors=true`.

| Recipe | Exact recipe SHA-256 | Performance SHA-256 | Native rows | Full recipe duration | Same-foot cycle | Result |
|---|---|---|---:|---:|---:|---|
| `recipes/heavy-biped/walk.v3.json` | `0e9c04f6e38d5d523cd354577ed82650846cf4edae3d1cddfacf76906530c783` | `ade6d37243d4b9597c9d2c15a86a667b5528654aca3998315abe7f2f06a968be` | 305 | `2.46 s` | `2.46 s` | 305 `AVAILABLE`, 0 unavailable |
| `recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v9.json` | `f55da91847dc63489f9655cfc3641bee665bf8ce6122755a61748d98fabf3ccd` | `e133819dddf19bd224ddec7419687208e01abf8f3906fa147837813710dc2dfc` | 297 | `2.46 s` | `2.46 s` | 297 `AVAILABLE`, 0 unavailable |

Each full recipe is exactly one same-foot cycle. The retained row counts differ
because the two exact program profiles use different native sampling grids.

Observed maxima/minima across every retained row:

| Recipe | Maximum loaded residual | Minimum swing gap | Maximum IK residual | Maximum extension | Maximum ROM violation |
|---|---:|---:|---:|---:|---:|
| walk v3 | `6.911417318157741e-06 m` | `0.00012077321833294137 m` | `1.2572341004431552e-07 m` | `0 m` | `5.774103328803903e-06 degrees` |
| adult V9 | `3.054149187286614e-05 m` | `0.00013353827310151798 m` | `1.9841950747802215e-07 m` | `0 m` | `0 degrees` |

The per-row files retain all declared input identities, current source-state
hashes, relevant code hashes, effective performance and plan hashes,
gaze/rostral calibration, articulation receipt, scaled contact hash, provider
and query bindings, constant calibration hash, source-row and checked-row
hashes, pose hashes, and every pointwise measurement.

## Retained evidence

- `manifest.json`: SHA-256 `9f57d178aa0fc3f3115257b798030a0be43aaa4ecc53821004bf9b03d0fae1ab`
- `run_exact_cycles.py`: SHA-256 `a39d36016efb985d46c27bfd2abd3e069085a83da2a59da8e5d60b5ee91346e3`
- `walk.v3-exact-cycle.json`: SHA-256 `f2487108d5f75ec5263a55279ac8a0c0d65f8649786d5325d1e07b18e8a226a8`
- `tarbosaurus-pin-552-1-adult-walk.v9-exact-cycle.json`: SHA-256 `a586e0628189fda15ce9e4400fdb4cd36bb4cfbc72ec9c3a978477a79daeb2a0`

The retained driver was executed from this task's assigned absolute SSD paths
and writes its outputs to the task-local `out/constant-skin-law-exact-cycles`
directory. The tracked copies above preserve the exact executed bytes; reruns
on another checkout must update the driver's three absolute roots explicitly
and will intentionally produce different path fields.

As executed:

```sh
source /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/task-env.sh
. .venv/bin/activate
PYTHONPATH=src python reports/V9-CONSTANT-SKIN-TARGET-LAW-001/run_exact_cycles.py
```

## Verification

- `33 passed in 133.66s`: `tests/test_constant_skin_targets.py`,
  `tests/test_canonical_support_anchors.py`, and
  `tests/test_source_motion_query.py`
- `19 passed in 54.95s`: law regressions plus existing factory-quality limits
- Ruff passed for all changed Python files.
- `git diff --check f847630..a625305` passed.
- An independent parser rehashed the manifest and both row files, asserted
  exact row ordering/counts, exact final code head, identical driver identity,
  and `AVAILABLE` at every retained native key.

This evidence is pointwise source geometry only. It grants no derivative,
global-C1, emitted CUBICSPLINE, sampled convergence, visual, Unity, biological,
or production authority.
