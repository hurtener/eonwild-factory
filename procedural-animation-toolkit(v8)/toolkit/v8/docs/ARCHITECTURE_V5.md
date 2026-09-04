# V5 Architecture

```text
Source GLB + semantic map
          │
          ├── Full constraint path ── contacts / terrain / anatomy / actions
          │
          └── Contact-preserving refinement path ── validated V4 tracks
                                      │
                              Rig jaw calibration
                                      │
                              Behavioral detail layers
                                      │
                       Protected-track quaternion polish
                                      │
                        Transition endpoint reconstruction
                                      │
                               37-clip V5 GLB
                                      │
                  ┌───────────────────┴───────────────────┐
                  │                                       │
          Offline CPU-skinned review              WebGL2 browser player
                  │                                       │
          Perceptual validation                  Exact sequence handoffs
```

## Why two build paths exist

The full path is appropriate when changing contacts, stride geometry, terrain logic, or joint constraints. The refinement path is appropriate when a prior pack already passed those gates and the requested change concerns neutral pose, secondary polish, action curves, transitions, or runtime presentation.

## Data boundaries

The GLB contains sampled skeletal tracks. Browser code does not execute Blender/Python procedural formulas. Runtime state selection, exact clip handoffs, phase scheduling, and root continuity are maintained outside the GLB.

## Protected tracks

The polish stage excludes root translation, both complete hindlimb chains, all toe chains, and the jaw action channel. These tracks have semantic timing or contact meaning that generic smoothing could damage.

## Determinism

The V5 builder uses fixed profiles, fixed witness selection, fixed sample arrays, deterministic tangent filtering, and exact endpoint restoration. Reports include input/output hashes.
