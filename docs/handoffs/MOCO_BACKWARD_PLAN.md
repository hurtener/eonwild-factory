# Moco backward walking — planned after C54 review

User authorized planning on 2026-09-23. Implementation and media are **NOT_RUN**.
Work directly, without subagents. Preserve C51 running, C52 B H walking and the
now-approved C53 A turn. C54 is a separate neck-profile turn candidate.

## Deliverable and artistic direction

First checkpoint: Tarbo adopts its existing grounded stance, transfers weight,
takes four deliberate alternating backward steps, then settles by placement.
Produce native-time plain-stage side and quarter videos, around 10–16 seconds,
with enough rest to read initiation and the final stance. Inspect every frame
and pause. Allo, backward curves, speed changes, slopes and hit-to-retreat joins
are later transfer checks, not prerequisites to this first visible trial.

The animal remains oriented toward the thing it is retreating from. A brief
flank scan can be a separate comparison once footwork reads well; retreat does
not automatically demand a permanently sideways head. Use central attention
intents and their cumulative heading limits. Do not imply that a sideways snout
proves rearward visibility.

## Reuse, without reversing forward walking

Reuse the admitted body, segment masses, coordinate limits, contact pads,
actuator capacities, bounded joint curves, state replay and skin retargeter.
Reuse world-contact anchor evaluation and the finite start/stop clock where
appropriate. A new directional task must own its release, placement and loading.
Do not reverse a clip, negate the forward foot trajectory, or carry a forward
push-off into retreat just by setting negative speed.

Existing shared-engine references remain useful visual starting points:
`catalog/behaviors/reverse-walking-review.v2.json`,
`src/eonwild_motion/planning/reverse_walking.py`, and principal
`game/Evidence/backward-walking-study/`. C19 ordinary and C20 stronger glances
were visually accepted on both animals. These do not certify a Moco result.
Their 0.32 normal-step / 0.36 normal-speed ratios are **authored priors**, not
measured dinosaur gait. Keep their provenance if used as an initializer;
derive placement feasibility from this model rather than copying final angles.

## Contact and load choreography

1. **Adopt the real state.** Inputs include root transform/velocity, joint
   positions and velocities, and each foot's current material contact witnesses.
   First placement starts there; no snap to a symmetric canonical pose. The first
   review starts at rest, with nonzero-velocity adoption explicitly deferred.
2. **Prepare support while initiating motion.** Move the mass toward the foot
   that will remain loaded as the other unloads. Overlap pelvic accommodation,
   unloading and the first reach. Avoid a stationary waiting beat followed by a
   sudden leg action. Do not create sideways knee/ankle bending under load.
3. **Release according to retreat mechanics.** Let changing pad pressure and
   foot orientation determine release. Do not impose the forward walking heel
   rise or full trailing-leg extension. Start with low clearance and relaxed
   distal articulation; evaluate which pads actually lift first. Toe/heel roll
   ordering is an explicit modeling hypothesis until supported by reference or
   a feasible solve, not an asserted universal rule for theropods.
4. **Place behind the traveling COM.** Solve reachable placement along the
   backward path while the other foot supports the mass. Preserve a stable lane
   width; use measured geometry to avoid crossed legs or an excessive reach.
   The foot's own heading remains broadly forward. Its world motion and the
   support sequence, rather than a reversed local animation, create retreat.
5. **Receive the load.** Contact decelerates backward body motion and flexes the
   appropriate joints together. Use the unchanged distributed pad forces and
   inverse-dynamics audit to locate excessive ankle demand; do not replace it
   with a pose that merely looks planted. Retain overlapping support for the
   initial slow task; any unsupported interval is reported, not hidden.
6. **Close through a real final step.** Shorten the last placement based on
   remaining displacement/momentum, then share weight in the final stance.
   Never take half a swing and retract the leg to a stored idle footprint.
   Neck and relaxed carried tail settle continuously with the torso.

## Minimal implementation sequence

- Add a direction-aware finite support task next to the current path task.
  Keep signed travel, support schedule, contact orientation and joint goals
  separate. Use dimensioned speed/step intent in the recipe; the shared solver
  reports reach limits rather than silently shortening intent.
- Start with the documented reverse priors for a conservative slow retreat.
  Re-solve bounded whole-leg placement from the approved neutral/support state.
  Optimize/audit COM support and effort, with the actual contact law. Label a
  contact-planned initializer honestly if full dynamics have not converged.
- Render promptly on the real Tarbo. Fix the largest visible problem first:
  likely release timing, early loading, clearance, or the final placement.
  Save exact recipe, source commits, returned trajectories, physical audit,
  retarget receipt, videos and review state together.

## What to measure and what can wait

At this checkpoint measure continuous foot witnesses during loaded intervals,
joint bounds and angular-rate reversals, minimum skin height, support forces,
COM travel, root residuals and motor demand. Compare source and reopened GLB.
Review uninterrupted movement through unloading, swing, landing and stopping;
frame sheets alone can miss a perceived pause, so request native-time feedback.

Do not build a broad controller/test framework before the first retreat render.
Only add focused tests for reversed travel with stable stance anchors, limit
enforcement and preservation of the input contact state. Generalized dynamic
joins, multiple masses, terrain, obstacle awareness and production acceptance
remain distinct later gates. No invented muscle strength or loosened tolerance
to turn an initializer into a claimed physical solution.
