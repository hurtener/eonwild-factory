# V9 Power Attack + Maneuver Plan 001

Sources: frame-by-frame subagent breakdowns of `attack-eat.mp4`
(reference lunge) and `FEEDING + TEAR:PULL — fixed side.mp4` (our take),
plus the backward shuffle visible in `GROUNDED COMMITTED BITE — fixed
side.mp4`. All frame ids below are ffmpeg 1-based @24fps on
`assets/examples/tarbosaurus/attack-eat.mp4` (736×400; leg ≈110–120px).

## A. Power attack (grounded-first, capacity-gated)

Reference phase table (subagent-measured):

| Phase | Frames | Duration | Key facts |
|---|---|---|---|
| Stalk-crouch | f12–28 | ~0.67 s | pelvis −20% leg; weight onto rear leg; tail level; jaw shut |
| Launch | f28–33 | ~0.21 s | trail-foot toe-off f30 (dust), lead leaves f31–32; hips→knee→ankle; jaw cracks f28, ~65–70° by f33 |
| Flight | f32–38 | ~0.25–0.29 s | zero contact f33–37; head aimed at ground target; tail kicks +18° then streams, lags body 2–4f |
| Contact (miss) | f38–48 | ~0.42 s | lead touchdown f38–39, trail f42–44; jaws slam f43–46; head reaches ground f44–46; tail low |
| Recover | f48–99 | ~2.1 s | 2–3 brake steps vaulting the lead leg; re-gape f54–60 held wide (display, not bite); walk by f90 |

Build order (each step lands with its acceptance check):

1. `planning/power_attack.py::plan_power_attack` — stance 0.25 s,
   flight target ~0.25 s, preload ≈ stalk speed, COM forward + slightly
   down (dive, not jump). ACCEPT: planner emits the f32–38 equivalent
   or clean `grounded_lunge` fallback with identical jaw/head tracks.
2. `capacity.py::assess_takeoff` gates the push (friction margin ≥0.1,
   peak ≤ force limit) else grounded_lunge. `assess_landing` +
   `assess_arrest` cover the lead-leg catch (decel within
   absorb multiple over ~20% leg crouch travel) + brake steps ≤1.5
   body lengths.
3. `transition.py::capture_step_target` plants the lead foot from the
   LIPM capture point (±0.3 m of one step ahead of launch COM);
   `bridge_impulse` + tail ODE conserve L over flight (tail +18° at
   toe-off → stream by touchdown, 2–4f lag, `clamped_samples == 0`).
4. `whole_body.py::solve_bite_window` over f28–46 (~0.75 s): gape
   0→65° by f33, hold, close f43–46; mouth residual ≤0.05 m at the
   ground target. Retire `profile.json` anticipation 0.55 s → 0.25 s,
   pelvis_drop ≈ 0.20 leg. Grounded-only until capacity passes.
5. Jaw-timing guard (risk R1): gape >45° at least 5f BEFORE lowest-head
   frame — assert in bite-window samples, or it reads as bite-at-air.
   Zero-contact window ≥4f or it moonwalks (R2). Tail pitch peak 2–4f
   after body pitch peak (R3, cross-correlate — lag must be >0).

## B. Feeding amplification (next build, spec accepted)

Current take: 1 yank in 6 s, 2.3 s pinned grip-hold (39% of take),
head <5°/s for 70% of the clip, jaw shut 2.26 s straight, tail
lateral ≈ 0. Target: **3 yanks / 6 s (~0.5 Hz)**, plunge 0.5 s →
clamp + pull-lift 0.6 s → settle overshoot 0.3 s → re-plunge; depth
±20% alternating, period jitter ±15%, pull yaw ±4° L/R alternating.
Head-stack range >25° (head leads lift 0.1–0.2 s) + 6–8 Hz ±0.7°
strain tremor in clamp only; pelvis counter-phase ±6° with >80 mm
cyclic travel; tail traveling wave base→tip lagging head 0.3–0.5 s,
tip >60 px vert + >25 px lateral (verify front/rear); jaw state
changes ≥6 per window, no state >0.8 s; re-plunge overshoot 10–15%.
Feet stay planted; ±30 mm fore-aft weight shift at yank frequency.

## C. Backward walk (corrective position shuffle)

What the bite video shows: short backward shuffle steps to re-aim —
toe-first contact, crouched, head STAYS on target while feet back up.

1. Plan: reverse support in `planning/airborne_gait.py` — short step
   length (≤0.3 BH), duty ≥0.7, double-support biased; touchdown
   BEHIND the COM with toe-first contact order (reverse the
   heel-strike assumption in the contact witnesses).
2. Solve: `solve_airborne_gait` with a negative-travel plan; guard
   knee hyperextension explicitly (reversed loading pushes the joint
   the other way) — new envelope check, fail-closed.
3. Axial: gaze stays locked forward on the target (decoupled from
   travel direction — the whole point of the maneuver); tail low,
   small-amplitude fast sway (step freq 2× walk).
4. ACCEPT: backward speed ≤1 m/s, zero skate on loaded feet (witness),
   head yaw drift <2° during the shuffle, loop seam <0.5°.

## D. Turning with head counterweight + directed gaze

Design: the head leads, the body follows, the tail answers.

1. Footfalls: `transition.py::turn_plan` (exists: yaw-rate-limited,
   alternating steps, speed retention) drives step placement; yaw rate
   cap ~60°/s loaded, tighter at sprint speed.
2. Head-lead: gaze target swings into the turn 0.2–0.3 s BEFORE body
   yaw (`solve_gaze_targets` with lateral offset). The neck/head
   chain needs YAW, not just pitch — generalize the iteration-013
   `yaw_tracks` machinery from tail-only to the head chain, driven by
   gaze yaw error through the same damped ODE (organic lag for free).
3. Counterweight: `redistribute_tail_head` already couples head sweep
   to tail answer — extend its drive with turn yaw rate so the tail
   swings out of the turn (centrifugal counter-balance) while the head
   looks in. Torso roll into the turn 3–5°, pelvis yaw lagging head by
   ~15% stride.
4. Gaze modes (patrol state machine, runtime-side): forward-fixate
   (prey), scan ±30° (sweep timing from the walking-looking reference:
   ~0.8 s look + 0.6 s gape-hold pattern), target-track (feeding/bite
   lock). Each mode is just a gaze-target policy on the same solver.
5. ACCEPT: head yaw leads pelvis yaw by ≥0.15 s on turn entry; tail
   tip displaces out-of-turn >100 mm; no foot skate during pivot
   steps; gaze saccades complete <0.4 s with <10% overshoot.

Order of implementation: A1–A4 (power attack, grounded) → B
(feeding, same axial machinery) → D2–D3 (head yaw generalizes the
tail-yaw work) → C (backward, needs reversed contact logic) → D4
(runtime gaze policies).
