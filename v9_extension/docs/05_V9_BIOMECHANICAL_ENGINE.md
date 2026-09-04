# V9 architecture review and implementation contract

## 1. Verdict

The proposal is the correct next step. It reinforces Eonwild’s most important promise: the player inhabits an animal with weight, momentum, contacts, limits, senses, condition, and costly commitment.

One refinement is essential:

> V9 must not become “physics animates the dinosaur.” It should be **authored motion programs constrained by centroidal/contact dynamics and realized by a whole-body solver**.

That boundary protects animal performance while making support, starts, stops, turns, takeoff, flight, landing, failed attacks, feeding contacts, and growth auditable.

## 2. Repository-specific seam

The repository review was pinned to commit `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3`.

At that pin:

- V5.5 contained constrained regeneration, 37 clips, transitions, posture/balance corrections, and contact-preserving polish. Its own documentation correctly classified its balance measures as skeleton proxies—not a physical COM validation.
- V8.2 was deliberately narrow and fail-closed: a chest/neck/head transfer over a frozen V8.1 contact solution, with hierarchy, timeline, bounds, loop, unchanged-channel, and exact-SHA validation.
- No inspected `v8.3` directory existed. This specification therefore treats “8.3” as the intended composition described by the project owner: V8.2 quality + useful V5.5 body balancing + reusable configuration/productization.

V9 should preserve V8.2’s release discipline while replacing proxy balance gains with a measured body model.

## 3. Public three-layer model; internal five-stage pipeline

The public architecture remains:

1. Intent.
2. Biomechanical planner.
3. Pose/contact solver.

Internally split it into five stages.

### `MotionIntent`

Inputs include action semantic, desired speed/direction/curvature, target geometry, current support phase, COM/root velocity, style, urgency, fatigue, injury, terrain, friction, and continuation intent.

### `MotionProgram`

This is the missing bridge between intent and physics. It defines:

- performance beats and phase graph;
- contacts that must remain, release, or be created;
- lead/lag relationships between body chains;
- target/contact windows;
- interruptibility;
- timing ranges;
- conditional branches;
- stylistic controls.

A program says *what the animal means to do*. It does not hard-code every bone curve.

### `CentroidalContactPlan`

Produces:

- whole-body COM position, velocity, and acceleration;
- linear and angular momentum;
- support/contact schedule and foot placements;
- required ground-reaction forces or impulses;
- takeoff, flight, landing, and arrest landmarks;
- feasibility margins and fallback selection.

### `WholeBodySolve`

Realizes the plan using root/pelvis motion, leg/foot/toe IK, joint limits, spine/neck/head/tail compensation, target/jaw contact, collision, terrain adaptation, and exact state continuity.

### Bounded presentation overlays

Gaze, breathing, exertion, injury, fatigue, throat detail, and biological variation are applied only inside declared masks and amplitude/COM/contact authority. They may not break higher-priority contacts or momentum.

## 4. Physical segments are not bones

Do not assign one rigid-body mass to every rig bone. A rich skeleton contains deformation, jaw, toe, and helper bones that should not each become physical segments.

Use approximately 16–24 physical segments mapped to semantic bones and mesh regions. Every segment records:

```text
id
parent articulation
semantic bone and mesh membership
mass fraction
local COM definition
inertia tensor + inertia frame
contact/collision proxy
joint-limit profile
speed/acceleration/capacity envelope
provenance, status, uncertainty
```

Preferred mass-property providers:

1. segmented watertight/repaired volumetric mesh;
2. voxelized or convex-decomposed mesh;
3. capsule/ellipsoid/frustum proxy;
4. explicitly provisional authored prior.

Head and neck should not be one lump. Bite targeting and pitch/yaw inertia need at least skull/head, proximal neck, and distal neck separation. Tail should have proximal, mid, and distal segments.

## 5. Centroidal state

For segment mass `m_i`, world COM `p_i`, velocity `v_i`, inertia `I_i`, and angular velocity `ω_i`:

