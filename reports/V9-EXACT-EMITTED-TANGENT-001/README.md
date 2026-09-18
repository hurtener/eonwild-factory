# Exact emitted tangent validation

Status: **VALIDATOR INTEGRATED; CURRENT MOTION BLOCKED.** Commit
`52e826ccd7e05dd2e82c37e889af8cf0a977c7a0` replaces the historical
three-sample quadratic acceptance estimate with derivatives of the actual glTF
LINEAR translation and shortest-path SLERP rotation channels. It evaluates
local steady loops and exact FK/LBS boundary velocities for connected clips.
The governed limits are unchanged.

Round-one commit `6370df15d26c991b9c58dbf0a62c8699b31f16fc` and the amended full
replacement `52e826c` share parent `3726cb7`; they are evidence identities,
not sequential patches. The final implementation was cherry-picked alone as
`61c7ffc99ac2c5166345c5b690328c55bce2aefd`. Independent review found and
closed fail-open handling of multiple cyclic clips, nonconstant animated scale,
missing or undersized exact handoff witnesses, and incomplete witness identity.
The narrow closure is clean.

The independently reproduced source measurements are in
`exact-emitted-reproduction.json`, SHA-256
`067985a967d586ae1005afac9c40f18cf86a149ffa8c45ed6a251620f635bb91`.
Exact local steady-loop linear mismatches are 2.282 mm/s for walk, 3.460 mm/s
for reverse walk, 47.942 mm/s for run and 70.390 mm/s for sprint, all above the
unchanged 1 mm/s limit. Adult v6 measures 1.728740 mm/s and fast recovery v3
measures 5.406219 mm/s. Both movement modes agree for each local loop. Generic
start and stop joins also remain blocked by exact world or skinned velocity
witnesses. Historical quadratic PASS values remain diagnostics only.

This change corrects measurement and fail-closed reporting. It does not modify
motion channels, rewrite packages, smooth or retime clips, enable CUBICSPLINE
playback, copy boundary poses, search phases, or weaken thresholds. Existing
visual and articulation evidence is unchanged. `continuation-plan.md` records
the remaining representation and trajectory work without authorizing it here.

The exact integration head passed 758 tests plus 21 subtests in 211.81 seconds
with real Blender 5.2.0 and Khronos glTF Validator 2.0.0-dev.3.10. The clean
full-suite receipt is `host-validation.json`, SHA-256
`59f7eacb41a2b8de76c00102144dbf57f12550e598f68324c7f8b23f44099eb6`.
Hosted CI, Unity parity and production approval remain pending.
