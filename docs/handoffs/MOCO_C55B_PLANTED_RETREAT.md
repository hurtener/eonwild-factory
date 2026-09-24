# C55 B — planted backward retreat

Candidate pending user review. Direct implementation, no subagents.
C55 A has changes requested: excessive sideways weight transfer rolled the
supporting foot onto an edge. Preserve approved C51/C52/C53 and favorable C54 B.

## Correction

The old task forced the reduced lateral COM path while leaving sole roll soft.
B jointly solves pelvis lateral position and both complete legs, giving material
foot position and orientation priority over the reduced COM reference. The
pelvis can find a compatible position instead of making the supporting sole
tilt to satisfy a reference curve. No ankle roll joint, changed joint limits,
extra strength, shifted contact anchors or runtime foot override is added.

This is a task-space correction in the shared model pipeline, not an independently
converged balance controller. The COM reference is now soft; deviation reaches
0.3644 m. Do not claim the reduced inverted-pendulum equation remains satisfied
by the resulting trajectory. Quicker transfer and flatter feet are visually
reviewable even though full force balance and independent stability are pending.

Contact and orientation objective weights are numerical task priorities, not
scientifically measured animal parameters. The new planted_whole_body recipe
switch preserves A reproduction. Existing walking/running/turning recipes and
their assets are unchanged. The simplified sagittal ankle/MTP topology limits
the space of flat-sole lateral motions; the new result is strongly restrained
laterally, and user review should assess whether it is now too stiff.

Four backward placements remain, covering 1.316 m. Swing duration is 0.70 s
(previously 1.0), step interval 1.15 s (1.8), and intervening transfer 0.45 s
(0.8). The native 16-second capture retains rest before and after. Head stays
forward and the final step closes through placement. Tail response remains
the prior small delayed authored response to the reduced balance reference;
it is not newly claimed as a simulated mass response.

## Exact-model comparison

| Measure | C55 A | C55 B |
|---|---:|---:|
| Lateral COM span | 0.9002 m | 0.0211 m |
| Peak absolute loaded-sole roll (>0.5 BW on foot) | 13.95 deg | 0.376 deg |
| Transfer between swing intervals | 0.80 s | 0.45 s |
| Root residual RMS BW/BWL | 0.21024 | 0.06499 |
| Peak normalized actuator command | 2.0093 | 1.7064 |
| Maximum loaded-pad tangential speed | 0.266 m/s | 0.179 m/s |
| Initial coordinate error | 0 | 0 |

B has 1,538 successful limb receipt entries (769 coupled solves), maximum 37
evaluations. Maximum foot task error is 0.439 mm. All sampled model coordinate
bounds and reopened knee/ankle limits pass. Reopened skin joint mapping error
is 1.16 micrometres; minimum skin floor height is +6.41 mm (no penetration,
but do not describe all visible sole vertices as exactly touching ground).
Minimum total modeled vertical support is 0.7458 BW; there is no airborne
interval below 0.05 BW. Peak backward COM speed is 0.481 m/s.

Residual forces, commands above capacity, and sliding remain. This is a
**visual candidate with inverse-dynamics audit, not full Moco convergence**.
No physical acceptance tolerances were weakened. Seventeen focused tests pass.

Numerical source commit: 6e44eb2.
Physical model SHA256 (identical to A):
2d233dc6eea15a87a24f7246afe6557d278330003ca9cc4054394d744d77cfa8
Emitted GLB SHA256:
007085ee405d922b3cb76972c49c91f57bde3884b800108a16a58e39dcfc1874

## Reproduction and review

Factory branch codex/moco-c52-walk-turn in the preserved
worktrees/stride-hip-visual-iteration. Game branch codex/moco-c52-walk-turn-review.
Task root:
 /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526
Research: research/moco-c55b-planted-retreat.
Evidence: principal game/Evidence/moco-c55b-planted-retreat.
Unity asset: game/Assets/Eonwild/MocoRetreat55B/tarbo.glb.

Use execution.json for exact commands. Generate from archived C52 B H finite
replay, C51 support-a baseline, this retreat-plan.json; replay the returned
trajectory, retarget through the same v15 12-tail-connected mapping, build
MocoRetreat55B, and capture 384 native frames per view at 24 fps.
No full world demo or long optimization is required.

Pause at the video checkpoint. Moving-state adoption, generalized heading,
Allo transfer and curved retreat remain NOT_RUN.

## Completed visual inspection

Inspected all 768 captured frames across 32 chronological sheets (384 per view), plus enlarged quarter frames 74, 101 and 130. This was frame inspection, not direct video perception. Supporting soles stay level without the previous edge tipping; no obvious ankle snap or pose discontinuity was found. The much quieter torso and faster cadence remain subject to user judgment at native time. Both 16-second videos are pending user approval.
