# V5 Quality Gates

A release fails when any of the following is false:

- 37 expected clips exist exactly once.
- All animation channel targets exist.
- The 75-joint skin order is unchanged.
- Inverse-bind matrices are byte/numerically unchanged.
- Neutral walk and idle jaw tracks remain at or beyond the calibrated closed threshold.
- Bite contact is closed.
- Eating and roar recover to living neutral.
- All authored transition endpoints equal their declared source and target samples.
- The browser supports active button state, play/pause synchronization, timeline, queue cancellation, spherical quaternion blending, root continuity, contact-phase scheduling, and embedded GLB loading.
- The rendered perceptual review is completed by a human.
