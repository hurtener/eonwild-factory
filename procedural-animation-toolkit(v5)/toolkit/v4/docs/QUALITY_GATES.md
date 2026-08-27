# V4 Quality Gates

## Structural

- GLB 2.0 header/chunks valid.
- Original mesh/material/image/skin counts preserved.
- Skin joint order and inverse-bind matrices unchanged.
- Every animation target names an existing node.
- Times strictly increase and accessor counts agree.
- Clip names are unique.

## Anatomy

- Zero signed knee reversals.
- Zero signed ankle reversals.
- Flexion remains within profile limits.
- Solver prefers feasible joints over exact unreachable targets.
- Jaw uses the resolved hierarchy and returns to living neutral.

## Contact and terrain

- Loaded selected-vertex penetration below profile gate.
- Loaded sole contact-quantile gap below profile gate.
- Terrain normals finite and upward.
- Foot pitch/roll remain within slope limits.
- Swing clearance is positive over uneven terrain.

## Motion signal

- Joint angular velocity and acceleration below gates.
- Exact loop endpoints for in-place loops.
- Root-motion distance equals schedule integration.
- Starts/stops have bounded speed/acceleration.
- Transition first/last poses match their declared source/target samples.

## Browser

- Manifest references all clips.
- State transitions resolve.
- Distance phase remains stable under variable dt.
- No external dependency is needed for the validation HTML.
- Human review covers side, three-quarter, front and action close-up views.
