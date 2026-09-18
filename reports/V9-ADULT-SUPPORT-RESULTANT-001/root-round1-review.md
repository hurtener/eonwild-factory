# Root support-resultant diagnostic round 1

Reviewed complete frozen head `2a985f36f987cd6c5dc07fcb053b230c60e5e31f`, implementation `0e4cfa45c192b43716fc223924cfec3e021ba9b4`, relative to published `83aa5e5`.

Decision: CHANGES REQUIRED, two P1 findings. Wait for the independent R1 before one consolidated postfix.

## P1: the claimed source binding omits consumed biomechanics data

The CLI reads `biomechanics.json` and uses its uniform scale for contact geometry and its semantic height to scale segment inertias. That file is absent from both expected and actual identity maps. Root created a package with all admitted inputs symlinked to the immutable V9 files and changed only `geometry.actual_semantic_pelvis_to_toe_plane_m` from 2.2841755838983118 to 2.741010700677974. The command succeeded and wrote a result with all recorded input identities unchanged (apart from the package location), while baseline midpoint yaw inertia changed from 10776.33858 to 10981.60438 kg m2 and the left-support forward resultant changed from 0.24849074 to 0.22798766 m. This is an actual input change that the asserted source binding misses.

Bind or independently validate every consumed biomechanics input before evaluation, retaining the exact file identity. Add a regression that changes only this input and proves rejection before output. Use the existing package identity contract where possible rather than an incomplete parallel inventory.

Proof package/result: `audits/root-support-resultant-unbound-biomechanics/package` and `result.json` (SHA-256 6dbce46b8ac81ec7ed339f81290c7c50d9c409e6f346b07393cf309f0d0ab361).

## P1: reported configurable contact assumptions are silently ignored

`engineering_model.contact_load_alternatives` is copied into the receipt, but the calculation hardcodes equal loading and 60/40 leading/trailing loading. Root supplied an assumption file changing the second double-support model to 90/10. The command succeeded, reported that 90/10 input, and still computed/emitted `leading_0.6_trailing_0.4`. The declared local COM alternatives are likewise descriptive while the model list is hardcoded.

Make numerical configuration drive the calculation, or explicitly validate/reject unsupported configurations. Do not retain one set of declared assumptions alongside a different hardcoded calculation. Add an executable configuration regression rather than testing only the standalone moment equation.

Proof inputs/result: `audits/root-support-resultant-unbound-biomechanics/load-model-90-10.json` and `load-model-result.json` (SHA-256 e5853d26ce61bd9bac382ca193eb61c70db51023f951f87ed7dd74a0c3292b3b).

## Local reporting and reproduction follow-ups

The report must keep its lateral recommendation conditional on the chosen unmeasured CoP proxy. Four mass/COM variants around one sole-support pressure proxy do not establish robustness to foot pressure distribution. The phrase “admitted semantic toe-proxy neighborhood” has no defined admitted distance criterion; report that distance and preserve existing gates instead of implying an additional authority.

The CLI's mandatory support audit is hardcoded to this task's absolute SSD path and has no override. Make the dependency available/reproducible from documented inputs, or add an explicit path argument and retain the required small audit with the report. This is a local portability fix for the new CLI; no unrelated architecture change is requested.

## Root verification

Root read the complete new module, CLI, profile, tests, and report; independently checked the tangential moment signs and frame projection; all five new analytic tests passed in 0.13 seconds. Both concrete CLI probes above executed against the frozen head. The moment equation itself had no finding. No runtime, recipe, accepted animation, source asset, or threshold was changed by this review.
