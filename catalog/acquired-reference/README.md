# Acquired reference inputs

Descriptors in this directory bind licensed raw authored source bytes, a
measured capsule, adapter model/version, and retime policy. Raw acquired files
remain outside Git. To compile the Allosaurus reference walk, provision the
licensed 15K Raptor FBX and the locally derived measured capsule at:

- `local/acquired/pbr-animated-dinosaurs/Raptor_Animated_FBX.fbx`
- `local/acquired/pbr-animated-dinosaurs/raptor-walk-authored-material-path.v1.json`

Its required SHA-256 is recorded in
`ferocious-industries.raptor-walk-material.v1.json`. The public factory command
then needs no code injection:

```sh
python -m eonwild_motion.factory compile-set \
  --root . \
  --motion-set catalog/motion-sets/allosaurus-engineering-acquired-walk.v3.json \
  --motions walk \
  --interpolation CUBICSPLINE \
  --output /path/on/local/storage/allosaurus-acquired-walk
```

The generated package carries immutable copies of the descriptor, capsule,
clearance policy, and raw source bytes. This is a non-promoted engineering
candidate; technical validation, native visual review, and production approval
remain separate.
