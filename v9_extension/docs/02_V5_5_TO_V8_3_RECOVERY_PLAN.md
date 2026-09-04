# V5.5 → V8.3 recovery plan

## Executive decision

V8.3 must recover **capabilities, semantics, and release discipline** from V5.5 while keeping V8.2 authoritative for the approved relaxed walk. The migration is intentionally asymmetric: some V5.5 systems return nearly intact, some are reimplemented against V8.2, some become labeled legacy proxies, and some are explicitly forbidden as new authority.

## What comes back immediately

### Factory and release discipline

- immutable historical inputs and SHA pinning;
- fail-closed inventory and changed-channel accounting;
- modular strict configuration and resolved profiles;
- deterministic builds, manifests, reports, and fixed-camera evidence.

### Rig, contact, and motion foundations

- semantic bone-role resolution and 75-joint deformation integrity;
- sole/toe witness extraction, contact phases, loaded-foot locking, and terrain interfaces;
- signed leg constraints and joint-rate validation;
- pelvis translations, support-phase body balancing with contact counter-solve, V8.2 trunk stabilization, damped tail state, and bounded overlays;
- mesh-witness jaw calibration and protected quaternion-space polish.

### Clip and runtime capabilities

- neutral idle, alert idle, alert walk, start, stop, grounded bite, feeding, and threat call as P0;
- turns, uneven terrain, and upslope fixtures as P1;
- endpoint/derivative/contact-compatible authored bridges;
- phase scheduling, exact handoffs, root continuity, typed events, and animation manifests.

## What does not come back as authority

- V5.5 relaxed-walk samples over the approved V8.2 walk;
- skeleton posture proxies renamed as physical COM;
- the monolithic parameter bag as the new canonical schema;
- independent root-motion and in-place solves;
- the stale 33-degree neutral jaw value;
- one generic monster roar standing in for all call semantics;
- automatic V5.5 inverse-bind/foot-pivot mutation of the V8.2 rig;
- unproven absolute Tarbosaurus force, jump, speed, or injury numbers.

## Disposition classes

- **`authoritative_baseline`** — The later approved artifact remains the source of truth.
- **`restore_contract`** — Restore the capability and its release/behavior contract, adapting interfaces where necessary.
- **`restructure_and_restore`** — Restore the capability but replace the old package/data shape with modular typed contracts.
- **`port_and_revalidate`** — Port tooling or algorithmic ideas and prove them against the V8.2 fixture before use.
- **`reimplement_against_v8_2`** — Keep the intended behavior but rebuild/fit it around the approved V8.2 motion and contacts.
- **`recover_as_legacy_proxy`** — Use only as a clearly labeled interim proxy that V9 will replace with measured biomechanics.
- **`reimplement_from_spec`** — Re-author from the detailed semantic animation specification, not historical sampled curves.
- **`add_new_contract`** — Add a missing contract required to productize the system.
- **`reference_only`** — Retain for comparison/provenance; do not feed it directly into the release output.
- **`reject_as_authority`** — Do not treat the historical implementation, value, or semantic collapse as canonical truth.

## Recovery summary

