# C64 — grounded rest, swung plant, tucked hands (get-up)

Status: **VISUAL REVIEW PENDING; PHYSICAL ACCEPTANCE FAILED (Allo force balance
regressed)**. Get-up family, both animals, shared opt-in mechanics. Claude
(Anthropic), 2026-09-28, answering the owner's review of C63.

## Owner feedback addressed

1. Lying body "flying" instead of resting on the floor (reference: sleeping
   Tarbosaurus, Prehistoric Planet).
2. Feet sliding "all over the place" into the plant; the reference counter-rolls
   and swings the legs under the body (a calm rise: one leg at a time).
3. Hands passing through the floor in the tripod, especially Allo.
4. Roll phase: thighs sinking, leg flicks.

## Media (game repo, `game/Evidence/moco-c64-roll-drape/`)

Native time, 24 fps, 1280×720, 9 s (216 frames). Start with
`c63-vs-c64-side.mp4` / `c63-vs-c64-quarter.mp4` (C63 left, C64 right; Tarbo
top, Allo bottom). Also `get-up-comparison.mp4` and individual views;
`inspection/` has every frame.

## What changed (shared, opt-in plan data; C61 reproduces bit-for-bit)

- **Rest drape** (`rest_drape`): neck, head and every tail segment are floor
  equalities while resting, within admitted joint ranges; eased in over 1 s and
  released through the counter-roll (0.9→2.0 s) so the head and tail lift as the
  animal starts to move.
- **Counter-roll** (`roll_keys`): authored ~8° wind-up onto the back before
  rolling upright. Momentum is *not* simulated.
- **Swung plant** (`support_transfer.swing`): from the solved foot position, each
  foot travels an arc (lift 3% of leg length) to its plant; left 1.9–2.9 s, right
  2.8–3.9 s. Replaces the fading-in tracking weight that dragged feet over the floor.
- **Limb inertia** (`limb_smoothing_seconds` 0.08): unloaded legs get the same
  physical-time inertia as the axial chain.
- **Skin feedback** (`tools/skin_clearance_feedback.py`, `skin_clearance_feedback`):
  measured floor penetration of the actual skinned mesh from previous passes is
  fed back as extra clearance per witness group (3 passes). Proxies: shin skin
  lifts the thigh group (shins have no usable witnesses, see below); forelimb skin
  lifts the chest — in the tripod the chest rests on folded arms.
- **Arm floor tuck** (retarget `arm_floor_tuck`): forelimbs are cosmetic, so the
  smallest extra carriage fold that keeps hand/arm skin above the floor is solved
  on the real mesh, anticipated 0.5 s and smoothed. Palaeo note: theropod sitting
  traces preserve hand impressions beside the body, so hands *touching* in a
  tripod is supported; passing through is the defect.
- **Measurement**: retarget now reports skin floor minima for every region
  (neck, tail segments, shins, forelimbs), not just five.
- The C63 post-hoc root smoothing is **not used** in C64: with swing and limb
  inertia it was unnecessary and it created tail/leg conflicts. Its re-anchor was
  also changed (seed from the previous frame; leg-only clearance), so C63's plan
  no longer regenerates bit-for-bit at this commit — use factory `954bd82` for C63.

Rejected along the way (ablation, `research/moco-c64-*`): shin witnesses (both
legs jumped on Allo; kept as `--include-shin` in the admission tool, off), a drape
held into the rise (tail driven 65 cm under the floor by the lean), stronger limb
smoothing (worse), planting at the reached pose (41 BW step spike).

## Results (same scripts; `metrics.json`)

| Get-up | C63 Tarbo | **C64 Tarbo** | C63 Allo | **C64 Allo** |
| --- | ---: | ---: | ---: | ---: |
| Worst body skin penetration, any region | 51 cm | **5 cm** | 72 cm | **13 cm** |
| Resting mean tail height above floor | 35 cm | **4 cm** | 18 cm | **2 cm** |
| Resting head lowest point | −0.3 cm | 0.9 cm | 26 cm | **1.2 cm** |
| Worst leg jerk (rad/frame²; flicks) | 1.25 | **0.08** | 2.59 | **0.83** |
| Max loaded foot slip | 14.6 m/s | **2.9** | 49.7 | **20.6** |
| Peak ground force | 15.3 BW | **3.5** | 47.0 | **16.3** |
| Dense 3-D force balance RMS | 18.4 BW | **0.67** | 10.5 | **39.5 (worse)** |
| Max command | 48.4 | **20.2** | 64.4 | 61.6 |

C63 skin values were re-measured with the C64 region masks (C63 GLBs re-emit
byte-identical); earlier C63 docs quoted fewer regions.

## Remaining defects

- **Allo** right leg: the free lower leg kicks up behind the body 2.3–2.7 s with a
  sharp hip change at 2.54 s (reads continuous on per-frame sheets); peak 16 BW
  and the force-balance regression come from this window. Allo shins still reach
  −13 cm (right) / −7 cm (left) in the fold.
- Tarbo left shin −5 cm; tail base (fixed to the pelvis) stays ~25 cm up at rest.
- The tail curls high as the drape releases (Tarbo ~2.8–3.2 s, Allo ~3.0–3.2 s).
- Tripod: chest witness sits on the arms, but the replay contact model still gives
  the chest little load; single-foot step frames remain dynamic, not static
  (ground force touches ~0 BW for single frames around 4.6–5.0 s).
- Counter-roll and step timings are authored; no momentum or full Moco solve.
- Not yet propagated to rest-sleep-rise, falls or the C62 encounter.

## Provenance

- Factory `claude/c63-balanced-rise` (continued); the commit adding this file.
  Generation ran from a working tree whose `src/`/`tools/` equal that commit.
- Selected research: `research/moco-c64-roll-drape-h/` (pass 3). Feedback sources:
  pass 1 `…-f`, pass 2 `…-g`. Letters a–e and `moco-c64-*ablation*`, `-lift`,
  `-allo*`, `-tarbo2`, `-check`, `-regression` are pilots/diagnostics.
- Shin-inclusive body surfaces: `research/moco-c64-roll-drape/*-body-surface.json`
  (existing sites byte-identical; shins added but not used as witnesses).
- Unity assets `Assets/Eonwild/Moco64RollDrape{Tarbo,Allo}GetUp/`.

Review method: all four views at 6 fps for 0–5 s plus full-resolution close-ups of
the resting pose and tripod hands; every frame of Allo quarter 2–4 s; numeric
traces over every frame. Per-frame sheets for the rest are saved, not all inspected.
