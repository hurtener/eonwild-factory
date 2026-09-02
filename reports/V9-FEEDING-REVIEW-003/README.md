# Feeding003 — closed grip, resisted pull, backward return, chew

Status: USER APPROVED on 2026-09-02; explicitly authorized for main persistence. Feeding002 remains unchanged at checkpoint `c1a8ed6`. Subsequent rear-quarter views change presentation only.

The six-second performance changes contact authority rather than adding a walking phase: close the jaw at 1.94 s, capture the oral contact at 2.05 s, keep it braced through 3.36 s while the pelvis/trunk/neck/tail move, yield into a backward return, release by 4.08 s, and only then permit chewing from 4.20 s. Side-to-side accommodation remains within the closed-grip interval.

## Implementation

`build/V9-FEEDING-REVIEW-003/feeding.py` uses five feeding-specific, bounded rotational correction modes: proximal trunk pitch, middle cervical pitch, distal neck/head pitch, and neck/head yaw. The target is the actual skinned upper rostral oral-surface centroid captured at grip, not a relocated attachment or an immobile-skull constraint. Existing full-foot/ankle support and proximal limb geometry are reused from Feeding001; channel interpolation is reused from Feeding002. No gait schedule is used.

Strict oral contact applies only while the target resists. At yield, a pose-space polynomial carries correction value and velocity into the authored return and then reaches zero correction/velocity. This avoids demanding an unreachable Cartesian chord between two valid poses. Feet stay constrained throughout. Unreachable resisted targets reject instead of changing bone lengths, attachment offsets or joint limits.

The first feasibility pass exposed a small opposing-lateral reach excess; the authored positive yaw signal was reduced from 6° to 5° and its lateral body shift from 0.014 to 0.010 body widths. The existing 2 mm contact tolerance and R5 bounds were not relaxed. A transition-only sweep then confirmed fixed contact through resistance and approximately 12 cm of actual backward oral travel before chewing.

## Artifacts and checks

The candidate directory contains `feeding.glb`, the semantic `profile.json`, `receipt.json`, `prop-coupling-receipt.json`, native `feeding-side.mp4`, `feeding-front.mp4`, `feeding-rear.mp4`, and `feeding-review-sheet.jpg`. The GLB clip is `feeding_braced_closed_grip_review`. Each video is a complete six-second 24 fps, 144-frame, 960×540 performance; native timing is not slowed for inspection.

`receipt.json` binds the exact GLB/profile hashes and records unchanged bone attachments/scales, foot and ankle transform drift, skinned sole drift, minimum jaw height, joint-rate and cervical-curve evidence, closed-jaw grip and resisted oral drift. `media-verification.json` beside this report binds the encoded media to the candidate and renderer hashes.

Focused tests check closed-jaw bracing, the reopened emitted oral anchor, whole-body movement around the contact, backward return before chewing, C1 handoff, duration scaling, existing joint/contact gates, rejection of unreachable oral targets and preservation of Feeding002. Mechanical checks and native-frame review do not constitute user acceptance.

Final focused result: **6 passed**. GLB SHA256: `8f70dcab8e8b56035ed0787ca15674166575213f098ec9c6579e6e8350b6d47b`; profile SHA256: `a4b60ef7b849c166327ee852a2921f939a2a5be5e57ead5de69d3b7e206eca79`.

Measured resisted oral drift is 0.07924 mm with jaw 0°. Maximum joint rate is 163.880 degrees/s (unchanged gate 220); maximum adjacent cervical pitch difference is 4.300° (gate 10); minimum cervical pitch is 0°. Minimum skinned lower-jaw height is 0.15394 m above canonical Y zero, versus the fixed floor at 0.0008015 m. Maximum foot matrix error is 2.122e-7; maximum ankle drift is 1.203e-7 m. Host native side/front probes were approved before the full media render. `state.anchor_error_m` is only an active constraint measurement before yield; its zero value after yield is not a claim that the released mouth remains anchored.

## Reproduction

From the repository root:

```sh
.venv/bin/python build/V9-FEEDING-REVIEW-003/feeding.py
.venv/bin/python -m pytest -q build/V9-FEEDING-REVIEW-003/test_feeding.py
/Applications/Blender.app/Contents/MacOS/Blender -b -t 4 --python build/V9-FEEDING-REVIEW-003/render_feeding.py -- --candidate build/V9-FEEDING-REVIEW-003/feeding.glb --clip feeding_braced_closed_grip_review --output build/V9-FEEDING-REVIEW-003/render --frames 144 --fps 24 --ground-level-canonical-y 0.0008014736783756348 --view side --view front --view rear
python3 build/V9-FEEDING-REVIEW-003/make_media.py
```

The preserved Feeding001/002 dependency closure is already committed. Numerical solving uses the existing NumPy-only bounded least-squares helper, not an added SciPy dependency. Output paths above belong only to this candidate; older files must not be overwritten.

## Limits

Resistance, yield and food retention are authored preview events, not force, friction, COM or tissue simulation. The grounded prop, connector and held fragment exist only in the renderer, not the animal GLB; the oral-surface centroid is not individual tooth collision. Closed-jaw gripping overrides the earlier free-tip/gape performance during the resisted phase by explicit user direction. Side-view evidence does not measure lateral loading. Fixed full ankle/foot transforms remain a prototype choice. This is one finite six-second performance, not a seamless loop or a production runtime implementation. Stop for user review after the bounded candidate is ready.
