# Sprint004 — visible flight and inclined posture

Status: FROZEN REVIEW CANDIDATE — host probe/playback gate, not user acceptance. Older accepted Run006 and persisted Run007/Sprint003 artifacts remain unchanged. No commit or push of this pass.

Selected directory: `build/V9-AIRBORNE-SPRINT-001/review-candidate-004/trial-06`.

## Changes and old/new comparison

Travel increases from 1.40 to 1.55 body heights per step; touchdown reach increases from 0.43 to 0.47. Same-frame split increases 9.5%, from 3.6508 m to 3.9988 m. Normalized split is 0.32935 body lengths versus 0.30520 (the frame-zero body length also changes with posture). Per-foot root-relative excursion increases from approximately 3.977 m to 4.279 m.

The front body pitches down 10° distributed across the semantic spine/chest chain; the tail elevates 18° distributed across its chain, with a smaller driven response retained. Lower pelvis posture and a coordinated elevated approach avoid the previous leading-leg extension corner. These are opt-in sagittal rotations, not bone-offset or skin changes.

Step period remains 11.5/24 s and native cycle 23/24 s. Flight fraction is an engineering variation of 0.22, still below Run008's 0.26667. It is not asserted to reconstruct the reference's exact flight timing. At native scene frame 11 (0.41667 s), both skinned toe surfaces clear the unchanged floor by approximately 0.182/0.297 m.

## Exact checks

- Focused suite: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_v9_airborne_gait.py -q` — 21 passed.
- Reopened maximum joint rate: 793.51°/s, below unchanged 1200°/s configuration; zero bend-plane sign flips.
- Maximum rotation seam: 0.02771°. No bone translation stretching; in-place derives from the single root-motion solve.
- Zero unreachable extension and zero articulation-envelope violations. Zero measured final-foot-surface penetration or interior-flight ground intersections at the unchanged source floor.
- Planted distal joint-point velocity: 9.448e-5 m/s. This is a skeletal anchor metric, not proof of friction.
- **Physical skin-ground velocity remains UNKNOWN:** no persistent sampled skin points within 0.1/0.5/1 mm of the fixed floor. The 0.766 m/s proximity-band velocity is deformation near the floor, not confirmed grounded skating.
- At highest common skinned-toe clearance (0.42500 s), left/right minimum gaps are 0.2056/0.2617 m.

`review-summary.json` binds hashes, media decoding metadata, parameters and comparisons. `articulation.json`, `solve-receipt.json`, `world-plan.json`, `final-skinned-ground-receipt.json` and `stroke-comparison.json` retain detailed evidence.

Root GLB SHA256: `f4497595c1039b38f0bcc569c9bb338991ceae980ec4ef1e3d1abf7d64f2cfa1`.
In-place GLB SHA256: `e053bba3da95d85af148111f3204c5a9717cf41ddce585c36a5396889473a2bb`.
Profile SHA256: `e8e691dade5cac454f5d9bd0a44fc9b8ba19dbba552cd34f5e48193fb4694989`.

## Review media

- `sprint-front-2cycles.mp4`: 46 frames, 24/1 fps, 1.916667 s.
- `sprint-rear-2cycles.mp4`: 46 frames, 24/1 fps, 1.916667 s.
- `sprint-side-2cycles.mp4`: 46 frames, 24/1 fps, 1.916667 s.

Videos repeat the original cycle twice without retiming. Side/front/rear use fixed all-frame full-body bounds; there is no camera motion. Blender scene frame `f` corresponds to `(f - 1) / 24` seconds because the imported action is placed at NLA frame 1. Therefore scene frame 21.2 is 0.84167 s, not 0.88333 s.

## Reproduction

From the repository root:

```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/build_airborne_run.py \
 --source build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb \
 --source-clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
 --binding catalog/rigs/hero-theropod-v8_3.semantic-rig.json \
 --profile build/V9-AIRBORNE-SPRINT-001/review-candidate-004/trial-06/engineering-profile.json \
 --output NEW_OUTPUT_DIRECTORY \
 --contact-profile build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json
/Applications/Blender.app/Contents/MacOS/Blender -b -t 3 \
 --python reports/V9-AIRBORNE-RUN-001/render_side_preview.py -- \
 --candidate NEW_OUTPUT_DIRECTORY/airborne-run-in_place.glb \
 --output NEW_OUTPUT_DIRECTORY/side-native-cycle --ground=-0.01200103802869944 \
 --frames 23 --view side
```

Use `--view front` and `--view rear` for the other full-body views. Build dependencies are the persisted checkpoint closure listed in `reports/V9-THREE-MOTION-REVIEW-001/gait-persistence-paths.txt`, plus this pass's planning/solve source and selected profile. Reproduce into a new directory rather than overwriting reviewed artifacts.

## Limits and stopping point

The reference's approximately 0.406-body-length split remains larger than this candidate's 0.329. Reference pixels have measurement and projection uncertainty; this is an improved feasible prototype, not exact parity. Two right-knee samples remain within 0.1° of the unchanged 65° minimum. Early/late flight frames approach the floor; the middle has visible clearance. No further parameter trials are planned before user feedback.

All bounds are provisional body-configurable engineering limits, not biological certification. The source skin/mesh and attachment translations are preserved. No claim of forces, COM reconstruction, collision-resolved contact or physical balance is made. Earlier trials in this iteration remain rejected diagnostic history, not alternate selected candidates.
