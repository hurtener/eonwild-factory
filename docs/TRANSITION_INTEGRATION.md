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

## Connected native-time diagnostic

After producing the three immutable packages, render the declared interface as
one connected film from side and three-quarter views in both movement modes:

```sh
uv run python tools/review_connected_sequence.py \
  --start out/sprint-pair/start --steady out/sprint-pair/steady \
  --stop out/sprint-pair/stop --output out/sprint-connected \
  --cycles 2 --blender /Applications/Blender.app/Contents/MacOS/Blender
```

The film evaluates start, steady phase-to-duration, complete steady cycles,
steady zero-to-phase and stop directly from their serialized GLBs. Root-motion
segments receive only the schedule's constant cumulative travel offset;
in-place segments reconstruct world travel from the declared motor trajectory.
The render receipt records every source hash and native interval, exact images
from both sides of each join, the exact stop terminal, encoded frame count and
post-render input immutability. It creates no NLA repeat, blend, retime, fitted
seam or copied boundary pose. Render completion remains distinct from human
visual approval and Unity validation.

## Current evidence and unfinished work

The 7920 source-bound pair report remains historical evidence for the former
three-sample quadratic estimator. Under that estimator, walk v3, reverse-walk
v4 and run v4 passed both joins in both movement modes, while sprint v4 was
blocked. Those values do not establish the endpoint derivatives of the emitted
LINEAR/SLERP channels. See the
[native-clock pair report](../reports/V9-NATIVE-CLOCK-PAIR-STATUS-001/README.md)
and the superseding
[exact emitted-tangent report](../reports/V9-EXACT-EMITTED-TANGENT-001/README.md).

At current source `83aa5e5391848493c902af0c6bd4ecab6228afe6`, exact emitted
evaluation keeps the generic direct joins and local steady loops `BLOCKED` at
their recorded velocity witnesses; the retained adult V9 loop is likewise
`BLOCKED` at `3.23101227406632 mm/s` against the unchanged `1 mm/s` limit.
The current local real-tool suite and hosted macOS arm64 CI each passed 928
tests plus 21 subtests. These code/contract results do not override failed
motion gates or grant visual, biological, Unity or production approval. The
[current continuity record](../reports/V9-CURRENT-CONTINUITY-83AA5E5-001/README.md)
pins the CI receipt and the bounded source-interface measurements supporting a
future source-derived tangent experiment.

Fast-walk v2 was already integrated at the recovered branch head. Reopened
metadata verification of its actual CI package passes. The preview clock now
avoids an extra duplicated frame from floating-point evaluation of 1.6 seconds;
30 fps produces 48 native samples. One-shots also emit a separately hash-bound
`terminal.png` at the exact endpoint, without inserting a held frame into video.