| ID | Category | Capability | Priority | Class | Detailed mode | V8.3 target |
|---|---|---|:---:|---|---|---|
| R001 | release discipline | Immutable historical baselines | P0 | `restore_contract` | `restore_contract` | repository/versioning policy |
| R002 | release discipline | Deterministic input/output hashing | P0 | `restore_contract` | `restore_contract` | src/eonmotion/release + artifacts/v8.3/manifest.json |
| R003 | release discipline | Fail-closed package inventory | P0 | `restore_contract` | `restore_contract` | scripts/verify_v8_3_release.py |
| R004 | release discipline | Changed-versus-unchanged channel accounting | P0 | `restore_contract` | `restore_contract` | validation/channel-scope-report.json |
| R005 | configuration | Externalized reusable profile | P0 | `restructure_and_restore` | `restructure_and_restore` | profiles/ + motions/ + config/v8_3/ |
| R006 | configuration | Semantic bone-role resolution | P0 | `restore_contract` | `restore_contract` | src/eonmotion/rig/semantic_map.py |
| R007 | rig and skin | 75-joint skin order and deformation preservation | P0 | `restore_contract` | `restore_contract` | validation/skin-integrity-report.json |
| R008 | rig and skin | Foot-pivot calibration tooling | P1 | `port_and_revalidate` | `port_tooling_not_mutation` | tools/rig/inspect_and_propose_foot_pivots.py |
| R009 | contacts | Skinned-vertex sole witness extraction | P0 | `port_and_revalidate` | `port_and_revalidate` | src/eonmotion/contacts/sole_witnesses.py |
| R010 | contacts | Contact phase schedule and loaded-foot locking | P0 | `reimplement_against_v8_2` | `reimplement_against_v8_2` | src/eonmotion/contacts/contact_schedule.py |
| R011 | contacts | Metatarsal, foot, and toe articulation sequence | P0 | `reimplement_against_v8_2` | `reimplement_against_v8_2` | src/eonmotion/solve/foot_toe_solver.py |
| R012 | contacts | Terrain probing and substrate adaptation | P1 | `port_and_revalidate` | `port_and_revalidate` | src/eonmotion/contacts/terrain_adapter.py + runtime adapter |
| R013 | constraints | Signed knee/ankle and hip envelopes | P0 | `port_and_revalidate` | `port_and_revalidate` | src/eonmotion/solve/joint_constraints.py |
| R014 | walk baseline | Approved V8.2 relaxed walk | P0 | `authoritative_baseline` | `authoritative_baseline` | fixtures/v8.2/tarbosaurus_v8_2_approved.glb |
| R015 | body balance | Pelvis support shift and load response | P0 | `recover_as_legacy_proxy` | `recover_as_legacy_proxy` | src/eonmotion/legacy_balance/support_phase_balance.py |
| R016 | body balance | Exported pelvis translations in root-motion and in-place clips | P0 | `restore_contract` | `restore_behavior` | src/eonmotion/bake/world_plan_views.py |
| R017 | body balance | Hip-led leg recovery and shortened rear stance | P0 | `reimplement_from_spec` | `recover_intent_not_curve` | motions/programs/alternating_gait.yaml |
| R018 | body balance | Chest counter-rotation and neck/head stabilization | P0 | `reimplement_against_v8_2` | `merge_with_v8_2_authority` | src/eonmotion/solve/trunk_stabilization.py |
| R019 | body balance | Damped segmented tail response | P0 | `port_and_revalidate` | `port_stateful_solver_relabel_gains` | src/eonmotion/solve/tail_response.py |
| R020 | presentation | Breathing, micro-attention, forelimb inertia, and asymmetry | P0 | `restore_contract` | `restore_as_bounded_overlays` | src/eonmotion/overlays/ |
| R021 | presentation | Quaternion-space smoothing with protected contact bones | P0 | `restore_contract` | `restore_tooling` | src/eonmotion/bake/polish.py |
| R022 | jaw and mouth | Mesh-witness jaw calibration | P0 | `restore_contract` | `restore_tooling_and_resolve` | tools/rig/calibrate_jaw.py + profiles/species/tarbosaurus/jaw.yaml |
| R023 | jaw and mouth | Action-specific jaw staging | P0 | `reimplement_from_spec` | `recover_semantics_reauthor_curves` | motions/programs/bite_action.yaml + feeding_interaction.yaml + vocal_display.yaml |
| R024 | clip recovery | Neutral idle | P0 | `reimplement_from_spec` | `reimplement_from_spec` | tarbosaurus_neutral_idle V8.3 |
| R025 | clip recovery | Alert idle | P0 | `reimplement_from_spec` | `reimplement_from_spec` | tarbosaurus_alert_idle V8.3 |
| R026 | clip recovery | Alert walk | P0 | `reimplement_against_v8_2` | `reimplement_from_v8_2_gait` | tarbosaurus_alert_walk V8.3 root/in-place views |
| R027 | clip recovery | Walk start | P0 | `reimplement_from_spec` | `reimplement_from_spec` | tarbosaurus_walk_start V8.3 |
| R028 | clip recovery | Walk stop / brake to idle | P0 | `reimplement_from_spec` | `reimplement_from_spec` | tarbosaurus_walk_stop V8.3 |
| R029 | clip recovery | 35-degree left/right turns | P1 | `port_and_revalidate` | `port_program_rebuild_clips` | tarbosaurus_walk_turn V8.3 parameterized curvature |
| R030 | clip recovery | Uneven-terrain walk | P1 | `reimplement_from_spec` | `recover_as_fixture_not_unique_gait` | terrain adaptation test plan |
| R031 | clip recovery | Upslope walk | P1 | `reimplement_from_spec` | `recover_as_parameterized_fixture` | slope-conditioned walk plan |
| R032 | clip recovery | Bite attack body mechanics | P0 | `reimplement_from_spec` | `recover_intent_reimplement_from_spec` | tarbosaurus_committed_power_bite V8.3 |
| R033 | clip recovery | Head-down feeding | P0 | `reimplement_from_spec` | `recover_intent_modularize` | FEED_SEARCH / FEED_BITE / FEED_PROCESS V8.3 modules |
| R034 | clip recovery | Roar/display animation | P0 | `reimplement_from_spec` | `split_semantics_and_reauthor` | threat_call V8.3; contact_call deferred or authored separately |
| R035 | transitions | Endpoint-exact derivative-aware pose transitions | P0 | `restore_contract` | `restore_algorithm_generalize` | src/eonmotion/transitions/pose_bridge.py |
| R036 | transitions | Phase-matched loop-to-loop transitions | P0 | `restore_contract` | `restore_algorithm` | src/eonmotion/transitions/phase_match.py |
| R037 | runtime | Snapshot blend for arbitrary non-authored changes | P1 | `restore_contract` | `restore_with_constraints` | runtime/motion_controller.ts |
| R038 | runtime | Contact-phase queued authored handoff | P0 | `restore_contract` | `restore_and_expand` | runtime/motion_controller.ts |
| R039 | runtime | Exact authored sequence handoffs and root continuity offsets | P0 | `restore_contract` | `restore_contract` | runtime/action_sequence.ts |
| R040 | metadata | Animation manifest and clip taxonomy | P0 | `restore_contract` | `restore_and_version` | artifacts/v8.3/animation-manifest.v8.3.json |
| R041 | metadata | Standard event vocabulary | P0 | `add_new_contract` | `add_in_v8_3` | motions/contracts/global-animation-contract.yaml |
| R042 | validation | Skeleton-based balance proxy metrics | P0 | `restore_contract` | `restore_as_labeled_visual_metrics` | validation/posture-proxy-report.json |
| R043 | validation | Fixed-camera perceptual evidence | P0 | `restore_contract` | `restore_contract` | artifacts/v8.3/evidence/media/ |
| R044 | validation | Automated quality gates and independent review | P0 | `restore_contract` | `restore_and_strengthen` | tests/ + validation/review-records/ |
| R045 | do not restore as authority | V5.5 relaxed-walk sampled curves | P0 | `reference_only` | `reference_only` | none |
| R046 | do not restore as authority | Skeleton proxy treated as physical center of mass | P0 | `reject_as_authority` | `reject_as_authority` | none |
| R047 | do not restore as authority | Monolithic parameter bag | P0 | `reject_as_authority` | `reject_shape_keep_values_as_migration_inputs` | modular versioned configs |
| R048 | do not restore as authority | Independent root-motion and in-place generation | P0 | `reject_as_authority` | `reject_implementation_pattern` | one world-space plan with derived views |
| R049 | do not restore as authority | Old 33-degree neutral jaw profile value | P0 | `reject_as_authority` | `reject_literal_value` | resolved jaw calibration |
| R050 | do not restore as authority | Generic roar as a universal call | P0 | `reject_as_authority` | `reject_semantic_collapse` | threat_call and contact_call specs |
| R051 | do not restore as authority | Blind inverse-bind/pivot mutation | P0 | `reject_as_authority` | `reject_default_behavior` | explicit migration lane only |
| R052 | do not restore as authority | Absolute Tarbosaurus force/jump/injury numbers | P0 | `reject_as_authority` | `reject_unproven_claims` | provisional normalized capacity profile |

## Detailed recovery ledger

### R001 — Immutable historical baselines

**Category / priority:** release discipline / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/`
- `procedural-animation-toolkit(v8.2)/`

**What V5.5 proved or attempted.** Both versions are reproducible release packages with their own artifacts and evidence.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `repository/versioning policy`

**Recovery method.** Never edit historical release directories. Consume their artifacts by pinned path and SHA. Build V8.3 in a new canonical directory.

**Invariants:**

- V8.2 and V5.5 bytes remain unchanged
- all migrations are additive
- every source artifact is SHA-pinned

**Required evidence:**

- git diff proves no historical file changed
- input SHA checks fail closed

**V9 disposition.** Remain permanent regression fixtures.

### R002 — Deterministic input/output hashing

**Category / priority:** release discipline / P0

**Historical source:**

- `procedural-animation-toolkit(v8.2)/config/release.json`
- `procedural-animation-toolkit(v8.2)/scripts/verify_release.py`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/v5.5-release-validation.json`

**What V5.5 proved or attempted.** V8.2 binds the base and approved output hashes; V5.5 records a generated artifact hash and validation result.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `src/eonmotion/release + artifacts/v8.3/manifest.json`

**Recovery method.** Every V8.3 build records source/config/tool hashes, output hashes, changed-channel scope, evidence hashes, and build environment facts.

**Invariants:**

- same inputs produce same binary where deterministic mode is declared
- non-deterministic render media is separated from deterministic mechanical output

**Required evidence:**

- two clean rebuilds
- manifest inventory exactness
- hash mismatch negative test

**V9 disposition.** Use the same release protocol for every V9 plan family.

### R003 — Fail-closed package inventory

**Category / priority:** release discipline / P0

**Historical source:**

- `procedural-animation-toolkit(v8.2)/scripts/verify_release.py`

**What V5.5 proved or attempted.** V8.2 rejects forbidden cache/temp/rejected paths, oversized files, missing inventory entries, and mismatched media facts.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `scripts/verify_v8_3_release.py`

