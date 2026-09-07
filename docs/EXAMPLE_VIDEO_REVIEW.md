# Tarbosaurus example-video review

Host review, 2026-09-07. The `assets/examples/tarbosaurus` videos are visual
direction for the reusable factory. They are not measurements of a living
Tarbosaurus, motion-capture ground truth, or evidence that a multi-tonne animal
could perform every depicted action. Scientific scale and mass provenance are
recorded separately in [ANIMAL_CONFIGURATION.md](ANIMAL_CONFIGURATION.md).

## Coverage and method

[EXAMPLE_VIDEO_REVIEW.json](EXAMPLE_VIDEO_REVIEW.json) records original paths,
SHA-256 hashes, dimensions, frame counts, native timing, full-decode results and
per-file visual coverage. All 17 original files decoded completely. There are
16 distinct videos: `tarbosaurus_walk copy.mp4` exactly duplicates
`tarbosaurus_walk.mp4`. The primary motion streams are 24 fps; attached thumbnail
streams are excluded from timing and frame counts.

The host inspected 24 evenly spaced native frames, including the first and last,
for every distinct video. Five priority references received additional inspection
of every consecutive native frame and complete original-speed browser playback:

| Reference | Frames inspected | Native duration |
| --- | ---: | ---: |
| `Tarbosaurus#walk_side_v02.mp4` | 193 | 8.041667 s |
| `v9_evidence/sprint-left.mp4` | 145 | 6.041667 s |
| `v9_evidence/RUN START-RUN-RUN STOP.mp4` | 193 | 8.041667 s |
| `v9_evidence/walking-back-gauge.mp4` | 145 | 6.041667 s |
| `v9_evidence/walking-front-gauge.mp4` | 145 | 6.041667 s |

Following the user's recovery-direction correction, the host also inspected
all 241 native frames of `tarbosaurus_walk.mp4`, then examined frames 101, 108
and 116 at full native resolution. Those frames show the foot hanging downward,
passing below the knee, and opening forward for placement, respectively. The
exact illustrated reference was confirmed in the live browser. A subsequent
independent browser playback ran this complete 10.041667 s clip at 1x from the
beginning to its terminal paused state; the original user-selected tab was retained.

Frames below are zero-based; time is frame index divided by 24. The full source
is retained. No source retiming, generated in-between frames or altered geometry
is used for this review. Comparisons between different clips are qualitative
phase comparisons, not pixel-correspondence or equal-speed measurements.

## Findings that affect implementation

| Region/action | Reference observations | Factory criterion and current gap |
| --- | --- | --- |
| Walking feet | Side walk frames 12–30 (0.50–1.25 s) show release, knee flexion and forward placement, repeated in later cycles. In `tarbosaurus_walk.mp4` at about 4.233 s, the knee is flexed while the distal foot hangs downward and the toes trail. | Distinguish knee clearance from distal recovery direction. The first adult polish folds the foot upward/forward beneath the leg and is rejected on this criterion; increasing articulation amplitude alone is not an improvement. |
| Walking neck/head | The side walk maintains a forward head with a continuous neck curve during the recurring gait. Its opening mouth/head gesture is an introductory action. | Preserve neutral-relative forward attention. The corrected gaze removes the former absolute-world upward correction; it does not excuse a compressed neck during sprint. |
| Foot track | Front/rear gauge sequences show alternating support beneath the torso and flexed toes during recovery; the body transfers over the support side without a wide lateral step. | Inspect front and rear output as well as side view. Preserve narrow support placement and check clearance throughout the crossing portion of swing. |
| Tail | Front/rear sequences show changing curvature and delayed distal response. The rear reference includes a large, slow lateral sweep and a low tail tip. | Use distributed, delayed response. Do not copy the full sweep amplitude or let a heavy tail become a fast independent whip. Adult polish is deliberately a modest increase. |
| Sprint legs/torso | Sprint frames 0–5 show support passing under the body; 10–14 (0.417–0.583 s) show rear extension/push-off; 18–20 show recovery and loading exchange. Later cycles repeat the pattern. | The engineering sprint's persistent deep crouch, folded recovery and low/compressed neck remain concerns. The reference has clearer rear extension and a steadier torso. Its depicted flight is not biological validation for PIN 552-1. |
| Acceleration/braking | Run/start/stop begins already moving, develops running by about 3 s, brakes around frames 144–154 (6.0–6.42 s), then recovers neck/body posture through about frame 174 and settles by 180–192. | Build staged loading, stride development, braking and settlement. A final planted pose alone is insufficient. The large braking tail raise/head recovery are action cues, not the default walking posture. |

