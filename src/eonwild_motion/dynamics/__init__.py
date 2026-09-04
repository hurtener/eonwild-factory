"""V9 reduced-order dynamics: world-frame centroidal state from rig FK.

This package is the first executable step from kinematic engineering
trajectories toward the V9 biomechanical engine
(v9_extension/docs/05_V9_BIOMECHANICAL_ENGINE.md):

* ``centroidal`` — rigid-body FK of bound rig nodes, then whole-body mass,
  world COM, linear momentum and centroidal angular momentum.
* ``ballistic`` — ballistic whole-body COM plans with takeoff/landing
  impulse accounting and feasibility-gated fallbacks.
* ``capacity`` — first-pass actuation envelopes (force, friction, work,
  power) kept strictly separate from passive mass properties.
* ``contact_authority`` — skinned sole/toe patch as the contact authority,
  with unknown-contact fail-closed gates.
* ``transition`` — cross-clip continuity packets plus turning/braking.
* ``growth`` — allometric scaling with hysteresis-preserving tier switches.
* ``runtime`` — minimal offline-to-runtime event/ interpolation contract.

Every module is measurement/planning only: pure functions, explicit inputs,
deterministic outputs, ``ContractError`` fail-closed. Nothing here mutates
animation curves. Provenance labels travel in every receipt; absolute
dynamics claims require an absolute-enabled body profile, otherwise the
planner reports normalized bookkeeping and marks physics unevaluated.
"""

from __future__ import annotations
