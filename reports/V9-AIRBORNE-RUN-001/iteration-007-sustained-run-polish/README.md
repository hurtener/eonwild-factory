# Run 007 sustained polish — review candidate

Status: bounded Stage A host motion gate passed; Stage B is ready for host/user playback, **not user accepted**. The original `iteration-006-anatomical-knee/feasible-recovery` remains the USER-ACCEPTED NEW BASELINE. Its GLBs, profile and media have not been replaced. No Sprint or Bite artifacts are owned here.

Final candidate: `build/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-b-driven-response/`. Exact parameters are in its `engineering-profile.json`; both root-motion authority and derived in-place GLBs are included. Main Run profile is not promoted.

## Motion changes and reference boundaries

Reference: `reports/V9-RUN-PERFORMANCE-REFERENCE-002/README.md`, covering all 145 source frames and all 30 baseline frames. Phase alignment uses touchdown, trough, toe-off, flight and catch, not matching elapsed timestamps: native candidate f1 touchdown aligns approximately with source f13/28/46; f5 trough with f17–18; f12 toe-off with uncertain source f24 boundary; f13–15 flight with f25–27; f16 catch with f28. Source dorsal contours are screen-space proxies, not measured COM or force evidence.

Stage A preserves the .625 s step, 4/15 flight fraction, 1.33 H travel, .32 H reach, .08 H crouch, .26 H peak foot clearance and .105 H low-to-apex body excursion. A continuous C2 carrier reaches 85% of its rise at toe-off, with +.8035 m/s vertical speed instead of a separate zero-speed flight bump. The 85% is an engineering choice within the .80–.90 bracket, not source physics. The analytic carrier is sampled at 120 Hz into LINEAR glTF tracks.

Rounded clearance uses .24/.32 lift/lower windows and .42 peak, removing the old broad plateau. The hip recovery preference is 45° rather than 60°, with existing anatomical plane, twist and hard limits preserved. `stage-a-c2-crown-45` is the frozen host-gated Stage A. Earlier Stage A trials are historical, not promoted.

Stage B adds only an opt-in sagittal response: chest gain 2°, head stabilization .85, total distributed tail gain 12°, base response time .06 s. The drive is the actual solved carrier vertical velocity normalized by its own rise/time scale, not an elapsed-time sine. Exact first-order lag filters start at their periodic fixed points. Neck response is delayed and distributed over semantic neck nodes; all nine bound tail nodes receive graded, lagged curvature. Tail response is down during launch/early flight and rises on approach/support. This is bounded kinematic follow-through, not momentum conservation. No yaw/roll, mesh edits, bone stretching or attachment relocation were introduced. Existing default behavior remains unchanged for profiles that do not opt in.

## Focused evidence

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_v9_airborne_gait.py -q`: **18 passed**, including unchanged original 13 tests, C2 joins, contact timing/anchors, rounded clearance, renamed/scaled emitted rig, periodic state, and zero-drive response. No tolerances relaxed.
- `stage-a-leg-equivalence.json`: all translation tracks and sample times identical; exact reopened semantic leg/toe world positions unchanged (0 m maximum difference). Tiny quaternion comparison values below 3e-6° are dot/acos rounding, not changed leg tracks.
- `articulation.json`: zero bend flips; zero solve envelope violation/reach extension. Knee minimum left 75.11°, right 66.19°; neither dwells at the 65° bound. Maximum knee increment 5.8724° at .325–.3333 s (704.68°/s), an existing stance event, not the former swing inversion. Right knee loop difference .02360° remains; body response state seam is 1.94e-16°.
- Stage A `free-swing-feasibility.json`: selected feasible interval always connected through the sampled recovery; neighboring active intervals overlap by at least 23°. Quarter-degree scan, .1° envelope tolerance; unused alternative intervals exist. Stage B leg positions are identical, so it does not alter that reach result.
- `stroke.json`: same-frame split 3.38070 m / .28257 body lengths, signed about hip −1.72981/+1.65089 m. Root-relative per-foot excursion 3.56464 m / .29795 body lengths. These are separate metrics; reference .296 BL is a single-frame split with about 18 px uncertainty on 561.5 px body length, not a required exact fit.
- `final-skinned-ground-receipt.json`: no foot penetration, no stance proximity misses, 24 clear interior-flight samples. Actual fixed-floor patch velocity remains **UNKNOWN**: no persistent points within .1/.5/1 mm of the source floor. Reported proximity velocities .4305/.7895 m/s occur 9.81–11.53 / 18.63–20.08 mm above the floor; they are deformation witnesses, not proven ground skate or zero-skate proof.

## Review media

Within the final candidate directory:

- `run-polish-side-2cycles.mp4`: full body, fixed side, 1100×620, 60 frames at 24 fps, 2.5 s. One native 30-frame/1.25 s cycle repeated once; no retiming.
- `run-polish-front.mp4` and `run-polish-rear.mp4`: fixed full-body views, native 30 frames / 1.25 s.
- `run-polish-opposing-joints.mp4`: opposing-side hip/knee/ankle diagnostic crop, native 30 frames / 1.25 s; intentionally not a full-body view.

All-frame union bounds plus margin fit the cameras. Each PNG directory contains exact render receipts: imported action frames 0–30 are presented on scene frames 1–31, source time = (scene frame − 1)/24. Scene f13 therefore means .5 s. Side/front/rear f13 were inspected for framing, flight and deformation; final native-speed host/user playback remains the motion gate.

## Reproduce

From repository root (write to a new output directory to preserve this candidate):

```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/build_airborne_run.py \
  --source build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb \
  --source-clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
  --binding catalog/rigs/hero-theropod-v8_3.semantic-rig.json \
  --profile build/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-b-driven-response/engineering-profile.json \
  --contact-profile build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json \
  --output build/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/reproduction
```

Rendering uses `render_side_preview.py --frames 30 --view side|front|rear`, source ground −.01200103802869944 m. Opposing uses `--joint-region --binding ... --camera-side -1`. No broad audit, commit or push performed. Stop after candidate handoff for user feedback.
