# Contact-owned transition integration

The current catalog uses sustained walk v3, reverse-walk v4, run v4, sprint v4,
fast-walk v2 and versioned start/stop v3 recipes. These are candidate selectors,
not approvals. Quality-01 remains rejected and approved historical assets stay
unchanged. Unity validation has not run.

## Shared coordination, not a speed-scaled clip

The start/stop profiles explicitly opt into `integrated_support`. At touchdown,
placement uses the root distance planned over the upcoming support interval.
During acceleration, release anticipates the next-step speed rather than keeping
a low-speed long stance while the pelvis runs out of reach. A committed anchor
never slides. Stop entry preserves the swing already in progress and its target.
The bound sustained gait's stride, cadence, flight fraction and anatomical/rate
limits are not changed. Root motion and in-place remain two exports of one solve.

`handoff_phase_fraction` is an authored interface setting, not a phase search.
The v2 start/stop profiles declare one eighth of a same-foot cycle, rounded to
the bound gait's native sampling clock. This leaves genuine loaded context
around the join instead of ending on a single newly landed terminal sample.
The derived `steady_phase_s` is recorded in the plan and runtime interface v2.
A consumer must use that phase explicitly; beginning the steady animation at
zero is not this contract. Legacy phase-zero recipes remain inspectable.

The transition's body response evaluates the same periodic driven-lag system
continuously. Linear interpolation of its output angles created velocity
corners between knots. The analytic interval solution preserves the sustained
reference states exactly without filtering exported rotations or changing skin
after validation. This is a kinematic response, not a muscle/force simulation.

## What constitutes a verified pair

```sh
uv run python tools/verify_transition_pair.py \
  --steady recipes/heavy-biped/sprint.v4.json \
  --start recipes/heavy-biped/sprint-start.v3.json \
  --stop recipes/heavy-biped/sprint-stop.v3.json \
  --output out/sprint-pair
```

The tool generates all three packages from current neutral geometry/programs.
It then checks the actual start-to-steady and steady-to-stop joins for both
root-motion and in-place plus declared motor travel. No crossfade, retiming,
best-fit phase or prior animated take is used. Both individual package gates
and both join gates must pass. Missing evidence or a failed join returns nonzero.

The evaluator validates full original timelines and material correspondence
before selecting native boundary context. It retains the real endpoint, checks
pose, rotation, contact state and one-sided velocity, and never converts a
single unsupported sample into zero slip. Recipe/profile hashes and the explicit
phase must agree. Package metadata verification independently checks identifiers,
normalized axes, duration, root mode, loop state, event/contact tracks and plan
identity in both serialized GLBs, not just their inventory hashes.

The inherited limits remain 1 mm world-position error, 0.5 mm material-position
error, 0.5 degree pose error, 1 mm/s world/material velocity mismatch and 10
degrees/s angular mismatch. This is an offline direct-join contract, not proof
of arbitrary Unity blending, interruption, event delivery or terrain adaptation.

## Current evidence and unfinished work

Local preliminary generation with the revised shared engine produced mechanically
passing sprint-start v3, sprint-stop v3 and run-start v3. Their direct handoffs
remain BLOCKED by velocity mismatch; pose and contact equality alone are not
completion. The permanent CI suite and all four pair jobs retain those failures.
Use their exact source/output receipts rather than treating this text as a
final-head acceptance report. Native media and Unity acceptance remain separate.

Fast-walk v2 was already integrated at the recovered branch head. Reopened
metadata verification of its actual CI package passes. The preview clock now
avoids an extra duplicated frame from floating-point evaluation of 1.6 seconds;
30 fps produces 48 native samples. One-shots also emit a separately hash-bound
`terminal.png` at the exact endpoint, without inserting a held frame into video.