**Recovery method.** Port the inventory and forbidden-path behavior. Extend it to schemas, configs, animation specs, resolved profiles, reports, and media.

**Invariants:**

- no hidden production debt
- no rejected candidate accidentally ships
- every file is represented exactly once

**Required evidence:**

- inject a .tmp file and confirm failure
- remove an inventory entry and confirm failure
- corrupt media metadata and confirm failure

**V9 disposition.** Generalize as the canonical Eonwild factory release verifier.

### R004 — Changed-versus-unchanged channel accounting

**Category / priority:** release discipline / P0

**Historical source:**

- `procedural-animation-toolkit(v8.2)/config/release.json`
- `procedural-animation-toolkit(v8.2)/scripts/verify_release.py`

**What V5.5 proved or attempted.** V8.2 permits changes only on a declared set of chest/neck/head rotation accessors.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `validation/channel-scope-report.json`

**Recovery method.** Every V8.3 operation declares which nodes, paths, clips, and channel types it may modify. The verifier compares all other binary accessors or sampled tracks.

**Invariants:**

- no accidental root/foot/toe changes
- no silent edit to non-target clips
- no JSON/schema drift unless declared

**Required evidence:**

- byte or sample equivalence outside scope
- negative test with one forbidden accessor edit

**V9 disposition.** Required for isolated solver-layer audits in V9.

### R005 — Externalized reusable profile

**Category / priority:** configuration / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** V5.5 exposed gait, contact, terrain, tail, idle, action, jaw, and transition parameters instead of burying all values in code.

**Disposition class:** `restructure_and_restore`

**Detailed migration mode:** `restructure_and_restore`

**Target:** `profiles/ + motions/ + config/v8_3/`

**Recovery method.** Do not copy the monolithic JSON as the new canonical shape. Split it into versioned family, species, rig, contact, gait, action, transition, and release configs with units, ranges, provenance, uncertainty, and unknown-field rejection.

**Invariants:**

- generic code has no species-name branches
- units are explicit
- all references resolve fail closed
- derived values are exported

**Required evidence:**

- schema validation
- unknown field test
- missing reference test
- resolved-profile snapshot

**V9 disposition.** Becomes the BodyInstanceProfile, GrowthProfile, MotionProgram, and capacity stack.

### R006 — Semantic bone-role resolution

**Category / priority:** configuration / P0

**Historical source:**

- `assets/examples/tarbosaurus/bone-map.edited-2.yml`
- `procedural-animation-toolkit(v5.5)/inputs/tarbosaurus_bone_map.edited.yml`

**What V5.5 proved or attempted.** The rig is addressed through roles such as pelvis, chest, neck chain, foot, toes, tail, jaw, and limbs.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `src/eonmotion/rig/semantic_map.py`

**Recovery method.** Port role-based resolution, hierarchy validation, confidence/evidence fields, and required/optional role sets. Generic solvers may not reference Bone_### literals.

**Invariants:**

- same semantic contract can resolve a second digitigrade biped
- hierarchy mismatch fails
- left/right completeness is checked

**Required evidence:**

- Tarbosaurus resolution report
- synthetic second-fixture resolution
- broken-parent negative test

**V9 disposition.** Foundation of species-family reuse.

### R007 — 75-joint skin order and deformation preservation

**Category / priority:** rig and skin / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/v5.5-release-validation.json`
- `procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb`

**What V5.5 proved or attempted.** V5.5 validated 75 skin joints and rest-skinned-mesh preservation; V8.2 preserves the existing GLB structure and JSON.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `validation/skin-integrity-report.json`

**Recovery method.** V8.3 must preserve joint count/order, mesh primitives, weights, materials, morph targets, inverse-bind behavior, and rest-pose skin unless a migration is explicitly approved.

**Invariants:**

- no deformation regression
- no lost jaw/toe/tail bones
- no hidden re-rig

**Required evidence:**

- joint-order equality
- rest-skinned vertex error
- mesh/material/accessor inventory

**V9 disposition.** Required for every baked V9 output.

### R008 — Foot-pivot calibration tooling

**Category / priority:** rig and skin / P1

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/pivots.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/adjust_v5_5_foot_pivots.py`

**What V5.5 proved or attempted.** V5.5 lowered foot pivots while preserving toe-root world positions and the rest-skinned mesh; it intentionally changed inverse-bind slots 43 and 56.

**Disposition class:** `port_and_revalidate`

**Detailed migration mode:** `port_tooling_not_mutation`

**Target:** `tools/rig/inspect_and_propose_foot_pivots.py`

**Recovery method.** Keep the diagnostic and migration capability, but do not reapply V5.5 inverse-bind changes to the V8.2 artifact by default. Produce a proposal report and require explicit approval before any structural mutation.

**Invariants:**

- V8.2 rig is authoritative until a need is demonstrated
- toe world origins remain stable
- rest mesh remains equivalent

**Required evidence:**

- before/after pivot visualization
- rest-skinned error
- contact comparison
- explicit migration flag test

**V9 disposition.** A general rig-import calibration tool, separate from motion solving.

### R009 — Skinned-vertex sole witness extraction

**Category / priority:** contacts / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/sole.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** V5.5 inherits V4 vertex-level sole witnesses, thresholds, height bands, padding, contact quantiles, and minimum witness counts.

**Disposition class:** `port_and_revalidate`

**Detailed migration mode:** `port_and_revalidate`

**Target:** `src/eonmotion/contacts/sole_witnesses.py`

**Recovery method.** Recover the vertex-based contact-patch method, but resolve witness sets against the V8.2 mesh/skin and freeze the resolved witness IDs in the V8.3 profile.

**Invariants:**

- support uses patches rather than ankle points
- left/right witness sets are deterministic
- witnesses belong to the intended foot/toe region

**Required evidence:**

- witness visualization
- stable ID/hash across rebuilds
- minimum witness count
- bad-weight negative fixture

**V9 disposition.** Feeds physical contact patches and support regions in V9.

### R010 — Contact phase schedule and loaded-foot locking

**Category / priority:** contacts / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/locomotion.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** V5.5 models stance fraction, contact lead, load ramp, pre-contact, toe-off, and sole/loaded-gap gates.

**Disposition class:** `reimplement_against_v8_2`

**Detailed migration mode:** `reimplement_against_v8_2`

**Target:** `src/eonmotion/contacts/contact_schedule.py`

**Recovery method.** Recover the semantics, not the exact old phase curves. Infer or bind the approved V8.2 contact phases, expose CONTACT/LOAD/UNLOAD/TOE_OFF states, and keep loaded witnesses fixed in world space within tolerance.

**Invariants:**

- no foot skate while loaded
- no arbitrary loaded-foot yaw
- toe-off releases progressively
- markers match measured contact

**Required evidence:**

- per-foot world-space drift
- loaded yaw drift
- penetration/gap report
- event-versus-geometry consistency

**V9 disposition.** Becomes the ContactState contract used by centroidal planning.

### R011 — Metatarsal, foot, and toe articulation sequence

**Category / priority:** contacts / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/locomotion.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** V5.5 parameterizes ankle swing, foot contact angle, toe-off foot rotation, toe push, and multiple toe branches.

**Disposition class:** `reimplement_against_v8_2`

