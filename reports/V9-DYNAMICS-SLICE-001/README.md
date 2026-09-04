# V9 dynamics slice — first true biomechanics pass (P0–P2)

Branch: `feat/spark-muse`. Reproduce: `PYTHONPATH=src uv run --frozen --group test
python reports/V9-DYNAMICS-SLICE-001/render_slice_evidence.py`
(+ `uv run --frozen --group test python -m pytest tests/ -q` — 130 passed).

This slice answers the adversarial review with executable code instead of
more parameters: world-frame centroidal state, ballistic COM with impulse
accounting, capacity-gated attack variants, skinned contact authority,
continuity/turning/braking, growth hysteresis and the runtime seam.

## Visual analysis (open the SVGs in a browser)

### 01 — Ballistic COM vs legacy kinematic sine (same endpoints)

![ballistic vs sine](01-ballistic-vs-kinematic.svg)

* Same launch/landing, different physics. The legacy `sin²` arc is
  symmetric: it implies phantom mid-flight forces (decelerating then
  re-accelerating the COM with no contact). The ballistic arc is
  asymmetric under gravity — the only force-free flight path.
* Numeric facts (`summary.json`): flight 0.6991 s, takeoff impulse
  (0, 4500, 0) N·s, landing impulse (−6000, 5787, 0) N·s for the
  1500 kg fixture; independent re-integration residual **0.0 m** (PASS).
* Improvement claim: the old flight arc could never be validated against
  gravity because it was never gravity. Now `verify_ballistic_samples`
  fails any tampered frame — the COM contract is enforceable.

### 02 — Contact authority: patch gap across stance and flight

![contact authority](02-contact-authority.svg)

* One loaded stance phase evaluated against the fixed floor: verdict
  **PASS**, patches within 0.2 mm of the floor, persistent-point skate
  inside thresholds.
* The gate that matters is the negative one (covered by tests, not
  plottable as a line): a loaded phase with **zero persistent ground
  points FAILs as unknown contact** instead of passing as zero-skate.
  Band-relative speeds are still reported but excluded from the verdict —
  the exact confusion the old reports flagged is now structurally
  impossible to present as evidence.

### 03 — Feasibility margins vs launch speed + growth ratios

![budgets and growth](03-budgets-and-growth.svg)

* Takeoff force margin and landing work margin both cross zero as launch
  speed rises: the engine now has a visible feasibility boundary, and
  `decide_attack_variant` falls back to `grounded_lunge` past it with the
  limiting factor named (`takeoff.force_ok` in the brutal case).
* Growth mass ratios from `m ~ L³`: juvenile 0.238 / subadult 0.551 /
  adult 1.0 / heavy 1.405 — tiers differ in more than scale because
  cadence (`1/√L`, Froude), force (`L²`) and inertia (`mL²`) scale
  independently, with hysteresis holding the tier at boundaries.

### Power-attack receipts

* Feasible running takeoff → `airborne`, physics evaluated, plan hash
  `8018253f…`. Brutal launch → `grounded_lunge`, limited by
  `takeoff.force_ok`, plan hash `e235adea…`. The behavior (committed
  forward bite) survives; the unphysical flight does not.

## What changed (source map)

* `src/eonwild_motion/dynamics/centroidal.py` — FK, segment binding,
  `M/c/P/L_c`, `p_root = c − R·c_rel`.
* `src/eonwild_motion/dynamics/ballistic.py` — ballistic plan, `J = MΔv`,
  discriminant rejection, independent verifier.
* `src/eonwild_motion/dynamics/capacity.py` — `CapacityProfile`
  (provisional), takeoff/landing assessments, friction cone, hard vs
  contracted preferred joint envelopes.
* `src/eonwild_motion/dynamics/contact_authority.py` — skinned patch
  gate, fail-closed on unknown contact.
* `src/eonwild_motion/dynamics/transition.py` — continuity packets,
  C1 blends, capture-point steps, turn/brake plans, momentum-aware
  tail/head redistribution (replaces the lagged sine where used).
* `src/eonwild_motion/dynamics/growth.py` — allometry + hysteresis tiers
  + condition-gated capacity.
* `src/eonwild_motion/dynamics/runtime.py` — event track
  (point/window/condition, `NON_INTERRUPTIBLE`), phase-preserving plan
  interpolation.
* `src/eonwild_motion/planning/power_attack.py` — the vertical slice.
* `tests/test_v9_dynamics_slice.py` — 32 tests, all passing.

## Honest limitations (not yet real life)

* Capacity numbers are first-pass engineering priors (`provisional`),
  not measured muscle — the gate logic is real, the thresholds need
  calibration against extant analogues (ratites) and trackways.
* Inertia uses `diag_normalized · M · H²`, not volumetric mesh
  segmentation — the spec's preferred provider is still ahead.
* The slice plans COM + root + contacts; whole-body IK resolving the
  remaining joints to the plan is the next step (the root solve is the
  seam it will hang from).
* No new GLB artifacts or perceptual review in this slice — that gate
  re-opens once the IK lands on top of these plans.
