# V5 to V5.5 transfer guide plan

## Task

Create one repository-grounded document describing every material engine and motion change between V5 and the accepted V5.5 release, then turn those findings into a practical V8.1 comparison and selective-porting guide. V8 itself is not yet present in this repository, so the document must not speculate about its implementation.

## Files

- `docs/V5_TO_V5_5_CHANGES_AND_V8_1_TRANSFER_GUIDE.md` — canonical human-readable change record and future comparison guide.
- `reports/V5-V5-5-TRANSFER-GUIDE/plan.md` — task scope, checks, and assumptions.

## Acceptance checks

1. Reconcile the document against direct V5/V5.5 diffs for profile values, locomotion, actions, transitions, build path, and lower-foot calibration.
2. Reconcile numerical outcomes against `reports/V5-5-BALANCE-001/metrics.json`.
3. Distinguish implemented facts, perceptual observations, and future V8.1 recommendations.
4. State explicitly that V8 and the failed V6 are outside the current repository evidence.
5. Include a comparison matrix and a bounded procedure for preserving V8 while creating V8.1.
6. Run Markdown whitespace checks and an adversarial accuracy review against the source files.

## Ownership and assumptions

The factory repository has no `config/ownership.yml`. This task only adds documentation and does not alter V5, V5.5, generated GLBs, media, or runtime code. The user’s current assessment is that V8 walking is stronger, while V8 retains V5's uncorrected chest attitude and idle stance. That assessment is recorded as the V8.1 design input but cannot be independently verified until V8 is imported.
