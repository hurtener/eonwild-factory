# C54 B — coordinated walking turn

2026-09-23. Candidate **pending user review**. C53 A turning, C52 B H walking and
C51 A running remain the approved references. Direct implementation, no agents.
Backward remains planning only. Pause at this checkpoint.

## User direction and implementation

C54 A looked as though only the inside foot advanced the turn. The evaluation
confirmed alternating landing-heading increments of 18.82 degrees inside versus
0.81 outside, despite both feet reorienting between their own successive steps.
The user clarified that outward foot position belongs to straight walking; a
turn need not retain it and the outer foot may point inward relative to the body.

The shared TurnPlan now fades the straight-walk toe-out preference with angular
advance per step. During sustained curvature, the feet follow the future support
path direction. No extra anatomical inward angle is imposed. Each support
heading is chosen at its anchor and remains fixed through the task's stance;
swing interpolates toward the next placement. The world-heading component of
the inherited reference-foot correction is suppressed with the same support-
frozen blend, retaining foot pitch, roll, toe peel and recovery. Exact anatomical
IK is then solved. Left/right placement still has different arc lengths.

Inherited local torso yaw oscillation retains 20% of its amplitude during the
curve, with a smooth transition to the original straight-walk reference. This
is an explicit engineering task preference, not a biological measurement or
new muscle controller. It changes neither the physical model nor constraints.
The 45-degree profile-led gaze, chest anticipation, twelve-link tail response,
path, native cadence, start/stop and skin/rig remain preserved. All shared code
is species-agnostic; existing plans without step_steering retain old behavior.

## Measured result (exact saved model trajectory)

| Measure | C54 A | C54 B |
|---|---:|---:|
| New inside landing heading vs preceding outside landing | 18.82 deg | 10.71 deg |
| New outside landing heading vs preceding inside landing | 0.81 deg | 8.92 deg |
| Steady torso rotation speed | 1.21–21.73 deg/s | 9.41–13.51 deg/s |
| Steady inherited torso yaw | −1.60–1.58 deg | −0.33–0.31 deg |
| Maximum relative skull heading | 45.00 deg | 45.00 deg |
| Peak normalized command | 3.7980 | 3.5714 |
| Root residual RMS BW/BWL | 0.10864 | 0.14383 |

These are kinematic landing orientations, **not each foot's causal share of
steering force**. The outside foot now faces approximately 5.36 degrees into
the curve relative to the current torso at landing; the inside is 6.20 degrees.
The root residual worsens by about 32%, despite lower peak command. This is a
visual/task candidate, not improved physical convergence. Full force balance,
contact acceptance and independent forward stability remain unresolved. No
acceptance threshold, strength, spring, mass or contact parameter was weakened.
The known excessive neutral-centering neck brace remains; C54 A contains its
corrected exact-model audit. Do not reuse the older C53 spring decomposition.

All 1,538 limb IK solves terminate successfully (maximum 48 evaluations).
Task position error reaches 32.75 mm: fixed planned anchors do not prove perfect
emitted contact. Reopened skin has no knee/ankle bound violations; ankle range
25.67–88.71 degrees and peak speed 370.08 deg/s, close to A's 369.56 deg/s.
Mapping error is 3.01 micrometres; minimum skin height is −5.21 mm. Eighteen
focused tests pass, covering turn mirroring, straight-walk preservation, loaded
support witnesses, foot heading correction, attention and joint bounds.

Physical model SHA256 remains identical to A:
`2d03ef9fa341d292b2dafdaf55a95359d6e0c94dc2b6e08d63da66176a158ff8`.
Numerical source commit: `cd84594` (includes preceding `76295bf`).

## Reproduction and checkpoint

Factory worktree: task root `worktrees/stride-hip-visual-iteration`, branch
`codex/moco-c52-walk-turn`. Principal game branch:
`codex/moco-c52-walk-turn-review`. Task root:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526`.
Research: task root `research/moco-c54b-coordinated-turn`.
Durable evidence: principal `game/Evidence/moco-c54b-coordinated-turn`.
Unity asset: `game/Assets/Eonwild/MocoTurn54B/tarbo.glb`.

Use evidence execution.json for exact commands/source hashes. Generate from
C52 walk-h, C51 support-a baseline, this turn-plan.json and the central tarbo.v1
attention profile; replay the returned sequence; retarget using the v15
12-tail-connected motion set and C50 source profile. Build MocoTurn54B through
MocoPrototypeReviewBuilder. Record 384 frames per view at 24 fps, 16 seconds
native time, using the plain stage. There is no runtime foot/head patch.

The initial intermediate attempt retained limited outward bias; it was
superseded before rendering when the user clarified the direction. It is not
candidate B or an approved output. Previous evidence and accepted main survive.

All 768 rendered frames were inspected as 32 chronological sheets, with enlarged
quarter frames 135/156 and side 225/275. This is frame inspection, not direct
video perception. No obvious new ankle snap, pose discontinuity or collapsed
stance was observed. Foot rotation into the curve is clearer and body progression
is more uniform; visual smoothness remains for user judgment at native time.
Camera follows pelvis translation but keeps world orientation; side becomes
rear as the turn progresses. Plain stage preserves the same review conditions.
