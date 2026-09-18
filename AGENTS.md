# Eonwild factory working rules

## Animation iteration comes first

- The primary deliverable is visible animal motion, not validation machinery.
  Work in this order: render the current walk, review it with the user, change
  the most important visible problem, and render again.
- Aim to show the first native-time preview within 15 minutes of starting an
  animation iteration. If that is blocked, explain the concrete bottleneck and
  use the fastest honest preview path. Do not spend hours building solvers,
  tests, reports, or edge-case handling before showing motion.
- Use the actual admitted animals and the shared engine from the beginning.
  Iterate contact, weight transfer, posture, timing, and smoothness on visible
  results. Unit-tested infrastructure is not a corrected animal animation.
- Expected stride belongs in animal onboarding configuration, with units and a
  clear distinction between one step and a complete same-foot stride. Record
  the source and rationale: published evidence when available, otherwise an
  explicitly labeled plausible estimate for the animal's body type. Preserve
  researched values and distinguish measurements from authored choices. The
  shared solver consumes this intent; it must report reach limitations rather
  than silently redefine the intended stride to fit a neutral-pose preference.
- Sub-millimetre contact errors, incomplete mass correction, and pending
  production checks must not block a diagnostic render or user review. Label
  what is missing or failing; do not claim that a rough preview is approved.
  If a preview omits final contact or mass corrections, say so explicitly.
- Keep diagnostic preview generation separate from production acceptance.
  Preserve production thresholds and final emitted-asset checks, but run them
  at the appropriate delivery checkpoint rather than gating every preview.
- Before adding machinery or tests, identify the observed animation problem
  it will resolve. Prefer the smallest shared-engine change that can be judged
  in the next render. Defer speculative edge cases and broad validation work
  until the visible direction has been reviewed.
- During iteration, run only focused checks needed for the current change.
  Full suites, adversarial release reviews, and Unity parity belong after a
  reviewable candidate exists. Stop at requested visual checkpoints for user
  feedback; do not keep polishing unseen motion.
- Orchestrators and implementors must prioritize producing and inspecting
  renders. Progress reports must distinguish implemented code, actual-rig
  execution, exported motion, and user-reviewed motion.

## Engine and delivery contracts

- Continue `src/eonwild_motion`; do not create another versioned toolkit.
- Read README.md, docs/FACTORY_ROADMAP.md and docs/UNITY_MOTION_CONTRACT.md.
- `build/` and `reports/` are historical experiments, never runtime imports.
- V8.2 under legacy/capsules is immutable. Do not rewrite its manifests or bytes.
- Preserve approved Run010/Sprint006/Feeding003 and walk references.
- New species differences belong in semantic rig/body/behavior data, not literal
  bone names or species branches in shared programs.
- A behavior owns its contact choreography. Grounded feeding and reverse walk
  are not airborne locomotion with extra offsets.
- Admit source geometry once. The active compiler may not depend on a prior
  animated take for timing or directions.
- Constraints follow all contact-affecting modifications. Reopen final emitted
  assets and measure them; never reuse a pre-overlay receipt.
- Candidate generation, technical validation, visual review, and Unity parity
  are distinct. BLOCKED/NOT_RUN/PENDING are truthful outcomes, not passes.
- No auto-approval, weakening thresholds, silent anchor sliding, or fabricated
  biomechanical/biological claims. Authored response is valid when labeled.
- Test deterministic replay, corruption, coordinate frames, contact transitions,
  renamed rigs and incompatible topology. A synthetic fixture is not proof of
  production transfer to another species.
- A Unity root has one final movement owner; world logic confirms bite/grip/
  damage/yield. Animation cues must not invent gameplay facts.
- Ship source, recipes, hashes, tests and native-time review media together.

## Artistic direction for animation continuation

Read the principal Eonwild repository's [animal animation artistic direction](../eonwild/docs/ANIMATION_ART_DIRECTION.md) before changing motion or presenting a new checkpoint. It records the user's coordinated walking, weight, attention, arms, jaw and review-format direction. In isolated checkouts, locate that document in the principal Eonwild repository rather than assuming the sibling path resolves. This is documentation guidance, never a runtime import. The latest user workflow instruction is direct implementation without subagents and review at bounded visual checkpoints.
