# V4 Clip Catalog

The validated GLB contains **37** named clips. Durations and tags below come from the generated runtime manifest.

| Clip | Duration | Loop | Root motion | Tags | Events |
|---|---:|:---:|:---:|---|---|
| `PROC_WALK_RELAXED_V4_ROOTMOTION` | 4.444s | yes | yes | walk, relaxed, reference_fitted | foot_contact(left), foot_contact(right) |
| `PROC_WALK_RELAXED_V4_INPLACE` | 4.444s | yes | no | walk, relaxed, reference_fitted | foot_contact(left), foot_contact(right) |
| `PROC_WALK_UNEVEN_TERRAIN_V4_ROOTMOTION` | 4.728s | no | yes | walk, terrain, uneven, sole_collision | foot_contact(left), foot_contact(right) |
| `PROC_WALK_UNEVEN_TERRAIN_V4_INPLACE` | 4.728s | no | no | walk, terrain, uneven, sole_collision | foot_contact(left), foot_contact(right) |
| `PROC_WALK_UPSLOPE_V4_ROOTMOTION` | 4.831s | no | yes | walk, terrain, upslope | foot_contact(left), foot_contact(right) |
| `PROC_WALK_UPSLOPE_V4_INPLACE` | 4.831s | no | no | walk, terrain, upslope | foot_contact(left), foot_contact(right) |
| `PROC_TURN_LEFT_35_V4_ROOTMOTION` | 5.420s | no | yes | turn, left, locomotion | foot_contact(left), foot_contact(right) |
| `PROC_TURN_LEFT_35_V4_INPLACE` | 5.420s | no | no | turn, left, locomotion | foot_contact(left), foot_contact(right) |
| `PROC_TURN_RIGHT_35_V4_ROOTMOTION` | 5.420s | no | yes | turn, right, locomotion | foot_contact(left), foot_contact(right) |
| `PROC_TURN_RIGHT_35_V4_INPLACE` | 5.420s | no | no | turn, right, locomotion | foot_contact(left), foot_contact(right) |
| `PROC_START_WALK_V4_ROOTMOTION` | 4.000s | no | yes | start, acceleration, locomotion | locomotion_start, locomotion_committed |
| `PROC_START_WALK_V4_INPLACE` | 4.000s | no | no | start, acceleration, locomotion | locomotion_start, locomotion_committed |
| `PROC_BRAKE_TO_IDLE_V4_ROOTMOTION` | 3.600s | no | yes | stop, braking, locomotion | brake_start, idle_settled, transition_commit |
| `PROC_BRAKE_TO_IDLE_V4_INPLACE` | 3.600s | no | no | stop, braking, locomotion | brake_start, idle_settled, transition_commit |
| `PROC_ALERT_WALK_V4_ROOTMOTION` | 3.846s | yes | yes | walk, alert, attention | foot_contact(left), foot_contact(right) |
| `PROC_ALERT_WALK_V4_INPLACE` | 3.846s | yes | no | walk, alert, attention | foot_contact(left), foot_contact(right) |
| `PROC_IDLE_BREATH_V4` | 6.000s | yes | no | idle, breathing | — |
| `PROC_ALERT_IDLE_V4` | 6.000s | yes | no | alert, idle | — |
| `PROC_EAT_LOOP_V4` | 8.000s | yes | no | eat, feeding, loop | feeding_bite |
| `PROC_BITE_ATTACK_V4` | 3.400s | no | yes | attack, bite, one_shot | attack_release, bite_contact, recovery_start |
| `PROC_ROAR_V4` | 5.400s | no | no | roar, display, one_shot | inhale_complete, roar_peak, roar_release |
| `PROC_IDLE_TO_WALK_V4` | 1.800s | no | no | transition, idle, walk | transition_commit |
| `PROC_WALK_TO_IDLE_V4` | 1.800s | no | no | transition, walk, idle | transition_commit |
| `PROC_WALK_TO_ALERT_WALK_V4` | 2.222s | no | no | transition, walk, alert | transition_commit |
| `PROC_ALERT_WALK_TO_WALK_V4` | 2.222s | no | no | transition, alert, walk | transition_commit |
| `PROC_IDLE_TO_ALERT_IDLE_V4` | 1.250s | no | no | transition, idle, alert | transition_commit |
| `PROC_ALERT_IDLE_TO_IDLE_V4` | 1.250s | no | no | transition, alert, idle | transition_commit |
| `PROC_IDLE_TO_EAT_V4` | 1.800s | no | no | transition, idle, eat | transition_commit |
| `PROC_EAT_TO_IDLE_V4` | 1.800s | no | no | transition, eat, idle | transition_commit |
| `PROC_IDLE_TO_ROAR_READY_V4` | 0.750s | no | no | transition, idle, roar | transition_commit |
| `PROC_ROAR_TO_IDLE_V4` | 1.250s | no | no | transition, roar, idle | transition_commit |
| `PROC_WALK_TO_BITE_READY_V4` | 0.750s | no | no | transition, walk, bite, urgent | transition_commit |
| `PROC_BITE_TO_WALK_V4` | 1.250s | no | no | transition, bite, walk, recovery | transition_commit |
| `PROC_WALK_TO_ROAR_READY_V4` | 1.250s | no | no | transition, walk, roar | transition_commit |
| `PROC_ROAR_TO_WALK_V4` | 1.800s | no | no | transition, roar, walk, recovery | transition_commit |
| `PROC_WALK_TO_EAT_V4` | 1.800s | no | no | transition, walk, eat, settle | transition_commit |
| `PROC_EAT_TO_WALK_V4` | 1.800s | no | no | transition, eat, walk, rise | transition_commit |

## Runtime notes

- In-place walk clips use the manifest stride and recommended speed for distance-driven phase.
- Root-motion clips are useful for validation, scripted sequences, and engines that extract authored root motion.
- One-shot actions should enter through the named ready transition and return through the matching action-to-locomotion transition.
- Transition clips are endpoint-validated or phase-matched by the generated pack validator.
- Contact, impact, bite, roar, chew, turn, start, and stop markers are intended for sound, particles, camera response, and AI synchronization.
