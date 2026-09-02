# Sprint006 — subtle breathing-style jaw

Status: USER APPROVED on 2026-09-02; explicitly authorized for main persistence. This is a jaw-only addition to Sprint005; all earlier candidates remain unchanged. Subsequent rear-quarter views change presentation only.

Selected directory: `build/V9-AIRBORNE-SPRINT-001/review-candidate-006/candidate`.
Exact binding: `profiles/v9/rig.airborne-jaw-breathing.json` (existing gait roles plus the existing neutral-idle semantic lower-jaw mapping).
Profile: `build/V9-AIRBORNE-SPRINT-001/review-candidate-006/candidate/engineering-profile.json`.

## Motion

The source spot-check used V07 native frames 8/24 and V08 frames 24/36 under `reports/V9-AIRBORNE-RUN-SPRINT-REFERENCE-ANALYSIS-001/frames/`. Run shows a small mouth opening while Sprint is near closed. These frames support subtlety, not a measured respiratory frequency or calibrated joint angle.

The chosen artistic opening is **0.5–3°**, smoothly varying once per same-foot cycle (0.958333 s). The minimum stays slightly open; the motion never becomes a snap shut, chew or attack gape. Amplitude and integer cycles-per-cycle are profile controlled. All defaults remain disabled (zero gape). A geometry-derived sagittal axis is transformed into the semantic lower jaw's local frame; no per-species runtime branch or hardcoded bone name is used.

## Exact verification

- `PYTHONPATH=src .venv/bin/python -m pytest tests/test_v9_airborne_gait.py -q`: **22 passed**.
- Reopened `jaw-validation.json`: all non-jaw channels and sample times are exactly identical to the preceding candidate.
- Root/pelvis/leg/tail world matrix maximum difference: **0**.
- Jaw angular range: 0.500001–3.000000°; peak angular speed 8.1937°/s; rotation seam 0°.
- Speed remains 30.7628 km/h. Stride, flight, body pose, chest/head stabilization and stronger tail response are unchanged.
- Final-skinned foot receipt remains separate from physical contact claims. No new assertion of forces, respiratory physiology, friction or biological behavior is made.

Reproduce the focused reopened checks with:
```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/iteration-010-breathing/validate_breathing.py
```

Root GLB SHA256: `d4682e87dbb73c55b2336cf0076c821639bc5573d97bda664a3e426df5fc62d4`.
In-place GLB SHA256: `69c0c27a19f51f3cadf26ceae911ca8b801027f3d947a8753ee8b912ae221e19`.

## Build and presentation

Use the existing `reports/V9-AIRBORNE-RUN-001/build_airborne_run.py` with the selected profile above, the new jaw binding, source `build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb`, source clip `PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION`, and that source folder's `candidate-contact-profile-root_motion.json`. Write to a new output directory to preserve the reviewed files.

The derived in-place clip is `V9_AIRBORNE_RUN_IN_PLACE`. Native presentation uses 23 frames at 24 fps, repeated twice without retiming. Scene frame `f` maps to `(f-1)/24` seconds. Textured side/front/rear output uses the original embedded albedo/UVs via the opt-in texture renderer; original GLB material assets remain intact. This Workbench presentation is not full PBR shading. Renderer receipts and encoded-media hashes bind the actual completed presentation.

The inherited game-engine scale/speed contract is documented in Sprint005's review-candidate-005 report: normalized travel × source semantic pelvis-to-toe height / step time, metre-scale export, actor scale/playback multiplier explicitly separate. Do not add controller travel on top of applied root motion.

## Completed original-texture media

- `build/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/sprint-side-textured-2cycles.mp4`
- `build/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/sprint-front-textured-2cycles.mp4`
- `build/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/sprint-rear-textured-2cycles.mp4`

All three are 1100×620 at 24 fps, 46 frames / 1.916667 seconds. Exact source GLB and media hashes, frame counts and durations are in `build/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/media-verification.json`. Independent renderer review confirmed original texture selection, full-body framing and a subtle downward lower-jaw opening in native frame 12. Both root-motion and in-place channels were independently checked: only jaw rotation changes.

No further body/jaw variants are planned before user feedback.
