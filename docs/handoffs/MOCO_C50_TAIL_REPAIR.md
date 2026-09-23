# C50 D — connected tail source and engine admission

2026-09-23. Tail repair visually accepted by the user; overall motion described as good and fluid. Remaining visual request: slower, more relaxed ankle recovery with less excursion. Full physical validation remains open. Continue directly
without subagents. This supersedes the tail-registration portion of the older
C47 handoff, not its scientific cautions or conventional-solver baselines.

## What failed

C50 B resampled eight source tail links into twelve physical links, then assigned
each new point its nearest original semantic role. Several physical bodies drove
the same skin bone in sequence. The emitted joint/physical-target mismatch reached
0.346053 m. The subsequent `12tail` source attempt contained three disconnected
new nodes and shortened the original tail translations. Its admission never
completed. Both failed sources and their catalogs are preserved for diagnosis;
do not use `adult-locomotion-12tail.v1.json` or `MocoTail12B` as the new baseline.

## Repaired source, shared implementation

The original animation-free source remains immutable. `prepare_moco_tail_source.py`
splits the longest admitted rest links, connects the new joints, interpolates tail
skin influence, and preserves all original joint world transforms and inverse
bind matrices. It does not import or edit an animated take. There are **12 driven
links, 13 ordered nodes including the terminal endpoint**, four more nodes than
the original nine-node/eight-link source. All inserted nodes carry skin weights.
This is engineering subdivision, not reconstructed dinosaur vertebral anatomy.

The tool creates hash-bound variants of the source, rig, animal, neutral pose,
contact, support, baseline, motion-set and runtime binding profile. The physical
builder rejects a requested count that differs from the admitted source. The
skin adapter rejects duplicate drive nodes and disconnected/out-of-order links.
There is no species-specific solver or bone-name branch in shared mechanics.

- Source SHA-256: `c06465ded3d110a4fbd3eac41a834af910547faca2382a37e193381d9976f0b7`
- Motion set: `catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.tail12-connected.json`
- Recipe: `catalog/behaviors/moco-c50-connected-tail.v1.json`
- Game asset folder: `game/Assets/Eonwild/MocoRig50D/`
- Evidence: `game/Evidence/moco-c50-caudofemoralis-study/candidate-d/`
- Working research: `.../eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c50-rig-repair-a/`

C50 D transfers the saved C50 B **physical initializer** by arc-overlap bending
density into the admitted links. Changed link lengths now trigger transfer even
when the link count is unchanged. No coefficient search or new gait optimization
was performed; baseline smoothing is disabled for this controlled comparison.
All non-tail exported landmarks match C50 B to numerical precision.

While auditing continuation, the CF objective was found to index effort by
coordinate order instead of actuator order (six free-root coordinates shift the
indices). This is corrected for future optimization. It does not change the
selected evaluate-only trajectory. CF coupling and wave continuity remain
**heuristic soft objectives**, not anatomical muscles, an enforced torque pair,
or demonstrated wave propagation. Counterbalance is also a reduced heuristic,
not a complete whole-body angular-momentum calculation.

## Reproduce or continue

Run from the active factory worktree, not the stale principal factory checkout:

```sh
cd /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration
TASK=/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526
P="$TASK/venvs/contact-mass/bin/python"
M="$TASK/research/opensim-2026-09-20/moco-venv/bin/python"
GAME=/Volumes/m2-extended-disk/Repos/eonwild/game
E="$GAME/Evidence/moco-c50-caudofemoralis-study/candidate-d"
# Always choose an unused output directory. Never overwrite a candidate.
N="$TASK/research/moco-c50d-reproduction"
mkdir "$N"
export N E
"$P" - <<'PY'
import gzip, os
from pathlib import Path
Path(os.environ['N'], 'baseline.json').write_bytes(gzip.decompress(
    Path(os.environ['E'], 'model/baseline-replay.json.gz').read_bytes()))
PY
PYTHONPATH=src "$P" tools/admit_moco_prototype.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.tail12-connected.json \
  --profile "$E/model/source.profile.json" --output "$N/admission.json"
PYTHONPATH=src "$M" tools/coordinate_moco_prototype.py \
  --admission "$N/admission.json" --recipe "$E/model/recipe.json" \
  --baseline "$N/baseline.json" --evaluate-only --output "$N/coordinate-a"
PYTHONPATH=src "$M" tools/replay_moco_prototype.py "$N/coordinate-a"
PYTHONPATH=src "$P" tools/retarget_moco_prototype.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.tail12-connected.json \
  --profile "$E/model/source.profile.json" --replay "$N/coordinate-a/replay.json" \
  --output "$N/skin-a"
```

