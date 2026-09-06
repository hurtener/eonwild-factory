# Eonwild Motion Factory

A reproducible motion-authoring factory for Eonwild, the dinosaur-life game.
**Python builds the motion; Unity will consume the motion package.**

This baseline continues V9 from `feat/spark-muse` at
`8c1f5c2bfea481a56916ee6e0bfa74961ca0d141`. It does not restart the project or
claim the entire biomechanical/runtime architecture is finished.

## The active path

```text
admitted geometry + semantic rig + versioned behavior recipe
    → contact plan → shared limb/body emission
    → reopen final GLBs → measure → immutable candidate package
    → review → Unity parity → explicit future production promotion
```

New code lives in `src/eonwild_motion/`. New inputs live in `catalog/` and
`recipes/`. Generated outputs belong in `out/`, not inside source modules.
No new factory code may import `build/`, `reports/`, or a retired toolkit.

## Install and generate

Use Python 3.12 or newer. The existing lock file and dependency pins remain.

```sh
uv sync --frozen --group test
uv run python -m eonwild_motion.factory compile \
  --recipe recipes/heavy-biped/run.v2.json --output out/run-v2
uv run python -m eonwild_motion.factory verify out/run-v2
```

Compilation creates a candidate, not an approval. `verify` returns nonzero
when technical acceptance remains blocked. Read `validation.json`: skeleton
proxies, final skinned contact, visual approval, and Unity parity are separate.
Do not weaken a gate just to turn a candidate green.

Available initial recipes are Run v1/v2, Sprint v1/v2 and a grounded reverse
walk. v1 recovers the earlier engineering parameters; v2 is an **unapproved**
restrained head/breathing-response alternative. Reverse walking owns a real
72%-duty support plan instead of reversing a solved forward animation.

```sh
uv run python tools/build_showcase.py --output out/showcase --render
```

Rendering needs Blender and ffmpeg. On macOS use `--blender
/Applications/Blender.app/Contents/MacOS/Blender` when Blender is not on PATH.
Actual generated clips, native-speed MP4s, and FBX transport candidates are
produced. FBX export is **not** Unity import validation.

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
reverse-walk builders have not been admitted into the production catalog.

## Current boundary

This baseline proves recipe-driven locomotion generation and final-artifact
accounting. It does not yet prove a real second skinned species, complete
feeding extraction, runtime terrain/target adaptation, or Unity/device budgets.
See [the implementation roadmap](docs/FACTORY_ROADMAP.md) and
[the Unity boundary](docs/UNITY_MOTION_CONTRACT.md).

One convincing, reproducible animal comes before a larger clip count.
