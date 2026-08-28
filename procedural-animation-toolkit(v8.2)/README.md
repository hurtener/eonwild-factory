# Procedural Animation Toolkit — V8.2 approved balance transfer

This is the lean, reproducible V8.2 Candidate-A release for the approved
Tarbosaurus relaxed walk. It starts from the included iteration-b base and
rebuilds the exact approved V8.2 GLB using a bounded world-relative chest
balance response. It is intentionally not a history dump.

## Contents

- `input/` — the single pinned pre-chest-solve base required for regeneration.
- `asset/` — the approved V8.2 GLB, SHA-256
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
- `config/release.json` — allowed chain, clips, gain, and hash contract.
- `scripts/release_generate.py` — deterministic generator.
- `scripts/verify_release.py` — fail-closed snapshot/accessor verifier.
- `evidence/` — official Candidate-A, structural/mechanical, and clean-output
  reproduction reports.
- `media/` — one fixed-camera V8.2 side review and one V8.1/V8.2
  three-quarter comparison.

## Reproduce

Use Blender 5.2+ (its bundled Python supplies NumPy):

```sh
blender --background --python-exit-code 1 --python \
  'procedural-animation-toolkit(v8.2)/scripts/release_generate.py' -- \
  --config 'procedural-animation-toolkit(v8.2)/config/release.json' \
  --output /tmp/tarbosaurus_v8_2_rebuilt.glb

blender --background --python-exit-code 1 --python \
  'procedural-animation-toolkit(v8.2)/scripts/verify_release.py' -- \
  --config 'procedural-animation-toolkit(v8.2)/config/release.json' \
  --candidate /tmp/tarbosaurus_v8_2_rebuilt.glb --output /tmp/v8_2_verify.json
```

Both commands fail closed. The rebuilt artifact must equal the approved SHA.

## Motion contract

For both relaxed RESPIN walk clips, only the chest and permitted neck/head
rotation accessors are regenerated. The solver applies gain `0.3984375` in the
same world-relative rotation-vector basis as the official evaluator, then
reconstructs the neck chain to preserve the head world pose. The root, pelvis,
legs, feet, toes, translations, tails, non-walk animations, GLB JSON, and all
other binary data remain unchanged from the included base.

See `RELEASE_MANIFEST.json` for provenance, evidence hashes, media facts, and
explicit exclusions. The V8.1 iteration-38 source is referenced by SHA only;
it is not duplicated in this package.
