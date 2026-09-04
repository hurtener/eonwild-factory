# Eonwild Procedural Animation Toolkit V8

V8 is the Design-Lab action-expression pass built on V7's contact-locked rich-rig architecture. It preserves the original Tarbosaurus skin and all 75 joints, keeps the final pelvis transform inside the leg/sole solve, and upgrades three perceptual systems:

1. a reference-staged, hindlimb-driven two-step power attack;
2. grounded, irregular bite–clamp–pull–chew feeding expression;
3. much stronger head/neck attention lead during turns.

The supplied `attack-eat` video is used as timing and behavioral evidence, not presented as calibrated motion capture. The package keeps observed evidence and authored inference separate in `reference_analysis/v8/attack-eat-reference-analysis-v8.json`.

## Core invariant

```text
root path + terrain
→ final pelvis transform
→ signed anatomical leg IK
→ weighted sole-vertex correction
→ upper body, neck, head, jaw and tail
→ export those exact solved transforms
```

No post-solve balance translation may move the body away from its solved contacts.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

./scripts/run_v8_tests.sh
./scripts/reproduce_v8.sh \
  /absolute/path/tarbosaurus.glb \
  /absolute/path/bone-map.yml \
  /absolute/path/attack-eat-reference.mp4 \
  /absolute/path/v8-output
```

The reproduction pipeline generates the 40-clip GLB, manifest, resolved profile, procedural report, reference analysis, release/contact/turn/action validators, browser player and fixed-camera review page.

## Main entrypoints

```text
learning-skill/PROCEDURAL_ANIMATION_SKILL_V8.md
docs/ARCHITECTURE_V8.md
docs/POWER_ATTACK_V8.md
docs/FEEDING_EXPRESSION_V8.md
docs/TURNING_V8.md
docs/QUALITY_GATES_V8.md
scripts/run_pipeline_v8.py
scripts/analyze_attack_eat_reference_v8.py
scripts/render_v8_validation.py
runtime/animation-controller-v8.ts
browser_demo/index-v8.html
```

## Clip catalog

V8 keeps the validated 40-clip contract:

- 16 locomotion clips: root-motion + in-place variants for relaxed walk, uneven terrain, upslope, left/right turn, start, brake and alert walk.
- 6 behavior clips: living idle, alert idle, detailed feeding, left/right power attack and roar.
- 18 endpoint-exact transitions.

## V8 review targets

- Attack: target lock → pelvis coil → first catch → second drive → late gape → snap closure → clamped side pull → recoil → grounded recovery.
- Feeding: low ready posture → search → retract → late gape → bite acquisition → clamp → braced side pull → chew/swallow → reacquire, with three unequal events per exact loop.
- Turn: eyes/skull predict the path, neck curves into it, chest follows, pelvis commits later and the distal tail counters before settling.

## Release status

Automated release status is deliberately `PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED`: numeric and structural gates establish contact, anatomy, endpoints and runtime integrity; final species character still receives human side/three-quarter/overhead review.