```text
M = Σ m_i
c = (1/M) Σ m_i p_i
P = M c_dot
L_c = Σ [ I_i ω_i + (p_i-c) × m_i(v_i-c_dot) ]
```

External dynamics:

```text
P_dot = M g + Σ f_k
L_dot_c = Σ [(r_k-c) × f_k + τ_k]
```

Direct segment summation is enough for V9. A centroidal momentum matrix can optimize later.

## 6. The COM path is not the rig-root path

In flight, gravity controls the **whole-body COM**, not necessarily the pelvis/root. The pelvis can move relative to COM as limbs tuck, neck extends, jaw opens, and tail reorients.

Plan `c_world(t)` first, then solve:

```text
p_root(t) = c_world(t) - R_root(t) * c_relative_to_root(q(t))
```

A hand-shaped parabolic pelvis curve can produce a non-ballistic true COM. Validation must measure the actual transformed segment COM.

## 7. Normalized mass is necessary but not sufficient

Total normalized mass `1.0` supports relative COM/inertia distribution and dimensionless fixtures. It does not alone determine:

- absolute launch/landing impulse;
- friction demand;
- force and torque capacity;
- injury thresholds;
- growth capability;
- braking/absorption duration.

Store normalized segment properties plus either a reviewed absolute mass range or an explicit dimensionless mode. The provisional Tarbosaurus template disables absolute dynamics.

### 7.1 Passive dynamics does not define active capacity

Mass, COM, inertia, gravity, contacts, and the requested trajectory tell the planner what forces, moments, work, power, and impulses are required. They do not tell it what the animal can produce or absorb. V9 therefore needs a separate `ActuationCapacityProfile` with at least:

```text
positive force/torque envelope
peak and sustainable power
positive-work and launch-impulse budgets
negative-work and landing/braking absorption budgets
angular/linear rate limits
fatigue, injury, pain-confidence, and growth modifiers
provenance and uncertainty
```

This profile is what turns “a jump path exists” into “this individual can launch, survive the landing, and arrest the remaining momentum.” Until those capacities are calibrated, the Tarbosaurus template may exercise normalized planning and fallback logic but may not export authoritative absolute capability claims.

### 7.2 Joint limits are coupled, load-conditioned envelopes

Do not treat a multi-axis hip, neck, spine, shoulder, or tail articulation as three independent Euler clamps. Keep two distinct boundaries:

- **Hard envelope:** bony/articular/non-interpenetration limit used as the final safety boundary.
- **Preferred envelope:** soft-tissue, load, speed, behavior, and performance range used by normal motion.

Represent these with swing-twist coordinates, a sampled orientation surface, a reviewed hinge, or another articulation-specific parameterization. Contract the preferred envelope under load, high angular rate, injury, or target resistance. Validate angular velocity and acceleration as well as pose. The included Tarbosaurus joint catalog intentionally defines the contract while leaving numerical ranges unresolved.

## 8. Balance is phase-dependent

### Quasi-static

Idle, alert, slow feeding/drinking, and settled ground postures use projected COM margin against real foot/toe/body support patches.

### Dynamic

Walk/run/start/stop/turn/attack/landing need COM velocity, planned next contact, contact timing, friction, required wrench/impulse, joint capacity, and angular momentum. A support-polygon-only rule would reject valid locomotion and approve invalid high-speed motion.

Use:

- signed support margin for quasi-static phases;
- extrapolated/capture-COM as a low-order heuristic;
- contact-wrench/impulse feasibility for dynamic actions.

When pelvis/chest/neck/tail compensation is insufficient, schedule a step. Upper-body offsets may not hide arbitrary imbalance.

## 9. Impulse and momentum continuity

Track across every clip/program boundary:

```text
position, orientation
linear velocity
angular velocity / centroidal angular momentum
support contacts and phases
tail state
target commitment
```

Takeoff and landing:

```text
J_takeoff = M(v_takeoff - v_preload)
J_land    = M(v_post - v_impact)
```

