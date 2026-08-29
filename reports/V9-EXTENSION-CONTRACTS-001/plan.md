# V9 Extension Contracts and Stationary-Support Slice

## Task

Implement the first executable V9 slice without creating a second engine or
touching the V8.2/V8.3 release state: strict versioned V9 contracts, two
normalized JSON body fixtures, and a generic grounded stationary-support
planner that emits deterministic centroidal/contact evidence.

The current checkout is the signed implementation head
`195a8b4707997b3309f86f8821217ed1d7e9c22a`. The V9 handoff pack is a
specification input pinned at `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3`;
its unversioned/open contracts are not imported silently.

## Intended files and ownership

The following files are in scope for this slice:

- `schemas/motion/v9/*.schema.json` — V9 contract-owned strict schemas.
- `profiles/v9/tarbosaurus-provisional.json` — normalized provisional profile;
  absolute dynamics remain disabled.
- `profiles/v9/synthetic-heavy-biped.json` — synthetic profile with reviewed
  fixture mass permitted for deterministic tests only.
- `src/eonwild_motion/contracts/v9_models.py` — typed immutable V9 models and
  canonical constants.
- `src/eonwild_motion/contracts/v9_loader.py` — strict schema/semantic loader.
- `src/eonwild_motion/contracts/v9_migration.py` — explicit migration boundary;
  no implicit aliases or field coercion.
- `src/eonwild_motion/planning/__init__.py` and
  `src/eonwild_motion/planning/stationary_support.py` — generic grounded
  planner and report writer.
- `tests/test_v9_contract_gateway.py` — positive, negative, and deterministic
  double-run coverage.
- `reports/V9-EXTENSION-CONTRACTS-001/evidence.json` — command results,
  hashes, limitations, and acceptance status.
- `reports/V9-EXTENSION-CONTRACTS-001/commands.md` and
  `reports/V9-EXTENSION-CONTRACTS-001/limitations.md` — raw command record and
  explicit non-claims for the handoff.
- `reports/V9-EXTENSION-CONTRACTS-001/review-fixes.md` — round-1 review
  findings, fixes, and final verification record.

The existing `src/eonwild_motion` package remains canonical. This slice will
not create `src/eonmotion`, modify `profiles/v8.2`, `profiles/v8.3`,
`profiles/channels`, existing assets, the CLI, or current V8.3 layer code.
`config/ownership.yml` is absent in this checkout; ownership is therefore
bounded by this task and the repository's existing package/data boundaries.

## Acceptance checks

1. Verify the exact HEAD, clean tracked/untracked status, historical V5/V8.2
   diff, and unchanged V8.2/V8.3 profile/channel/asset hashes.
2. Validate every new JSON document against a strict Draft 2020-12 schema.
3. Reject missing/unknown schema fields, unknown properties, stale family or
   axis aliases, ambiguous units, cross-document coordinate mismatches,
   airborne stationary intents, and contradictory absolute-dynamics flags.
4. Resolve both body fixtures through identical generic planner code; no
   species-specific branch is permitted.
5. Produce a grounded plan with normalized COM, loaded contacts, support
   weights, deterministic plan hash, and evidence hash. Provisional
   Tarbosaurus output must remain explicitly non-absolute.
6. Run the focused V9 tests and the existing 29-test regression suite (52
   tests: 23 focused plus 29 legacy) with no skipped tests. Run a
   deterministic two-call hash comparison.
7. Record commands, exact hashes, scope, and limitations in `evidence.json`.

## Unresolved assumptions and boundaries

- V9 canonical axes for this slice are right-handed, Y-up, forward `-Z`, with
  metres, seconds, and kilograms explicitly declared. The current V8 rig's
  forward `X` and the pack's `+Y` spelling are stale aliases and fail closed.
- Canonical V9 family identity is `heavy_predatory_biped`; the current V8
  `heavy-predatory-biped` spelling is not silently normalized.
- Tarbosaurus mass is normalized only. Its fixture cannot claim absolute
  dynamics, forces, impulses, or airborne feasibility.
- The synthetic fixture is a deterministic contract/algorithm fixture, not a
  scientific animal model.
- Stationary support proves contract composition and deterministic COM/contact
  bookkeeping only. It does not prove a whole-body solve, baked animation,
  runtime integration, V8.3 completion, or V9 readiness.
- The pack's open decisions (joint/force tolerances, foot pivot, runtime
  language boundary, event embedding, and real second-fixture validation)
  remain outside this slice.
