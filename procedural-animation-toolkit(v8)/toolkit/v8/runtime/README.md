# V4 browser runtime

The generated GLB contains authored root-motion and in-place variants. For ordinary gameplay, use the in-place walk/alert/turn clips and advance the actor with the distance-driven phase clock. This prevents foot sliding when browser frame rate or gameplay speed changes.

Recommended stack:

1. `BabylonV4Backend` wraps imported `AnimationGroup`s.
2. `DistancePhaseClock` advances by metres travelled, not elapsed animation time.
3. `MotionGraphV4` selects locomotion, attention and action states.
4. `ActionController` applies priority and explicit action-to-locomotion bridges.
5. `TerrainContactAdapter` adds a low-authority residual correction for live terrain that differs from the authored terrain clips.

Do not apply a second full IK solve over the authored V4 clip. Runtime terrain correction should remain a residual overlay; otherwise the offline balance, tail and contact relationships will be destroyed.


## Runtime events

`event-dispatcher.ts` consumes each manifest clip's deterministic `events` array. Use it for footstep audio, dust/ground reactions, bite hit windows, roar audio/VFX peaks, feeding sounds, and transition commits. Events are authored in clip time and survive loop wrap without duplicate endpoint firing.
