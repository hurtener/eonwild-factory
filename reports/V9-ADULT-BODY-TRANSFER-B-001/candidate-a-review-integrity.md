# Body-carrier integrity review — `9d5ae0f`

## Verdict

**CLEAN.** No P0, P1, or P2 findings in the bounded diff from
`63b87b3e140314c051c92ffa901eb407b79a986a` to
`9d5ae0fe873507e6088714727943dfd8b293b2c2`.

## Scope reviewed

- New optional `GroundedGait.pelvis_height_carrier` validation, sampling, and
  serialization behavior.
- New optional `Performance.support_directed_pelvis_carrier` validation,
  grounded-only binding, semantic-hip direction derivation, and solver order.
- The three new versioned inputs and every locked SHA-256 binding in the v4
  diagnostic recipe.
- Legacy byte preservation, transition clock/gain behavior, renamed semantic
  sides, non-axis-aligned frames, malformed values, missing lateral hip
  separation, package integrity, and source-scope boundaries.
- New tests for independence from the implementation under test rather than
  accepting only implementation-shaped values.

## Evidence

- `git diff --check` passed for the exact review range.
- The working tree was clean at exact head
  `9d5ae0fe873507e6088714727943dfd8b293b2c2` during review.
- All v4 recipe bindings independently matched their declared SHA-256 values.
- The default `None` values are omitted by `gait_parameters` and
  `decorate_plan`; the regression witnesses retain exact legacy plan hashes.
- The height carrier is periodic with matching endpoint value and derivative,
  and its sampled high/low extrema align with single-support and
  double-support stages respectively.
- The support carrier uses the admitted semantic hip geometry to determine
  lateral sign, preserves the existing yaw/chest/tail clocks, and runs before
  the existing contact-affecting limb solve.
- Focused and adjacent validation passed:
  `148 passed in 390.00s` across `test_motion_performance.py`,
  `test_adult_body_weight_transfer_catalog.py`, `test_factory.py`,
  `test_transition_support_coordination.py`,
  `test_motion_contact_adversarial.py`, and `test_package_metadata.py`.
- The compiled v4 package at
  `out/continuation-adult-v4-body-carrier-001/package` reports technical
  `PASS`; root-motion and in-place outputs, final skinned contact, cyclic
  continuity, rotation rates, solver feasibility, and articulation envelopes
  pass. Its status remains `visual_review: PENDING`, `unity_parity: NOT_RUN`,
  and `production_approved: false`.

## Review boundary

This is an integrity and code-contract review of the new bounded feature. It
does not make a visual-quality decision, a Unity parity claim, a biological or
force-simulation claim, or a promotion decision. The v4 recipe remains an
unselected diagnostic; existing documented v3 selection and bindings are not
silently changed.
