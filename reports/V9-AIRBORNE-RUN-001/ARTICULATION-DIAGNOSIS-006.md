# 005 visual rejection: measured cause and bounded 006 fix

Current status: the user explicitly accepted the original `iteration-006-anatomical-knee/feasible-recovery` full-body preview as the **USER-ACCEPTED NEW BASELINE**. The chronological trial findings below remain historical. Motion polish/reference performance are pending; the exact-pitch variant remains unpromoted, and physical ground-contact velocity remains unknown.

The user rejected005 for an angular knee glitch and lower-leg/hip skin collapse. Foot-ground passes and earlier reviews did not cover this articulation defect.

Exact emitted005 tracing found:

- Right knee sagittal bend sign flips at 0.3083–0.3167 s and 0.6667–0.6750 s, repeated in the second cycle. The right knee moves almost 0.9 m laterally from its hip, and a knee local rotation changes 22.75 degrees in 1/120 second.
- Minimum knee interior angles collapse to 29.93 degrees left and 22.07 degrees right. The unchanged accepted Walk source remains on the positive bend branch, with minima 108.81/106.24 degrees.
- The old solver projects a fixed source hip-to-knee vector onto each changing ankle target plane. Passing that source-pole ray changes the branch. Solving only bone direction also leaves hip twist unconstrained. Heel-up pitch persisting into mid-recovery further compresses the hip-to-ankle distance.

006 uses the oriented source bend normal, maps both upper-leg direction and bend normal to preserve twist, and coordinates sagittal ankle recovery with body-configurable engineering hip/knee/ankle envelopes. Toe trajectories and bone lengths remain unchanged; no mesh or skin weight edits were made. These limits are not certified biological ranges, and consolidation with the existing provisional species envelope remains future work.

The first006 diagnostic removes all bend sign flips and limits knee interior angles to about65 degrees, but independently selecting ankle pitch introduces a new46-degree pitch-branch jump. That trial is **not viable**. Its short joint-region images demonstrate the structural improvement only.

The `continuous-recovery` trial additionally releases heel-up pitch before under-hip recovery and bounds selected pitch changes continuously. Exact reopened output has zero knee bend-sign flips, knee interior minima64.988/65.000 degrees, and maximum knee lateral offsets0.201/0.113 m. Maximum selected pitch step is5 degrees at120 Hz; maximum knee step is9.283 degrees (1113.91 degrees/s). The right knee loop seam is0.036 degrees and pitch seam0.018 degrees. Maximum engineering envelope miss is0.0695 degrees; there is no unreachable extension, and foot-target error is5.35e-7 m.

These figures are **not a visual acceptance**. At0.8167–0.8250 s the left pitch reverses5.325→8.011 degrees, with knee interior83.38→74.10 degrees. The residual derivative kink must be judged in playback; the provisional rate ceiling does not bless the output. Joint-region probes at the original defect intervals no longer show the inverted triangular skin shape. Focused120 Hz subframes around the new peak show no inversion, but that recovery leg is partly occluded by the near stance leg. A complete30-frame joint-region cycle is the next motion gate; no full-body release render has been made for this trial.

Opposing-side probes now expose the left recovery leg. Their runtime NLA receipt proves source time=(scene frame−1)/24: scene20.6 is0.816667 s, scene20.8 is0.825 s. There is no one-frame mismatch in the earlier probes; the earlier receipt omitted the NLA scene-start authority. The tight rearward recovery and derivative kink remain visible-motion questions, not numerical passes.

Three targeted pole/twist/recovery regressions pass. Mesh, weights, bone attachment translations, and nominal longer Run toe trajectories are unchanged. Exact final skin-ground checks report zero penetration, zero planned-stance misses, and34 interior flight samples without intersection. Active near-ground surface motion remains0.430657 m/s at0.1–1 mm bands and0.789385 m/s at3 mm; contact-drift acceptance is still open.

## Targeted feasible-recovery correction

Host opposing-side inspection confirmed the derivative kink. A preferred-margin local-cost trial moved it earlier and was rejected without rendering. A free-swing geometric trace then showed why: the pitch range splits at0.8167 s, and the selected upper branch collapses into the ankle30°/knee65° corner. The lower branch exists but keeps the thigh rearward and knee nearly extended, conflicting with intended recovery lift. Advancing the foot phase made the range disappear and was not emitted.

The new `feasible-recovery` variant lowers swing clearance by0.04 body heights (0.106 m), retaining a connected feasible pitch range while keeping stride, contacts, flight, pelvis posture, and hard limits unchanged. Its reopened knee steps at0.8083→0.8167→0.8250 s are2.00/2.11°, not1.95/9.28°; pitch is monotone13.398→10.817→8.386°. Minimum left ankle angle rises to34.927°, avoiding the active corner. No branch flips or unreachable extension occur. No visual acceptance is claimed.

The skin metric is now separated from proximity deformation. The0.430657 m/s peak occurs during left push-off at stancephase0.673,9.81–11.53 mm above the fixed floor; the0.789385 m/s peak occurs during right push-off atphase0.636,18.63–20.08 mm above the floor. Across108 stance pairs there are no persistent sole/toe points within0.1/0.5/1 mm of the floor. Actual ground-contact velocity is therefore unknown/null, not a zero-skate pass. The original broad source tolerance is retained and explicitly distinguished from true ground occupancy. Four focused anatomy/ground-classification regressions pass.