**Detailed migration mode:** `reimplement_against_v8_2`

**Target:** `src/eonmotion/solve/foot_toe_solver.py`

**Recovery method.** Use the V8.2 tracks as the reference contact behavior. Recover heel/metatarsal/toe sequencing and all toe branches through semantic roles, with contact-state-conditioned limits.

**Invariants:**

- foot is not a rigid board
- toes are last to leave
- loaded toes do not rotate freely
- all branches remain anatomically coherent

**Required evidence:**

- toe witness trajectories
- toe-off ordering
- joint/rate limits
- side and three-quarter video

**V9 disposition.** Primary pose/contact solver component.

### R012 — Terrain probing and substrate adaptation

**Category / priority:** contacts / P1

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/terrain.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/runtime/terrain-contact-adapter.ts`

**What V5.5 proved or attempted.** V5.5 inherits terrain probes, normal blending, foot roll/pitch limits, pelvis height/roll/pitch response, and uneven/slope fixtures.

**Disposition class:** `port_and_revalidate`

**Detailed migration mode:** `port_and_revalidate`

**Target:** `src/eonmotion/contacts/terrain_adapter.py + runtime adapter`

**Recovery method.** Port terrain interfaces and bounded adaptation. Separate terrain query, planned contact patch, foot orientation solve, pelvis response, and final penetration correction.

**Invariants:**

- flat-terrain V8.2 regression is unchanged when adaptation is zero
- terrain corrections never exceed declared limits
- support remains valid

**Required evidence:**

- flat no-op equivalence
- slope fixture
- uneven fixture
- edge/step negative cases

**V9 disposition.** Runtime receives a bounded version; full planning remains offline.

### R013 — Signed knee/ankle and hip envelopes

**Category / priority:** constraints / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v3/rig.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** The inherited solver uses signed anatomical bases and explicit hip, knee, and ankle limits with velocity/acceleration gates.

**Disposition class:** `port_and_revalidate`

**Detailed migration mode:** `port_and_revalidate`

**Target:** `src/eonmotion/solve/joint_constraints.py`

**Recovery method.** Recover anatomical coordinate construction, hinge sign, hard ranges, continuity, velocity, and acceleration checks. Keep V8.3 values as animation-engineering constraints, not biological certainty.

**Invariants:**

- no knee inversion
- no snapping to a straight leg
- no discontinuous quaternion sign
- rates stay bounded

**Required evidence:**

- range sweep
- joint-rate report
- broken-axis negative fixture
- visual pose grid

**V9 disposition.** Expand into hard versus preferred coupled envelopes in V9.

### R014 — Approved V8.2 relaxed walk

**Category / priority:** walk baseline / P0

**Historical source:**

- `procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb`
- `procedural-animation-toolkit(v8.2)/config/release.json`

**What V5.5 proved or attempted.** V8.2 is the approved Candidate-A walk with bounded world-relative chest balance and preserved root, pelvis, legs, feet, toes, tail, and non-walk data.

**Disposition class:** `authoritative_baseline`

**Detailed migration mode:** `authoritative_baseline`

**Target:** `fixtures/v8.2/tarbosaurus_v8_2_approved.glb`

**Recovery method.** Pin the exact SHA. V8.3 first reproduces it as compatibility mode before any whole-body balance migration. Any balanced variant must report every changed channel and prove contact/root equivalence.

**Invariants:**

- approved perceptual target is never overwritten
- compatibility output remains byte-identical where feasible
- root trajectory and contacts remain authoritative

**Required evidence:**

- exact SHA reproduction
- fixed-camera side/3Q comparison
- channel diff

**V9 disposition.** Remains the adult-walk regression for V9.

### R015 — Pelvis support shift and load response

**Category / priority:** body balance / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/README.md`

**What V5.5 proved or attempted.** V5.5 adds a principal support leg, pelvis translations, support shift, loading drop, roll/yaw/pitch, and less extreme rear stance.

**Disposition class:** `recover_as_legacy_proxy`

**Detailed migration mode:** `recover_as_legacy_proxy`

**Target:** `src/eonmotion/legacy_balance/support_phase_balance.py`

**Recovery method.** Recreate the intended behavior from measured foot phases and configured bounded gains. When the pelvis changes, counter-solve the loaded leg/foot/toe chains to preserve world contacts. Label the result a support-phase balance proxy, not physical COM.

**Invariants:**

- feet remain planted
- root displacement remains aligned
- pelvis responds to the loaded side
- no body sway is added without support reason

**Required evidence:**

- pelvis/load phase correlation
- foot drift after counter-solve
- before/after V8.2 video
- gain sweep

**V9 disposition.** Replace the proxy with segment-level COM/support solving in V9.

### R016 — Exported pelvis translations in root-motion and in-place clips

**Category / priority:** body balance / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/README.md`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/build_v5_5.py`

**What V5.5 proved or attempted.** V5.5 explicitly exports pelvis translations for locomotion and actions, including in-place views.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_behavior`

**Target:** `src/eonmotion/bake/world_plan_views.py`

**Recovery method.** Use one authoritative world-space solve. Derive root-motion and in-place views from it by factoring root displacement, never by solving the body twice.

**Invariants:**

- same relative body/contact motion in both views
- no independent phase drift
- pelvis translation is not discarded

**Required evidence:**

- root-motion versus in-place reconstruction equivalence
- contact comparison
- phase equality

**V9 disposition.** Required for V9 plan baking and runtime previews.

### R017 — Hip-led leg recovery and shortened rear stance

**Category / priority:** body balance / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/README.md`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/v5.5-release-validation.json`

**What V5.5 proved or attempted.** V5.5 reduced excessive rear reach and specified hip-led recovery with delayed knee, ankle, foot, and toe response.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `recover_intent_not_curve`

**Target:** `motions/programs/alternating_gait.yaml`

**Recovery method.** Encode the sequencing and reach limits in the gait program. Fit against the V8.2 approved leg trajectories rather than importing V5.5 samples.

**Invariants:**

- economical swing
- no piston legs
- no overextended rear foot
- toe clearance remains sufficient

**Required evidence:**

- rear reach metrics
- phase ordering
- joint velocity
- side-video review

**V9 disposition.** Continuous parameter inside growth-aware gait regimes.

### R018 — Chest counter-rotation and neck/head stabilization

**Category / priority:** body balance / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`
- `procedural-animation-toolkit(v8.2)/scripts/release_generate.py`

**What V5.5 proved or attempted.** V5.5 has spine/neck/head gains; V8.2 provides the approved bounded world-relative chest solve and neck reconstruction.

**Disposition class:** `reimplement_against_v8_2`

**Detailed migration mode:** `merge_with_v8_2_authority`

**Target:** `src/eonmotion/solve/trunk_stabilization.py`

**Recovery method.** Use V8.2 as the authoritative adult-walk reference. Productize its world-relative basis, allowed nodes, residual fractions, and limits; make gains profile-driven and clip/program-scoped.

**Invariants:**

- head is not a gimbal
- large orientation changes involve the chain
- V8.2 local-delta bounds are honored for compatibility mode

**Required evidence:**

- exact V8.2 reproduction
- gain/limit negative tests
- head world-pose comparison

