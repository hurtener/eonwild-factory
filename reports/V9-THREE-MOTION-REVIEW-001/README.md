# V9 — Run, Sprint, and feeding review

Status: **PAUSED FOR USER FEEDBACK.** All three review candidates are prepared. Workers and generation jobs are stopped; no further animation work or automatic refinement is authorized until the user returns and resumes. The larger V9 goal is not complete.

## Baselines remain unchanged

- Run: `build/V9-AIRBORNE-RUN-001/iteration-006-anatomical-knee/feasible-recovery/` is the user-accepted foundation.
- Bite R5: the improved nose-down head/neck remains a useful foundation, not acceptance of its ankle drift, back shape, or static post-contact behavior.
- Idle, Relaxed Walk, and existing Walk Start/Stop work are outside this pass.

## Review intent

| Motion | What to judge |
|---|---|
| Run | Buoyant compression-to-launch rhythm; smooth leg recovery rather than Sprint-like aggression; coordinated chest, neck, and tail response. |
| Sprint | Lower posture, faster strokes, stronger fore/aft split; brief flight without making flight fraction larger than Run by default; no knee/hip collapse. |
| Feeding | Planted feet with moving proximal legs and body; distributed forward lean and curvature; nose-down acquisition followed by purposeful pulls and jaw regrips, not a static display pose. |

A candidate is for user review, not automatic baseline promotion or scientific/physics validation.

## Run candidate — ready for user review

- [Side, two cycles](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-b-driven-response/run-polish-side-2cycles.mp4)
- [Front](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-b-driven-response/run-polish-front.mp4)
- [Rear](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-b-driven-response/run-polish-rear.mp4)
- [Opposing-side joints](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-b-driven-response/run-polish-opposing-joints.mp4)
- [Implementation and limits](../V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/README.md)

Run007 carries its upward movement through takeoff, rounds leg recovery, and adds a modest driven chest/neck/tail response. The host played the final native-speed side clip and inspected consecutive poses through launch and flight, plus native frames 10 and 18 for tail curvature. The leg solution is unchanged from the separately checked stage A. This is a polish candidate, not a replacement for accepted Run006. Actual fixed-floor contact velocity remains unknown, and the body response is kinematic rather than simulated force balance.

## Sprint candidate — ready for user review

- [Side, two cycles](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-003/trial-04-conservative-approach/sprint-side-2cycles.mp4)
- [Front, two cycles](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-003/trial-04-conservative-approach/sprint-front-2cycles.mp4)
- [Rear, two cycles](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-003/trial-04-conservative-approach/sprint-rear-2cycles.mp4)
- [Implementation and limitations](../V9-AIRBORNE-SPRINT-001/review-candidate-003/README.md)

The host loaded the side video in the browser and observed consecutive playback poses through recovery, extension, flight, and the next support. Front/rear native frames 8 and 12 were inspected for leg deformation. No return of the old inverted knee triangle is visible in those checks. This is a conservative Sprint prototype: its cadence is faster and posture lower, but the stride remains materially less expansive than the reference, and its torso/tail are not yet as expressive as the reference. Those are review limitations, not solved parity.

## Feeding candidate — ready for user review

- [Side](http://127.0.0.1:8896/V9-FEEDING-REVIEW-001/feeding-side.mp4)
- [Front](http://127.0.0.1:8896/V9-FEEDING-REVIEW-001/feeding-front.mp4)
- [Rear](http://127.0.0.1:8896/V9-FEEDING-REVIEW-001/feeding-rear.mp4)
- [Implementation and limitations](../V9-FEEDING-REVIEW-001/README.md)

Six seconds at native 24 fps. The new feeding-specific composition keeps support planted while the pelvis, proximal legs, trunk, neck, jaw, and tail participate. It includes acquisition, a first forward/down pull with rising hips, release/reposition, a shorter regrip, raised gape, and recovery. The 145-frame reference analysis is preserved, including its real setup steps; those steps are intentionally outside this planted-only candidate.

The host inspected final side/front/rear poses and browser playback in all three views, including consecutive first-pull side frames and front/rear support progression. The old inward ankle compensation is absent in the checked views. The food and oral strand remain a schematic authored preview, not tooth/tissue collision or physics; the animal GLB does not contain the prop simulation. Fixed ankle transforms are a conservative prototype choice, not a permanent restriction on all planted behaviors.

## Completed checkpoints

- Run007 stage A: continuous launch and rounded clearance with 45-degree recovery target pass the focused floor/reach/articulation gates. Host checked native browser playback and opposing-side frames 8, 12, 15, and 21; the old inversion is absent in those views. This authorizes the driven chest/neck/tail pass, not baseline replacement. Stage A remains available separately under `build/V9-AIRBORNE-RUN-001/iteration-007-sustained-run-polish/stage-a-c2-crown-45/`.
- Sprint003 conservative trial: numerical and skin gates pass; maximum same-frame split is approximately 0.305 body lengths, versus accepted Run006's 0.283 and the uncertain reference Sprint witness near 0.406. Faster cadence and lower posture are retained. Native multiview rendering is complete. The larger-stride rejected trials are not review candidates.
- Feeding: full 145-frame analysis completed and used. Host corrections distinguish hip rise from simultaneous head/front-body descent in frames 48–59. Independent review caught a reversed first-pull direction, corrected locally without relaxing limits; final timing removes a short stop/start. Final GLB is `51ef2bc8f7d8990f54948a410c89eb777f57e71b97ba48eb2236524949be3682`.
- Host test runs: airborne suite **18 passed**; final feeding suite **7 passed**. Focused independent source/sequence checks found no remaining concrete P0/P1 blockers in these review candidates. These are not user artistic acceptance or production-runtime certification.

## Persistent design notes

- [Behavior-specific solver composition](../../v9_extension/docs/V9_BEHAVIOR_SOLVER_COMPOSITION.md)
- [Full Run reference analysis](../V9-RUN-PERFORMANCE-REFERENCE-002/README.md)
- [Run/Sprint timing reference](../V9-AIRBORNE-RUN-SPRINT-REFERENCE-ANALYSIS-001/README.md)
- [Feeding frame-by-frame analysis](../V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/README.md)

## Resume rule

After delivery, wait for the user to review each movement and explicitly resume. Do not start additional animations or automatically refine these candidates. Keep generated candidates and rejected trials available for comparison; no commits, pushes, cleanup, or baseline replacement are part of this pass.

The local preview server may remain available for viewing; it is not a motion-generation job. If the machine sleeps, all MP4s also remain under the `build/` paths given above. No scheduled follow-up was created.
