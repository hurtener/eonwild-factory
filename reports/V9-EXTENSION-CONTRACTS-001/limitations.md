# Scope and limitations

- This slice proves strict JSON contract composition and deterministic grounded
  contact/COM bookkeeping only. It is not a whole-body solver, animation
  baker, runtime integration, or V9 release.
- The Tarbosaurus profile uses normalized mass fractions and explicitly keeps
  absolute dynamics disabled. No absolute force, impulse, inertia, or airborne
  claim is made for it.
- The synthetic heavy-biped profile is an algorithm fixture, not a scientific
  body model or validation of animal biomechanics.
- The planner emits a grounded stationary-support plan only. It does not
  modify or consume the current V8.3 GLB/layers/channel state and does not wire
  the CLI.
- No V9 animation catalog, 29 baked clips, transition runtime, growth solver,
  airborne feasibility, perceptual media, or second real biological fixture is
  claimed.
- The handoff pack remains specification-only. Its legacy schema IDs, missing
  version roots, snake_case field shape, family/axis aliases, and open schema
  objects require an explicit reviewed migration before import.
- Existing V8.3 evidence remains a working-candidate machine PASS with visual
  approval pending; this slice does not promote it or change stable channel
  state.

## Review boundary

- Round-1 review fixes are recorded in `review-fixes.md`: absolute dynamics
  require synthetic fixture provenance with scientific claims disabled;
  non-finite values and exponent overflow fail closed; body-frame COM and
  acyclic topology are explicit; and the synthetic body remains fictional.
- The evidence manifest hashes and semantically binds the intent, program,
  body, and both named contact source documents to the embedded plan IDs,
  contact identities/states, and contact payloads. It is an input-integrity
  record, not a claim that the contact centroid lies inside a physically
  feasible support region.
- The planner consumes already-resolved body-frame segment COM points and keeps
  inertia typed for later stages. It does not solve transforms, contacts,
  support polygons, friction, forces, momentum, or actuator feasibility.
