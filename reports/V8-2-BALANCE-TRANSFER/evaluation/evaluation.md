# V5.5 → V8.2 balance-transfer evaluation

## Conclusion

**The user's impression is substantially correct, with an important qualification.**

V5.5 has a much more visible, connected **whole-body balance envelope**: lateral pelvis travel, vertical bob, pelvis roll/yaw, chest counter-roll, and tail sweep are all materially larger when normalized by hip height. Its phase-matched frames read as a body negotiating support rather than as a mostly rigid trunk riding a very good leg solve.

Iteration-38 V8.1 is the better **leg/foot/contact** candidate. Its distal rocker, toe dwell, release order, passive lag, dense contact lock, and seam behavior are all specifically validated. V8.2 should therefore be a narrow torso/pelvis/tail overlay onto V8.1—not a V5.5 walk transplant and not a change to the V8.1 lower-leg solve.

This is not a claim that V5.5 has a physical center-of-mass solution. “COM” below means a declared geometric body-centroid proxy, not mass, inertia, or biomechanics.

## Exact inputs and coordinate boundary

| Input | Identity | Walk clip | Video |
|---|---|---|---|
| V5.5 | GLB SHA `4e6e85dc…b22fe65` | `PROC_WALK_RELAXED_V5_5_INPLACE`, 4.444445 s | Candidate-5 960×540/24fps, 4.458333 s |
| V8.1 iteration 38 | GLB SHA `1b9a7d07…f744b73e` | `PROC_WALK_RELAXED_V8_1_RESPIN_INPLACE`, 4.069565 s | Iteration-4 960×540/24fps, 10.0 s |

The V8.1 candidate includes `RESPIN_REFERENCE_SCALE_ROOT` with uniform scale `2.008695643`; V5.5 does not. Both use the same rig semantics, but static pose, wrapper scale, and clip duration are not motion differences. The comparison resamples each loop to 120 normalized phases and divides translation by the asset’s median pelvis-to-lowest-distal-foot height. glTF world basis is **X lateral, Y up, Z sagittal**.

The phase-matched and normal-speed sweeps show the same qualitative distinction as the channels: V5.5 visibly transfers trunk/tail mass around the gait; V8.1 retains a quieter head-tail line and lets the feet carry most of the read.

## What V5.5 does better

| Cycle-local, hip-normalized measurement | V5.5 | V8.1 i38 | Reading |
|---|---:|---:|---|
| Pelvis lateral X travel, peak-to-peak | `.1017 H` | `.0149 H` | **6.84×** more lateral support response in V5.5 |
| Pelvis vertical bob, peak-to-peak | `.0388 H` | `.0124 H` | **3.14×** more visible loading/unloading |
| Pelvis sagittal Z travel, peak-to-peak | `.0196 H` | `.0041 H` | **4.75×** more forward/back mass adjustment |
| Pelvis roll about fore-aft Z | `7.36°` | `2.70°` | V5.5 visually leans into support rather than holding a near-rigid trunk |
| Pelvis yaw about vertical Y | `6.63°` | `3.14°` | V5.5 carries a clearer side-to-side transfer |
| Chest roll relative to pelvis | `9.80°` | `4.67°` | V5.5 has 2.10× the chest compensation; both are correctly counterphased (Pearson `-.87` vs `-.83`) |
| Tail mid yaw relative to pelvis | `32.34°` | `17.06°` | V5.5 sends the balancing response down the tail instead of concentrating it in the torso |
| Tail tip yaw relative to pelvis | `42.48°` | `20.32°` | V5.5 has a much clearer tail lag/sweep |

V5.5 also has more time in the simple distal-foot support proxy’s single-support state (`51.7%` versus `22.5%`), and its body-centroid proxy makes twice the mean lateral correction (`.1749 H` versus `.0885 H`). That supports the visual “balancing” read, but it must not be interpreted as a physical COM proof—support classification from bone endpoints cannot substitute for skinned sole contact.

## What V8.1 does better and must retain

The lower leg is not the part to re-open:

