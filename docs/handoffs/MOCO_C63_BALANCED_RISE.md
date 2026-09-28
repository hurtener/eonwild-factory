# C63 — balanced, rear-first get-up

Status: **VISUAL REVIEW PENDING; PHYSICAL ACCEPTANCE FAILED (improved)**. Stop for
user review. Scope: the get-up family only, both admitted animals, as a shared
opt-in mechanism. Work by Claude (Anthropic), 2026-09-28.

## Review media (game repository, `game/Evidence/moco-c63-balanced-rise/`)

Native time, 24 fps, 1280×720, 9 s (216 frames each).

- `c61-vs-c63-side.mp4` — before/after: C61 left, C63 right; Tarbo top, Allo bottom.
- `get-up-comparison.mp4` — C63 only: Tarbo top, Allo bottom; side left, quarter right.
- `tarbo-get-up-side.mp4`, `tarbo-get-up-quarter.mp4`, `allo-get-up-side.mp4`,
  `allo-get-up-quarter.mp4` — full resolution.
- `inspection/<take>/{side,quarter}-NN.jpg` — every frame, 48 per sheet.

## Diagnosis of C61 (measured, not inferred from the picture)

The C61 rise moved every leg joint and root height with one scalar and held trunk
pitch at its standing value, so the body lifted level like a platform. Auditing
the replay (CoM ground projection vs. the loaded foot-pad hull):

- Feet were planted at the standing stance relative to the lying root. Folded legs
  cannot reach there, so the per-frame solver slid the lying body ~1 m forward
  during the roll; at lift-off the CoM was 0.7 m (Tarbo) / 1.1 m (Allo) *ahead* of
  the feet and the body then slid back over them while unsupported.
- The CoM-over-feet term had weight 3 against 65 (clearance) and 40 (feet), and
  targeted the bare toe midpoint rather than a standing animal's CoM offset.
- Allo's ground reaction fell to ~0 BW mid-rise (airborne for a frame); both had
  frame-to-frame branch switching (e.g. Allo ankle 0.93→1.69 rad in one frame).
- The locomotion knee limit (−2.0 rad, 115°) saturated for ~3 s whenever the
  solver tried to gather the feet under the body.

## What changed (shared; no species-specific code)

All new behaviour is opt-in plan data under `support_transfer`; the archived C61
plan reproduces its seed poses bit-for-bit (max difference 0.0) with this code.

1. **Gathered plant** (`gathered_plant`): the admitted standing stance keeps its
   width and foot orientation, but its placement is solved jointly with bounded
   leg joints of the lying body, so the feet land where folded legs can reach.
   The fold now aims at that solved pose (`fold_to_gathered_plant`), not a
   separately authored crouch — this removed Allo's branch flip.
2. **Staged, rear-first rise** (`staged`): pelvis and chest clearances are separate
   equalities. The pelvis rises first while the chest is held at the floor, the
   feet then step forward (left, then right) to the balanced stance under the
   lying mass, and only then does the chest lift. The animal stands up where it
   lay instead of sliding.
3. **Balance** (`balance`): CoM ground projection is held at the *standing*
   CoM-to-feet offset with weight 45 once the chest unloads (smooth ramp).
   Trunk pitch is a solver variable during the rise (±0.45 rad envelope), held to
   its roll reference beforehand. The visible nose-down/tail-high lean comes from
   these constraints, not from keyed pitch.
4. **Physical-time smoothing**: root pitch/height/forward are Gaussian-smoothed
   (σ 0.22 s) over the rise window, then only the legs are re-solved to the same
   foot goals (max re-anchor error 5.7 mm Tarbo / 6.9 mm Allo).
5. **Smooth witness minimum**: soft-min over body witness points (a hard min
   switched points and made the lean snap).

## Joint envelope (user-authorized review, 2026-09-28)

The user asked for a review of limits set for walking/running. Floor recovery now
has a separately sourced `recovery_envelope` in the plan, applied to this model's
coordinate range and OpenSim limit force only. Locomotion limits are unchanged.

| Joint | Locomotion | Recovery | Evidence |
| --- | --- | --- | --- |
| Knee | −2.0 rad (115°) | **−2.5 rad (143°)** | Coelophysis OpenSim model (Bishop et al. 2021, PMC8457660) knee 0–144°; resting birds and theropod sitting traces imply a deep fold (qualitative) |
| Hip flexion | 1.45 rad (83°) | unchanged | Coelophysis 83° — already equal |
| Ankle | 0.15–2.25 rad | unchanged | Ours (129°) already exceeds Coelophysis (119°) |

