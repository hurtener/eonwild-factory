# Eonwild Procedural Animation Toolkit — V1 through V5

This is the complete reproducible toolkit used to build and validate the Tarbosaurus V5 animation pack.

## Start here

- `validated_result/v5/OPEN_ME_tarbosaurus_v5_3d_browser.html` — self-contained interactive WebGL2 player with the complete 37-clip GLB embedded.
- `validated_result/v5/OPEN_ME_tarbosaurus_v5_validation.html` — self-contained CPU-skinned visual validation with the 60 FPS walk and action/keyframe audits.
- `validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb` — final animation pack.
- `validated_result/v5/v5-release-validation.json` — structural, jaw, transition and player-contract validation.
- `toolkit/v5/README.md` — V5 architecture, limitations and reproduction instructions.

## Version structure

```text
toolkit/v1/  original phase/FK baseline
toolkit/v2/  contact-aware gait, balance and dynamic-tail architecture
toolkit/v3/  signed anatomical knee/ankle constraints and reference posture
toolkit/v4/  vertex sole witnesses, terrain, turns, start/brake and action pack
toolkit/v5/  calibrated jaw, baked-track polish, exact transitions and revised browser player
```

V1–V4 remain available as regression baselines. V5 does not destroy or overwrite any earlier version.

## V5 validated-build strategy

V5 deliberately preserves V4's already-validated:

- vertex-level sole and terrain tracks;
- signed knee and ankle constraint solution;
- root-motion paths;
- turns, starts, braking and action body mechanics;
- 75-joint skin and inverse-bind matrices.

It then performs a deterministic refinement pass over the baked animation pack:

1. Calibrate a living-neutral jaw pose against weighted jaw/skull mesh witnesses.
2. Replace the generic V4 jaw offset in all 21 non-transition clips.
3. Fix bite contact so the jaw closes fully and does not reopen during recoil.
4. Apply quaternion-continuous, loop-safe zero-phase polish to expressive bones only.
5. Preserve root, pelvis contact requirements, all leg/foot/toe tracks and sharp action beats.
6. Rebuild all 16 transitions with endpoint-exact rotation splines and translation Hermite curves.
7. Rebuild the player around snapshot blends for arbitrary selection and exact authored handoffs for action queues.

This is intentionally safer than rerunning a good contact solve merely to fix the mouth and presentation layer.

## Reproduce

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r environment/requirements-v5.txt

./scripts/reproduce_v5.sh
./scripts/run_v5_tests.sh
```

The offline CPU-skinned movie renderer is optional and computationally expensive. The reproducible core build, GLB validation and self-contained browser build do not require Blender.

## Serve the folder-based browser demo

```bash
python3 scripts/serve_v5_browser_demo.py
```

Open `http://127.0.0.1:8765`.

## Inputs

The exact fixture used for this result is under `inputs/`:

- source Tarbosaurus GLB;
- user-edited semantic bone map;
- supplied side-walk reference video.

## Release truthfulness

Automated release status is `PASS`, but animation taste remains a perceptual review gate. V5 fixes the concrete V4 defects without claiming that every species-specific action is permanently finished.
