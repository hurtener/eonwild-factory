# Feeding review candidate 001

Status: review-only; not user accepted or promoted. R5, accepted Idle/Walk/Run foundations, unfinished R6 source, and shared gait files remain unchanged. Stop after the three-motion handoff; no automatic continuation.

## Review artifacts

- `build/V9-FEEDING-REVIEW-001/feeding.glb` — animal-only sampled execution, clip `feeding_planted_wholebody_review`, six seconds, 361 samples.
- `build/V9-FEEDING-REVIEW-001/feeding-side.mp4`, `feeding-front.mp4`, `feeding-rear.mp4` — native 24 fps, six-second full-body playback with floor. These include the explicitly authored grounded prop/tissue approximation, which is not baked into the animal GLB.
- `build/V9-FEEDING-REVIEW-001/profile.json` — semantic body coordination, variable phase timing, joint envelopes, gape, small lateral accommodation, and event definitions.
- `build/V9-FEEDING-REVIEW-001/receipt.json` — serialized-artifact checks and 361 semantic/support samples.
- `build/V9-FEEDING-REVIEW-001/prop-coupling-receipt.json` — preview-only grip windows, lower-oral surface attachment, grounded prop edge response; not a contact/force solver.

The rejected/intermediate `probe`, `probe-coupled`, and partial `render` folders are retained. Use final `render-coupled` frames and the top-level MP4s for review.

## Reference and composition

The implementer read the complete 145-frame ledger and final synthesis in `reports/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/`, and inspected native sheets 54–59, 72–77, and 108–113. The source includes two early setup steps (F004–F016); these are intentionally omitted from this planted-support composition, not reinterpreted as fixed contacts.

The candidate retains purposeful acquisition, first grip/pull, high-hip/anterior-down counter-motion, delayed prop response, release/reposition, a shorter near-closed regrip/pull, raised no-prop gape, and return to hover. Timings follow the reference's broad sequence but are engineering parameters, not a frame-exact reconstruction. First robust reference coupling is F048; first release is F078; established second grip is F089; second clear release is F105. The simulated events are authored preview assumptions, not inferred forces.

The pelvis moves over planted support. Hip/knee rotations are solved against unchanged bone offsets, with both foot and ankle world transforms anchored to neutral. The fixed ankle is a deliberately conservative prototype constraint that prevents the R5 distal-inward compensation; it is not a rule that a future planted support solver must forbid ankle articulation. Stable limb geometry is shared; no gait plan, stride oscillator, or walking phase is reused. Source-idle body/foot motion is not mixed into the active feeding solve.

Pelvis/spine/chest/neck pitches form a distributed forward curve inside the unchanged R5 per-joint envelopes. The head follows nose-down without counter-up kinking. Tail counter-curvature and small lateral/head accommodation respond to particular phases rather than a constant decorative oscillator. Side-view footage cannot measure the chosen yaw or lateral magnitude.

## Verification

The exact GLB SHA-256 is `51ef2bc8f7d8990f54948a410c89eb777f57e71b97ba48eb2236524949be3682`.

- Reopened 361 samples: bone attachment translations unchanged except the authored pelvis motion; scales unchanged.
- Maximum foot world-matrix error `2.04e-7`; maximum ankle origin drift `1.15e-7 m`; ground-band skinned vertex drift `1.91e-7 m` relative to the neutral anchored pose.
- All original R5 body-pitch envelopes pass; maximum adjacent cervical pitch difference `4.375 degrees`; no reverse cervical bend; world nose-down pitch range `4.80–42.02 degrees`.
- Maximum whole-rig angular rate `203.14 degrees/s` (jaw), below the explicit `220 degrees/s` review limit. Support-joint rate peaks at `77.162 degrees/s` (limit 80); consecutive bend-plane change peaks at `0.05053 degrees` (limit 0.1).
- First-pull pelvis rises approximately `53 mm` while the upper mouth descends approximately `22 mm` and moves approximately `33 mm` forward. Post-contact pelvis, neck/head, tail, and jaw do not hold a static pose.
- Seven focused tests pass in 3.61 s: serialized gates, forward/down counter-motion, support-joint/bend-plane continuity, all phase-boundary continuity, unreachable support rejection, time scaling, and a renamed 2x-scale rig. These are engineering tests, not biological or physics validation.

An independent direction review caught an early candidate retracting the mouth during the first pull. The final profile increases the pelvis forward target from `0.040` to `0.075` body lengths, retaining the high-hip/down-head composition. A trial beyond the original hip envelope was rejected before emission. The final timing removes the intermediate 2.18 s pose stop, places the same first-pull peak at 2.55 s, and places the following settle key at 2.85 s. This small timing change passes the original limits and the focused continuity check without loosening them.

Host side-probe feedback identified that the initial independent ellipsoid read as nose-pushing. The local renderer correction attaches a visible tissue proxy to an actual skinned lower-oral surface witness through both grip windows, disconnects during release/reposition, and gives the floor-supported prop a smaller delayed edge response. The animal GLB is unchanged by that presentation correction. The connector remains a schematic authored strand, not solved tooth/tissue collision.

The preserved R5 GLB still hashes to `d6995eaace81030ee359c93b97b7275a912d9add3e5051dbd1334730f6274ac2`.

## Reproduction

From `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`:

```sh
.venv/bin/python build/V9-FEEDING-REVIEW-001/feeding.py
.venv/bin/python -m pytest -q build/V9-FEEDING-REVIEW-001/test_feeding.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python build/V9-FEEDING-REVIEW-001/render_feeding.py -- --candidate build/V9-FEEDING-REVIEW-001/feeding.glb --clip feeding_planted_wholebody_review --output build/V9-FEEDING-REVIEW-001/render-coupled --frames 144 --fps 24 --ground-level-canonical-y 0.0008014736783756348 --view side --view front --view rear
ffmpeg -y -framerate 24 -i build/V9-FEEDING-REVIEW-001/render-coupled/side-candidate-frames/frame-%04d.png -c:v libx264 -threads 2 -crf 18 -pix_fmt yuv420p -movflags +faststart build/V9-FEEDING-REVIEW-001/feeding-side.mp4
```

Repeat the last command with `front` and `rear`. Blender uses four CPU threads and a 960x540 full-sequence-union camera. Source action time is `(scene_frame - 1) / 24`; the 144-frame preview presents a six-second interval, ending at source time 5.9583 s. The exact terminal hover is included in the 6.0 s GLB sample. The animal GLB is not a loop: start-ready and end-hover are distinct.

Alternatively, after rendering, `python3 build/V9-FEEDING-REVIEW-001/make_media.py` encodes all three views, creates the review sheet, and writes `media-verification.json` with exact hashes, 24 fps, 144-frame counts, and durations. This helper needs Pillow and ffmpeg/ffprobe.

## Limits and next gate

No force, COM, friction, muscle, biological chewing/swallowing, collision-complete food engagement, or runtime physics is established. The food connector and prop are preview geometry. Geometry overlap/attachment is not proof of a physically secured bite. Front/rear temporal playback and the user's whole-body/interaction review remain the acceptance gate. No baseline promotion is authorized by numerical tests or rendering success.
