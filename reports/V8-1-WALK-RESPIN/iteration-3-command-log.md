# Iteration 3 presentation-only render log

## Scope

Render a new approval MP4 from the existing validated candidate GLB only. The candidate-owned renderer changes the stage ground material to a lighter neutral value and increases the existing key/fill/rim energies for contact-shadow readability. It does not change the GLB, animation data, profile, camera envelope, resolution, frame count, or duration.

## Input identity

- Candidate GLB: `candidates/v8.1-walk-respin/generated/iteration-15/tarbosaurus_procedural_v8_1_walk_respin.glb`
- Candidate GLB SHA-256 before and after render: `96bf5c37402bd784b23785173fbb9a45cd8cbbed33ea2fd0675bdfd11c48a5a1`
- Clip: `PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE`

## Render command

```text
/opt/homebrew/bin/blender -b --python candidates/v8.1-walk-respin/scripts/render_walk_respin_blender.py -- --input candidates/v8.1-walk-respin/generated/iteration-15/tarbosaurus_procedural_v8_1_walk_respin.glb --manifest candidates/v8.1-walk-respin/generated/iteration-15/animation-manifest.v8.1-walk-respin.json --output showcase/v8.1-walk-respin/iteration-3 --clip PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE --duration-seconds 10 --fps 24 --width 960 --height 540
```

## Tool versions

- Blender 5.2.0 LTS
- FFmpeg 9.0.1
- uv 0.7.13
- Python 3.14.6

## Results

- Output MP4: `showcase/v8.1-walk-respin/iteration-3/walk-relaxed-v8-1-respin-side.mp4`
- MP4 SHA-256: `4a654cad0878dcb710090b44d7647644215b0c3b9a696566c1638ecf347145dc`
- ffprobe: H.264, yuv420p, 960x540, 24/1 fps, 10.000000 seconds, 240 decoded frames.
- Final output directory contains exactly the MP4 and `render-run.json`.
- Visual review: full-body locked side framing retained; the neutral floor and contact shadow make the lifting metatarsal and retained toes materially easier to inspect.

## Accepted V8.1 proof

- Source GLB SHA-256 remains `fbb42c2edad4eadebbcf808d32028d7c73b3fbfd6172610eddd5df84990a65c7`.
- Canonical profile SHA-256 remains `f128bd39cca62a674855ffbcce2e88226cec3b17048bf9a830bd158238240143`.
- `PACKAGE_MANIFEST_V8_1.json` checked all 285 recorded non-cache package files: zero mismatches.
- The render imported the candidate GLB read-only; no accepted V8.1 file was written.
