# PROCEDURAL-ENGINE-V8-3 — channel P1 fix plan

## Scope

Close only the two technical-review findings in the stable promotion path:

1. derive the next stable manifest and artifact references from the installed
   promoted destination and validate their exact hashes and bindings;
2. make channel state and immutable history installation rollback-safe as one
   transition, including controlled filesystem-failure injection and retry.

## Intended files

- `src/eonwild_motion/contracts/resolve.py`
- `src/eonwild_motion/pipeline/channels.py`
- `src/eonwild_motion/pipeline/promote.py`
- `tests/test_channels.py`
- `tests/test_integration.py`
- this task's summary/evidence documentation

The reviewer-owned deletion of the original plan and untracked review report,
all V8.2/legacy bytes, existing reviewed reports, profiles, and motion layers
are outside this patch and will be preserved.

## Acceptance checks

- A distinct repository-owned promotion destination becomes the exact stable
  manifest/artifact source and resolves successfully afterward.
- Stable manifest contents bind the promoted artifact, profile, and hashes.
- Failures injected at each state/history install boundary restore exact prior
  state, leave no new history or destination, and permit an identical retry.
- Existing destination/history no-overwrite gates remain fail-closed.
- Focused channel/integration checks and the complete test suite pass.
- V8.2 artifact/profile/release hashes and legacy/review trees remain unchanged.

## Assumptions

- `releases/` is the canonical repository-owned immutable release area defined
  by the accepted procedural-engine architecture.
- A stable update is valid only for a promotion destination strictly below
  that directory; ordinary temporary promotions may still target external
  paths when `--update-stable` is not requested.