Uncertainty: Coelophysis is small and gracile; tyrannosaurid/allosaurid thigh and
shank soft tissue probably stops the fold before bone does. Treat 143° as a
comparative upper bound. The Hutchinson et al. 2005 T. rex SIMM ranges (knee
−10…90°) are moment-arm analysis sliders, not ROM, and were not used. The
Coelophysis model is CC BY-NC: studied for a number, not redistributed.

## Results (same scripts on C61 and C63; `metrics.json`)

| Get-up | C61 Tarbo | C63 Tarbo | C61 Allo | C63 Allo |
| --- | ---: | ---: | ---: | ---: |
| Dense 3-D force balance RMS (BW) | 52.7 | **18.4** | 1407 | **10.5** |
| Max actuator command | 194.5 | **48.4** | 89.3 | **64.4** |
| Ground force during rise, min (BW) | 0.10 | **0.64** | 0.00 | **0.87** |
| Ground force during rise, max (BW) | 19.2 | **2.7** | 18.0 | 47.0 |
| Max loaded pad slip (m/s) | 16.3 | 14.6 | 77.8 | 49.7 |
| CoM outside feet while body unloaded, worst (m) | 0.40 | 0.49* | 0.53 | 0.43* |
| Skin floor minimum (retarget, m) | −0.034 | −0.017 | −0.055 | −0.062 |
| Knee/ankle limit violations | none | none | none | none |

\* C63's out-of-support frames are the two single-foot steps (~1 s total). The
chest witness is at the floor then, but the replay contact model gives the chest
no load, so those steps are dynamic, not statically supported. With both feet
down, the CoM stays inside the support (≈ +0.07…+0.37 m margin) from ~4.3 s on.

The C61 README table (8.26 / 10.83 BW, 200.7 command) does not match C61's own
archived replay receipts (52.7 / 1407 BW, 194.5); the receipts are used here.

## Remaining defects (visible or measured)

- **Before the rise** (0–3.8 s, roll/fold, not targeted by C63): body skin still
  penetrates — Tarbo thighs to −15 cm, Allo thighs to −32 cm (worse than C61's
  −24 cm, likely the deeper knee fold). Right-leg flicks and pad slip during the
  roll are inherited from C61 and remain; Allo's peak 47 BW is at the plant (3.6 s).
  Allo's tail swings high briefly (~2.0 s) as the lateral bend rolls upright.
- Allo's pelvis overshoots ~14 cm at ~6.5 s before settling.
- Steps are authored timing (left 4.5–5.0 s, right 4.95–5.45 s), not planned
  footfalls; step length comes from the gathered/balanced placement difference.
- Residuals of 10–18 BW RMS remain; this is not a converged or force-feasible
  recovery. **No full Moco solve was run.** Method remains authored behaviour
  intent + bounded contact coordination + OpenSim inverse-dynamics audit.
- Not yet propagated to rest-sleep-rise, the C62 encounter clips, or falls.

## Exact provenance

- Factory branch `claude/c63-balanced-rise` (from `eaa909b`); the commit that adds
  this file contains the exact source used. Generation ran from a working tree
  whose `src/` and `tools/` match that commit (tests/docs were added afterwards).
- Research: `research/moco-c63-balanced-rise-i/` (selected). Letters a–h are
  pilots — a/b (balance only; body slid 1 m), c/d (staged; knee saturated),
  e–g (smoothing/branch fixes), h (bad re-anchor window). Do not present them.
- Inputs: C61-E running-fall end state as source, C51 support-a baseline, C52B
  walk as standing reference, motion sets/profiles as recorded in `inputs.json`.
- Commands: `takes/run.sh <dir> <animal>` (generate → replay → native select),
  retarget per `inputs.json`, `takes/render.sh <animal>`.
- Unity assets: `Assets/Eonwild/Moco63BalancedRise{Tarbo,Allo}GetUp/`; evidence
  records the GLB hash rather than a second 45 MB copy.
- Audit scripts: `scripts/support_audit.py`, `scripts/audit2.py`.

Review method: every frame of the 4–6 s rise inspected (side view, both animals,
`inspection/*/side-02.jpg`); the whole take at 3 fps in both views; a per-frame
close strip of the Tarbo roll (1.8–2.8 s). Sheets for all 216 frames per view are
saved but the remaining ones were not individually inspected. Numeric traces for
balance, forces, slip and joint jerk cover every frame. Not direct video perception.
