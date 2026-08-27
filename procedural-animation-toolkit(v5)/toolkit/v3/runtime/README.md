# V3 Runtime Integration

V3 exports:

```text
PROC_WALK_LARGE_V3_INPLACE
PROC_WALK_LARGE_V3_ROOTMOTION
```

Use the in-place clip for ordinary gameplay. Move the actor from the same resolved gait profile that drives animation phase.

For the supplied Tarbosaurus V3 profile:

```text
resolved stride per cycle ≈ 1.0229 m
cycle frequency = 0.5 Hz
recommended relaxed speed ≈ 0.5115 m/s
```

General rule:

```text
runtime speed = resolved stride × cycle frequency
```

Do not tune actor speed independently from clip phase. Distance-driven phase is preferable when speed varies.

## Contact events

The manifest identifies left/right contact phases. Use them for sound, dust, compression, and later terrain target acquisition. Event firing must be based on phase crossing so events survive variable frame rates and playback speed.

## V4 terrain adapter

A future terrain layer should provide a persistent contact target:

```ts
interface TerrainContact {
  position: Vector3;
  normal: Vector3;
  reachable: boolean;
  stableUntilRelease: boolean;
}
```

Once a loaded foot accepts a contact, do not replace it every frame. Re-raycasting without persistence creates jitter even when the constrained leg solver is correct.