The landing planner distributes absorption timing and posture across leading leg, catch leg, pelvis, thorax, and tail. It may not invent or delete net external impulse.

## 10. Ballistic actions

For launch COM `c0`, launch velocity `v0`, and gravity `g`:

```text
c(t) = c0 + v0 t + 0.5 g t²
```

With gravity magnitude `g`, a desired COM apex rise `h_apex` gives `v_y0 = sqrt(2 g h_apex)`. For landing displacement `delta_y = y_land - y_takeoff`, solve `T = (v_y0 + sqrt(v_y0² - 2 g delta_y)) / g`, then solve predicted horizontal launch velocity from target-relative displacement divided by `T`. Reject a request when the vertical discriminant is invalid or when launch capacity, friction, angular-momentum budget, collision corridor, landing speed, or arrest distance is infeasible.

## 11. Tail behavior

The tail redistributes momentum internally and changes ground-coupled turning through contact reactions. In flight it cannot create or destroy total angular momentum.

Use a damped response, not a free sine:

```text
theta_ddot + 2*zeta*omega*theta_dot + omega²*theta
    = k * desired_balance_moment
```

Carry tail state across transitions. Proximal tail stays muscular and pelvis-coupled; distal motion is progressively delayed and damped.

## 12. Growth and allometry

Motion tiers are authored regimes, not discontinuous body states. **Resolved structural mass/weight is the primary family selector**, expressed as a neutral-condition structural-mass ratio to a reviewed reference adult when absolute mass is unavailable. Age fraction is a morphology input and scientific/biological descriptor; it must not silently stand in for weight. Condition can constrain capacity without changing the underlying ontogenetic body. Continuous traits should include mass, proportions, COM, inertia, strength/torque capacity, cadence, stride, turning authority, jump authority, landing tolerance, braking horizon, and tail frequency.

Useful configurable defaults:

```text
mass ~ length³
rotational inertia ~ mass * length²
muscle force capacity ~ length²
```

They are starting assumptions, not hard biological truth. Ontogenetic proportions and strength exponents remain profile-driven. Froude number is a useful baseline, not a universal gait generator.

Tier switching uses hysteresis and preserves gait phase, contacts, root/COM velocity, angular momentum/tail state, target commitment, and interruption state.

## 13. Ordered pose authority

Replace the unordered additive formula with:

```text
1. MotionProgram performance and phase
2. centroidal/contact plan
3. root/pelvis and primary limbs
4. foot/toe/terrain contacts
5. spine/neck/tail inertial compensation
6. target/water/carcass/jaw contacts
7. injury/fatigue/exertion within remaining capacity
8. gaze/breathing/throat/biological variation
9. final joint-limit, collision, contact, and continuity projection
```

## 14. Events are points, windows, and conditions

- Point: `L_FOOT_CONTACT`, `JAW_CLOSE`, `VOCAL_START`.
- Window: `HEAD_TARGET_WINDOW`, `CONTACT_WINDOW`, `NON_INTERRUPTIBLE`.
- Condition: `CONTACT_MISSED`, `TEAR_RELEASE`, `SUPPORT_FAILED`.

Interruptibility is phase/window state, not merely a marker. Loop safety checks pose, velocity, acceleration, contacts, and overlay state.

## 15. Offline versus runtime

Factory/offline:

- segment mass-property estimation;
- optimization/trajectory solve;
- contact schedule and foot placement;
- whole-body IK/constraint projection;
- validation renders and metrics;
- baking and metadata export.

Runtime:

- select family/regime/program;
- parameterize/interpolate compatible plans;
- preserve phase and velocity;
- bounded terrain/contact IK and overlays;
- gameplay/audio/particle event dispatch.

## 16. Determinism

Each release records inputs/config hashes, solver version, tolerances, body/growth/motion versions, seeds, environment fixture, numeric reports, fixed-camera review media, changed/unchanged channels, and approval state.

Numeric PASS is necessary, never sufficient for animation taste.