- Iteration 38 has a final-skinned rocker onset only `.09596–.09954` cycle before preserved rear-extension peak, then `15/16` loaded keys, `7/8` passive toe-down keys, zero metatarsal reversals over 1 mm, and at most `.000789 m` adjacent dense-witness movement.
- V8.1 exposes dedicated foot translations on `Bone_008` and `Bone_012`; its local foot envelopes are `74.12°/46.18°`, compared with V5.5’s `56.12°/37.89°`. The animation’s superiority is not simply more rotation—its key ordering and dense skinned contact evidence are stronger.
- Both GLB loop seams are effectively exact (`≤ 0.000002958°` local rotational difference, zero local translation). The V8.1 ten-second MP4 ends mid-action, so its video alone is not a final-to-first loop proof; the GLB seam is.

V8.1’s head is objectively more stabilized in world space (pitch/yaw/roll envelope `2.58°/1.86°/1.03°`, versus V5.5 `4.44°/2.72°/2.43°`). A balance overlay should add torso and tail response while keeping that V8.1 head-stability benefit.

## V8.2 transfer contract

Use the ranges in [`evaluation-metrics.json`](evaluation-metrics.json) as release-gated envelopes. The exact allowed seam is:

1. **Protect completely:** `Bone_000` root motion; `Bone_008…Bone_015` leg/ankle contact solve; `Bone_008`/`Bone_012` translations; every toe/distal contact channel; current key times; passive-lag timing; and all seam keys.
2. **Overlay only:** `Bone_001` pelvis, `Bone_002` chest, `Bone_041…Bone_036` neck/head compensation, and `Bone_024…Bone_016` tail.
3. **Pelvis target:** raise lateral travel from `.0149 H` to `.045–.060 H`; vertical bob to `.018–.026 H`; roll to `4.2–5.2°`; yaw to `3.8–4.8°`. This deliberately takes roughly half of V5.5’s body envelope rather than copying its full `7.36°` roll or `.1017 H` sway into an already contact-tuned walk.
4. **Chest target:** increase relative roll to `6.5–7.8°`, retain a negative chest-roll/pelvis-roll correlation in `[-.95,-.70]`, and keep pitch/yaw in `5.5–6.8°` / `3.8–4.8°`.
5. **Tail target:** increase smooth, base-to-tip yaw lag to base `7–9°`, mid `22–27°`, tip `28–34°`; use pitch `7–9°`, `8–10°`, `8–11°` respectively. Preserve the V8.1 phase ordering; do not add high-frequency reversal.
6. **Head rule:** solve neck/head only as a compensator for the new chest motion. Cap world-space head pitch/yaw/roll at `2.9°/2.1°/1.2°`; do not import V5.5’s larger head-world motion.

Required V8.2 proof: the current V8.1 contact/rocker/passive-lag checks must remain byte-for-byte equivalent for protected channels; no leg or foot channel delta is allowed; no seam delta beyond zero translation and `.00001°` rotation; and the head caps above must pass at all sampled/exported keys.

## Interpretation for the next iteration

The right synthesis is **V8.1 feet carrying V5.5-like mass response**. V5.5’s advantage is not an abstract “more movement”: it is the coherent relationship between pelvis lateral shift, chest counter-roll, and progressively delayed tail response. V8.1 should retain its quieter head, near-peak rocker, planted toe patch, and passive toe-down behavior while adding only enough torso/tail motion for the support transfer to become readable at normal speed.

## Reproduction

```sh
# Phase-aligned GLB analysis: 120 samples per native in-place loop,
# with GLB Y-up semantics and per-asset hip-height normalization.

ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,avg_frame_rate,nb_frames \
  -of default=noprint_wrappers=1 \
  reports/V5-5-BALANCE-001/render-candidate-5/films/walk-relaxed-inplace.mp4

ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height,avg_frame_rate,nb_frames \
  -of default=noprint_wrappers=1 \
  showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4
```

## Limits

- The two camera/light treatments differ. The video comparison is perceptual; the GLB values provide the normalized motion comparison.
- The V8.1 wrapper is scale-only, but no absolute dimension from one package is treated as a movement difference.
- The support/centroid calculation is a declared skeleton proxy, not a scientific kinetic, inertial, or biological model.
- This evaluation does not modify or supersede the candidate-only V8.1 acceptance status.
