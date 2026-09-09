# Shared locomotion v2 narrow P1 closure

Reviewed exact commit `58c4f763d3bb1cabd333c4e27ee7a0aabc39d3f3`, tree `344736c0ef6d4d5cdeb585546b886b4e8b99368b`, relative to parent `eca89c3e43a3c6e5740b37f42327bcb54dc2dd84`. This was a narrow diff-only closure of the two P1 groups reported against `996e4b4`; it was not a third whole-stage review.

Result: **CLEAN — P0 0, P1 0, P2 0** within this closure scope.

- Package verification now reloads and hash-checks the locked source, rig, animal, contact and articulation snapshots; repeats source calibration and scaling; recreates the source-owned touchdown observations; and requires exact equality with the retained derived geometry before resolving the gait. The prior altered-right-coordinate path is covered by `test_v2_provenance_remeasures_touchdown_geometry_from_source`, which rejects with `source authority`.
- Generic v2 admission now excludes airborne gait and additionally rejects an airborne choreography profile until the separately reviewed recovery provider exists.
- The shared response path derives semantic lateral sign from the actual bilateral hip geometry, applies that sign to sway/yaw/tail response, and bypasses the legacy support-timed axial carrier when a resolved response state owns the motion. The focused pose test exercises a real semantic left-support direction and asserts the old carrier is not called.

Focused exact-head checks: `tests/test_motion_set_v2.py` plus `tests/test_locomotion_regime_response.py`: **25 passed in 3.53 s**. `git diff --check eca89c3..58c4f76`: PASS. The reviewed worktree was clean and remained unmodified.

This closure does not admit airborne v2, approve an Allosaurus motion, or replace final package verification and native review.
