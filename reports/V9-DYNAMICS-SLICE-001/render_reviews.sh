#!/usr/bin/env bash
# Re-render review previews for the dynamics work: unified run (legs +
# axial), regrounded run (toe engagement), and the relaxed walk baseline.
# Usage: bash reports/V9-DYNAMICS-SLICE-001/render_reviews.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/build/V9-DYNAMICS-SLICE-001-reviews"
GROUND="-0.01200103802869944"
mkdir -p "$OUT"

render() { # <name> <glb> <clip> <frames> <view>
  local name="$1" glb="$2" clip="$3" frames="$4" view="$5"
  echo "=== render $name ($view, $frames frames)"
  blender --background --python "$ROOT/reports/V9-AIRBORNE-RUN-001/render_side_preview.py" -- \
    --candidate "$glb" --clip "$clip" --output "$OUT/$name" \
    --ground "$GROUND" --frames "$frames" --view "$view" --material-mode clay \
    >/dev/null 2>&1
  ffmpeg -y -v error -framerate 24 -i "$OUT/$name/frame-%04d.png" \
    -c:v libx264 -pix_fmt yuv420p "$OUT/$name/cycle.mp4"
  ffmpeg -y -v error -i "$OUT/$name/cycle.mp4" -i "$OUT/$name/cycle.mp4" \
    -filter_complex "[0:v][1:v]concat=n=2:v=1" -c:v libx264 -pix_fmt yuv420p \
    "$OUT/$name/preview-2cycles.mp4"
  echo "=== wrote $OUT/$name/preview-2cycles.mp4"
}

RUN012="$ROOT/build/V9-AIRBORNE-RUN-001/iteration-012-unified/airborne-run-root_motion.glb"
RUN012IP="$ROOT/build/V9-AIRBORNE-RUN-001/iteration-012-unified/airborne-run-in_place.glb"
RUN011="$ROOT/build/V9-AIRBORNE-RUN-001/iteration-011-regrounded/round-0/airborne-run-root_motion.glb"
WALK="$ROOT/build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb"

render unified-run-side "$RUN012IP" V9_UNIFIED_RUN_IN_PLACE 30 side
render unified-run-front "$RUN012IP" V9_UNIFIED_RUN_IN_PLACE 30 front
render regrounded-run-side "$RUN011" V9_AIRBORNE_RUN_ROOT_MOTION 30 side
render walk-side "$WALK" PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION 98 side
echo ALL_RENDERS_DONE
