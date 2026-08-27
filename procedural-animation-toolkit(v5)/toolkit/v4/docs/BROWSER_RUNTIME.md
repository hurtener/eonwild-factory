# Browser Runtime Integration

## Preferred playback

Use in-place locomotion clips for gameplay and move the actor from game simulation. Seek the AnimationGroup to the distance-derived gait phase. Use root-motion clips for offline review, scripted sequences or explicit root extraction.

## Why distance-derived phase

At variable frame rate, simply playing an animation at nominal speed accumulates disagreement between foot contact and actor displacement. V4 defines:

```text
absolute gait cycles = travelled distance / resolved stride
normalized phase     = fractional part of absolute gait cycles
```

This keeps contact markers stable during speed scaling.

## Babylon integration

The runtime folder avoids pinning a particular Babylon package version. `babylon-v4-adapter.ts` wraps imported AnimationGroups through structural interfaces. Wire it after `SceneLoader.ImportMeshAsync`, then construct `MotionGraphV4` from `animation-manifest.v4.json`.

## Terrain

Query the live surface beneath the root and each planted foot. Smooth root height and normal. Apply only residual correction to feet because the authored clip already contains the primary terrain response.

## Performance

- Do not skin the full mesh in JavaScript for contact checks.
- Use engine ray/height queries and authored contact metadata.
- Keep animation sampling at 60 Hz; the renderer can interpolate at display refresh.
- Reuse AnimationGroups and avoid allocating quaternions/vectors per frame.
- Update low-frequency attention layers independently from contact-critical locomotion.

## Included dependency-free validation viewer

`browser_demo/` contains an actual WebGL2 viewer for the baked pack rather than a mock UI. It:

- parses the GLB directly in the browser;
- uploads the 75 joint matrices through a floating-point matrix texture;
- evaluates all three `JOINTS_n` / `WEIGHTS_n` sets for twelve-influence skinning;
- crossfades clips and executes action sequences from the V4 state graph;
- follows root-motion clips and displays matching flat, uneven, or sloped ground;
- requires no CDN or third-party JavaScript package.

Use `browser_demo/serve.py`, or open the supplied self-contained HTML where the GLB and viewer are embedded into one file.
