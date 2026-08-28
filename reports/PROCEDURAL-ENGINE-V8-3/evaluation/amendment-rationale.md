# V8.3 upper-body counterbalance amendment

## Why this is necessary

The recorded 120-phase search found no intersection between the requested
pelvis-roll progression and the previous requirement that chest/tail locals
stay exact while component-wise chest/tail world-relative bands remain narrow.
At the lowest roll candidate that passes the pelvis requirement (3.591 deg),
chest-relative pitch is 4.491 deg, above the former 4.282 deg cap. Solving the
chest axis instead drives pelvis pitch/yaw to 8.261/8.840 deg, far beyond their
frozen bounds.

This is expected transform coupling: an added pelvis world rotation conjugates
descendant relative rotations even when their local tracks are unchanged. It
is not evidence that foot restoration, the lower-leg solve, or V8.2 is wrong.

## Narrow correction

`chest_tail_head_stabilization@1` may now add only declared, rotation-only,
zero-mean upper-spine/chest/tail/neck/head deltas. The counterbalance curves
share the bounded pelvis sweep scale; neck/head are residual head stabilizers.
Their role set, P2P ranges, phase lags, total envelopes, continuity, seam, and
world-head caps are hard machine gates. Root, timeline, stride, speed,
final-skinned feet/contact/trajectory, rocker, passive, receiving, and all
non-counterbalance channels remain frozen.

The targets deliberately take a restrained fraction of V5.5's chest and tail
response. They do not import V5.5 animation data or authorize a free-form
upper-body polish pass. A candidate still needs independent mechanical and
three-view visual review plus explicit user approval before promotion.
