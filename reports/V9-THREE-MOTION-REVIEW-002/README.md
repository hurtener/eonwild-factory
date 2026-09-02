# V9 second three-motion review

Status: **USER REVIEWED; PERSISTENCE AUTHORIZED — 2026-09-02.** The user regards
Run008 and Sprint004 as much better, and Feeding002 as an improved direction.
These three are the saved foundation for the next bounded examples. They asked
to push this checkpoint to main before continuing. Historical pause and
not-yet-pushed statements below describe the previous delivery, not current authority.

Next pass: stronger vertical tail compensation, greater in Run than Sprint;
closed-jaw braced biting/pulling, followed by backward accommodation and chewing.
Reopened root tracks already meet the requested speed ranges: Run 20.2373 km/h
and Sprint 30.7628 km/h at the current rig metre scale. Keep speed/cadence and
leg articulation unchanged while adjusting tails. No new animation categories.

The previous Run007, Sprint003 and Feeding001 checkpoint is persisted on `main`
at `ca2cdd2`. Both the shared working tree and remote main contain that checkpoint.
Its 25 focused tests also passed from a clean committed export; no hosted CI is
configured. This preserves working baselines without claiming reference parity.

## Review targets

- Run: less folded supporting ankle and less excessive recovery tuck, preserving
  the smooth, buoyant rhythm and stable knee bend.
- Sprint: clearly visible flight during the long split, forward/downward torso
  and raised rear/tail; retain faster cadence and less flight fraction than Run.
- Feeding: continuous preparation/pull/regrip/chew transitions, stronger whole-body
  compensation and lateral head tearing while the food is held, with stable feet.

These new candidates are not automatically promoted over their predecessors.

## Feeding002 — ready

- [Side](http://127.0.0.1:8896/V9-FEEDING-REVIEW-002/feeding-side.mp4)
- [Front](http://127.0.0.1:8896/V9-FEEDING-REVIEW-002/feeding-front.mp4)
- [Rear](http://127.0.0.1:8896/V9-FEEDING-REVIEW-002/feeding-rear.mp4)
- [Implementation and reproduction](../V9-FEEDING-REVIEW-002/README.md)

Channel-specific shape-preserving curves carry motion through intermediate
poses, with different timing for the body, jaw, yaw, and tail. The first pull
raises the pelvis about 66 mm while moving the mouth 32 mm forward and 30 mm
down. Lateral head movement is deliberately more visible. Feet remain planted.

Host reran six focused tests and inspected native front/rear/side poses plus
consecutive browser playback samples of approach, pulling and lateral movement.
Two independent reviews found no P0/P1 issue. The videos are 144 frames at
24 fps, six seconds each. The small held food fragment and tissue connector
are authored preview geometry, not tooth/tissue collision or physics.

## Run008 — ready

- [Side, two cycles](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-008-open-support/trial-05/run-side-2cycles.mp4)
- [Front](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-008-open-support/trial-05/run-front-2cycles.mp4)
- [Rear](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-008-open-support/trial-05/run-rear-2cycles.mp4)
- [Opposing-side joints](http://127.0.0.1:8896/V9-AIRBORNE-RUN-001/iteration-008-open-support/trial-05/run-opposing-2cycles.mp4)
- [Implementation and reproduction](../V9-AIRBORNE-RUN-001/iteration-008-open-support/README.md)

More open support/recovery articulation, with reduced crouch and compression,
an earlier toe-off roll and an elevated approach before touchdown. Cadence,
stride travel, contact schedule and total body rise remain unchanged. The minimum
ankle interior angles are now approximately 68/83 degrees rather than 33/47;
this describes geometric folding, not measured forces or joint loading.

Two independent checks found no P0/P1 issue. Host inspected side playback through
support/recovery and native front/rear frames. No old knee inversion appeared
in those checks. All four videos retain native 24 fps, repeating the same
30-frame cycle twice. Strict skin-level no-slip remains unproven.

## Sprint004 — ready

- [Side, two cycles](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-004/trial-06/sprint-side-2cycles.mp4)
- [Front](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-004/trial-06/sprint-front-2cycles.mp4)
- [Rear](http://127.0.0.1:8896/V9-AIRBORNE-SPRINT-001/review-candidate-004/trial-06/sprint-rear-2cycles.mp4)
- [Implementation and reproduction](../V9-AIRBORNE-SPRINT-001/review-candidate-004/README.md)

Selected candidate: `build/V9-AIRBORNE-SPRINT-001/review-candidate-004/trial-06/`.
Its sampled flight pose visibly clears both feet, with a front-body inclination
of 10 degrees and distributed tail elevation of 18 degrees. Step travel grows
from 1.40 to 1.55 body heights; same-frame separation grows from about 3.65 to
4.00 metres on this rig. This is still short of the reference's normalized split.

Flight fraction is 0.22, below Run's 0.267. This is an engineering variation of
the uncertain reference timing seed, not a newly measured timing fact. The
candidate keeps the existing articulation bounds and avoids the straight-knee
limit encountered by larger-stride trials. It remains kinematic, not physical
muscle tension or force balance. Host checked consecutive normal-speed side
playback through recovery, extension, flight and catch, plus native front/rear
frames. Two independent checks found no P0/P1 issues. All three videos contain
46 frames at native 24 fps, repeating the same 23-frame cycle twice.

## Final checkpoint

- Host combined suite: **27 passed** (21 airborne and six new feeding tests).
- Independent reviews: no remaining P0/P1 findings; no additional review round
  was needed for the frozen selected candidates.
- Prior Run007, Sprint003 and Feeding001 outputs remain unchanged and persisted
  on main at `ca2cdd2`. New versions and code are local review work, not yet pushed
  or substituted for the saved checkpoint.
- Blender and encoding processes are finished; all three native workers stopped.
  The existing preview server may remain running for user playback.
- The broader V9 engine goal is unfinished. User feedback is the next step.

## Stop condition

After these three candidates are delivered, stop motion workers and generation
jobs. Wait for explicit user feedback; no other animations or automatic refinement.
