# Root adult load-acceptance round 1 — implementation

Reviewed source `94c81e7e3bb00e2e6057fd1babb183adb70ff9e3` relative to published `83aa5e5391848493c902af0c6bd4ecab6228afe6`.

Decision: no code P0/P1 found. Source implementation PASS; actual compiled geometry/continuity and rendered visual comparison remain PENDING and are required before candidate acceptance.

Root read the complete 113-line performance delta, focused tests, and both new versioned profile/recipe bindings. The three parameters are explicit, paired, finite and opt-in; absent values preserve the historical decorated-plan digest. Existing controls remain exactly equal in the successor profile. The recipe changes only its versioned metadata and performance hash; source/rig/animal/gait/contact/articulation/frame are identical and the recipe is unselected.

The carrier uses native locomotion time and existing transition gain. Its phase derives from the grounded duty factor and step period, placing zero value/velocity/acceleration at consecutive sole-support midpoints and the peak at intervening double-support midpoint. The polynomial is applied before limb resolution. The world-up pelvis displacement has the intended negative sign; positive world-lateral trunk rotation lowers the declared forward direction. Semantic spine/chest topology is validated, the existing distributed-world rotation helper is reused, and gaze still resolves afterward. No floor, stance anchor, root clock, bone scale or leg recovery control changes.

Root independently calculated the timing consequence in `body-compression-pulse-timing.json` (SHA-256 `6e158b05d1cdc4b131f9c2c87bad01a1156d8ed930d62ba409a62213850aff81`). At actual 2.284175584 m body height, the 0.01 BH/0.35-degree comparison gives 22.841756 mm peak extra compression and 0.362352 m/s2 peak added upward acceleration over the broad 1.23 s interval. A pulse confined to the 0.2952 s double-support window would have produced 6.290831 m/s2; the implementation correctly avoids that timing. These are kinematic calculations, not inferred muscle or ground forces.

Root focused verification: `tests/test_motion_performance.py tests/test_adult_load_acceptance_catalog.py` — 122 passed in 25.66 s, executed with worker source and external SSD basetemp. Full actual recipe compilation and same-camera front/side renders are in progress under the author. No visual or physical approval is inferred from these tests.
