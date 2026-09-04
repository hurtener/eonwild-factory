# Reproduce and verify the approved V8.1 walk

This snapshot is an immutable V8.1 relaxed-walk base for future V8.2 work. It
does not replace `validated_result/v8.1` or claim approval for its unrelated
animations.

Run the snapshot integrity check first:

```text
python3 approved_snapshots/v8.1-walk-iteration-38/reproduction/verify_snapshot.py
```

The following is the exact iteration-38 generation/validation sequence from
the factory root. The copied scripts in this snapshot are the immutable source
record; this command intentionally uses the original candidate paths, which
the verifier checks by hash before a rerun. Use a new empty output directory.

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
  --output-dir <empty-output-dir>

PYTHONPATH=/Users/santiagobenvenuto/.local/lib/python3.13/site-packages \
  /Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13 \
  candidates/v8.1-walk-respin/scripts/validate_walk_respin.py \
  --glb <empty-output-dir>/tarbosaurus_procedural_v8_1_walk_respin.glb \
  --bone-map procedural-animation-toolkit(v8.1)/inputs/v8/bone-map.edited.yml \
  --profile <empty-output-dir>/resolved-profile-v8.1-walk-respin.json \
  --overlay candidates/v8.1-walk-respin-2/profile-overlay.json \
  --generation-report <empty-output-dir>/generation-report.json \
  --output <empty-output-dir>/base-validation.json
```

Then invoke the copied authoritative validator with the same arguments as the
generation log, using the iteration-15 `walk-respin-validation.json` as its
front-reach provenance input. The expected final GLB SHA-256 is
`1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`.

The stored review media is H.264, 960x540, 24 fps, 240 frames, and exactly
10 seconds. It is evidence only; do not derive motion channels from the MP4.
