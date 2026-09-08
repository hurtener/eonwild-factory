# Adult sagittal response review, round 1

- Reviewed head: `7e90292c4bd92c35bd40906537371d072a4c2899`
- Reviewed implementation: `3e012cd`
- Diff base: `3726cb7fe4e620745f83d1e5ea7499561a1191ae`
- Scope: only the new support-timed sagittal carrier, its profile/recipe, and focused tests.
- Result: **CLEAN** — no P0, P1, or P2 finding.

## Mechanics and contracts checked

- `_support_timed_sagittal_pulse` derives from the declared `same_foot_cycle_s` and duty factor. It is `-gain*cos(2π*(phase/step-duty))`: positive at the declared double-support midpoint and negative at either single-support midpoint. The regression checks both extrema, zero crossings, periodicity, and first/second finite-difference repeatability.
- Performance validation requires all four sagittal amplitudes when the opt-in flag is true, rejects them otherwise, validates finite strict booleans and bounded amplitudes, and rejects an airborne plan.
- `_sagittal_body_chains` uses semantic roles, checks types/nonempty lists/duplicates/disjointness and confirms actual parent topology for pelvis→spine→chest→neck→head and pelvis→tail. The actual adult rig admitted trunk nodes `37..32`, neck `31..27`, and tail `72..64` with the expected parents.
- World-axis deltas are sequenced after the existing yaw/roll/tail centering operations. The pitch test observes accumulated world rotations on the actual source rig, and the serialized-GLB test observes the authored pelvis/chest/neck/head/tail response after the limb/contact solve.
- Omitted optional controls preserve the existing fixed legacy plan and decorated-plan hashes; profile v5 and recipe v6 retain v5 gait, source, rig, animal, contacts, articulation, axes, and lateral controls. Only the opt-in sagittal fields are added.

## Targeted evidence

`uv run --frozen --group test pytest tests/test_motion_performance.py tests/test_adult_body_weight_transfer_catalog.py -q`: **79 passed**.

No rendering, source mutation, or historical A/B reopening occurred during this review.
