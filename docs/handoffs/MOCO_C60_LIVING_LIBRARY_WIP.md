# C60 — 29-family living library, work in progress

User request: finish the roadmap breadth with living behavior on both admitted
animals, then pause for one combined video review. Work directly, NO subagents.
The goal remains ACTIVE. This handoff is an internal continuation, not delivery.
C59B has no inferred user approval. Accepted main is unchanged.

The older inventory had 32 mixed rows including secondary layers and machinery;
no numbered 29-item list was found. An optional asynchronous clarification was
sent; absent another list, `catalog/behaviors/moco-c60-library.v1.json` maps the
inventory into 29 actual review families. Do not count breathing/arm layers or
OpenSim infrastructure as standalone motions. Every selected family needs both
animals, saved native-time media and a truthful pending-review status.

## Workspaces and commands

Factory: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration`.
Principal game: `/Volumes/m2-extended-disk/Repos/eonwild`.
Research: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c60-library`.
Factory branch `codex/moco-c52-walk-turn`, game branch
`codex/moco-c52-walk-turn-review`; preserve main and unrelated untracked files.
Python P: task storage `venvs/contact-mass/bin/python` (numpy/scipy/PIL/pytest).
Python M: task storage `research/opensim-2026-09-20/moco-venv/bin/python`.
All command cwd is the factory worktree, PYTHONPATH=src, BLAS threads=1.
`research/generate.py <take IDs>` runs sequence, exact-model replay and retarget,
two ordinary subprocess jobs concurrently (not agents). Per-stage durable logs
and process receipts are in research. Do not re-run existing output directories.
`renderqueue.py <IDs>` serializes Unity builds and captures side/quarter views;
run ONLY ONE queue at once because the player build target is shared.
`compact-sheets.py <IDs>` includes every native 24-fps frame in 48-frame sheets.
Use `batch.json` for current plans/sources/motion sets/profiles. Some entries are
exploratory/rejected: not every generated directory is a selected candidate.

## Shared implementation

`moco_behavior_intent.py`: unit-explicit keyed behavior intents; smooth bounded
articulation offsets; C2 monotone support retiming for earlier unloading and
longer recovery. Retiming changes motor/contact intent BEFORE IK and force
replay, not playback speed. Species parameters remain in admitted anatomy/data.

`sequence_moco_behavior.py`: shared whole-body contact coordinator over saved
Moco warm references; purpose/attention, living chest/tail, optional oral target,
world-anchored placements, body-support transitions, environment load audit.
All outputs remain authored kinematic/finite inverse-dynamics candidates;
NONE is a new converged full Moco optimal-control simulation.

Oral tasks now solve mouth position, horizontal COM, limbs, pelvis and tail
carriage together. Target angles alone failed cross-animal reach. Action jaw
opening has a separate declared envelope; the existing <=8 degree breathing
limit is intact. Semantic arm carriage tucks hands during lowered postures.

Body-support recipes add segment-radius contact proxies. `full_foot_hull` adds
side/upper witnesses from admitted 3D material vertices; upright sole pads are
insufficient for a fallen foot. Masses, joint ranges and capacities stay intact.
Clearance fitting adapts limbs, neck and tail around broad body support, then
physical-time smoothing and exact-model replay measure the emitted trajectory.
This is not a certified impact/controller or an exact deforming skin collision.

`moco_environment.py` computes hydrostatic buoyancy and quadratic drag using
explicit engineering coefficients, then installs time-baked PrescribedForce
curves in the exported OpenSim model. These loads apply to the specified
trajectory only; no fluid simulation, propulsion prediction or feedback claim.

Unity viewer adds optional plain-stage water/obstacle context only. It NEVER
corrects animation. Water side view has a raised camera; quarter view omits the
surface to expose limb movement for inspection. No demo world is launched.

## Known exploratory rejections / next checks

- First feeding/drinking A used fixed joint offsets; Allo did not reach low
  enough. B oral target produced branch/acceleration defects. C reached but
  raised the tail excessively. D adds tail-height and COM goals plus tucked
  arms. D exports exist; render and inspect before choosing.
- First fall floated on its tail; broad-support primary sites corrected this.
  B/C still have large physical errors and emitted foot skin reached ~0.307 m
  below floor during descent. D adds full 3D foot material hull; inspect it and
  retain failure if still wrong. Do NOT promote C automatically.
- First swim put feet through the shallow floor, causing absurd force residual.
  Rejected. Tarbo swim B raises body/water depth, root RMS ~0.19 and max command
  ~0.91; still diagnostic, not independent swimming convergence. Earlier B
  capture camera passed below water plane. Viewer is corrected; re-render.
- First sprint only changed stride/cadence; B shortens support for both legs,
  extending recovery/airborne availability. Inspect actual final contact and
  skin; source bounds unchanged. Limp retimes only injured right support.
- Get-up adopts a selected fallen terminal state and aims at the source standing
  state translated to that real location. It must be generated AFTER its fall.
  Initial Allo get-up failed because its source had not finished; empty output
  can be removed with rmdir after checking, then re-run once source exists.
- Allo walking turn is generated first with shared `sequence_moco_walk.py` and
  the existing C54B plan, then living intent. `generate-allo-turn.py` handles it.
  Reference attention is now preserved and added to secondary gaze, rather
  than replaced by a tiny new glance. Re-run Tarbo final turn with this fix.
- Rest/sleep/rise, death, running/sprint falls, jump, terrain, wade and second
  species counterparts need final selection, generation, capture and review.

## Delivery requirements

Freeze source and selected data, then run a final reproducible batch in a NEW
research directory. Exploratory jobs span source changes; do not claim their
current source hash is the code used to generate every earlier take. Preserve
rejected receipts separately. Archive exact final commands, commits, policies,
models/STOs/receipts, compressed replays, GLBs and native-time media in principal
`game/Evidence/moco-c60-library/`. Preserve C59B four-family media byte-for-byte
if those are the selected library entries. Create per-family both-animal reels
and a combined review index, with direct saved MP4 links. Inspect all frames of
selected media; this agent uses frames/contact sheets, not direct video vision.

Keep physical acceptance, visible review, generation and gameplay parity
separate. Most new physical candidates still fail force/slip acceptance.
No auto-approval or blanket completed/production-ready marking from clip count.
Update both roadmaps and artistic direction, push explicit task paths on review
branches, then pause the goal at the combined review as the user requested.
