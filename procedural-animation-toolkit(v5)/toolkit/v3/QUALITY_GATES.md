# V3 Quality Gates

## Hard structural failures

Generation or validation fails when:

- a required semantic role is absent;
- a mapped node is missing from the GLB;
- skin/inverse-bind accessors are invalid;
- internal Hz is not an integer multiple of export Hz;
- animation sample times are not strictly increasing;
- channel dimensions disagree;
- a generated channel targets an invalid node;
- skin joint order or inverse-bind matrices change.

## Hard anatomical failures

For every internal 120 Hz sample:

- knee signed angle must retain the rest-pose anatomical sign;
- ankle signed angle must retain the rest-pose anatomical sign;
- knee flexion must remain above the configured minimum margin;
- ankle flexion must remain above the configured minimum margin;
- flexion may not exceed configured maxima.

The real-rig fixture requires:

```text
anatomical_flip_count.knee == 0
anatomical_flip_count.ankle == 0
```

A target is allowed to remain slightly unreachable rather than violating anatomy.

## Numeric motion targets

Metrics are normalized by measured hip height when possible.

| Metric | Prototype ceiling | Production-candidate target |
|---|---:|---:|
| Loaded horizontal contact error | 1.0% hip height | 0.5% |
| Loaded toe/sole joint-proxy error | 3.0% hip height | 1.5% |
| Knee/ankle reverse samples | 0 | 0 |
| Minimum knee/ankle flex margin | > 5° | profile minimum |
| Rotation loop endpoint | exact | exact |
| Tail periodic endpoint | ≤ 0.1° | ≤ 0.03° |
| Internal solve | ≥ 120 Hz | ≥ 120 Hz |
| Export rate | ≥ 60 Hz | 60 Hz or validated reduced curve |

Joint velocity and acceleration are reported even when they are not automatic hard failures. A spike triggers frame-step review and target/constraint tuning rather than silent approval.

## Mandatory perceptual review

Review at 1×, 0.5×, and frame stepping from side, front, three-quarter, and gameplay cameras. Check:

- no split-second knee or ankle reversal;
- loading compression and extension;
- swing clearance and forward recovery;
- foot acceleration before contact;
- pelvis shift before opposite-foot unload;
- relaxed versus running-like torso attitude;
- horizon-facing skull without gimbal-like stabilization;
- muscular tail root and compliant distal lag;
- mostly closed neutral mouth;
- no visible loop pop.

## Runtime gate

For the in-place clip:

```text
actor speed = resolved stride per cycle × cycle frequency
```

Playback phase and world translation must share the same gait profile. Otherwise a correct authored contact still appears to slide.
