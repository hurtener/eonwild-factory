# V5-SHOWCASE-001 Summary

## Claim

This lane delivers an offline editorial showcase for the validated Tarbosaurus V5 animation pack. A committed Blender 5.2 headless script imports the source GLB read-only, preserves its embedded textured material, samples evaluated/deformed bounds across the 21 non-transition clips, locks a Z-up side camera, and renders all 21 priority clips as stills. It also emits seven local MP4 films: idle, relaxed walk, turn, start, eat, bite, and roar. The page presents the material as a field journal rather than a runtime validation dashboard.

## Evidence

- [Desktop 1440×900 capture](desktop-1440x900.png) shows the complete hero animal head-to-tail with the 960×540 hero film.
- [Mobile 375×812 capture](mobile-375x812.png) shows the contained full-body hero and responsive editorial layout.
- `site-check.json` passes offline/local-only asset, accessibility anchor, reduced-motion, and behavior-control checks.
- `tests.json` records Python compilation, MP4 ffprobe checks, and immutable-toolkit proof.
- `provenance.json` records the source hash, tool versions, 37-clip source scope, stale-report hash mismatch, and toolkit boundary hash.

## Acceptance result

PASS for the requested showcase milestone, with perceptual review still required for final art approval. This is Blender visual evidence only; it does not claim browser FPS/runtime-package acceptance for the 60 MB source GLB or its observed 11-weight vertices.

## Limitations

- The page ships stills for all 21 priority clips and films for seven representative clips; authored transitions remain documented in `site/asset-manifest.json` but are not each standalone films.
- MP4s are silent, locally encoded H.264 previews. No external or copyrighted media was added.
- Blender's current build lacks an FFMPEG image-format enum, so the renderer intentionally encodes temporary PNG frames with host ffmpeg and removes those temporary frame directories after each film.
