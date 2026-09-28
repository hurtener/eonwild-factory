# C65 — effort, sitting plant, Froude timing (EXPERIMENT, NOT DELIVERED)

Status: **REJECTED INTERNALLY; C64 remains the review candidate.** Claude
(Anthropic), 2026-09-28, in response to the owner's C64 frame review.

## Owner feedback being addressed

Feet reach backward to plant instead of knees coming up; Tarbo over-leans (tail
flies) while Allo's ankle collapses; odd settling after standing; opening frame
unsettled; and whether hand-set choreography can scale to other rigs.

## Diagnosis (measured on C64)

- Trunk pitch was frozen through the rise (Tarbo −0.287, Allo at its −0.43 bound):
  the hip/chest stages used lowest-witness heights, which both animals satisfy
  with the lean held; it released in ~0.2 s when the legs ran out (the snap).
- Tarbo's knee stayed 0.2–0.6 m behind the hip; feet planted ~1 m behind it. The
  solved plant pose was hip-extended with knee/ankle at their fold limits.
- Nothing chose how load is shared across hip/knee/ankle.

## Opt-in mechanics added (C61 and C64 plans still reproduce bit-for-bit)

- `leg_effort`: quasi-static sagittal joint torque / admitted capacity, used in
  the plant solve (`effort.plant_weight`) and during loaded phases
  (`effort.weight`, fading as the chest reaches standing).
- `swing.space='joint'`: legs travel in joint space to the solved plant pose;
  unloaded legs track their joint-space intention.
- `staged.rise_by='joint_centres'` + `max_lean_degrees`: pelvis/shoulder joint
  heights drive the rise; the lean follows each animal's proportions and is capped.
- `sitting_posture` (+ multi-start seed): tarsal-resting plant — ankle near the
  ground behind forward-pointing metatarsi (Milner et al. 2009 resting trace;
  resting birds).
- `settle_initial_pose`: the opening pose is settled before frame 0.
- `time_scale`: all plan times scale with sqrt(L/L_ref) (dynamic similarity).

## Results

Worked: settled opening; Froude timing (Allo 8.16 s vs Tarbo 9.0 s); smooth,
capped lean without the snap (pitch 2nd difference ≤0.03); Allo knee/ankle share
load; Tarbo reaches a knees-up sitting plant (knee 0.83 m ahead of hip).

Failed (render `research/moco-c65-effort-d`): with feet planted far forward the
per-frame solver satisfies whole-body CoM balance by **curling the tail upright**
(Tarbo from ~4.5 s to the end); Allo right-knee flick at 2.25 s (116 BW spike);
the sitting plant needs ankle flexion 2.6 rad (149°), which conflicts with the
Coelophysis model range (119°) — recorded as an unapproved recovery-envelope
proposal, not adopted.

## Conclusion for the next step

The limitation is structural: each frame is a posture solve. Whole-body CoM is
balanced (all segment masses), but inertia, momentum and muscle effort of the
tail/neck/trunk are only audited afterwards, so the solver moves the cheapest
DOF (e.g. the tail) and cannot make motion carry weight. The next step is
dynamics inside the solve (direct collocation / Moco with the admitted masses,
inertia, contact and capacities), seeded from C64, on a short phase first.
