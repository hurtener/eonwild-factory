# Independent visual review — V8.2 iteration-g

**Verdict:** `P0=0`, `P1=1` (evidence/claim boundary; not a visible motion
regression), `P2=1`.  Iteration-g is suitable for a **focused user-approval
comparison** of the safe upper-body balance overlay.  It is not, on this
side-only evidence, sufficient to claim that lateral balance has been
visually proven from every relevant view.

## Evidence inspected

- Synchronized 10 s, 24 fps comparison: left approved V8.1 iteration-38;
  right V8.2 Candidate-A iteration-g:
  `showcase/v8.2-balance-transfer/iteration-g/comparison/v8-1-approved-vs-v8-2-balance-transfer-side-by-side.mp4`.
- Candidate side render:
  `showcase/v8.2-balance-transfer/iteration-g/side/walk-relaxed-v8-1-respin-side.mp4`.
- Phase-matched frames at source frames 0, 30, 60, 90, 120, 150, 180, and
  210, with extra samples across frames 232, 236, 239, 0, 3, and 7 at the
  loop boundary.  I also used the V5.5 source walk as a qualitative historical
  reference, not as a gate baseline.
- Candidate mechanical and official-basis evidence in
  `reports/V8-2-BALANCE-TRANSFER/implementation/iteration-g-official-chest-solver/`.

The side render is framed consistently and shows the whole animal and every
contact phase.  Its 240-frame duration and phase correspondence make it a
valid comparison of regressions, rather than a selectively chosen clip.

## What is visibly better

The V8.2 upper trunk no longer reads as a completely rigid continuation of the
pelvis while the feet exchange support.  Around the alternating swing/support
poses, the chest and neck make a small, smooth counter-response; it takes some
of the "single stiff beam on two legs" quality out of the approved clip without
introducing a head bob.  The response is restrained: the animal remains a
heavy, deliberate walker rather than acquiring V5.5's more conspicuous
whole-body sway.  The preserved tail motion continues to counter the front
mass and does not appear to whip, reverse abruptly, or overtake the stride.

This matches the measured candidate envelope: chest roll is 5.618 degrees
peak-to-peak with a -0.901 counterphase correlation, while head roll stays
below 0.967 degrees.  Those values are supporting evidence only; the visually
important result is that the extra chest response is smooth and does not make
the head look independently animated.

## Protected locomotion checks

No visual degradation was found in the approved lower-body result.  Across the
matched contact, mid-stance, lift, and swing frames:

- foot placement, ankle/toe rocker, contact timing, stride reach, and swing
  clearance remain phase-aligned with V8.1;
- there is no new heel/toe float, foot twist, knee snap, or change in the
  supported-versus-advancing-leg read;
- the neutral forward posture and head stability remain intact; and
- the end/start samples show no visible seam pop or discontinuity.

This visual result agrees with the independent structural evidence: lower-body
world-origin drift is zero and angular difference is only
`1.50e-15` degrees.  That is a useful corroboration, not a substitute for the
frame review.

## Findings

### P0 — none

There is no foot/contact, posture, loop, head-stability, tail-whip, or
robotic/excess-sway regression that would make the comparison unfit to show.

### P1 — lateral-balance visual proof is incomplete in the supplied camera

The intended improvement is lateral/depth-axis balance, but the sole review
render is a pure side view.  In that projection, the new chest roll is
necessarily subtle; the footage convincingly establishes *non-regression* and
a gentler chest/neck response, but cannot by itself establish the full lateral
weight-transfer claim or distinguish depth sway from a good side silhouette.

This is an evidence/wording blocker, not a request to alter iteration-g.  For
approval materials, describe it as a **subtle upper-body balance overlay that
preserves the approved gait**.  Before declaring lateral balance visually
solved, add one synchronized front or three-quarter normal-speed render with
the same full-body/contact framing.

### P2 — the improvement is intentionally easy to miss from side view

The solve is appropriately bounded, but a casual viewer may read the right
clip as nearly identical to V8.1.  This is the correct trade-off for Candidate
A, whose lower body is frozen; it is follow-up presentation work, not a reason
to enlarge the solve or reopen the feet.  A front/three-quarter comparison will
make the approved subtlety legible without changing motion data.

## Approval recommendation

**Show iteration-g to the user now** as the conservative V8.2 candidate:
better-connected chest/spine/neck balance with approved V8.1 leg and foot
quality retained.  Do not present this side-only clip as definitive visual
proof of all lateral balance behavior.  User approval can choose the desired
subtlety; a second camera is required only for the broader visual claim.

## Re-pin — fixed three-quarter synchronized comparison

**Scope:** narrow re-review of
`showcase/v8.2-balance-transfer/iteration-g/threeq/comparison/v8-1-approved-vs-v8-2-threeq-side-by-side.mp4`
only.  This is a fixed, synchronized 1920 x 540, 24 fps, 240-frame (10 s)
approved-V8.1-left / V8.2-right presentation.  I checked alternating support
frames 0, 30, 60, 90, 120, 150, 180, and 210, plus the 232/236/239/0/3/7 seam
sequence.

### Result: prior P1 resolved

The three-quarter view provides the missing depth cue.  The V8.2 shoulder/
chest mass makes a restrained, continuous lateral counter-response across the
opposed support phases, while the neck keeps the head quiet and the tail
remains a coherent rear counterweight.  It reads as weight settling through a
single body, rather than as a head-led bend or isolated decorative sway.  The
amount remains appropriately small for a walk; it is visible in this camera
without becoming a side-to-side wobble.

No P0 or P1 regression appears in the added view: planted and swinging feet
remain phase-matched to approved V8.1, toe/ankle contact reads are retained,
the neutral posture and head stability are preserved, and the loop boundary is
continuous.  The locked framing also retains full-body/contact readability.

**Re-pin verdict: `P0=0`, `P1=0`, `P2=0` for this narrow camera-evidence
scope.**  The former P1 was solely the lack of a depth-revealing camera; this
comparison resolves it.  Iteration-g is now suitable as the user-approval
candidate, with the three-quarter pair included alongside the side pair.
