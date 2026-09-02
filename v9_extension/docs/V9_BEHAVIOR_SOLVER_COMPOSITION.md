# V9 decision: behavior-specific solvers and runtime composition

Status: agreed architectural direction, 2026-09-01. This records the user's game-engine intent; it does not claim that the runtime or physics integration exists today.

## Decision

V9 is a reusable, parameterized motion system, not a universal walking solver and not a collection of Tarbosaurus-only baked clips. Different situations select different motion programs, planning assumptions, and solver combinations. Reuse body descriptions, constraints, geometric primitives, and transition state where appropriate; do not reuse gait choreography merely because it already exists.

`WholeBodySolve` in the architecture describes a responsibility, not a requirement for one algorithm to handle every behavior. The twelve motion programs are semantic families, not a mandatory one-to-one mapping to twelve solvers.

## Motivating evidence

The feeding/tear-pull reference shows why planted feet cannot mean an immobile body. Feeding can coordinate pelvis shifts, proximal leg flexion, trunk lean/curvature, neck pulls, jaw grip changes, and tail response while retaining the same foot contacts. That differs from alternating stance/swing locomotion. The dedicated frame analysis must establish the actual sequence and timing; apparent loading or lateral movement in a side view is not a measured force or reconstructed 3D center of mass.

The current Bite R5 illustrates the failure mode: contact checks can pass while ankles compensate badly and the body remains visually rigid. It is not enough to move a mouth target and let leg IK repair the rest. The user regards its improved head/neck as a useful foundation, not a rejection of all prior work.

## Composition by situation

| Situation | Behavior-specific coordination | Potentially shared components |
|---|---|---|
| Walking and transitions | Alternating support, swing trajectories, first/last step and speed intent | Body mapping, contact geometry, bounded limb solve, transition continuity |
| Running and sprinting | Propulsion, aerial intervals, landing, recovery and regime-specific posture | Articulation primitives, body profile, contact events and capacity constraints |
| Feeding and tear/pull | Persistent support, body movement over planted feet, grip/regrip, resistance and release | Contact constraints, joint envelopes, target geometry, collision and tail response |
| Ground postures or recovery | Different support sets, lowering/rising effort or corrective steps | Body/contact descriptions and compatible state handoff |

These are examples, not a requirement to build a large solver framework before the next useful animation.

## Shared primitives versus shared behavior

- Reusable primitives may include a stable limb bend plane, bounded joint orientation, contact projection, semantic rig mapping, and continuity checks.
- Feeding must own its body coordination and contact schedule. A planted foot can retain its anchor while the pelvis and joints move; a deliberate step must release and recreate contact explicitly.
- Balance is not a command to freeze the pelvis. Conversely, plausible-looking movement does not prove physical balance.
- Tail and neck responses belong to the whole-body performance, not arbitrary motion added after solving the feet.
- Parameters belong to behavior and body profiles: timing, target height/reach, pull direction, grip intervals, articulation envelopes, and response strengths. Avoid GLB bone-name assumptions in general behavior logic.

## Runtime and physics boundary

The proposed division is:

1. Gameplay supplies intent and target context.
2. A behavior program selects phases, desired body coordination, contacts, and branches.
3. A coordinator combines compatible solver tasks, resolves competing demands, and produces a coherent pose or motor targets.
4. A game-engine adapter exchanges collision/contact information, target motion/resistance, and supported physical state with the physics engine.
5. Feedback changes subsequent behavior: continue a pull, regrip, yield, release, reposition a foot, or recover.

Physics coupling is not permission to replace authored animal performance with a passive ragdoll. Start with bounded kinematic adaptation; introduce force-driven or hybrid control only when the selected engine, body model, and interaction require it.

For each controlled channel and simulation phase, choose one final writer. Do not independently apply baked root motion, procedural root offsets, and physics-body transforms as if all three owned the same displacement. Solver tasks must resolve shared contacts and joint limits together or in an explicit priority order; blindly blending finished poses can violate both.

