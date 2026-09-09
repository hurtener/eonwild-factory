# Adult v7 support-speed pelvis diagnostic

Status: **SOURCE REVIEW CLEAN; MODEST TRAVEL-RHYTHM IMPROVEMENT;
WHOLE-BODY POLISH REQUIRED; CURRENT EXACT LOOP BLOCKED.** This is one bounded
kinematic pelvis-proxy candidate. It is not a
center-of-mass, force, work, mass-response or biological model. Unity parity
is `NOT_RUN`, production approval is false, and direct transition continuity
is a separate gate from this steady-loop result.

## Bounded mechanism

The candidate keeps the v6 gait, contact choreography, root motor, pelvis
height, lateral carrier, pitch carrier, tail, gaze, cadence and stride inputs.
It adds one opt-in dimensionless performance value,
`pelvis_forward_velocity_modulation_fraction`. With support clock
`u = t / step_period - duty_factor`, the pre-IK pelvis carrier is

```
delta_v = -k * mean_velocity * cos(2*pi*u)
delta_x = -k * mean_velocity * step_period / (2*pi) * sin(2*pi*u)
```

The displacement is periodic and has zero net travel. The root channel stays
constant-speed. The pelvis translation is applied in the declared world
forward direction before gaze stabilization, leg IK and final skin
refinement. Nonzero use requires grounded locomotion, the existing
`stance_vault_proxy`, an actual semantic root-to-pelvis hierarchy, orthonormal
axes and finite bounded gait inputs. Omission and explicit zero serialize to
the same plan and produce byte-identical motion on the actual rig.

For this single candidate, `k = 0.14519967609352594` is recorded once from the
first-order exchange analogy
`g * (pelvis_excursion / 2) / mean_velocity^2`, using `g = 9.80665 m/s^2`,
pelvis excursion `0.016 * 2.270663281560174 = 0.036330612504962785 m`, and
mean root speed `1.1076406251513045 m/s`. Mass cancels algebraically. This is a
reusable normalized art-direction hypothesis, not a value fitted to the
walking videos or evidence of actual potential/kinetic-energy exchange.

Reusable source and focused tests are commit
`50e909e02100aa448716b0ce41fd34b02b922ec7`, based on
`30f434ce914b6392f1438f0ff234718c82d2e985`. The versioned v7 recipe,
performance input and derivation checks are commit
`98ab0af6610267a27373d8f6f91b8ce850028394`.

## Reopened emitted evidence

The immutable package is retained outside Git at
`out/continuation-adult-v7-support-speed-001`. Its 297 serialized keys span
one 2.46-second cycle. Factory verification reports integrity `PASS` and the
package's historical quadratic-estimator technical status `PASS`. The current
exact exported-channel evaluator supersedes that continuity interpretation and
blocks this loop, as recorded below. The package and its original receipts are
preserved byte for byte. Key hashes are:

- manifest: `7c01449f874c740b7700daae5f2ada531263df23060901b9252d0d582c2861e0`
- root-motion GLB: `9d823831c2f6bf6b3eb1482784fb75ef3532838385bf111a683ee2c7d0986e0c`
- in-place GLB: `1110f89eed7a4de38245a4620d0c10f92e589fb4c703e9360011b3be03e12ce0`
- plan: `7873aeb5984bb9a0b4ecd146bad79fc08eea5133a9699da871d008df309df731`
- solver receipt: `649abf7940f12bdcdddb7e0623c34ef466130958a4fbb4f815fb3a0f8e0973d4`
- validation: `8f58b292f8819cf565c28dc772915dfc7d7bd9ce182ab956e803ba2a0a42e469`
- input lock: `af8dd5fe284c0f9e74be9a0fddc0e8a5892e18d5e870b6432d6d64e679456896`

The reopened root-motion pelvis speed is `0.946824656..1.268449260 m/s`,
with time-weighted mean `1.107640652 m/s`. The emitted residual is therefore
approximately `-0.160816..+0.160809 m/s`, matching the analytic
`k * mean_velocity = 0.16082906 m/s` within float32 sampling. Minimum speed is
at interval midpoint `1.990439177 s`, nearest the second declared stance
midpoint (`1.9926 s`); maximum is at `0.145439185 s`, nearest the first
double-support midpoint (`0.1476 s`). The world-forward displacement relative
to v6 is `-0.031482355..+0.031482358 m`, against the analytic amplitude
`0.031483990 m`.

Root travel remains `2.724796051 m`, its emitted time-weighted mean remains
`1.107640654 m/s`, and its v6/v7 local translation channels are exactly equal.
The in-place root stays fixed while its pelvis carries the same residual with
zero net travel. Root-motion and in-place pelvis-local carrier tracks are
exactly equal. Every non-pelvis local translation and every scale is exactly
equal to v6. Pelvis height span remains `0.036328728 m`; the v7/v6 forward
translation adds at most `7.4e-9 m` in the up projection and `1.3e-8 m` in the
lateral projection from serialization arithmetic.

The emitted geometric rostral direction is unchanged from v6: elevation is
`-22.252384113..-22.252372611 degrees` and yaw is
`-0.000014971..-0.000002996 degrees`; the head local rotation channels are
exactly equal. These are admitted head-to-upper-rostrum geometry values, not
an optic-axis claim.

## Contact and constraint checks

All v6 authored plan fields are exact after removing the one new performance
value and compiler-owned skin-refinement offsets. Refinement changes those
offset vectors by at most `0.000380363 mm`; no gait contact, timing, foot
height, foot pitch, toe recovery or root-travel input changes.

Both reopened skin-contact gates pass with zero penetration and maximum stance
gap `0.000139649 m`. Maximum persistent material-point speed is
`0.000058848 m/s` in root motion and `0.000066337 m/s` in place. Maximum
planted distal target velocity is `0.000057845 m/s`, and maximum planted
distal step drift is `0.000000481 m`.