**V9 disposition.** Driven by measured balance/momentum error in V9.

### R019 — Damped segmented tail response

**Category / priority:** body balance / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/locomotion.py`

**What V5.5 proved or attempted.** V5.5 exposes tail stiffness root/tip, damping, coupling, parent follow, lag, dynamic limits, COM/velocity gains, sag, and warmup.

**Disposition class:** `port_and_revalidate`

**Detailed migration mode:** `port_stateful_solver_relabel_gains`

**Target:** `src/eonmotion/solve/tail_response.py`

**Recovery method.** Recover the stateful damped chain, proximal-to-distal stiffness gradient, lag, limits, and warmup. Treat old COM gain as a tuned presentation proxy until V9 supplies real COM/momentum requests.

**Invariants:**

- tail base remains muscular and pelvis-coupled
- no endless oscillation
- state carries across transitions
- no decorative wag

**Required evidence:**

- impulse response/damping plot
- loop seam state
- turn/start/stop review
- limit checks

**V9 disposition.** Connect input torque to centroidal angular-momentum and balance requests.

### R020 — Breathing, micro-attention, forelimb inertia, and asymmetry

**Category / priority:** presentation / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/build_v5_5.py`

**What V5.5 proved or attempted.** V5.5 includes breathing, head micro-motion, arm inertia, asymmetry, and secondary residual detail.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_as_bounded_overlays`

**Target:** `src/eonmotion/overlays/`

**Recovery method.** Recover as separate seeded, aperiodic, masked overlays with per-channel authority. They may not move root, invalidate COM/support, rotate loaded feet, or erase action beats.

**Invariants:**

- forelimbs never become human running arms
- breathing is not torso bob
- micro-attention is non-rhythmic
- variation is reproducible from seed

**Required evidence:**

- mask audit
- COM/contact authority audit
- loop seam
- seed determinism
- visual repetition review

**V9 disposition.** Remain final bounded presentation layers.

### R021 — Quaternion-space smoothing with protected contact bones

**Category / priority:** presentation / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/polish.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/build_v5_5.py`

**What V5.5 proved or attempted.** V5.5 applies sign-continuous zero-phase smoothing to expressive bones while protecting root, legs, feet, toes, and jaw/action beats.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_tooling`

**Target:** `src/eonmotion/bake/polish.py`

**Recovery method.** Port smoothing as an explicit post-process with masks, loop/cyclic support, endpoint restoration, delta reports, and a no-op threshold. Never run it implicitly over contact-critical tracks.

**Invariants:**

- contacts and sharp action beats survive
- quaternion signs are continuous
- loops remain exact
- maximum change is reported

**Required evidence:**

- protected-track equality
- loop derivative test
- maximum angular delta
- action contact timing

**V9 disposition.** Reusable V9 bake refinement after constraint solve.

### R022 — Mesh-witness jaw calibration

**Category / priority:** jaw and mouth / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/jaw.py`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/animation-manifest.v5.5.json`

**What V5.5 proved or attempted.** V5.5 discovers the mandible/skull chains, samples weighted mesh witnesses, and calibrates a living-neutral close near 50 degrees for this fixture.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_tooling_and_resolve`

**Target:** `tools/rig/calibrate_jaw.py + profiles/species/tarbosaurus/jaw.yaml`

**Recovery method.** Run calibration against the V8.2 source mesh/rig and write the resolved result with witness IDs, gaps, candidate search, and uncertainty. Do not hard-code 50 degrees as a family-wide value.

**Invariants:**

- neutral mouth is closed without intersection
- jaw chain is complete
- calibration result is fixture-specific

**Required evidence:**

- witness-gap report
- mesh intersection checks
- jaw pose images
- calibration determinism

**V9 disposition.** Used by all bite, feeding, vocal, and breathing programs.

### R023 — Action-specific jaw staging

**Category / priority:** jaw and mouth / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/build_v5_5.py`

**What V5.5 proved or attempted.** V5.5 separates locomotion breathing-scale jaw motion from feeding, bite, and roar curves and ensures bite closure at contact/recovery.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `recover_semantics_reauthor_curves`

**Target:** `motions/programs/bite_action.yaml + feeding_interaction.yaml + vocal_display.yaml`

**Recovery method.** Keep the staging rules: open before arrival, maximum gape before contact, close at contact, bounded rebound, closed recovery. Re-author timing from the new animation specs rather than copying numeric curves blindly.

**Invariants:**

- no permanently open running mouth
- bite contact closes
- feeding has acquisition/processing cycles
- call jaw follows respiration

**Required evidence:**

- event-to-jaw timing
- contact closure
- neutral recovery
- range limits

**V9 disposition.** Feeds target- and resistance-aware jaw contact in V9.

### R024 — Neutral idle

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_IDLE_BREATH_V5_5`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/animation-manifest.v5.5.json`

**What V5.5 proved or attempted.** V5.5 provides a six-second breathing idle and improved asymmetric stance.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `reimplement_from_spec`

**Target:** `tarbosaurus_neutral_idle V8.3`

**Recovery method.** Generate from the global contract and animation 01 spec using V8.3 support/contact, calibrated jaw, breathing, gaze, and tail overlays. Preserve two planted feet and an asymmetric load bias.

**Invariants:**

- no frozen statue
- no rhythmic head bob
- no tail wag
- loop-safe pose and derivatives

**Required evidence:**

- support/load visualization
- loop seam
- fixed camera
- overlay authority

**V9 disposition.** Becomes a stationary_support motion program instance.

### R025 — Alert idle

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_ALERT_IDLE_V5_5`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/animation-manifest.v5.5.json`

**What V5.5 proved or attempted.** V5.5 provides an alert idle with raised head/neck and scan controls.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `reimplement_from_spec`

**Target:** `tarbosaurus_alert_idle V8.3`

**Recovery method.** Keep head-led recognition, posture elevation, ready bilateral support, optional bounded adjustment step, and low-amplitude vigilance. Remove automatic aggression or generic roar behavior.

**Invariants:**

- alert is distinct from threat
- mouth remains neutral
- body does not spin over loaded feet

**Required evidence:**

- target azimuth sweep
- adjustment-step threshold
- loop seam
- entry/exit tests

**V9 disposition.** Stationary support plus attention system.

### R026 — Alert walk

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_ALERT_WALK_V5_5_ROOTMOTION`
- `PROC_ALERT_WALK_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 provides an alert gait variant with shorter stride, raised head/neck, scan, and increased step height.

**Disposition class:** `reimplement_against_v8_2`

**Detailed migration mode:** `reimplement_from_v8_2_gait`

**Target:** `tarbosaurus_alert_walk V8.3 root/in-place views`

**Recovery method.** Use the approved V8.2 alternating support and foot trajectories as the base. Change posture, attention authority, stride/cadence envelope, and readiness without creating a separate disconnected gait.

**Invariants:**

- contact phase aligns with relaxed walk for transitions
- head target does not break balance
- no excessive high stepping

**Required evidence:**

- phase mapping
- foot contact equivalence
- walk↔alert transition
- target sweep

**V9 disposition.** Continuous attention-conditioned gait program.

### R027 — Walk start

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_START_WALK_V5_5_ROOTMOTION`
- `PROC_START_WALK_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 includes intention, load, first propulsion, and speed-building parameters.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `reimplement_from_spec`

**Target:** `tarbosaurus_walk_start V8.3`

**Recovery method.** Build support shift before foot release, shorter first step, first/second contact, and exact handoff into V8.2 walk phase. Root velocity must ramp rather than jump.

**Invariants:**

- support leg loaded before swing
- first step shorter than mature stride
- root/COM velocity continuous
- no foot slide

**Required evidence:**

- velocity curve
- contact markers
- endpoint phase/pose/velocity
- left/right launch variants

**V9 disposition.** Gait-transition planner input for V9.

### R028 — Walk stop / brake to idle

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_BRAKE_TO_IDLE_V5_5_ROOTMOTION`
- `PROC_BRAKE_TO_IDLE_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 provides braking duration, lean, shortened steps, and exact idle transitions.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `reimplement_from_spec`

**Target:** `tarbosaurus_walk_stop V8.3`

**Recovery method.** Use incoming speed to create one or more braking/support steps, pelvis continuation, torso/head lag, tail compensation, and final load settle. The root may not stop before the body resolves momentum.

**Invariants:**

- no walk→freeze
- foot placement explains deceleration
- final support is stable
- head/tail settle after pelvis

**Required evidence:**

- incoming-speed sweep
- braking distance
- contact impulses proxy
- idle handoff

**V9 disposition.** Becomes momentum-aware braking in V9.

### R029 — 35-degree left/right turns

**Category / priority:** clip recovery / P1

**Historical source:**

- `PROC_TURN_LEFT_35_V5_5_ROOTMOTION`
- `PROC_TURN_LEFT_35_V5_5_INPLACE`
- `PROC_TURN_RIGHT_35_V5_5_ROOTMOTION`
- `PROC_TURN_RIGHT_35_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 includes eased arc paths, inside/outside stride scaling, body lean, and loaded-slide limits.

