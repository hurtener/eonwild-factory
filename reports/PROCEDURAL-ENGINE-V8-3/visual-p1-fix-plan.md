# V8.3 visual evidence P1 fix plan

## Scope

Correct only the two findings in `reviews/visual-final.md` on exact commit
`c2701d0`: remove non-integral-cycle looping from the review UX and re-render
the unchanged V8.2/V8.3 artifacts against a neutral matte ground plane with
readable contact shadows.

## Files intended to change

- `reports/PROCEDURAL-ENGINE-V8-3/tools/render_comparison_blender.py`
- `reports/PROCEDURAL-ENGINE-V8-3/media/**`
- `reports/PROCEDURAL-ENGINE-V8-3/review/index.html`
- `reports/PROCEDURAL-ENGINE-V8-3/evidence/media-manifest.json`
- `reports/PROCEDURAL-ENGINE-V8-3/evidence.json`
- `reports/PROCEDURAL-ENGINE-V8-3/summary.md`
- `reports/PROCEDURAL-ENGINE-V8-3/commands.md`
- this plan and the independent review input

Engine, motion, catalog, profile, channel, and GLB files are read-only.

## Acceptance checks

- exact pre/post hashes for V8.2, V8.3, profile, profile lock, and channel;
- no `loop` video attribute or JavaScript replay path;
- three synchronized 960x540, 24 fps, 240-frame, 10.000-second comparisons;
- all nine full-body and nine foot-detail phase crops regenerated;
- representative frames visibly show a matte floor and contact shadows;
- media hashes and manifests updated, JSON valid, `git diff --check` clean;
- full automated suite passes; signed hurtener commit; no promotion.

## Assumptions

- The existing cameras, framing calculation, animation timing, phase frames,
  and left/right composition remain authoritative.
- The ground plane is evidence-only scene geometry and must not influence the
  camera bounds or artifact bytes.
