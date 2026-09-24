# C57 — connected walking, running and retreat

User approved C56 visually and authorized the next transition checkpoint,
explicitly adding running to exercise different generator modes. Work directly,
without subagents. Preserve C51 running, C52 B H walking and C56 retreat originals.
No main merge or automatic visual approval.

## Scope and architecture

The new shared handoff utilities live in `src/eonwild_motion/solve/moco_handoff.py`.
`StateCarry` reconciles joint/root position, velocity and acceleration with a
quintic correction. Joint corrections operate inside the admitted bounded latent
coordinates; root travel correction accumulates displacement instead of pulling
the animal back to an incoming clip origin. `FootCarry` retains each inherited
support correction until release, changes placement in swing, and holds future
footprints during support. Future placements anticipate the incoming support
interval. Vertical pelvis correction is never added to a new ground anchor.

`tools/sequence_moco_connected.py` selects a compatible support phase, adopts the
outgoing state and foot transforms, and resolves pelvis/both-leg IK under the
same anatomical bounds. `tools/refine_moco_connected.py` uses C56's shared finite
whole-body optimizer across the two running handoffs. All admitted coordinates,
including torso, neck and twelve tail links, participate in that refinement.
The physical model, forces and capacities remain those of C56, throughout.
There is no animal-specific solver branch or runtime motion correction.

This checkpoint deliberately uses the approved *saved trajectories as warm
references* for an offline integration experiment. It is not a new physical
prediction of the three gaits, production geometry admission, or a real-time
controller that accepts arbitrary gameplay state. C2 inertial state carry is
exact at its analytic boundary; subsequent IK, final interpolation and finite
optimization must be judged from the final emitted motion, not that property
alone. No exact contact or momentum conservation is implied.

Running is expanded through the saved half-stride symmetry with its native
clock. Walking and retreat retain their native clocks. No slow-motion video or
reversed forward gait is used. Phase selection uses consistent contact thresholds
and avoids adopting an airborne foot immediately before its touchdown.

## Sequence

Approximately 28 seconds rather than squeezing the added run into sixteen:

1. Rest into normal forward walking.
2. Walk into running, with a sustained running interval and airborne support.
3. Return to walking and brake into the actual resulting stance.
4. Four backward placements using the approved C56 reference.
5. Stop, then resume forward walking from that stance.
6. Finish with a walking stop.

Exact phase choices and native intervals are stored in `sequence-receipt.json`.
One final exported source owns root motion. Unity only plays the saved trajectory.

## Internal failures and correction

Early A–E numerical sketches are rejected, not review candidates. They exposed
inconsistent support thresholds, too little swing time for an incoming placement,
a discontinuous correction at a later release, vertical pelvis correction leaking
into ground anchors, and angle-limit artifacts from applying physical-space
inertial corrections near a joint stop. These were corrected in shared handoff
logic. The compatible-phase seed reduced worst foot-task mismatch from ~0.88 m
to ~5 mm. This is IK task error, not a claim of zero material slip.

The first internal Unity capture covers the walk/run/braking section only and
is diagnostic. Final delivery requires the complete side and quarter recordings,
all captured frames inspected, final replay and reopened skin audit, and an
explicit PENDING user-review receipt. Do not promote an intermediate preview.

## Reproduction and limits

Factory source: `d6705a2` (shared handoff, refinement and duration-aware replay).
Working research directory:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c57-connected-gaits`.
Factory branch `codex/moco-c52-walk-turn`; game branch
`codex/moco-c52-walk-turn-review`.

The bounded refinement uses five optimizer evaluations over 4.5–9.6 seconds.
It is not a full Moco solve. Force and contact residuals remain measured limits,
not supplied by hidden actuators or waived acceptance thresholds. Existing model
capacity estimates do not become measured dinosaur strength through this work.
Replay preserves at least 48 samples/second for longer finite sequences instead
of reducing every sequence to the old fixed 769-point sixteen-second grid.

Cross-animal transfer, arbitrary state adoption in Unity, turning/terrain,
collision interruption and independent forward-dynamics stability remain NOT_RUN.
Pause after the complete visual checkpoint.

## Rejected numerical candidate H

Exact C56 model hash remains
`2d233dc6eea15a87a24f7246afe6557d278330003ca9cc4054394d744d77cfa8`.
Five bounded evaluations hit their limit: no convergence claim. Global root
residual RMS falls from 0.6494 to 0.4516 BW/BWL, and peak normalized command
from 17.5267 to 12.7815. These errors are substantial and physical acceptance
is **FAILING**, despite the improved visual integration. They are not comparable
to a verified stable controller and must not be silently treated as a pass.

All dense sampled anatomical bounds pass, as do reopened knee/ankle limits.
The skin reaches 8.11 mm below the nominal floor at its worst sample; modeled
contact pads and rendered skin remain imperfectly matched. Peak ankle speeds
are 594/625 degrees per second, so handoff recovery sharpness requires explicit
visual review. Sustained-run samples retain ~5.3% time below 0.05 BW total
support. This is measured replay of the existing running reference, not a new
biological airborne-duration estimate.

Rejected H GLB SHA256:
`e0a7a0cf8d07ab355503beab8637d98e10aa6bbd0b0216726220ebf8619464be`.
Duration is 27.8125 seconds. Capture 668 frames per view at native 24 fps
(last sampled pose is before the source endpoint; no loop reset is captured).
Twenty-four focused checks pass. Final visual review is still PENDING.


## Final review candidate I

H reduced force residuals but visibly dipped the tail too far during the
walk/run changes. It was rejected before user delivery. I retains H as a
numerical warm start, then tightens tail coefficient search radii to 0.05
(common other-coordinate radius 2). This limits deviation from the carried
approved tail reference, not biological range of motion. All tail coordinates
remain active. No model capacity, contact mechanics or acceptance limit changed.

Source commit for this shared trust-region option and its focused checks:
`4dc5c4d`; the equivalent inline implementation was used during generation,
then extracted without numerical changes into a tested helper. G/H source
remains `d6705a2`. Both recipes and warm-start coefficients are archived.

Three additional bounded evaluations hit their limit: **not convergence**.
I root residual RMS is 0.45206 BW/BWL, peak normalized command 16.5581.
Physical acceptance remains **FAILING**. The large transition residuals are
worse than the isolated approved C56 retreat; visual success must not hide
that integration limitation. This is a motion handoff prototype.

Dense sampled anatomical bounds and reopened knee/ankle bounds pass.
Minimum skin floor height is -8.20 mm. Peak ankle rates remain 594/625
degrees/s, so a brief sharp recovery remains a visual review focus.
The exported I GLB SHA256 is
`661d36b642b585eb78e3aca1047aa2be317fd8bc79c69d32c0f068654ef03859`.
Twenty-five focused checks pass. Final side and quarter captures each
contain 668 native-time frames. User approval remains PENDING.


## Saved visual checkpoint

I side and quarter recordings are complete: 668 frames each, native 24 fps.
Every captured frame was inspected in chronological contact sheets, with enlarged
transition witnesses. This is framewise inspection, not direct video perception.
No visible pose reset was found, H's excessive tail dip is corrected, and
retreat/forward restart retain body carriage. Brief ankle recovery sharpness
around the run handoffs remains a review point. User review **PENDING**.

Game evidence: `game/Evidence/moco-c57-connected-gaits/review-side/tarbo-c57-i-side.mp4`
and `review-quarter/tarbo-c57-i-quarter.mp4`. The full recipes, model,
unscaled trajectories, audits, rejected H witnesses and exact source hashes
are archived alongside them. Stop here for user feedback.
