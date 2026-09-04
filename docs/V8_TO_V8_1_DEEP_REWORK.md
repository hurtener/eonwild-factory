# V8 to V8.1 deep rework

V8.1 is an isolated copy of V8. The original imported `procedural-animation-toolkit(v8)/` remains untouched. V8 walking/contact code remains the locomotion foundation; V8.1 changes neutral posture, idle support, jaw-axis composition, foot-pivot calibration, attack semantics, transitions, and evidence.

## Posture and stance

- Neutral body lean: `-2.8°` inherited baseline to `-1.0°`.
- Pelvis neutral pitch: `-0.35°` to `-1.10°`.
- Relaxed neck pitch: `-1.35°` to `-0.60°`.
- Head horizon pitch: `-0.45°` to `+0.35°`.
- Relaxed idle nominal support: left `0.66`, right `0.34` with the accepted small cyclic transfer.
- Relaxed idle foot offsets: left `-0.030h`, right `+0.320h`.

These are the accepted V5.5 body-balance measurements, ported into V8.1 without replacing V8's gait/contact solver.

## Lower-foot calibration

The accepted V5.5 90% measured gap rule now runs before jaw calibration, locomotion, sole fitting, IK, and animation generation. Both foot pivots move `0.104443 m` toward their own three-toe-root centroid planes. Exactly two inverse-bind slots change. Toe-root error is `1.72e-16 m`; undeformed rest-skinned mesh error is `2.24e-8 m`.

## Jaw centering

V8 reapplied a moving world lateral axis to the lower jaw after head yaw/roll. V8.1 derives the hinge once in jaw rest-local space and applies one local rotation channel. Generated turns/actions show maximum off-hinge rotation of `1.29e-14°`. A separate geometric test at fixed 25° gape transforms weighted lower-jaw and upper-skull vertices into animated skull space; maximum midline offset across neutral and symmetric ±18° yaw/±2° roll is `1.526 mm` (gate `2 mm`).

## Normal versus power attack

V8's grounded two-step bite curves remain available as distinct normal attacks:

- `PROC_NORMAL_ATTACK_V8_1`
- `PROC_NORMAL_ATTACK_MIRRORED_V8_1`

V8.1 adds mirrored power attacks with a separate contract:

- `PROC_POWER_ATTACK_V8_1`
- `PROC_POWER_ATTACK_MIRRORED_V8_1`

The 2.80-second power attack has gaze/approach, 72% launch-leg loading, a measured 0.08h back/0.06h down planted preload, connected compression/extension, one-foot release, a `0.1898–0.1904 s` both-feet-clear interval measured from all 169 baked keys, pre-toeoff gape and exact contact clamp, lead-foot landing, second-foot catch, pelvis/chest arrest, and a feeding-ready endpoint. Root apex is `0.12075 m`; persistent delivery is `0.53516 m`; maximum baked both-sole clearance is `0.07291–0.07331 m` (`0.0531–0.0534h`), and worst penetration across every key is `0 m` on both mirrored variants. The non-launch leg folds higher while both feet travel with the airborne root, then shorten into a feeding brace.

Events are separate and ordered: `launch_leg_loaded`, `takeoff`, `apex`, `bite_contact`, `landing`, `second_foot_catch`, `weight_arrest`, `feeding_ready`.

## Transitions and runtime catalog

The generic walk-to-bite blend is retained only for normal attack. Power attack uses lead-support-phase-specific walk transitions and exact endpoint transitions to eating. A recovery-to-walk path also exists. The manifest exposes normal and power attacks as separate one-shots and provides left/right walk → power → eat action sequences.

## Canonical inputs and gates

- Canonical profile: `procedural-animation-toolkit(v8.1)/toolkit/v8/examples/profiles/tarbosaurus-v8.1.json`
- Profile SHA-256: `f128bd39cca62a674855ffbcce2e88226cec3b17048bf9a830bd158238240143`
- Release validator: `procedural-animation-toolkit(v8.1)/toolkit/v8/tests/validate_v8_1_release.py`
- Jaw geometry validator: `procedural-animation-toolkit(v8.1)/toolkit/v8/tests/validate_jaw_centering_v8_1.py`

The automated release is a pass with perceptual review still required. Numerical correctness is not a substitute for full-body review of weight, timing, and silhouette.