**Disposition class:** `port_and_revalidate`

**Detailed migration mode:** `port_program_rebuild_clips`

**Target:** `tarbosaurus_walk_turn V8.3 parameterized curvature`

**Recovery method.** Recover the arc/path, inside/outside contact planning, and no-pivot-loaded-foot rules. Replace fixed left/right algorithms with signed curvature and generate review presets at ±35 degrees.

**Invariants:**

- inside/outside stride differ appropriately
- heading change matches root path
- tail opposes turn
- loaded foot does not twist

**Required evidence:**

- curvature sweep
- turn radius
- foot slide/yaw
- phase continuity

**V9 disposition.** Continuous turning-authority model by growth/mass.

### R030 — Uneven-terrain walk

**Category / priority:** clip recovery / P1

**Historical source:**

- `PROC_WALK_UNEVEN_TERRAIN_V5_5_ROOTMOTION`
- `PROC_WALK_UNEVEN_TERRAIN_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 contains terrain-aware walk clips and sole-collision tags.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `recover_as_fixture_not_unique_gait`

**Target:** `terrain adaptation test plan`

**Recovery method.** Do not maintain a special hand-authored uneven animation as the main solution. Reuse V8.3 walk with terrain/contact adaptation and bake a deterministic showcase fixture for validation.

**Invariants:**

- same gait identity
- terrain height/normal drive corrections
- no penetration
- pelvis response remains bounded

**Required evidence:**

- known terrain fixture
- flat equivalence
- contact patch video
- stress terrain failures

**V9 disposition.** Runtime terrain adaptation and offline contact planning.

### R031 — Upslope walk

**Category / priority:** clip recovery / P1

**Historical source:**

- `PROC_WALK_UPSLOPE_V5_5_ROOTMOTION`
- `PROC_WALK_UPSLOPE_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 contains slope-aware root/in-place examples.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `recover_as_parameterized_fixture`

**Target:** `slope-conditioned walk plan`

**Recovery method.** Generate from the common gait with slope-adjusted foot placement, pelvis height/pitch, torso bias, step clearance, effort, and root path. Preserve contact phase and avoid a separately maintained unrelated clip family.

**Invariants:**

- feet match slope
- root vertical path matches terrain
- body remains horizontally balanced
- no downhill-style braking on ascent

**Required evidence:**

- slope sweep
- joint/capacity margin
- foot penetration
- visual review

**V9 disposition.** Growth and fatigue affect slope authority.

### R032 — Bite attack body mechanics

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_BITE_ATTACK_V5_5`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/README.md`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/v5.5-release-validation.json`

**What V5.5 proved or attempted.** V5.5 changed bite delivery from head-first to rear-loaded and leg-driven, with preload before drive and full jaw closure at contact.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `recover_intent_reimplement_from_spec`

**Target:** `tarbosaurus_committed_power_bite V8.3`

**Recovery method.** Recover rear load, crouch, hindlimb extension, pelvis/torso/neck/skull force chain, contact/follow-through/recovery, and commitment windows. Do not call it an airborne attack in V8.3.

**Invariants:**

- attack begins in support/legs
- jaw opens before target
- miss cannot instantly reset
- root and feet explain lunge

**Required evidence:**

- preload-before-drive metric
- contact window
- hit/miss branch
- recovery vulnerability

**V9 disposition.** Grounded benchmark before V9 airborne power attack.

### R033 — Head-down feeding

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_EAT_LOOP_V5_5`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/README.md`

**What V5.5 proved or attempted.** V5.5 adds pelvis-and-knee descent, bounded torso pitch, neck lowering, tail counterbalance, multiple bites, and jaw processing.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `recover_intent_modularize`

**Target:** `FEED_SEARCH / FEED_BITE / FEED_PROCESS V8.3 modules`

**Recovery method.** Recover the stable stance and whole-chain lowering, but split the old repeated loop into modular search/acquire/bite/process clips or segments with target-relative carcass points.

**Invariants:**

- head does not lower via final neck bone alone
- COM/support remains valid
- jaw endpoint follows target
- feeding remains interruptible only at safe phases

**Required evidence:**

- target height sweep
- support margin proxy
- ground/carcass penetration
- modular loop variation

**V9 disposition.** Target/contact-aware feeding program.

### R034 — Roar/display animation

**Category / priority:** clip recovery / P0

**Historical source:**

- `PROC_ROAR_V5_5`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** V5.5 provides inhale, peak, release, neck/head raise, jaw opening, chest expansion, head shake, and tail brace.

**Disposition class:** `reimplement_from_spec`

**Detailed migration mode:** `split_semantics_and_reauthor`

**Target:** `threat_call V8.3; contact_call deferred or authored separately`

**Recovery method.** Recover respiratory generation, body resonance, jaw/throat/chest staging, post-call hold, and tail brace. Replace the generic monster-roar semantic with an explicit threat/territorial call. Do not reuse the same performance for long-distance contact calling.

**Invariants:**

- call begins with inhalation
- audio markers drive sound
- post-call hold waits for response
- no automatic combat outcome

**Required evidence:**

- respiration/jaw timing
- VOCAL_START/END
- throat/chest review
- threat versus contact readability

**V9 disposition.** Two vocal_display program instances: animations 27 and 28.

### R035 — Endpoint-exact derivative-aware pose transitions

**Category / priority:** transitions / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/transitions.py`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/v5.5-release-validation.json`

**What V5.5 proved or attempted.** V5.5 uses RotationSpline and Hermite translations, exact endpoint restoration, and records source/target phase metadata with near-zero endpoint errors.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_algorithm_generalize`

