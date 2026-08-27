# Blockers and failed approaches

## Resolved

- First coordinate pass used Y as floor height and produced a wall that occluded the body; the r1–r3 outputs were rejected and are not page assets. The renderer now uses Blender's Z-up basis with an XY floor and a locked side camera across X.
- Blender 5.2 on this host does not expose `FFMPEG` as an image-format enum. The first film attempt emitted `.mp4####.png` frames and was stopped. The committed path now writes temporary numbered PNGs and encodes deterministic MP4s with ffmpeg; the erroneous generated frames were removed.

## Open review item

- `procedural-v5-render-report.json` contains a stale GLB SHA-256 (`caa303...`) while `KEY_SHA256SUMS.txt` and the current source agree on `66cf116a...bacd0`; this mismatch is disclosed in `provenance.json` and does not change the read-only source used here.
