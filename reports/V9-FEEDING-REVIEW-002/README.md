# Feeding002 — overlapped planted feeding review

Status: local review candidate, not user accepted. Feeding001 and the accepted Bite R5 artifacts remain unchanged. No publication is requested by this candidate.

The six-second action retains acquisition, two planted pulls, regrips, raised jaw cycles and settling. Compared with Feeding001, each body channel now has its own timing and a shape-preserving C1 cubic interpolation: monotonic waypoints carry velocity through, while genuine extrema stop only that channel. Pelvis, trunk, neck and tail overlap instead of arriving at every pose simultaneously. Stronger alternating head accommodation occurs while the food is held; a small held fragment continues through the later jaw cycles.

## Review artifacts

All candidate files are under `build/V9-FEEDING-REVIEW-002/`:

- `feeding.glb`: clip `feeding_overlapped_grip_review`, 6 seconds, 361 motion samples.
- `feeding-side.mp4`, `feeding-front.mp4`, `feeding-rear.mp4`: complete native 24 fps, 144-frame, 960×540 views with floor and whole animal visible.
- `feeding-review-sheet.jpg`: representative native poses.
- `profile.json`, `receipt.json`, `prop-coupling-receipt.json`: semantic controls, sampled geometric evidence and preview interaction definition.

GLB SHA256: `93310474d65a00d601a60c0b3f8ba9d6cb4150dae632e206f4a6188cf618d181`.

Profile SHA256: `58cb321a4177ece5c3ead68759aa93bd8a0b12030913c5fbcb6b56ced44f084b`.

The final media hashes and decoded frame/rate/duration checks are recorded in `media-verification.json` beside this report. The host approved native side/front probes before the full three-view render; full playback and user acceptance remain separate gates.

## Focused evidence

`test_feeding.py`: 6 passed. Checks cover C1 continuity, nonzero monotonic-waypoint velocity, overlapping channels, no interpolation overshoot, duration scaling, directional first pull, unchanged baseline hash, joint bounds, unreachable-target rejection, fixed contact transforms and serialized motion evidence.

- First pull, 1.95→2.60 s: pelvis rises 0.06629 m while upper mouth moves 0.02956 m down and 0.03159 m forward, preserving the reference's critical direction.
- Upper-mouth lateral span during the first grip: 0.42378 m; this is authored accommodation, not a measurement from the side reference.
- Maximum ankle position drift: 0.000000133 m. Maximum foot-matrix error: 0.000000209. Ground-band skin drift: 0.000000209 m.
- Maximum sampled joint rate: 172.672 degrees/s, below the unchanged 220-degree/s gate. Minimum lower-jaw height: 0.10885 m.
- No bone attachment translations were changed except the authorized pelvis motion; no scale changes, joint-limit relaxation, or counter-up cervical kink.

## Reproduction

From the repository root, with its existing virtual environment and Blender installation:

```sh
.venv/bin/python build/V9-FEEDING-REVIEW-002/feeding.py
.venv/bin/python -m pytest -q build/V9-FEEDING-REVIEW-002/test_feeding.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python build/V9-FEEDING-REVIEW-002/render_feeding.py -- --candidate build/V9-FEEDING-REVIEW-002/feeding.glb --clip feeding_overlapped_grip_review --output build/V9-FEEDING-REVIEW-002/render --frames 144 --fps 24 --ground-level-canonical-y 0.0008014736783756348 --view side --view front --view rear
python3 build/V9-FEEDING-REVIEW-002/make_media.py
```

`feeding.py` composes the preserved Feeding001 serializer and planted-support geometry in memory; `channels.py` is the shared numerical channel evaluator for this candidate and its renderer. The transitive Feeding001 dependency closure was persisted at checkpoint `ca2cdd2`; see `reports/V9-FEEDING-REVIEW-001/persistence-manifest.json`. Do not substitute unfinished Bite R6 output as an input.

## Limits

Fixed full ankle and foot transforms are this prototype's contact choice, not a universal ban on ankle articulation. Joint-rate and contact evidence are kinematic checks, not proof of force balance, center of mass, friction or biological chewing. The side reference cannot determine lateral motion or loading. The grounded prop, connector and held food fragment are renderer-only authored proxies and are not included in the animal GLB; their oral attachment follows skinned mouth centroids, not solved tooth/tissue collisions. Resistance, release and fragment retention are scripted approximations. This is a finite six-second performance, not a seamless loop. No additional motion sweep is intended before user review.
