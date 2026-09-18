# Neutral jaw round 1 — reviewer 1

Exact frozen implementation `b13efbdc48e174b2c7d9568fe61d086967cef5c6`, base `26ec06837cd03d59bd03d6bf948ae6e7d8cf4212`. Scope: this six-file jaw behavior/calibration diff. Independent focused run: `tests/test_neutral_jaw_calibration.py tests/test_phase_local_solved_pose.py`, **19 passed in 32.57 s**. The raw/scaled source reopens a positive sampled gap; measured influence is confined to the lower-jaw channel in the provided tests. No code edits by reviewer 1.

Decision: changes required, two P1 findings and one local P2.

## P1 — neutral jaw posture must survive zero locomotion gain

`solve/jaw_response.py:268` calculates `gain * (breathing_gape_degrees - neutral_close_degrees)`. A constant neutral calibration of 50.10730272766756 degrees consequently becomes 0 degrees at gain 0, -25.05365136383378 at gain .5, and -50.10730272766756 at gain 1. Starts and stops therefore open the mouth back toward the original modeling gape as motion fades. The standing implementation criteria explicitly specified a neutral offset independent of locomotion gain; only breathing is gain-driven.

Compose `gain * breathing_gape - neutral_close` once about the admitted local hinge. Keep omitted/zero neutral calibration on the legacy breathing arithmetic path. Test actual start/stop gain-zero endpoints and partial-gain rows, including a 2-degree breathing delta without fading the neutral closure. No copied standing poses or head compensation is needed.

## P1 — source.raw hash does not bind the geometry actually being solved

`admit_neutral_jaw` verifies immutable `source.raw`, but then uses mutable `source.rest_*`, document/accessor data and cached topology without checking their relationship to those bytes beyond the jaw index and positive gap. I changed only the cached jaw rest rotation by +5 degrees while leaving `source.raw` unchanged. Admission still passed the supposedly exact calibration; its current gap became **0.04464113830666783 m**, versus the frozen source witness **0.003426263375848837 m**.

Explicitly admit only the intended relationship between frozen source and current geometry: the existing uniform animal scale across scene roots. Check current binary, document/topology, local translations/rotations and cached state consistently against the frozen source plus that allowed scale. Rebound renamed/rotated sources can remain valid with their own new hash/calibration. Arbitrary post-admission jaw, skin, hierarchy, accessor or local-transform edits must require a new calibration, even if the resulting sampled gap stays positive. Test stale cached TRS and document/binary/topology changes alongside valid uniform scaling.

## P2 — normalized clearance combines raw gap with scaled body height

The frozen profile labels `measured_body_height_m=2.2841755838983118` and `clearance_body_heights=.0015`, but the raw source's measured semantic height is **2.657391579010845 m**. The admitted raw gap is **0.003426263375848837 m**, giving **0.0012893332706067305 body heights**. After uniform animal scaling, the measured height is **2.2841755838983118 m** and gap **0.002945063576226925 m**: still **0.0012893332706064137 body heights**, not .0015. The loader only multiplies caller-supplied evidence fields and does not verify the declared body height against source geometry.

Measure and bind height and gap in the same source space, and verify that uniform scaling preserves the declared ratio. Preserve the intended .0015 body-height engineering clearance by recalibrating the small closure difference if appropriate; alternatively a changed authored ratio must be explicitly identified and justified. Do not retain a field labelled measured source height that is actually a different scaled space. Refresh the versioned profile and evidence from the resulting pose; source bytes remain immutable. This is an engineering calibration correction, not a tooth-contact or biological claim.

The new head/hinge transform direction appears consistent in the inspected code and existing transformed-source test. Native animated jaw/body inspection and the final combined package remain pending.
