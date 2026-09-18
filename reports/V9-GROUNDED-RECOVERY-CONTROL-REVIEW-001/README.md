# Grounded recovery control narrow review

This report records a bounded review of the reusable grounded recovery controls.
It is not the final round-two branch review or a visual acceptance result.

The reviewed implementation was
`00e33a4d5b6513c1b2166623b1e14337df16a0df`, whose parent was
`a6267b1dd2580756d76e8bcfb1d4900ac3ec61e4`. The same implementation was
integrated onto the current documentation line as
`420326f9b0c7225f25464c5b7265d6bf732c0ff9`.

The narrow review covered zero-gain pose continuity, sampling-history
independence, hard-feasibility ordering, optional-field validation and legacy
omission, arbitrary-axis and bilateral-lane assumptions, and separation of
grounded recovery from airborne motion. One P1 was found: the grounded
transition planner sampled the controlled foot but reconstructed its output
without the world-metatarsus target and recovery gain. A direct plan-level
reproduction found 353 start-transition swing-foot samples and 294
stop-transition swing-foot samples; none retained either recovery field.
The declared handoff pose remained equal because the configured interface was
in double support, but the start and stop motion silently used the old recovery
behavior.

Fix `6ce73a43ccdd91699b759d4ea2c58abbd7da8653` propagates the paired fields only
on grounded swing rows. It preserves the common world target and multiplies the
canonical C2 recovery gain by the transition's existing pitch scale. Contact,
airborne, and legacy rows continue to omit the fields. The same fix makes plan
override validation reject incomplete pairs, airborne use, and grounded-contact
use. Diff-only re-review of `420326f..6ce73a4` found no remaining P0, P1, or
reachable local P2 in those corrections.

The fix was integrated on the main development line as
`5304b1967ad350737cf7e9ee6555a5f4de9e9bff`. Its `src/eonwild_motion` tree is
byte-identical to `6ce73a4` at Git tree
`253ca09713f8a5e19c844d856b7702dd824f8082`.

The host-retained focused run at exact original commit `00e33a4` passed 129
tests in 5.13 seconds. Its receipt is
`out/continuation-world-recovery-00e33a4-focused/host-validation.json`, SHA-256
`5568d39b8c2cb5a030b2ee5904d2795a262dad21c5b0c390c0a0237ebdb40a16`; the
complete log SHA-256 recorded there is
`14a5a65e65eaf00a2108282a83c79156355526986fc023685a306dfc7f1b4530`.

The current full suite was still running when this report was written. Adult
recovery visual acceptance, biological validation, Unity validation, remote
CI, and production approval remain unresolved.