The runtime adapter must define units, coordinate frames, simulation timing, kinematic/dynamic authority, and transition handoff. Preserve contact anchors, velocities, grip/target state, event cursor, and tail state when switching compositions. The upstream Eonwild product constitution already selects Babylon.js + TypeScript with fixed-timestep simulation and render interpolation as its initial runtime path. This standalone motion-factory iteration does not implement that integration. The physics backend, exact adapter APIs, and solver scheduling remain future integration decisions, not a reason to reopen the existing initial runtime choice.

The interaction simulation owns whether resistance changes or a tear releases. Animation reacts to `TARGET_RESISTED`, `TARGET_YIELDED`, and `TEAR_RELEASE`; a preview may script these events, but they must not become unconditional gameplay facts tied to a baked frame. If resistance is unavailable, use an explicitly authored approximation, not a claim of simulated force.

## What travels with the GLB

### Locomotion speed and scale

User targets recorded 2026-09-02: sustained Run 18–24 km/h; Sprint 28–32 km/h.
The reviewed Run008 and Sprint004 root tracks already travel at approximately
20.24 and 30.76 km/h respectively at this rig's current metre scale. An in-place
preview removes root translation but retains cadence; it cannot show forward
speed directly. Derive speed from root displacement / elapsed seconds, then
multiply metres/second by 3.6 for km/h.

These values are animation/gameplay targets, not biological maximum-speed claims.
The generic gait uses body-normalized travel and explicit seconds. A runtime
adapter must reconcile desired world speed, model scale, stride and cadence;
do not move an avatar at an unrelated speed while replaying fixed foot contacts.
Changing the imported scale changes physical travel unless the controller
deliberately recalibrates. Never hide that mismatch by sliding planted feet.

### Feeding grip authority

The next feeding refinement distinguishes closed-jaw resisted pulling from
backward accommodation/chewing. During resistance, the oral grip witness can
serve as a world/target-space anchor while neck and body articulation move
behind it; release or target yield permits retraction. Jaw grip state and target
resistance are separate inputs, not consequences of a walking phase. Authored
preview events approximate this exchange; a physics adapter can later provide
target movement/resistance without changing the behavioral distinction.

Contact authority ends when resistance yields; it must not force the released
mouth through an unreachable Cartesian path. Preserve pose and velocity through
that handoff, then allow bounded backward retraction before jaw cycling. Test
oral anchoring during resistance separately from foot planting throughout the
body pull. A stationary bite point does not require a stationary skull or body.

### Asset, data and code

- **GLB asset:** rigged geometry and sampled animation used as a visual baseline or fallback. A baked execution is one outcome at one parameter point.
- **Companion runtime data:** semantic rig/body mapping, behavior parameters, joint envelopes, contact/event windows, transition state, and permitted procedural corrections. Keep these versioned with the asset; engine import must preserve or explicitly load them.
- **Runtime code:** behavior selection, solver composition, target/terrain adaptation, event handling, and physics integration. Do not assume importing a GLB imports these algorithms or their intent.
- **Reference evidence:** observed frame sequences and their uncertainties explain why the behavior is designed this way. Preserve them beside the implementation so future ports do not regress to a generic gait solver.

This distinction extends the existing runtime metadata contract; it does not prescribe a new GLB extension or a particular game engine.

## Immediate implementation consequence

Complete the feeding sequence analysis first, then implement the smallest feeding-specific whole-body composition that reproduces the observed coordination. Verify moving planted support and articulation from side/front/rear, followed by temporal playback. Keep the accepted locomotion foundations unchanged. Do not require a general physics runtime or a new optimization framework to make this next iteration useful.

Related: [animation system](V9_ANIMATION_SYSTEM.md), [runtime metadata](06_RUNTIME_METADATA_AND_SPEC_FORMAT.md), [architecture](V9_ARCHITECTURE.md), and [current motion iteration](../../reports/V9-CURRENT-MOTION-ITERATION.md).
