# C53 A — head-led walking turn, visual checkpoint

User requested the next turning pass after approving C52 B H walking, explicitly
requiring the head/neck to lead the turn. Work directly, without subagents.
C53 A is a new candidate, **pending user review**. Preserve approved C52 B H
walking and C51 A running; neither is replaced by this candidate.

## What this checkpoint contains

Sixteen native seconds: quiet stance, slower first step, 1.6 m/s walking into
an approximately 80-degree curve, then closing steps and rest at the new heading.
This is a forward walking turn. Stationary turning, sharp reversals and the
broader speed/mass/strength controller are not delivered by this pass.

The shared finite contact planner now accepts a versioned turn intent. C2 yaw-rate
ramps integrate into a curved root path at the original speed. Future path heading
provides continuous chest/neck/head anticipation (3-second preview; shares
0.10/0.40/0.35/0.15). Measured head heading relative to trunk reaches 38.41 degrees;
the planned extra lead peaks at 34.38 degrees. Attention begins before body yaw,
and eases back as the torso catches up. These are authored task values, not
measured dinosaur behavior. Existing neck limits are retained.

Foot anchors are planned on the curve. Inner/outer placements follow different
arc lengths; loaded heading remains fixed until recovery. The approved walk's
foot peel/recovery and cadence remain references, with bounded limb IK solving
against actual anatomy after body lean and attention. A small lateral lean intent
uses atan(speed*yaw_rate/gravity); twelve-link tail orientation follows delayed
path headings. These are engineering motion priors, not a solved force response.
No species branch, final pose clamp, runtime correction, changed strength, new
joint limit or contact-law adjustment was added. The serialized physical model
is byte-identical to the approved walking model.

## Review and physical limits

Two native-time Unity videos: 384 frames / 24 fps / 16 seconds each. All 768 frames
inspected in chronological sheets; enlarged quarter frames 72/150 and side
frames 150/290 checked. Cameras translate with pelvis but retain world heading.
The side view progressively sees the back; the quarter view better exposes neck
anticipation. This inspection is not direct video perception or user approval.

13 focused tests pass. All 1,538 local limb IK solves terminate (maximum 46
evaluations). No sampled source joint bounds or reopened skin knee/ankle bounds
are violated. Ankle coordinates span 25.46–88.62 degrees with peak 369.56 deg/s,
close to approved straight walking's 27.71–88.05 / 368.3. These are model-coordinate
angles, not anatomical included-angle measurements.

**Not converged physical dynamics.** Root residual RMS is 0.10887 BW/BWL,
maximum normalized command 4.5534; neck-yaw activation peaks at 4.5265 versus
capacity 1.0. Neck-upper yaw also exceeds capacity. The head-led pose thus needs
future mechanically feasible effort/distribution refinement; visual review must
not be described as validating its forces. Maximum target-foot error is 32.19 mm,
reopened joint mapping error 2.96 micrometres, and minimum skin height −5.50 mm.
Residual contact and proxy/skin mismatch remain explicit. No thresholds weakened.

## Files and reproduction

Factory source commit: `088fc54` on `codex/moco-c52-walk-turn`.
Game review branch: `codex/moco-c52-walk-turn-review`.
Task storage root:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526`.
Research: `research/moco-c53-head-led-turn`.
Factory worktree: `worktrees/stride-hip-visual-iteration`.
Principal game repository: `/Volumes/m2-extended-disk/Repos/eonwild`.
Unity asset folder: `game/Assets/Eonwild/MocoTurn53A`.
Durable evidence: `game/Evidence/moco-c53-head-led-turn`.

Use `execution.json` in that evidence folder for ordered commands. OpenSim Python
is task-root `research/opensim-2026-09-20/moco-venv/bin/python`; geometry/plot Python
is `venvs/contact-mass/bin/python`. Unity is
`/Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity`.
The offline sequence command adds `--turn-plan <C53>/turn-plan.json` to
`tools/sequence_moco_walk.py`, using the preserved C52 `walk-h` and C51 baseline.
Replays, source reference, exact models, recipes, final solution and retarget
receipts are archived; large JSON replays use gzip. The v15 admitted twelve-link
motion-set and source profile remain in existing catalogs/evidence. Runtime only
samples the emitted GLB. Capture uses the existing plain-stage review builder.

Videos:
- `review-quarter/tarbo-c53-a-turn-quarter-16s.mp4`
- `review-side/tarbo-c53-a-turn-side-16s.mp4`

Pause for user feedback. No follow-up artistic pass or new optimization is active.

## Neck research integration audit — user question, 2026-09-23

The inherited Moco path does not directly consume canonical embodiment
`attention.envelope` or its regional neck weights. Do not claim full research
profile integration. Source of authority remains factory
`docs/research/THEROPOD_NECK_BASELINE.md` and `catalog/embodiment/tarbo.v1.json`:
ordinary 35 degrees, scan 45, strong 55, routine cap 60, exceptional 65; skull
heading relative to torso. Tarbo is a provisional related-animal proxy; numeric
animation envelopes are not measured biological hard stops.

C53 A measured 38.41 degrees relative heading stays below the profile scan target
and routine cap. Its inherited neck/upper-neck/head yaw coordinate bounds are
each ±0.35 rad (20.05 degrees), not the same as enforcing the cumulative profile.
Regional distribution is also an authored reduced-model approximation and does
not use the canonical five-control Tarbo base-to-head weights.

Peak neck-yaw activation demand is 4.5265 against capacity 1.0: approximately
9.661 kNm demanded versus 2.134 kNm assigned. Peak control is 4.5534. These strength
and passive-stiffness inputs are engineering estimates, not neck torque capacities
established by the user's ROM research. The straight reference calibration sees
zero yaw gravity demand and leaves that axis at its prior capacity. Thus this
mismatch warrants calibration and distribution analysis, not the biological claim
that a Tarbosaurus cannot look 38 degrees into a turn. Next development should
connect the central cumulative envelope/regional semantics to the reduced anatomy
and audit strength/passive support and motion demand without silently increasing
capacity to pass. This audit changes no animation bytes or acceptance thresholds.