**Target:** `src/eonmotion/transitions/pose_bridge.py`

**Recovery method.** Port as a generic bridge generator, then add velocity/contact/tail-state validation and target-phase search. Exact pose endpoints alone are insufficient when root/COM/contact velocity is discontinuous.

**Invariants:**

- exact source/target poses
- no root pop
- derivatives remain bounded
- contact states are compatible

**Required evidence:**

- endpoint rotation/position
- velocity/acceleration mismatch
- contact state mismatch
- tail-state mismatch

**V9 disposition.** Extended into plan-state transitions.

### R036 — Phase-matched loop-to-loop transitions

**Category / priority:** transitions / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/transitions.py`

**What V5.5 proved or attempted.** V5.5 provides phase-matched minimum-jerk loop blending for relaxed↔alert walking.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_algorithm`

**Target:** `src/eonmotion/transitions/phase_match.py`

**Recovery method.** Recover phase mapping and C2 blend behavior. Match foot contacts, support foot, root velocity, and gait phase—not normalized time alone.

**Invariants:**

- no contact phase swap
- no double support glitch
- root speed remains continuous
- loop identity preserved

**Required evidence:**

- phase-map table
- foot marker comparison
- root velocity
- blend duration sweep

**V9 disposition.** Supports walk/fast-walk/run regime blending.

### R037 — Snapshot blend for arbitrary non-authored changes

**Category / priority:** runtime / P1

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/runtime/animation-controller-v5.ts`

**What V5.5 proved or attempted.** V5 runtime uses minimum-jerk snapshot blending with root offsets for arbitrary selections.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_with_constraints`

**Target:** `runtime/motion_controller.ts`

**Recovery method.** Retain as a fallback presentation bridge only when source/target states are mechanically compatible. It may not bypass authored commitment, contact, or momentum requirements.

**Invariants:**

- no teleport
- no cancellation through NON_INTERRUPTIBLE windows
- no loaded-foot crossfade failure

**Required evidence:**

- compatibility predicate tests
- forbidden transition tests
- root offset continuity

**V9 disposition.** Runtime plan selection uses compatible state manifolds.

### R038 — Contact-phase queued authored handoff

**Category / priority:** runtime / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/runtime/animation-controller-v5.ts`

**What V5.5 proved or attempted.** V5 queues authored transitions until a declared source phase is crossed.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_and_expand`

**Target:** `runtime/motion_controller.ts`

**Recovery method.** Keep source-phase scheduling, but use typed support/contact windows and an explicit latest-start deadline. Do not wait indefinitely when gameplay requires a response; choose a compatible alternate or authored emergency transition.

**Invariants:**

- action starts from a valid support phase
- player input is acknowledged predictably
- commitment rules survive

**Required evidence:**

- phase-crossing tests
- deadline/fallback tests
- left/right support selection

**V9 disposition.** Motion query selects launch/support leg from live state.

### R039 — Exact authored sequence handoffs and root continuity offsets

**Category / priority:** runtime / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/runtime/animation-controller-v5.ts`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/build_v5_5.py`

**What V5.5 proved or attempted.** V5 chains transition→action→recovery→return and computes root offsets at exact handoffs.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `runtime/action_sequence.ts`

**Recovery method.** Use explicit state packets containing pose, root/COM velocity, angular state, contacts, tail state, target commitment, and event cursor. Root offsets alone are necessary but not sufficient.

**Invariants:**

- no root reset
- events fire once
- recovery is not skipped
- return gait phase is valid

**Required evidence:**

- bite/roar/eat sequence tests
- cancel-window tests
- root/velocity continuity

**V9 disposition.** Becomes DynamicActionPlan execution.

### R040 — Animation manifest and clip taxonomy

**Category / priority:** metadata / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/animation-manifest.v5.5.json`

**What V5.5 proved or attempted.** V5.5 records clip names, durations, loops, root motion, tags, terrain/path, transition endpoints, and sequences.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_and_version`

**Target:** `artifacts/v8.3/animation-manifest.v8.3.json`

**Recovery method.** Adopt the expanded V9 AnimationSpec vocabulary: semantic ID, family, program, entry/exit, phases, point/window/condition events, procedural authority, growth response, validation, and provenance.

**Invariants:**

- manifest is generated from specs
- GLB clip facts match manifest
- runtime never infers critical semantics from string names alone

**Required evidence:**

- schema validation
- GLB cross-check
- event range/ordering
- missing semantic negative test

**V9 disposition.** Canonical runtime metadata contract.

### R041 — Standard event vocabulary

**Category / priority:** metadata / P0

**Historical source:**

- `V5.5 transition metadata`
- `project global animation contract`

**What V5.5 proved or attempted.** V5.5 has transition/source phase metadata but not the complete standardized gameplay event model.

**Disposition class:** `add_new_contract`

**Detailed migration mode:** `add_in_v8_3`

**Target:** `motions/contracts/global-animation-contract.yaml`

**Recovery method.** Emit foot contact/load/toe-off, anticipation, commit, contact begin/peak/end, recovery, jaw, head-target, loop-safe, interruption windows, vocal, water, tear, and failure conditions as typed events.

**Invariants:**

- events are measured or authored explicitly
- windows are not collapsed into points
- conditions come from interaction simulation where appropriate

**Required evidence:**

- event schema
- ordering checks
- geometry/contact correlation
- runtime dispatch test

**V9 disposition.** Core interface between animation, gameplay, audio, particles, AI, and networking.

### R042 — Skeleton-based balance proxy metrics

**Category / priority:** validation / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/v5.5-release-validation.json`
- `procedural-animation-toolkit(v5.5)/validated_result/v5.5/constrained-solve-report.json`

**What V5.5 proved or attempted.** V5.5 measures torso/head pitch, foot spread, rear reach, preload/drive, pelvis drop, feeding excursion, and explicitly says they are visual proxies, not physical COM validation.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_as_labeled_visual_metrics`

**Target:** `validation/posture-proxy-report.json`

**Recovery method.** Keep the useful posture and action-sequencing metrics with their measurement boundary clearly labeled. Never rename them COM, force, impulse, or biological validation.

**Invariants:**

- metrics remain comparable to V5.5
- labels state proxy boundary
- numeric pass cannot override poor perceptual review

**Required evidence:**

- regression report
- measurement-boundary assertion
- visual reviewer sign-off

**V9 disposition.** Superseded or supplemented by real segment COM and momentum metrics.

### R043 — Fixed-camera perceptual evidence

**Category / priority:** validation / P0

**Historical source:**

- `procedural-animation-toolkit(v8.2)/media/`
- `procedural-animation-toolkit(v5.5)/validated_result/v5/showcase/`

