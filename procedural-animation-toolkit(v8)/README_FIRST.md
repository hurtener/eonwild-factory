# Eonwild Procedural Animation V8 — Full Toolkit

V8 is the Design-Lab power-attack, feeding-expression and turn-attention release built on V7's contact-locked 75-joint Tarbosaurus architecture.

## Review first

```text
validated_result/v8/OPEN_ME_tarbosaurus_v8_3d_browser.html
validated_result/v8/OPEN_ME_tarbosaurus_v8_validation.html
validated_result/v8/showcase/tarbosaurus_v8_master_montage.jpg
```

The first page is the dependency-free interactive WebGL2 player with the complete 40-animation GLB embedded. The second is a fixed-camera CPU-skinned reviewer that works without WebGL.

## Main generated assets

```text
validated_result/v8/tarbosaurus_procedural_v8_animation_pack.glb
validated_result/v8/animation-manifest.v8.json
validated_result/v8/procedural-v8-report.json
validated_result/v8/v8-release-summary.json
validated_result/v8/v8-final-test-run.txt
```

## What V8 adds

### Power attack

```text
target acquisition
→ pelvis back/down coil
→ hindlimb release
→ first advancing catch
→ second drive/catch
→ late gape
→ snap closure at contact
→ clamped lateral tear
→ recoil and grounded recovery
```

The root delivery is persistent; recovery does not teleport the animal to the start. Left- and right-lead variants are generated independently.

### Feeding expression

The exact 10.8-second loop contains three unequal events with alternating pull direction:

```text
search → retract → late gape → bite acquisition → clamp
→ foot/pelvis brace → diagonal pull → chew/swallow → reacquire
```

The source video has camera cuts and perspective changes, so it is used as behavioral/timing evidence rather than represented as calibrated motion capture.

### Turns

The eyes/skull predict the future path, the five-joint neck forms curvature, the chest follows, the pelvis commits later, and the distal tail keeps an opposite shape before settling. The feet and pelvis remain governed by the V7 contact architecture.

## Reproduce

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r environment/requirements-v8.txt

./scripts/run_v8_tests.sh
./scripts/reproduce_v8.sh
```

The full reproduction includes reference analysis, GLB generation, fixture/release/contact/turn/action/browser validation and both review pages.

## Source map

```text
toolkit/v8/README.md
toolkit/v8/learning-skill/PROCEDURAL_ANIMATION_SKILL_V8.md
toolkit/v8/docs/ARCHITECTURE_V8.md
toolkit/v8/docs/POWER_ATTACK_V8.md
toolkit/v8/docs/FEEDING_EXPRESSION_V8.md
toolkit/v8/docs/TURNING_V8.md
toolkit/v8/docs/QUALITY_GATES_V8.md
toolkit/v8/scripts/eonproc_v8/
toolkit/v8/browser_demo/
toolkit/v8/runtime/
toolkit/v8/tests/
```

## Validation interpretation

The release status is `PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED`. Structural and numeric gates passed, but species character remains a human perceptual decision.

The power attack contains a bounded two-frame support-release interval at 60 Hz: maximum lowest-sole contact quantile is below 19 mm, with zero measured selected-sole penetration. This is treated as an intentional force-transfer beat, not the sustained pelvis-flight defect found in V6.
