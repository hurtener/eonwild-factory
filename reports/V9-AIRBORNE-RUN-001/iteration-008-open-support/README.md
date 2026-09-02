# Run008 — open support and coordinated recovery

Status: FROZEN REVIEW CANDIDATE — host probe/playback gate, not user acceptance. Older accepted Run006 and persisted Run007/Sprint003 artifacts remain unchanged. No commit or push of this pass.

Selected directory: `build/V9-AIRBORNE-RUN-001/iteration-008-open-support/trial-05`.

## Changes and old/new comparison

Support ankle minima increase from 75.38/90.22° to 86.29/100.68° (left/right); whole-cycle minima increase from 33.44/47.05° to 67.87/83.06°. The pelvis is less crouched, compression is redistributed into rise, and the total low-to-apex excursion remains 0.105 body heights. Recovery clearance is reduced from 0.26 to 0.16 body heights, with a neutral preferred metatarsal recovery pitch and retained 45° hip-lift target. A C2 approach lift anticipates leading-leg extension without shortening the horizontal foot trajectory.

Step period remains 0.625 s, flight fraction 0.26667, and the native cycle remains 1.25 s. Same-frame split is 3.3819 m / 0.28268 body lengths versus 3.3807 m / 0.28257 previously; root-relative per-foot excursion remains 3.5646 m / 0.29795 body lengths. Root travel is unchanged. The driven chest/head/tail response from Run007 is retained.

## Exact checks

- Focused suite: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_v9_airborne_gait.py -q` — 21 passed.
- Reopened maximum joint rate: 633.02°/s, below unchanged 1200°/s configuration; zero bend-plane sign flips.
- Maximum rotation seam: 0.02336°. No bone translation stretching; in-place derives from the single root-motion solve.
- Zero unreachable extension and zero articulation-envelope violations. Zero measured final-foot-surface penetration or interior-flight ground intersections at the unchanged source floor.
- Planted distal joint-point velocity: 5.884e-5 m/s. This is a skeletal anchor metric, not proof of friction.
- **Physical skin-ground velocity remains UNKNOWN:** no persistent sampled skin points within 0.1/0.5/1 mm of the fixed floor. The 0.623 m/s proximity-band velocity is deformation near the floor, not confirmed grounded skating.
- At highest common skinned-toe clearance (0.55833 s), left/right minimum gaps are 0.1178/0.1488 m.

`review-summary.json` binds hashes, media decoding metadata, parameters and comparisons. `articulation.json`, `solve-receipt.json`, `world-plan.json`, `final-skinned-ground-receipt.json` and `stroke-comparison.json` retain detailed evidence.

Root GLB SHA256: `0ed1093aab2009057a45e44e445afca5a30b15239a1558c7c3c90fec24918460`.
In-place GLB SHA256: `be2235f64693ddeaebc35616514992e6f74d742265c84f5e70a99b28c3ce990e`.
Profile SHA256: `ff97780a406d37428dbabb9d18054c5d5f66332a2afef195b9ccc3b12de4a9cf`.

## Review media

- `run-front-2cycles.mp4`: 60 frames, 24/1 fps, 2.500000 s.
- `run-opposing-2cycles.mp4`: 60 frames, 24/1 fps, 2.500000 s.
- `run-rear-2cycles.mp4`: 60 frames, 24/1 fps, 2.500000 s.
- `run-side-2cycles.mp4`: 60 frames, 24/1 fps, 2.500000 s.

Videos repeat the original cycle twice without retiming. Side/front/rear use fixed all-frame full-body bounds; opposing view is a readable joint-region sequence. Blender scene frame `f` corresponds to `(f - 1) / 24` seconds because the imported action is placed at NLA frame 1. Therefore scene frame 21.2 is 0.84167 s, not 0.88333 s.

## Reproduction

From the repository root:

```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/build_airborne_run.py \
 --source build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb \
 --source-clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
 --binding catalog/rigs/hero-theropod-v8_3.semantic-rig.json \
 --profile build/V9-AIRBORNE-RUN-001/iteration-008-open-support/trial-05/engineering-profile.json \
 --output NEW_OUTPUT_DIRECTORY \
 --contact-profile build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json
/Applications/Blender.app/Contents/MacOS/Blender -b -t 3 \
 --python reports/V9-AIRBORNE-RUN-001/render_side_preview.py -- \
 --candidate NEW_OUTPUT_DIRECTORY/airborne-run-in_place.glb \
 --output NEW_OUTPUT_DIRECTORY/side-native-cycle --ground=-0.01200103802869944 \
 --frames 30 --view side
```

Use `--view front` and `--view rear` for the other full-body views. Build dependencies are the persisted checkpoint closure listed in `reports/V9-THREE-MOTION-REVIEW-001/gait-persistence-paths.txt`, plus this pass's planning/solve source and selected profile. Reproduce into a new directory rather than overwriting reviewed artifacts.

## Limits and stopping point

Run is not an exact reference match: flight still reads modestly at frame 14 and the silhouette differs from the reference's approximately 0.296-body-length single-frame witness. Seven right-knee samples remain within 0.1° of the unchanged 65° interior-angle minimum; this is recorded rather than hidden or “solved” by relaxing limits. No further art tuning is planned before user feedback.

All bounds are provisional body-configurable engineering limits, not biological certification. The source skin/mesh and attachment translations are preserved. No claim of forces, COM reconstruction, collision-resolved contact or physical balance is made. Earlier trials in this iteration remain rejected diagnostic history, not alternate selected candidates.
