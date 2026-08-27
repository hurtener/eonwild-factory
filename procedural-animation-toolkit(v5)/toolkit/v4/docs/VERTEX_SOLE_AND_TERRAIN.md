# Vertex-Level Sole Collision and Terrain Adaptation

## Why V3 toe-tip proxies were insufficient

A toe-tip joint is a useful coarse contact marker, but it does not describe the skinned surface that viewers actually see. A foot can satisfy a joint target while the visible sole penetrates, floats, or rolls incorrectly. V4 therefore derives contact witnesses from the real mesh and skin weights.

## Sole discovery

For each side, the analyzer gathers the complete semantic foot system:

```text
ankle
foot / metatarsal
all three toe roots
all toe descendants
```

For every mesh vertex it computes the summed weight contributed by those skin joints. It then:

1. filters by side and influence;
2. restricts candidates to a low vertical band relative to the foot skeleton;
3. rejects isolated/unrepresentative points;
4. favors surface-facing candidates when normals are available;
5. applies deterministic farthest-point sampling in foot-local space;
6. stores source vertex indices, weights, rest positions and local envelopes.

## Validated and ultra profiles

```text
browser-production:   64 selected vertices per foot / 128 total
ultra-offline:        up to 192 per foot / 384 total
```

The validated fixture report also records candidate counts before deterministic selection so later rig changes are detectable.

## Contact solve

For each loaded sample:

1. Plan the contact in path space.
2. Query terrain height and normal at representative sole locations.
3. Solve the anatomical thigh–shin–ankle chain toward the contact.
4. Orient the foot toward the support plane while respecting pitch/roll limits.
5. Skin the selected sole vertices using the exact current joint matrices.
6. Measure signed distance from every witness to the terrain.
7. Apply bounded vertical/orientation residual correction.
8. Re-solve only within the iteration budget.
9. Record maximum penetration, clearance, support error and convergence.

The solver is allowed to miss an unreachable target slightly rather than reverse a knee or ankle.

## Terrain surfaces

V4 includes:

- `FlatTerrain` for baseline locomotion and actions;
- `PlaneTerrain` for deterministic slopes;
- `SmoothTerrain` for analytic uneven-ground tests;
- `RuntimeTerrainAdapter` contract for engine-provided height/normal queries.

Each surface returns:

```text
height(x, z)
normal(x, z)
surface identifier / diagnostics
```

## Pelvis and upper-body adaptation

Foot targets alone are insufficient. Terrain response also drives:

- pelvis height from support geometry;
- pelvis roll and pitch from the support plane;
- lateral support transfer;
- spine compensation;
- neck/head horizon stabilization;
- tail counterbalance and damping.

This keeps the dinosaur from looking like a rigid torso with independently moving feet.

## Current validated contact result

Across all locomotion schedules in the produced pack:

```text
left maximum loaded sole penetration:   0.0000 m
right maximum loaded sole penetration:  approximately 0.0001 m
left maximum loaded sole clearance:     approximately 0.00258 m
right maximum loaded sole clearance:    approximately 0.00271 m
anatomical reverse samples:              0
```

These are automatic gates, not a substitute for perceptual review. The validation package includes a sole-debug video with witnesses and terrain visible.