For a new optimization, use this new physical replay as baseline with no `--initial`
and a new output directory. Do not apply old C50 B coefficients a second time.
Full Moco collocation remains separate; see the original handoff's build command.
Before a long optimization, fix/audit the remaining counterbalance approximation
and the optional figure-eight objective (inactive here; its frame indexing and
root-relative coordinates need correction). Do not spend hours optimizing an
unvalidated objective before rendering a bounded candidate.

To reproduce source preparation from the pristine original, run:

```sh
PYTHONPATH=src "$P" tools/prepare_moco_tail_source.py \
  --motion-set catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v15.json \
  --profile "$GAME/Assets/Eonwild/MocoCF50B/tarbo.profile.json" \
  --target-links 12 --catalog-suffix tail12-connected --output "$N/source"
```

Existing matching content is accepted; differing content is rejected. The tool
rebuilds geometry and all source-bound references together. Never merely replace
an end GLB or change a profile's list of tail names.

Render with the existing saved-clip stage (no runtime motion correction): copy
`skin-a/root_motion.glb` and `skin-a/source-animal.profile.json` into a **new**
`game/Assets/Eonwild/<candidate>/` as `tarbo.glb` and `tarbo.profile.json`, then:

```sh
UNITY=/Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity
"$UNITY" -batchmode -quit -projectPath "$GAME" \
  -executeMethod MocoPrototypeReviewBuilder.Build -moco-folder '<candidate>' \
  -logFile "$N/unity-build.log"
# Require MOCO_REVIEW_BUILD_SUCCESS in that log before capture.
PLAYER="$GAME/Builds/Eonwild Moco.app/Contents/MacOS/Eonwild Floodplain"
"$PLAYER" -capture-dir "$N/frames-side" -capture-frames 144 \
  -candidate '<candidate>' -description 'Native time / experimental / pending review' \
  -logFile "$N/capture-side.log"
"$PLAYER" -capture-dir "$N/frames-quarter" -capture-frames 72 -front-quarter \
  -candidate '<candidate>' -description 'Native time / experimental / pending review' \
  -logFile "$N/capture-quarter.log"
/opt/homebrew/bin/ffmpeg -framerate 24 -i "$N/frames-side/%05d.png" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart "$N/side.mp4"
```

## Evidence and limits

- Actual rig admission and Unity import/build/capture completed.
- Eight focused tests passed: skin/bind/influence/topology regression checks and
  physical support/tail-count/stop checks. Every inserted joint moves skin when
  independently perturbed; unrelated skin weights and original inverse binds stay exact.
- Reopened emitted clip: 961 samples; maximum physical target error 0.001543 mm.
- Non-tail landmark change from C50 B: < 5e-15 m; existing foot penetration 7.187 mm.
- All 144 side and 72 quarter frames inspected in ordered sheets, plus enlarged
  frames. No visible disconnected tail, collapsed rest geometry or abrupt tail
  break. Direct video temporal feel remains for user review; do not call it approved.
- Saved half-stride position join < 1e-15 m, rotation < 5.2e-8 rad. A smooth replay
  is not independent dynamic stability.
- This remains a reduced inverse-dynamics initializer, **not a converged Moco
  solution**. Contact/actuator limits and independent forward stability are
  unresolved. Do not claim production or biological validation.

Next: user review of the repaired tail, then a bounded reoptimization on this
actual admitted chain. Keep focused head/neck, carried tail and muscular running
intent; retain the conventional C39–C42 branch as a separate baseline.
