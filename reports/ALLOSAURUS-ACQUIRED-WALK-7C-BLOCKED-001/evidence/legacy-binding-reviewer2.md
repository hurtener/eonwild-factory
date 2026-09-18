# Legacy authored-adapter binding narrow review

Reviewed exact commit `655bd1d6048147cf1e1aa00d03512b44c2f42461`
(tree `a16bd8fd3c3f7c5d82905f9c0373d665d2afe282`, parent
`06cb58a`) read-only in
`ARC/worktrees/eonwild-legacy-authored-binding`.

Verdict: **PASS**, P0=0, P1=0, P2=0.

The two-file fix restores the historical steady-adapter binding field set
exactly.  The new mode and steady query/adapter digests are emitted only for
`transition_locomotion_time.v1`, so transition dependency authority remains
bound without changing archived grounded replay identities.

Evidence:

- `git diff --check 06cb58a..655bd1d`: PASS.
- `pytest -q tests/test_authored_material_contact.py`: 26 PASS in 25.41 s.
- Public verification of retained package
  `ARC/out/allosaurus-acquired-reference-walk-007-release-7c62723/walk`:
  integrity PASS, technical BLOCKED, visual PENDING, Unity NOT_RUN.  Exit 2 is
  the expected technical-blocked result and preserves the package's separate
  mechanical failures.
- Reviewed worker was clean at the exact commit before and after the checks.

This is a diff-only closure of the legacy binding regression.  It does not
reclassify the retained Allosaurus package as technically accepted.