The other overview reviews add these constraints:

- `tarbosaurus-walking-looking.mp4` separates attention changes around 4.7–6.5 s
  from the continuing gait and returns toward forward attention by about 8 s.
  `LISTEN REACTION` similarly changes attention before stepping away. Head
  direction should not require a rigid whole-body turn.
- `tarbosaurus-stops-stands.mp4` shows final placement and body settlement around
  3.7–4.5 s, followed by a supported stand. The stop must finish its dynamics,
  not merely acquire two contact flags.
- `running-sustained-left.mp4` reinforces coordinated leg recovery, relatively
  stable forward attention and body/tail response. It supplies no measured speed
  ceiling for this animal.
- The three-quarter walk and `tarbosaurus_walk.mp4` help assess spatial clearance,
  turning/attention and tail curvature beyond a side silhouette.
- Feeding/tear and grounded-bite references show bracing before neck/torso reach,
  followed by recovery. Bite-miss and body-shove references show a compensating
  step after overshoot. These are sequencing cues, not force/contact measurements.
- `attack-eat.mp4` includes substantial viewpoint changes and close-ups. It is
  useful for behavior staging, but unsuitable for fixed-view gait measurement.

Some references change apparent proportions or contain exaggerated tail/head
gestures. Their uncalibrated cameras and visual inconsistencies prevent deriving
exact bone lengths, joint angles, center of mass or ground reaction forces.

## Candidate evidence and acceptance boundary

The pre-polish adult candidate was inspected at all 74 native review frames in
side, three-quarter and foot-close views, with complete media decode and native
1x playback. The first adult-only polish increased articulation in matched-camera,
matched-time Blender frames. Emitted push-off rose
from 20.372° to 28.000° and recovery pitch from −26.659° to −31.110°; the measured
tail-tip lateral range in eight matched poses rose from 0.879 m to 1.125 m.
These are output comparisons, not scientific target values.

The host initially called the stronger recovery an improvement. The user's
comparison of the candidate at 0.600 s with `tarbosaurus_walk.mp4` at about
4.233 s exposed the opposite distal direction: the candidate tucks the foot
upward/forward, while the reference hangs it downward with trailing toes beneath
a flexed knee. The host confirmed the exact reference in the live player and
withdrew that positive assessment. This polish is **visually rejected for foot
recovery**. Correcting it requires checking the emitted tibia, metatarsus and
toe directions through release, recovery and placement; changing a numeric
pitch amplitude is not evidence of reference alignment.

An isolated signed-pad probe subsequently pointed the foot farther downward
and passed the existing technical gates (root-motion GLB
`af00f83f90ce9af91f08572267a3031e20d0a5c2179f05c619f53767c54b5c2e`).
The host rejected this probe after inspecting actual side-foot and three-quarter
skin frames at 0.600 s: the toes still project forward and have little ground
clearance. Its remaining render was stopped; no full-cycle render or visual
acceptance is claimed. A downward vector alone does not establish the trailing
recovery seen in the reference. Foot orientation, toe articulation and clearance
must be evaluated together before selecting a successor.

That polish was compiled independently at `2e718a37dbe3e43094b1c75dc31e86d5021c96f7`.
It must be corrected, regenerated and reviewed with the shared solver.
The historical approved V9 artifacts remain frozen comparison sources. Technical
package acceptance, raw direct-join acceptance, host visual inspection, human art
approval, biological validation and Unity parity remain separate evidence levels.

Review artifacts are in ignored `out/continuation-example-video-audit-001/`:
`inventory.json`, the original-video browser player, overview sheets and
consecutive native-frame sheets. These local evidence files are not runtime
generation dependencies. The committed receipt retains their source identities
and the honest scope of the host's inspection.
