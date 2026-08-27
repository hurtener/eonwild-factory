# Runtime integration

V2 exports two ordinary glTF skeletal clips:

- `PROC_WALK_LARGE_V2_INPLACE`: use for gameplay locomotion; advance the actor in the game world and seek/play the clip from the distance-driven phase clock.
- `PROC_WALK_LARGE_V2_ROOTMOTION`: use for offline review, scripted shots, or engines with explicit root-motion extraction.

## In-place rule

The tested Tarbosaurus profile recommends approximately `0.6801 m/s`. More generally:

```text
runtime speed = resolved stride per cycle × cycle frequency
```

Do not independently change playback speed and actor velocity. Either update both from the same gait profile or drive clip phase directly from traveled distance.

## Terrain adapter contract

A production terrain layer should provide, per planned contact:

```ts
interface TerrainContact {
  position: Vector3;
  normal: Vector3;
  reachable: boolean;
  stableUntilRelease: boolean;
}
```

Once a loaded foot accepts a contact, keep that target stable until release. Re-raycasting and replacing the target every frame produces visible jitter even when the leg solver is correct.
