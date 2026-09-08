# Adult v7 support-speed pelvis diagnostic

Status: **TECHNICAL PASS; VISUAL REVIEW PENDING.** This is one bounded
kinematic pelvis-proxy candidate. It is not a center-of-mass, force, work,
mass-response or biological model. Unity parity is `NOT_RUN`, production
approval is false, and the existing exact-C1 transition blocker is outside
this steady-loop experiment.

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
one 2.46-second cycle. Factory verification reports integrity and technical
`PASS`. Key hashes are:

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
skinned-contact measurement passes. Cyclic continuity passes in both modes.

## Verification and remaining decision

The focused carrier tests exercise coefficient rejection, grounded and vault
scope, both stride signs, the analytic derivative, periodic closure, zero net
travel, a rotated production coordinate frame, the actual production
root-to-pelvis hierarchy, a forged hierarchy and zero/omitted byte identity.
The complete performance test module passes 86 tests. Together with the three
versioned-input checks, the focused candidate set passes 16 tests. Ruff passes
for the changed source and new catalog test, and `git diff --check` is clean.

The mechanical result establishes that the new local pelvis speed wave is
present, phase-aligned, periodic, root-neutral and compatible with the existing
contact and engineering gates. Whether it reduces the visible glide and
communicates the intended effort remains a native-time visual decision. No
amplitude sweep or production claim follows from this candidate.
