# Verification commands

Run all commands from the repository root with bytecode disabled.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Build and validate the working candidate outside source:

```sh
work_root="$(mktemp -d /tmp/eonwild-v83-verify.XXXXXX)"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m eonwild_motion.cli build --profile working --work-root "$work_root"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m eonwild_motion.cli validate --profile working --artifact assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb --work-root "$work_root"
```

Verify exact stable and working artifacts:

```sh
shasum -a 256 procedural-animation-toolkit\(v8.2\)/asset/tarbosaurus_v8_2_approved.glb assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb
```

Regenerate synchronized comparison frames with Blender 5.2.0 LTS:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python-exit-code 1 --python reports/PROCEDURAL-ENGINE-V8-3/tools/render_comparison_blender.py -- --baseline procedural-animation-toolkit\(v8.2\)/asset/tarbosaurus_v8_2_approved.glb --candidate assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb --output /tmp/eonwild-v83-render --frames 240 --fps 24
```

The committed evidence bundle records the complete five-scale sweep, layer
delta manifest, independent 240 Hz final-skinned vertex witnesses, media hashes,
and channel locks. Visual approval is deliberately left to an independent
reviewer.

The ordinary `validate` command invokes the normative evaluator. Its automated
negative suite covers false status, wrong artifact/scale, null/missing/nonfinite
metrics, wrong threshold/sweep binding, a contradictory or false selected
winner, and corrupted final-skinned witnesses.

Evaluator dispatch is resolved from the profile capability
`normative-evidence@1#eonwild.motion.v8_3_evaluation.v1`. The negative suite
also deletes every required normative top-level field independently and tampers
with the profile declaration; no malformed normative report may fall back to
legacy selectors.