**What V5.5 proved or attempted.** The repository uses fixed-camera side and three-quarter media plus keyframe sheets for review.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_contract`

**Target:** `artifacts/v8.3/evidence/media/`

**Recovery method.** Generate fixed camera, identical lighting, identical playback, contact-debug, COM/support-proxy, and side-by-side baseline media. Do not accept only free-camera beauty renders.

**Invariants:**

- comparisons are reproducible
- camera does not hide foot defects
- all P0 clips receive side and 3Q review

**Required evidence:**

- media facts/hash
- frame count/duration
- review checklist
- independent reviewer verdict

**V9 disposition.** Required for every motion family and growth tier.

### R044 — Automated quality gates and independent review

**Category / priority:** validation / P0

**Historical source:**

- `procedural-animation-toolkit(v5.5)/tests/`
- `procedural-animation-toolkit(v8.2)/evidence/`

**What V5.5 proved or attempted.** Both lines include automated validation, while documentation acknowledges that animation taste remains perceptual.

**Disposition class:** `restore_contract`

**Detailed migration mode:** `restore_and_strengthen`

**Target:** `tests/ + validation/review-records/`

**Recovery method.** Separate author and reviewer roles. A numeric PASS is necessary but insufficient. Require mechanical, schema/provenance, perceptual, and scientific-honesty reviews.

**Invariants:**

- reviewers do not approve their own work
- failed perceptual review blocks release
- all waivers are explicit and temporary

**Required evidence:**

- review record schema
- author/reviewer identity check
- waiver expiry test

**V9 disposition.** Permanent factory governance.

### R045 — V5.5 relaxed-walk sampled curves

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `PROC_WALK_RELAXED_V5_5_ROOTMOTION`
- `PROC_WALK_RELAXED_V5_5_INPLACE`

**What V5.5 proved or attempted.** V5.5 has a valid historical walk, but V8.2 is the later approved walk baseline.

**Disposition class:** `reference_only`

**Detailed migration mode:** `reference_only`

**Target:** `none`

**Recovery method.** Use V5.5 only to understand body-balance intentions and regression metrics. Do not overwrite or average its leg/root/foot curves into V8.2.

**Invariants:**

- V8.2 remains perceptual and contact authority

**Required evidence:**

- test that compatibility walk uses V8.2 source SHA/track lineage

**V9 disposition.** Historical comparison only.

### R046 — Skeleton proxy treated as physical center of mass

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `V5.5 balance gains`
- `v5.5-release-validation measurementBoundary`

**What V5.5 proved or attempted.** V5.5 explicitly does not validate physical COM.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_as_authority`

**Target:** `none`

**Recovery method.** V8.3 may call the method legacy support-phase balance or posture proxy. It may not claim segment COM, angular momentum, force, or biological correctness.

**Invariants:**

- scientific honesty
- no misleading variable/report names

**Required evidence:**

- terminology scan
- report schema check

**V9 disposition.** V9 introduces actual segment mass properties and centroidal calculations.

### R047 — Monolithic parameter bag

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `tarbosaurus-v5.5.json`

**What V5.5 proved or attempted.** The old profile usefully exposed values but mixes unrelated concerns and does not consistently attach units/provenance/uncertainty.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_shape_keep_values_as_migration_inputs`

**Target:** `modular versioned configs`

**Recovery method.** Write a one-time migration loader that maps old keys to new modules and emits warnings. New code reads only the resolved modular profile.

**Invariants:**

- no duplicated conflicting setting
- all old keys accounted for
- unknown/unmapped keys fail or require explicit waiver

**Required evidence:**

- migration coverage report
- round-trip snapshot where meaningful

**V9 disposition.** Replaced by typed V9 schemas.

### R048 — Independent root-motion and in-place generation

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `paired V5.5 clip outputs`

**What V5.5 proved or attempted.** The historical pack exports both views, but future architecture should not solve them independently.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_implementation_pattern`

**Target:** `one world-space plan with derived views`

**Recovery method.** The in-place representation is a presentation/export transform over the same plan. It must preserve body-relative trajectories, phases, and events.

**Invariants:**

- no divergence between views

**Required evidence:**

- view equivalence report

**V9 disposition.** Required for plan interpolation.

### R049 — Old 33-degree neutral jaw profile value

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `tarbosaurus-v5.5.json`
- `build_v5_5.py`

**What V5.5 proved or attempted.** The profile still contains 33 degrees, while the mesh-based calibration resolves approximately 50 degrees.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_literal_value`

**Target:** `resolved jaw calibration`

**Recovery method.** Use the calibration output; preserve the old value only as provenance showing why calibration was needed.

**Invariants:**

- fixture-specific resolved neutral pose

**Required evidence:**

- assert runtime/export uses resolved calibration

**V9 disposition.** Per-instance jaw profiles.

### R050 — Generic roar as a universal call

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `PROC_ROAR_V5_5`

**What V5.5 proved or attempted.** V5.5 has one display clip, but Eonwild requires calls with distinct ecological meanings.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_semantic_collapse`

**Target:** `threat_call and contact_call specs`

**Recovery method.** Migrate body mechanics into explicit call semantics. Audio and body language must communicate intention and remain distinguishable.

**Invariants:**

- threat is not contact
- no generic victory roar

**Required evidence:**

- blind semantic review with/without audio

**V9 disposition.** Vocal-display family with compact species vocabulary.

### R051 — Blind inverse-bind/pivot mutation

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `V5.5 intentionalChangedInverseBindSlots 43 and 56`

**What V5.5 proved or attempted.** V5.5 performed a controlled rig correction that was valid for its source package.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_default_behavior`

**Target:** `explicit migration lane only`

**Recovery method.** The V8.2 artifact must not inherit those changes automatically. First prove that its pivot/contact geometry needs the same migration.

**Invariants:**

- rig integrity
- baseline preservation

**Required evidence:**

- migration disabled by default
- explicit approval required

**V9 disposition.** Rig-import tooling remains available.

### R052 — Absolute Tarbosaurus force/jump/injury numbers

**Category / priority:** do not restore as authority / P0

**Historical source:**

- `V5.5 normalized/tuned animation parameters`
- `V9 provisional profiles`

**What V5.5 proved or attempted.** Neither historical animation package establishes authoritative biological capacities.

**Disposition class:** `reject_as_authority`

**Detailed migration mode:** `reject_unproven_claims`

**Target:** `provisional normalized capacity profile`

**Recovery method.** Keep absolute dynamics disabled until geometry, mass range, actuation, and uncertainty are reviewed. V8.3 is animation-engineering, not a biological simulator.

**Invariants:**

- all provisional values are labeled
- no marketing/scientific claim from tuning values

**Required evidence:**

- provenance gate
- absolute_dynamics_enabled false

**V9 disposition.** V9 enables absolute outputs only after reviewed evidence and calibration.

## Final V8.3 recovery scope

The final compatibility-complete V8.3 line should semantically recover all 21 V5.5 base/action clips and 16 authored bridges. Delivery may be staged: P0 establishes the approved walk, states, start/stop, alert gait, grounded bite, feeding, threat call, and their handoffs; P1 adds parameterized turns, uneven terrain, and slope fixtures. “Recover” does not mean the old sampled tracks are copied. Every clip is regenerated or migrated under the new contracts, and all paths that touch the approved walk prove equivalence.

See `matrices/v8_3_clip_recovery.yaml` for exact source-to-target mapping.
