# C52 B revised — centered walking and finite transitions

The user corrected the requested name from C51 B to **C52 B**. Earlier C52 B
media remains preserved in `moco-c52-walk-turn`; it has changes requested for
rearward support, repeated ankle extension/flexion and rigid tail carriage.
C51 A remains the approved faster-gait baseline and is unchanged.

This pass uses the same spatial OpenSim anatomy and shared task generator.
The former placement aligned the **front toe witness** with the stride center;
subtracting the full forefoot lever put the MTP well behind the hip. The revised
walking task aligns the pad-area-weighted support region with the warm posture's
modeled center of mass. Pad area is a geometric prior, not measured pressure or
a demonstrated optimal COP. No body mass distribution is changed.

Walking tail damping ratios are estimated at 0.5 proximal / 0.9 distal, instead
of the faster-gait 0.8 / 1.5. All twelve links are freed in the periodic
initializer and their reference penalty reduces from 30 to 5. Stiffness,
gravity preload, joint limits, contact law, capacities and physical acceptance
thresholds remain unchanged. Running recipes retain their existing settings.

The user requested a more normal speed and a **16-second idle → start → walk →
stop sequence**. Target steady speed is 1.6 m/s (5.76 km/h), an authored test
informed by the tyrannosaurid trackway range of 4.5–8 km/h in [the Glenrock
study](https://www.sciencedirect.com/science/article/abs/pii/S0195667115301452).
This is not a measured Tarbosaurus speed. Preferred speed and speeds at a
particular trackway are different quantities: [the T. rex tail-frequency
study](https://pmc.ncbi.nlm.nih.gov/articles/PMC8059583/) estimates a preferred
1.28 m/s, with a sensitivity range of 0.80–1.64 m/s. The original 1 m/s profile
is not silently rewritten; this candidate records its speed in the admission.

## Generation

Work directly, without subagents. Task root:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526`.
Working factory: `worktrees/stride-hip-visual-iteration` under that root.
Research: `research/moco-c52b-centered-walk`.

1. `tools/coordinate_moco_prototype.py` with the research admission, walk/turn
   recipes and `research/moco-c51-support-feasibility/support-a/replay.json`.
   First refinements were bounded to 20 evaluations. The current hard-limit refinements are bounded to 24 evaluations, with 61 full-stride samples. No full Moco solve.
2. `tools/replay_moco_prototype.py <candidate>` replays the exact saved model.
3. `tools/sequence_moco_walk.py --source <candidate> --baseline <C51 replay>
   --output <new sequence directory>` creates the finite choreography.
   It plans world support anchors, a slower first step, final closing steps,
   and shorter root travel during acceleration/deceleration. It re-solves
   admitted limbs and audits exact inverse dynamics after all pose changes.
   Static contact depth is settled with the unchanged contact law.
4. Replay the sequence, then `tools/retarget_moco_prototype.py` with the v15
   tail12 motion set and original C50 profile. This adapter does not correct
   contacts. It emits the whole finite trajectory without mirroring/repetition
   and reopens the actual skin for measurement.
5. Build the existing plain-stage Unity review player using new asset folders.
   Capture 384 frames at 24 fps, encode a native 16-second video, inspect all
   frames, preserve evidence and pause for explicit user review.

The steady cycle is a guided inverse-dynamics initializer. The finite start/stop
is an authored contact plan with an inverse-dynamics audit, **not** a solved
optimal-control transition, forward-stability demonstration or biological
validation. Report its actual residuals separately. A visually useful diagnostic
must not be relabeled a physically converged simulation.

## Results and review

The user saw the first draft during generation and explicitly rejected its
ankle artifacts. **Do not present that draft.** Centering alone was insufficient.
Two soft-limit follow-up refinements were cancelled before returning solutions;
no convergence or final result is claimed for them.

Comparison with C51 found that ankle bounds (0.15–2.25 radians), torque capacity
(0.26 BW*L), contact law, and unloaded ankle comfort settings were unchanged.
The walking transfer changed stance fraction 0.43 → 0.62 but sampled its running
joint reference without aligning the two support intervals. That allowed a
running recovery preference to conflict with a still-planted walking foot.
The new C2 phase map aligns support/recovery before limb IK. A smooth bounded
latent-coordinate parameterization now enforces all admitted joint ranges
throughout coefficient optimization. Finite-sequence IK includes the digit
inside its bounded solve; continuous interpolation is bounded as well.
This is not a final-angle clamp. Every contact and internal effort is recomputed.
Existing authored root height/pitch/roll envelopes are also enforced so the
optimizer cannot hide distal-joint error in a bouncing torso. Source commit
`9b7886a` introduces the repair; later source-duty validation is numerically
inactive for this correctly matched C51 baseline.

The configuration preserves the reviewed faster-gait recipes. More harmonics
are available to the whole leg, and load-gated ankle rate/acceleration comfort
penalties discourage high-frequency reversals without prescribing a knee or
metatarsal angle. These are engineering regularizers, not biological proofs.
Current hard-limit candidates are being evaluated; do not infer approval.


## User's next-iteration boundary

Get correct walking first. The user explicitly asked to defer the broader
normal-locomotion generalization discussion until after this walking checkpoint.
Do not grow per-gait/species hardcoded choreography into the lasting engine.
Animal mass, strengths, admitted anatomy and ranges are semantic model inputs;
direction/speed/support intent are movement requests. Reference phase maps,
contact placement priors and finite start/stop schedules here are declared
initializer/task aids, not predicted biological laws or permanent per-animal
solvers. Future work should replace these aids with reusable dynamics-driven
coordination across direction, speed, mass and strength. Do not start that
architecture project before obtaining a credible walk for user review.

The root-posture bounds initially disturbed feet because they were applied
after IK. That trial was stopped, not accepted. Establishing posture before
foot IK and settling initial pad compression against body weight restores a
usable seed. Straight-path derivatives now use exact splines/parameter-map
chain rules, matching the established straight-running derivative path instead
of finite differences of accelerations. `walk-e` is the current bounded
straight-walk refinement. Turning trials are held; no rejected draft should be
presented again.


## Intermediate candidate E/G outcome (2026-09-23; changes requested)

The final periodic initializer is `walk-e` (solver source `c922beb`), followed
by `walk-sequence-g` (finite-transition source `2d9fe44`). The latter blends
reference joint posture toward neutral as speed falls, retains final world
support anchors, and allows its local bounded IK to finish. Earlier 35-evaluation
IK budgets left numerical jitter near the final closing step. All 1,538 final
local solves finish successfully, requiring at most 47 evaluations. This is
local IK termination, **not full Moco convergence**.

The periodic stance ankle audit finds one prominent peak per side (using a
3-degree prominence threshold), compared with four prominent extrema per side
in rejected `walk-a`. Small sub-threshold ripple remains; no claim of a perfectly
monotone biological trajectory is made. All replayed joint angles and reopened
skin knee/ankle angles remain inside admitted bounds. Reopened rig joint mapping
error is at most 3.12 micrometres. Continuous bounded interpolation is covered
by focused tests; 11 focused path/support checks pass.

Finite sequence: 16 seconds, idle to 2 seconds, 12 steps, 1.6 m/s cruise,
stop at 12.684 seconds, 14.215 metres total travel, then rest. Unsupported root
residual RMS is 0.09507 in normalized BW/BWL components; maximum normalized
command is 1.4748 (above its 1.0 capacity). Reopened skin reaches 9.0 mm below
the stage floor. These are unresolved physical/contact limitations, not waived
acceptance thresholds. This candidate is a reviewable motion diagnostic, not
production physical validation, a forward-stable simulation, or a converged
optimal-control solve.

Review assets: principal game `Assets/Eonwild/MocoWalk52BCentered`; durable
receipts/media under `game/Evidence/moco-c52b-centered-walk`. C51 A is preserved.
Turning stays on hold until the corrected walking is reviewed. User approval
is PENDING. No new generalization stage has begun.


The user saw E/G during rendering and said it was much better, but still too
extended/forceful for relaxed walking. Do not present E/G as the corrected final
checkpoint. Its formal ROM pass does not establish appropriate functional gait.
Current `walk-h` reduces *all* warm leg excursions around their mean using the
ratio of current/source dimensionless speed, and scales the source toe-off
intent by the same ratio. This is an explicit initialization prior, not a proven
biomechanical scaling law or a per-species joint-angle override. Exact anatomy,
contact/effort evaluation, bounds and strength remain unchanged. H seed ankle
range is 27.7–87.9 degrees and maximum rate 369 degrees/s, versus E 9.7–103.3 and
625 degrees/s. All-angle scaling also removes the doubled recovery bend at the
knee in the seed. Await bounded physical refinement, final sequence/rig replay,
and a fresh 16-second render. Broader generalized locomotion remains deferred.


## H relaxed walking — final candidate for this checkpoint

Source `9db524f`, recipe `walk-h-recipe.json`, returned periodic `walk-h`,
finite `walk-sequence-h`. The 16-evaluation refinement preserves the gentler
ankle curve. Across the full final 16-second sequence ankle angles span
27.71–88.05 degrees and peak angular speed is 368.3 degrees/s (previous E/G
steady cycle: 9.69–103.31 degrees, 624.9 degrees/s). These are model-coordinate
angles, not an externally measured anatomical included angle. One principal
stance peak remains per side; no sampled admitted range violations.

All 1,538 finite local IK solves terminate successfully (maximum 48 evaluations).
Reopened final skin has no knee/ankle ROM violations; maximum joint mapping error
2.79 micrometres. Material reaches 3.95 mm below the floor. Finite root residual
RMS is 0.09184 BW/BWL and maximum normalized control is 1.7552: physical acceptance
is still unresolved. Local IK success is not Moco convergence. The selected
periodic initializer likewise is not a converged full Moco solution.

The reduced gait demand is an engineering warm-start prior using relative
`speed / sqrt(gravity * leg_length)`, not a discovered dinosaur scaling law.
It scales all leg-reference excursions together; no per-animal joint solver,
playback clamp, capacity increase, or changed anatomical stop was introduced.
Keep this limitation explicit when designing the next generalized locomotion
stage. Review walking before starting that work or resuming turning.

Final media path in the principal repository:
`game/Evidence/moco-c52b-centered-walk/review/tarbo-c52-b-revised-walk-16s.mp4`.
User approval PENDING; pause after presenting this candidate.

All 384 final H frames were inspected in sixteen chronological sheets, with
original-size release/recovery/closing-step poses. Media receipt records the
method and limits. The saved video is ready for user review; approval remains
PENDING. No active optimization or player remains.
