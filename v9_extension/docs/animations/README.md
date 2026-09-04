# Tarbosaurus animation catalog reading guide

The catalog specifies **29 semantic animations**, each with purpose, performance character, entry/exit contract, complete normalized phase progression, support/COM/dynamics intent, body-chain behavior, events, procedural channels, growth response, and release-blocking validation.

## Files

- `ALL_29_ANIMATIONS.md` — canonical combined human-readable catalog.
- `01_STATES_LOCOMOTION_AND_TRANSITIONS.md` — animations 01–10.
- `02_PERCEPTION_AND_COMBAT.md` — animations 11–17.
- `03_FEEDING_DRINKING_AND_GROUND_POSTURE.md` — animations 18–24.
- `04_INJURY_CALLS_AND_DEATH.md` — animations 25–29.
- `../../motions/tarbosaurus/catalog.yaml` — machine-readable canonical catalog.

## Implementation rule

Do not implement each animation as an unrelated script. The 29 contracts map to twelve reusable MotionPrograms:

```text
stationary_support
alternating_gait
gait_transition
attention_reaction
bite_action
recovery_failure
body_pressure
feeding_interaction
ground_posture
vocal_display
terminal_fall
dynamic_launch_attack
```

The semantic animation owns performance and gameplay meaning. The reusable program owns shared mechanics. A solved plan owns one body/state/terrain/target execution. A baked clip is only one sampled output.

## V8.3 versus V9

V8.3 recovers the historical core states/actions and prepares the data/runtime contracts. The full 29-animation set is the V9 target, delivered in waves:

- V9.1: 01–10, 25, 26.
- V9.2: 11–21 plus grounded and feasibility-gated airborne power attack.
- V9.3: 22–24, 27–29.
