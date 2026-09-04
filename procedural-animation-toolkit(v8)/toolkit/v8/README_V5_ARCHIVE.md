# Eonwild Procedural Animation V5

V5 is a quality, jaw-calibration, transition and runtime-player layer built on the V4 production animation architecture.

## Concrete V5 fixes

### 1. Real living-neutral mouth

V4 applied a generic 33-degree closure and left this Tarbosaurus visibly open-mouthed. V5:

- discovers the actual five-bone mandible hierarchy;
- chooses weighted jaw and upper-skull mesh witnesses;
- tests closure candidates from 42 to 52 degrees;
- selects the tightest non-intersecting living-neutral pose;
- stores the result in the manifest and generation report.

For this fixture the calibrated closure is **50.0 degrees**, with a tightest witness gap of approximately **2.04 mm**.

Normal locomotion and idle retain only sub-degree breathing-scale jaw movement. Eating, bite and roar intentionally override neutral closure, then recover fully.

### 2. Animation polish without damaging contacts

`eonproc_v5.polish` works in quaternion tangent space with:

- sign continuity;
- zero-phase Savitzky–Golay filtering;
- cyclic padding for loops;
- exact endpoint restoration.

The validated refinement path protects root, thighs, shins, ankles, feet, all three toe branches per side and the complete jaw chain. That preserves V4's sole contact and anatomical constraints while smoothing secondary spine, neck, head, arm and tail tracks.

### 3. Fixed bite contact

V4 reopened the mouth slightly after contact. V5's bite curve now has:

```text
anticipation
→ intentional delivery gape
→ full closure at contact
→ tiny damped rebound only
→ closed recoil and recovery
```

### 4. Endpoint-exact transitions

All 16 action transitions are rebuilt using:

- `RotationSpline` with source/target neighboring samples;
- cubic Hermite translations with endpoint velocity estimates;
- exact first and last sample restoration;
- explicit source clip, target clip and phase metadata.

### 5. Revised browser player

The dependency-free WebGL2 player now includes:

- true quaternion slerp;
- minimum-jerk snapshot blending for arbitrary direct selection;
- exact no-crossfade handoff after authored transition clips;
- root-position continuity offsets;
- contact-phase scheduling when leaving a looping walk;
- visible active buttons and `aria-pressed` state;
- synchronized play/pause label;
- timeline scrubbing;
- queue status and cancellation;
- correct loop-time display.

## Main commands

Build the validated V5 pack from the preserved V4 GLB:

```bash
PYTHONPATH=scripts python3 scripts/upgrade_v4_pack_to_v5.py \
  --source-glb ../../validated_result/v4/tarbosaurus_procedural_v4_animation_pack.glb \
  --bone-map ../../inputs/tarbosaurus_bone_map.edited.yml \
  --v4-report ../../validated_result/v4/procedural-v4-report.json \
  --output-dir ../../validated_result/v5
```

Run tests:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests -p 'test_*v5.py' -v
```

Validate the baked release:

```bash
PYTHONPATH=scripts python3 tests/validate_v5_release.py \
  --source ../../validated_result/v4/tarbosaurus_procedural_v4_animation_pack.glb \
  --generated ../../validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb \
  --bone-map ../../inputs/tarbosaurus_bone_map.edited.yml \
  --manifest ../../validated_result/v5/animation-manifest.v5.json \
  --player-js ../../validated_result/v5/browser/v5-viewer.js \
  --output ../../validated_result/v5/v5-release-validation.json
```

## Result

- 37 clips total.
- 21 base/action/locomotion clips.
- 16 authored transitions.
- 75 skin joints preserved.
- Exact inverse-bind matrices preserved.
- Neutral jaw minimum closure above 49.5 degrees in locomotion and idle.
- Bite fully closed at contact and recovery.
- Transition endpoint rotation error below `1e-4` degree.
- Transition endpoint translation error below `1e-6` model units.

## Full-solver versus validated-refinement path

The V5 directory retains the complete V4 procedural solver and all V4 utilities. The release GLB uses the contact-preserving refinement path because the visible V5 defects did not justify disturbing the already validated sole/terrain solution. A future full regeneration can integrate the same jaw, polish and transition modules directly into the generator.