Hard articulation violation is zero. The largest preferred-envelope departure
is `3.364556 degrees`; solved foot-pitch speed is `479.869184 degrees/s` under
the unchanged `600 degrees/s` limit. The toe-joint proxy reaches
`-0.011004394 m`; this is not skin penetration, and the independent final
skinned-contact measurement passes.

The current exact adjacent-LINEAR/shortest-SLERP evaluator reports local linear
seam mismatch `0.0032116449766123154 m/s` against the unchanged `0.001 m/s`
limit in both root-motion and in-place exports. The witness is pelvis
`Bone_001`. Angular mismatch is `3.652031815499178 degrees/s` and remains under
the `10 degrees/s` limit. Current exact local-loop status is therefore
`BLOCKED`. This is a local serialized-channel result; it does not replace the
separate direct start/stop transition checks. The attached
`host-exact-continuity-status.json` is SHA-256
`1e2e7bc13746b0af232a764c00cd905c90aa09791ff71ae9ea270e3b663483be`
and identifies evaluator source
`61c7ffc99ac2c5166345c5b690328c55bce2aefd`.

The host inspected all 370 rendered frames across five native-time views and
completed five paired v6/v7 native-speed playbacks. The forward carrier is
smooth, preserves the accepted leg recovery, and gives a modest improvement in
travel rhythm. It remains too subtle to establish convincing whole-body effort.
The scoped decision is therefore `MODEST_TRAVEL_RHYTHM_IMPROVEMENT;
WHOLE_BODY_POLISH_REQUIRED`. The byte-for-byte host receipt is
`host-review.json`, SHA-256
`710795062f32ff29fe8d51d51d0338adfb0223908e5f2377afc3a948e3df6ad8`.
It grants no user art-direction, biological, Unity or production approval.

## Combined-source regeneration

The v7 diagnostic was regenerated once after integrating the shared
CUBICSPLINE-capable reader at source
`3b1f55602ba2d8d177c42ec15ccb02d401f92b7d`. The regenerated package remains
truthfully `BLOCKED` by the same exact local-loop witness. It is not byte
identical to the package used for the films because the corrected shared SLERP
sampling changes skin-refinement arithmetic at float precision.

Across all 297 serialized keys in both movement modes, translations and scales
are exact and only eight hindlimb rotation tracks differ. The maximum local
quaternion angle difference is `1.1542389828584848e-7 rad`; maximum world bone
origin displacement is `1.6123272999182854e-7 m`; and maximum displacement over
all 59,169 skinned vertices is `1.753765605561636e-7 m`. The independent
exact-key receipt is `combined-source-equivalence.json`.

The host independently checked all 59,169 vertices at all 74 native render
sample times in both modes and found a maximum displacement of
`9.63609056e-8 m` at frame 66 (`t = 2.2 s`). That receipt is
`root-render-sample-equivalence.json`, SHA-256
`392e54a83ba3e6ceefb9848b9bdd137556b5fb3fba344086c57f08d647e9a6cb`.
These numerical witnesses support reuse of the original films' observations;
they do not claim that new films were rendered or expand the original review
scope.

The combined package identities are:

- manifest: `af3f7ed57ca31d4272b38ecbc65c0fafe2ab65bb4a1439988d8876ad556faa09`
- root-motion GLB: `03da1a7ed5d8d38fc190307ae2e41efa23156158b837c27445ec5809e14878e9`
- in-place GLB: `3d984b535ae22ea776d9111e9bdd52f55cfb05bf7a2cd1741c3354df75d9bdcc`
- plan: `d3fa822226fef7b477837ba008e907b47f76f648e307747596a3d7376066d229`
- solver receipt: `5425714dee66216a0f3b04be91318a2670a13f921eb0489ae031609709be0a7d`
- runtime: `a4a49279ecf648e5b0d5fb396bf9b3a071ce4af752a76abf891ae7fe2be62005`
- validation: `5b5be14b898cafb9ebbbc519ddc9984533e98a90474b658a4fcdbc6f1074a5f6`
- input lock: `21cef43105bd3ae089e7835282b620f19014f7b30fabf8893ace5692b75ad20c`
- numerical equivalence receipt: `d39c73811a56ab1f5999cfc0c25f9d92338c6e3d50ed9e6e87e6d90a859ca79c`

## Verification and remaining decision

The focused carrier tests exercise coefficient rejection, grounded and vault
scope, both stride signs, the analytic derivative, periodic closure, zero net
travel, a rotated production coordinate frame, the actual production
root-to-pelvis hierarchy, a forged hierarchy and zero/omitted byte identity.
The reproduced combined invocation passes 89 tests: 86 in the complete
performance test module plus three versioned-input checks. The narrower 16-test
selection covers the newly added carrier and catalog cases only. Ruff passes
for the changed source and new catalog test, and `git diff --check` is clean.

Two independent round-one reviews found no P0/P1 source defect and converged on
the report-only continuity correction above. Their preserved files are
`review-root-round1.md` (SHA-256
`88a34e4cfe645b4e3928f7a332527212e6fd02cce9a36c152c8a390dcf36bbc7`)
and `review-independent-round1.md` (SHA-256
`cd8168a8a842f9ac798ca5e3444d6afd29fa9557879234d01e0c0bbd9a39105f`).

The mechanical result and host review establish that the new local pelvis speed wave is
present, phase-aligned, periodic, root-neutral and compatible with the existing
contact and articulation gates, with a modest visible rhythm improvement. The
current exact local-loop continuity gate remains blocked and whole-body polish
is still required. No amplitude sweep or production claim follows from this
candidate.
