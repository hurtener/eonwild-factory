# Final mechanics review — 3219d65d66f4408e1eaf05d4eccec39409b474e1

Reviewed against `origin/main` `712708652b1035526b38d06fa7d487fe3c919117`.

## P1 — Grounded plans can pass an articulation profile without sampling swing

- **Paths:** `src/eonwild_motion/planning/grounded_gait.py:178-196`, `src/eonwild_motion/factory/quality.py:66-123`, and `src/eonwild_motion/factory/compiler.py:314-318`.
- **Trigger:** `GroundedGait(step_period_s=0.06, duty_factor=0.999, cycles=1, sample_hz=24)` is accepted by the public profile validator. Its 0.12 s plan has four samples, all double support. It contains no release/swing sample or swing articulation evidence.
- **Evidence:** On the frozen head, using the admitted adult source, its bound articulation profile, and the ordinary grounded-to-solver adapter, the reopened final articulation gate returned `PASS` with `phase_sample_counts={"support": 8, "swing": 0}` and `observed_degrees["swing"]` all `null`; the solver also reported zero hard-envelope violation. `emitted_articulation_envelopes()` returns PASS based only on hard violations and never rejects an empty phase, and `technical_status` consumes that PASS.
- **Impact:** A future allowed grounded recipe can be labeled as a technically accepted alternating gait and as having passed support/swing articulation guardrails without ever emitting or measuring a swing. This is a fail-open coverage gap; it does not alter the current adult-v3 result, whose package reports 370 support and 224 swing samples.
- **Recommendation:** Make `build_grounded_plan()` inject each per-leg toe-off and touchdown boundary (and, where needed, an interior swing witness), then make final plan/articulation validation require both support and swing samples for each cyclic grounded gait. Add a regression for the trigger above and require the compiled gate to be BLOCKED if either phase is absent.

## Scope and non-findings

- No additional P0 or P2 mechanics finding identified in the frozen branch.
- The adult PIN 552-1 package preserves its evidence boundary: uniform geometry scaling is source-hash-bound; morphology remains `UNVERIFIED`; force-aware solving, contact-force distribution, segment inertia, stress, and biological validation remain explicitly not implemented/evaluated.
- The known sprint direct-join result remains the documented `BLOCKED` condition, not a new finding.
- Final-suite JUnit evidence for this exact head records 682 tests, 0 failures, 0 errors, 0 skipped in 218.194 s. It does not cover the P1 trigger above.

