# V8.1 Walk Respin 2 — Command and tool record

Canonical candidate generation and verification used Blender 5.2.0 LTS's
Python 3.13 runtime, with local SciPy 1.16.3 and PyYAML 6.0.3 available to the
existing V8.1 script dependency chain. The accepted package itself was not
altered.

```text
PYTHONPATH=/Users/santiagobenvenuto/.local/lib/python3.13/site-packages \
  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 \
  candidates/v8.1-walk-respin-2/scripts/generate_walk_respin_2.py \
  --source procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus.glb \
  --bone-map procedural-animation-toolkit(v8.1)/inputs/v8/bone-map.edited.yml \
  --canonical-profile procedural-animation-toolkit(v8.1)/validated_result/v8.1/resolved-profile-v8.1.json \
  --overlay candidates/v8.1-walk-respin-2/profile-overlay.json \
  --immutable-toolkit procedural-animation-toolkit(v8.1) \
  --immutable-showcase showcase/v8.1 \
  --output-dir candidates/v8.1-walk-respin-2/generated/iteration-15

.../validate_walk_respin.py --glb .../iteration-15/tarbosaurus_procedural_v8_1_walk_respin.glb ...
.../validate_walk_respin_2.py --glb .../iteration-15/tarbosaurus_procedural_v8_1_walk_respin.glb ...

/opt/homebrew/bin/blender --background --python-exit-code 1 \
  --python candidates/v8.1-walk-respin-2/scripts/render_walk_respin_2_blender.py -- \
  --input .../iteration-15/tarbosaurus_procedural_v8_1_walk_respin.glb \
  --manifest .../iteration-15/animation-manifest.v8.1-walk-respin.json \
  --output showcase/v8.1-walk-respin-2/iteration-1 \
  --clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
  --duration-seconds 10 --fps 24 --width 960 --height 540
```

## Iteration 38 final commands

```text
PYTHONPATH=/Users/santiagobenvenuto/.local/lib/python3.13/site-packages \
  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 \
  candidates/v8.1-walk-respin-2/scripts/generate_walk_respin_2.py \
  --source procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus.glb \
  --bone-map procedural-animation-toolkit(v8.1)/inputs/v8/bone-map.edited.yml \
  --canonical-profile procedural-animation-toolkit(v8.1)/validated_result/v8.1/resolved-profile-v8.1.json \
  --overlay candidates/v8.1-walk-respin-2/profile-overlay.json \
  --immutable-toolkit procedural-animation-toolkit(v8.1) \
  --immutable-showcase showcase/v8.1 \
  --output-dir candidates/v8.1-walk-respin-2/generated/iteration-38

.../validate_walk_respin.py --glb .../iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb ...
.../validate_walk_respin_2.py --glb .../iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb ...

/opt/homebrew/bin/blender --background --python-exit-code 1 \
  --python candidates/v8.1-walk-respin-2/scripts/render_walk_respin_2_blender.py -- \
  --input .../iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb \
  --manifest .../iteration-38/animation-manifest.v8.1-walk-respin.json \
  --output showcase/v8.1-walk-respin-2/iteration-4 \
  --clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
  --duration-seconds 10 --fps 24 --width 960 --height 540
```

Tools verified: Blender 5.2.0 LTS, Blender Python 3.13, SciPy 1.16.3,
PyYAML 6.0.3, ffmpeg 9.0.1. Raw command output is retained under `logs/`.

Tool versions: Blender 5.2.0 LTS; ffmpeg 9.0.1; uv 0.7.13.

The `logs/` directory preserves raw output, including invalid local setup
attempts. Iterations 15 and 16 are quarantined. Iteration 21 is the current
mechanically validated candidate; its validation derives no-translation,
monotonic exported-channel decay, distal skinned toe witnesses, and later
receiving-arm onset from the final GLB.

```text
.../generate_walk_respin_2.py ... --output-dir candidates/v8.1-walk-respin-2/generated/iteration-21
.../validate_walk_respin.py .../iteration-21/tarbosaurus_procedural_v8_1_walk_respin.glb ...
.../validate_walk_respin_2.py .../iteration-21/tarbosaurus_procedural_v8_1_walk_respin.glb ...
/opt/homebrew/bin/blender --background --python-exit-code 1 \
  --python candidates/v8.1-walk-respin-2/scripts/render_walk_respin_2_blender.py -- \
  --input .../iteration-21/tarbosaurus_procedural_v8_1_walk_respin.glb \
  --manifest .../iteration-21/animation-manifest.v8.1-walk-respin.json \
  --output showcase/v8.1-walk-respin-2/iteration-3 \
  --clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
  --duration-seconds 10 --fps 24 --width 960 --height 540
```
