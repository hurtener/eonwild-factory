# Transition and Browser Player Contract

## Offline transition clips

Each authored transition stores exact source and target endpoints. Rotations use a cubic `RotationSpline` fitted with neighboring source/target samples. Translations use cubic Hermite interpolation with source and target endpoint velocities.

## Runtime rules

1. **Arbitrary direct clip selection:** capture the displayed pose and perform one minimum-jerk snapshot blend into the target clip.
2. **Authored transition sequence:** hand off exactly at the final sample. Do not apply another crossfade.
3. **Locomotion-to-action request:** when the transition declares a source phase matching the current locomotion loop, queue it until that planted-foot phase is crossed.
4. **Root continuity:** compute an offset between the displayed root and incoming root at every clip switch.
5. **Quaternion blending:** use spherical interpolation, not component-linear interpolation.

## UI state

Buttons expose `aria-pressed`, active visual state, player state, clip name, queue progress, timeline, speed, play/pause/replay, and queue cancellation. State changes are driven by the player, not optimistic button text.
