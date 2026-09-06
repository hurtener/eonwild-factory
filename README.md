# Eonwild Motion Factory

A reproducible motion-authoring factory for Eonwild, the dinosaur-life game.
**Python builds the motion; Unity will consume the motion package.**

**Current continuation: DRAFT / NOT PRODUCTION-APPROVED.** The quality-01 walk
is rejected. The preserved V9 narrow-gauge take, not that candidate, is the
walking comparison authority. Read [current verification and remaining motion
acceptance](docs/MOTION_QUALITY_STATUS.md) before replacing approved assets.
The last inspected full test run has unresolved integration errors; the final
continuation changes still need execution and actual motion review.

This work continues V9 from `feat/spark-muse` at
`8c1f5c2bfea481a56916ee6e0bfa74961ca0d141` through the merged factory baseline.
It does not restart the project or claim the entire biomechanical/runtime
architecture is finished.

## The active path

```text
admitted geometry + semantic rig + versioned behavior recipe
    → behavior-owned plan → shared limb/body/contact solving
    → reopen final GLBs → measure → immutable candidate package
    → native-time review → Unity parity → explicit production promotion
```

New code lives in `src/eonwild_motion/`. New inputs live in `catalog/` and
`recipes/`. Generated outputs belong in `out/`, not inside source modules.
No new factory code may import `build/`, `reports/`, or a retired toolkit.
Read-only quality comparisons may inspect an explicitly selected, hash-bound
historical asset; its animation is never a generation input.

## Install and generate

Use Python 3.12 or newer. The existing lock file and dependency pins remain.

```sh
uv sync --frozen --group test
uv run python -m eonwild_motion.factory compile \
  --recipe recipes/heavy-biped/run.v3.json --output out/run-v3
uv run python -m eonwild_motion.factory verify out/run-v3
```

Compilation creates a candidate, not an approval. `verify` returns nonzero
when technical acceptance remains blocked. Read `validation.json`: skeleton
proxies, final skinned contact, visual approval, and Unity parity are separate.
Do not weaken a gate just to turn a candidate green.

## Candidate behavior catalog

The compiler now dispatches grounded gait, airborne gait, gait-transition and
persistent-support programs. The current catalog contains:

| Program group | Candidate recipes |
|---|---|
| Locomotion | `walk.v2`, `fast-walk.v1`, `reverse-walk.v3`, `run.v3`, `sprint.v3` |
| Supported behavior | `idle.v1`, `alert.v1`, `call.v1`, `bite-miss.v1`, `feeding.v1` |
| Starts/stops | `walk-start.v1`, `walk-stop.v1`, `reverse-walk-start.v1`, `reverse-walk-stop.v1`, `run-start.v1`, `run-stop.v1`, `sprint-start.v1`, `sprint-stop.v1` |

Catalog membership is not motion acceptance. Earlier run/sprint/reverse recipes
remain historical candidates and must not silently replace newer recipe inputs.
The supported-action implementation does not import the historical feeding
builder. Its grip, support, timing and recovery still require final skinned
and visual acceptance.

## Render and compare

```sh
uv run python tools/build_showcase.py --output out/showcase --render \
  --views side front rear three-quarter --mode root_motion --fps 60
```

Rendering needs Blender and ffmpeg. On macOS pass
`--blender /Applications/Blender.app/Contents/MacOS/Blender` when Blender is not
on PATH. Each requested camera produces its own native-time MP4 and receipt.
One FBX transport is exported per candidate. FBX export is **not** Unity import
validation.

Use `tools/prepare_motion_reference.py` for an explicit read-only reference,
then pass its prepared package to `--reference-package` with exactly one
recipe. The showcase renders the reference first and reuses each locked camera
for the candidate without retiming the reference or modifying either motion.
It verifies the candidate again after rendering. See
[MOTION_QUALITY_STATUS.md](docs/MOTION_QUALITY_STATUS.md) for the exact preserved
walking artifact and its hash.

The showcase deliberately retains diagnostic renders for blocked candidates,
but returns **exit 2** for mechanical rejection or **exit 1** for generation,
integrity, missing-view or render failures. Even exit 0 does not grant visual
approval, biological correctness, or Unity parity.

## Verification

```sh
uv run python -m pytest tests -q --tb=short
```

CI uses read-only repository access, runs the full suite including the legacy
integration fixture, strictly verifies all 18 current recipes, and has separate
native-time multi-view jobs. There are no integration exclusions or temporary
workflows committing results back to the branch. Diagnostic logs and artifacts
remain separate from approval. Failure or missing execution is not a pass.

## What is preserved, and what is retired

Run010, Sprint006, Feeding003, and the accepted walk remain historical quality
references. A new recipe never inherits their visual approval automatically.
See `catalog/baselines/approved-takes.json` and the original review reports.

V8 and V8.1 toolkits are retired from the active tree, recoverable from the
source commit above. The byte-identical V8.2 capsule is under
`legacy/capsules/v8.2/`, only for compatibility and provenance. The old
`eonwild-motion build/validate/promote` CLI remains the compatibility path;
it is not the new candidate compiler. V5/V5.5 stay as breadth-recovery sources.

Historical `build/` and `reports/` contain useful but unstandardized experiments.
They are **not** the public factory API. In particular, Feeding004 and the old
reverse-walk builders are not production generation dependencies.

## Current boundary

The factory has reusable program implementations and final-artifact accounting;
it does not yet establish accepted natural motion for the entire catalog, a
real second skinned species, runtime terrain/target adaptation, or Unity/device
budgets. See [the implementation roadmap](docs/FACTORY_ROADMAP.md),
[the Unity boundary](docs/UNITY_MOTION_CONTRACT.md), and the current status above.

One convincing, reproducible animal comes before a larger clip count.
