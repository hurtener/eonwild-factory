# Sprint005 — stronger vertical tail response

Status: new review example, not user accepted. Built from checkpoint `c1a8ed67d90854a850169123118a3376141cb864`; Run008/Sprint004 and older accepted artifacts remain unchanged. No new commit/push.

Selected artifact directory: `build/V9-AIRBORNE-SPRINT-001/review-candidate-005/candidate`.

The only motion parameter change is `tail_response_gain_degrees`: 6 → 10. Existing cyclic velocity-driven response, 0.06 s lag, semantic nine-node distribution, phase, 18° elevated static tail posture, body motion, legs, stride and cadence are retained. No runtime/default/source changes or new solver.

## Measured change

- Tail-tip world vertical excursion: 0.2758 → **0.4234 m**.
- Tail-tip excursion relative to pelvis: 0.3662 → 0.6098 m.
- Sum of dynamic chain rotations: -8.45 to 6.21°. This is distributed articulation, not one hinge.
- Run009's world vertical excursion (1.088 m) is greater than Sprint005's (0.423 m).
- Exact reopened root travel: 8.18918153 m over 0.95833331 s; **30.7628 km/h**, unchanged.
- All non-tail sampled local channels, sample times and contact proxies are identical to the prior candidate. Maximum difference across root/pelvis/leg/toe world matrices: **0**.
- Cyclic response state seam below 1e-8°. Feet retain zero measured penetration/interior-flight intersections. Tail surface is independently checked by `tail-skinned-floor-receipt.json`, using final Blender-deformed vertices, not a tail-joint proxy.

`tail-speed-validation.json` records the reopened comparison, speeds and GLB hashes. `media-verification.json` records media hashes and decoded durations. Root GLB SHA256: `5fe86acc629635e5c9e00c9597794b6fd88b6e648bfc7aaa4525331ac661ca8e`; in-place: `04c05de255b65ec3fc960fed7ff88461bbcfa35b892aa287629c39f99cedd273`.

## Native review media

`sprint-side-2cycles.mp4`, `sprint-front-2cycles.mp4`, `sprint-rear-2cycles.mp4`: 24 fps, 46 frames / 1.91667 s, two original cycles without retiming. Fixed camera bounds cover the full body across the native frames.

Tail-low probe: `tail-minimum-probe/frame-008.20.png` at 0.300 s. Native neighboring frame 8 is also present in `side-native-cycle`. Renderer scene frame `f` maps to `(f - 1)/24` seconds; probe is the lowest tail-tip joint pose, while the skin-floor receipt searches all motion samples independently.

## Game-engine speed and scale contract

Profiles use normalized step travel, not an absolute speed field:

`speed_m_per_s = step_length_body_heights × H_metres / step_period_seconds`.

For this rig, `H = 2.6416714066 m`: source semantic pelvis height above the source's lowest toe-joint plane. It is an engineering normalizer, **not** full-animal height, body length or measured COM. Exported GLB coordinates are interpreted as metres at the current rig scale.

At playback rate 1 and actor scale 1, use 8.54523308 m/s for the derived in-place clip. If the engine uses centimetres, convert this to 854.52331 cm/s. A uniform actor scale multiplier `s` multiplies world root travel/speed by `s`; playback multiplier `r` multiplies speed by `r`. The quoted km/h ranges apply at `s=r=1`. Do not scale only the root channel or add controller travel on top of already-applied root motion. Root-motion and derived in-place playback are alternative authorities.

Current speeds satisfy user ranges: Run 18–24 km/h; Sprint 28–32 km/h. No retiming was needed. `validate_tail_examples.py` asserts these ranges and compares the formula against reopened root displacement/time.

## Reproduction and checks

From repository root:
```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/build_airborne_run.py \
 --source build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb \
 --source-clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
 --binding catalog/rigs/hero-theropod-v8_3.semantic-rig.json \
 --profile build/V9-AIRBORNE-SPRINT-001/review-candidate-005/candidate/engineering-profile.json --output NEW_OUTPUT_DIRECTORY \
 --contact-profile build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/iteration-009-tail-compensation/validate_tail_examples.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_v9_airborne_gait.py -q
```

The existing 21-test suite passes. The task-local validator passes exact channel/trajectory identity, speed formula/ranges, larger tail excursion and Run>Sprint excursion. Render with the existing `render_side_preview.py`, `--frames 23`, `--view side|front|rear`, source floor `-0.01200103802869944`; then repeat the native cycle twice in encoding. Use a new output directory to preserve reviewed files.

## Limits and stop

This is a kinematic artistic compensation driven by body velocity, not a force, momentum or biological model. Existing Run/Sprint stance-skin physical ground velocity remains UNKNOWN; stronger tail motion does not resolve that earlier limitation. Existing stride/reference differences remain. No leg mechanics were re-tuned. These are the requested new examples; stop for user feedback.
