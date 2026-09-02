# V9 third three-motion review

Status: USER APPROVED on 2026-09-02; user explicitly requested publishing
Run010, Sprint006 and Feeding003 to main, followed by textured rear-quarter
camera exports and Downloads copies. Motion is frozen; only presentation changes
are requested next. The historical foundation below remains preserved.
Preserve the current
Run008, Sprint004 and Feeding002 foundation pushed to main at `c1a8ed6`.

Additional user direction during this pass: add a small breathing-like mouth
opening to Run/Sprint, using the reference footage, and render the examples
with the original model textures if available. Run010/Sprint006 extend the
completed tail-only examples below; Feeding003 motion stays frozen. Preserve
clay previews alongside the new textured views for articulation comparison.

## Latest textured review videos

| Example | Side | Front | Rear |
|---|---|---|---|
| Run010 | [Play](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-010-breathing/textured/run-side-textured-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-010-breathing/textured/run-front-textured-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-010-breathing/textured/run-rear-textured-2cycles.mp4) |
| Sprint006 | [Play](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/sprint-side-textured-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/sprint-front-textured-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-006/textured/sprint-rear-textured-2cycles.mp4) |
| Feeding003 | [Play](http://127.0.0.1:8896/V9-FEEDING-REVIEW-003/textured/feeding-side.mp4) | [Play](http://127.0.0.1:8896/V9-FEEDING-REVIEW-003/textured/feeding-front.mp4) | [Play](http://127.0.0.1:8896/V9-FEEDING-REVIEW-003/textured/feeding-rear.mp4) |

All use the original embedded color texture and UVs under consistent studio
lighting, not a full PBR material render. Clay views below remain available.
Run010 adds a smooth 1–4° mouth opening and Sprint006 adds 0.5–3°; every non-jaw
channel is exactly unchanged from the tail-only examples. Speeds remain
20.24 / 30.76 km/h. Host final tests: **22 gait + 6 feeding passed**. Two bounded
independent jaw reviews found no P0/P1 issues; material helpers were cross-reviewed.
Host opened all three final textured side videos in the browser.

Latest detailed reports: [Run010](../V9-AIRBORNE-RUN-001/iteration-010-breathing/README.md),
[Sprint006](../V9-AIRBORNE-SPRINT-001/review-candidate-006/README.md),
[Feeding texture presentation](../V9-FEEDING-REVIEW-003/TEXTURED.md).

## User direction

- Eating: close the jaw after gripping; keep the mouth contact point braced while
  the head/neck/body perform the resisted pull. Retract/backward accommodation
  and chewing follow, rather than chewing throughout the pulling action.
- Run and Sprint: retain the much-improved leg movement. Increase vertical tail
  compensation in both, with a larger up/down response in the more buoyant Run.
- Target travel speeds: Run 18–24 km/h, Sprint 28–32 km/h.

## Speed check

Current exported root tracks already match these ranges at the present rig's
metre scale: Run travels 7.02685 m in 1.25 s (20.2373 km/h); Sprint travels
8.18918 m in 0.958333 s (30.7628 km/h). In-place previews remove that translation,
not the animation timing. Preserve speeds/cadence during this tail-only gait pass.

## Bounded delivery

Prepare Run009, Sprint005 and Feeding003 with native-speed side/front/rear
previews. Keep prior files intact. Check the braced oral anchor and closed jaw
separately from planted support; record any target/resistance approximation.
Check tail response without changing root/leg motion. Deliver these examples
for user feedback; do not start other animation categories.

## Completed gait examples

| Example | Side | Front | Rear | Speed |
|---|---|---|---|---|
| Run009 | [Play](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-009-tail-compensation/candidate/run-side-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-009-tail-compensation/candidate/run-front-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-009-tail-compensation/candidate/run-rear-2cycles.mp4) | 20.24 km/h |
| Sprint005 | [Play](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-005/candidate/sprint-side-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-005/candidate/sprint-front-2cycles.mp4) | [Play](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-005/candidate/sprint-rear-2cycles.mp4) | 30.76 km/h |

Tail-tip vertical travel increases from 0.605 to 1.088 m in Run and from 0.276
to 0.423 m in Sprint. Exact exported non-tail channels, legs, contacts, timing,
and speeds are unchanged. The host opened and sampled both native-speed side
videos in the browser. These remain artistic kinematic responses, not a
momentum/physics simulation. The speeds assume metre-scale GLBs, actor scale 1
and playback rate 1; use root motion or matching controller travel, not both.

Full gait measurements and reproduction notes:
[Run009](../V9-AIRBORNE-RUN-001/iteration-009-tail-compensation/README.md),
[Sprint005](../V9-AIRBORNE-SPRINT-001/review-candidate-005/README.md).

## Feeding003

[Side](http://127.0.0.1:8896/V9-FEEDING-REVIEW-003/feeding-side.mp4) ·
[Front](http://127.0.0.1:8896/V9-FEEDING-REVIEW-003/feeding-front.mp4) ·
[Rear](http://127.0.0.1:8896/V9-FEEDING-REVIEW-003/feeding-rear.mp4)

The jaw closes at 1.94 s, the oral contact stays braced from 2.05–3.36 s, and
the body/neck move behind that fixed contact. Yield releases the oral constraint
smoothly; the mouth travels about 12 cm backward before chewing begins after
4.20 s. The feet remain planted throughout. The native side/front probes show
the intended sequence without the earlier inverted upper-neck bend.

This deliberately changes grip coordination, not the walking solver. Food
resistance and tear release are authored preview events, not simulated tissue
or forces. The prop/held fragment are renderer aids and are not in the GLB.
[Full report and reproduction](../V9-FEEDING-REVIEW-003/README.md).

## Focused verification

Host tests: 21 gait tests plus 6 Feeding003 tests pass. Reopened gait validation
confirms exact unchanged leg/root motion and speed ranges. Feeding tests check
the emitted fixed oral contact, closed jaw, backward return before chewing,
planted support, joint bounds and release continuity. Independent bounded
reviews supplement the host's native-frame/browser checks; these are review
candidates, not user acceptance or physics validation. No hosted CI is configured.

Persisted on main: Run008 / Sprint004 / Feeding002 at `c1a8ed6`.
New local examples: Run010 / Sprint006 / Feeding003 (Run009 / Sprint005 are the
preserved tail-only comparison). Do not replace the saved
foundation or start another animation category without user feedback.
