# V5-SHOWCASE-001 Plan

## Task restatement

Build a polished offline/local Blender showcase from the immutable validated V5 Tarbosaurus GLB. Render real GLB animation clips with Blender 5.2 into browser-ready stills and MP4s, then ship a deterministic local HTML gallery/player with provenance and evidence. Do not alter any tracked file under `procedural-animation-toolkit(v5)/`; prove its tracked-entry tree hash is unchanged before and after the work.

## Intended touch paths

- `showcase/v5/` — deterministic Blender render script, HTML/CSS/JS showcase source, generated local copies/derived preview assets needed by the page.
- `reports/V5-SHOWCASE-001/` — this plan, commands, manifests, metrics, provenance, screenshots, and pipeline evidence.

The source GLB is read from `procedural-animation-toolkit(v5)/validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb`. No tracked file below `procedural-animation-toolkit(v5)/` is an output target or edit target.

## Ownership confirmation

`reports/**` is task-owner scope. `showcase/v5/**` is a task-scoped addition explicitly authorized by the V5 showcase request; it does not overlap the WS00 shared contracts, the WS03 canonical Blender factory paths, or the immutable toolkit. No files under `config/**`, `docs/**`, `schemas/**`, `tools/**`, `apps/**`, `packages/**`, or canonical asset paths will be changed.

## Acceptance checks

1. Capture pre/post hash of all tracked entries under `procedural-animation-toolkit(v5)/`; hashes must match and `git diff -- procedural-animation-toolkit(v5)` must be empty.
2. Verify source GLB exists, is readable, and its SHA-256 is recorded; inspect V5 manifest clip inventory and select all feasible base/action/locomotion clips.
3. Run the committed Blender 5.2 headless renderer against the source GLB; emit deterministic scene setup, per-clip stills, and browser-sized MP4 previews without editing animation data.
4. Build the showcase from local relative assets only; no network dependency, external copyrighted media, or hidden manual step.
5. Run offline HTML/page asset checks and verify all referenced files resolve; serve locally and capture browser-visible screenshots when available.
6. Emit provenance, manifest, tool versions, commands, metrics, artifacts, failures, assumptions, and acceptance summary using the pipeline evidence template.

## Unresolved assumptions

- Blender 5.2 and a usable headless render backend may or may not be available on this host; if unavailable, record the exact blocker and preserve a reproducible fallback path.
- The validated V5 GLB may carry embedded base-color textures but no independent Blender scene; the renderer will import the GLB and use its materials/textures as-is.
- Authored transitions are included in the manifest and page inventory when available, but the first milestone prioritizes the 21 non-transition/base/action/locomotion clips and may render only representative transition previews if budget requires.
- Generated video/still outputs are evidence artifacts; the canonical production record remains the committed renderer and manifests outside the immutable toolkit.

## Initial immutable boundary

- Tracked toolkit entries: 501
- Pre-work tracked-entry hash: `c4f4905f2974aa751a7fe0485a44d194898ead71280992c34d0129dc81362119`

