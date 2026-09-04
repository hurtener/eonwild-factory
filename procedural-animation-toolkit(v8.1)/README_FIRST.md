# Eonwild Procedural Animation V8.1 — Full Toolkit

V8.1 is the posture, jaw-hinge and airborne-power rework built from the preserved V8 contact-locked 75-joint Tarbosaurus architecture. V8's grounded bite is retained as a distinct normal attack; the new mirrored power attacks use a planted one-foot preload, true flight, ordered landing/arrest, and feeding handoff.

## Review first

```text
validated_result/v8.1/OPEN_ME_tarbosaurus_v8_1_3d_browser.html
validated_result/v8.1/tarbosaurus_procedural_v8_1_animation_pack.glb
validated_result/v8.1/v8.1-release-validation.json
```

The first page is the dependency-free interactive WebGL2 player with the complete 47-animation V8.1 GLB embedded. It exposes normal and power attacks as separate runtime actions. V8 remains under `validated_result/v8/` for comparison.

## Main generated assets

```text
validated_result/v8.1/tarbosaurus_procedural_v8_1_animation_pack.glb
validated_result/v8.1/animation-manifest.v8.1.json
validated_result/v8.1/procedural-v8.1-report.json
validated_result/v8.1/v8.1-baked-ground-validation.json
validated_result/v8.1/v8.1-release-validation.json
```

## Attack catalog

### Normal attack (preserved V8 grounded behavior)

The normal left/right variants retain the grounded two-step delivery, snap contact, lateral tear and grounded recovery. They do not use root-height flight.

### Power attack (new V8.1 airborne behavior)

```text
target acquisition
→ pelvis back/down coil
→ planted launch-foot compression
→ connected hip/knee/ankle extension and toe-off
→ both-feet-clear airborne bite
→ lead-foot landing
→ second-foot catch and weight arrest
→ feeding-ready handoff
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

./scripts/run_v8_1_tests.sh
./scripts/reproduce_v8_1.sh reproduced_result/v8.1-clean
```

The V8.1 reproduction requires the canonical V8.1 profile, refuses a non-empty output directory, and runs release, all-baked-key ground, jaw-centering, browser-contract, and V8-walk-preservation validation.

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
