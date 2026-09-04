# V8.1 walk respin 2 — iteration-21 / iteration-3 independent visual review

**Disposition:** not yet suitable for user-facing approval under the strict rocker-timing intent; approval-candidate only, not final release.
**Review date:** 2026-08-28
**Scope:** read-only review of the iteration-3 MP4, using native 24-fps frame cadence and dense representative frame sequences. No engine, GLB, showcase, or media file was changed.

## Inputs and identity

Candidate MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-3/walk-relaxed-v8-1-respin-side.mp4`

SHA-256: `2ba831dddd482ae8f512f229a71257c76e1a730c969cccf1ac8bc6a9f5b5d0ac`.

`ffprobe` reports H.264/yuv420p, `960x540`, `24/1` fps, `240` decoded frames, and `10.000000 s`. Its render manifest points to the iteration-21 GLB:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-21/tarbosaurus_procedural_v8_1_walk_respin.glb`

GLB SHA-256: `c53e8f67df930a1a455bb7c35c041dd736753c90242321fc623489590781b329`.

Reference MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4`

SHA-256: `b0401fc76a202d6ed5dc9a5515f1054eab8bed8075c04f6167ff426fd603f5ae`; `672x448`, `24/1` fps, `241` frames, `10.041667 s`. The reference has a different camera, model, lighting, and framing, so it was used for cadence, mass, and contact semantics rather than pixel matching.

The five supplied user captures were also inspected directly:

- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-da9a8952-56d3-4797-b190-96bd0b6a1f94.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-1d1a8cfb-577d-4cac-90ce-590bb646a6ec.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-69bddfde-74d4-43ca-8067-1917cd2cc536.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-c17c9fd3-7eb1-471b-8384-0bbde0637436.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-6f98d490-7de4-4416-a013-d453153b7df1.png`

They have no embedded phase timestamps; they were used for the user-requested foot morphology, loaded-toe, and mid-transfer comparison only.

## Method and evidence

I decoded the candidate and reference at native 24 fps, inspected the candidate's first 20 frames individually and in a lower-foot contact sheet, then reviewed dense sequences around both toe-offs (first occurrence approximately frames `23-45`, repeat approximately `48-70`). Full-body phase sheets and internal action-repeat boundaries were checked for posture, support transfer, and seam continuity. The five captures were compared for the same side-view contact language; no camera calibration was inferred.

The iteration-21 respin validator is corroborating evidence only. It reports world-space distal-witness drift below its limits, zero metatarsal reversals over 1 mm, eight passive toe-down keys, and zero seam toe drift. Those results close the iteration-16 planted-toe reset mechanism but do not enforce the desired upper bound on rocker timing.

## Findings

| Criterion | Observation | Disposition |
|---|---|---|
| Startup / first 20 frames | The loaded toe patch remains at a stable screen location through roughly frames `1-17`; feet overlap gradually around `17-19` rather than resetting. No iteration-16-style first-20-frame toe witness jump or whole-foot pop is visible. | Pass; old startup P1 closed |
| Relaxed heavy cadence | Native-rate sequential playback reads as a calm, heavy walk. Pelvis motion is restrained, head-tail axis stays near level, and the longer stroke does not become a run or rear kick. | Pass |
| Hip-knee-ankle chain and support transfer | Around mid-transfer the pelvis/COM remains stacked over the loaded foot, the opposite leg folds and passes close beneath the body, and there is no persistent split/stretch. The chain remains cohesive in both repeats. | Pass |
| Loaded distal toe patch | In both toe-off windows the same forward/distal toe patch remains visibly down and slightly weighted while the metatarsal/ankle segment rises. No persistent horizontal slide, penetration, hover, or one-frame witness reset is visible. The dense world witness maxima are about `0.0064-0.0074 m` horizontal and `0.0016 m` adjacent movement, below the validator limits. | Pass |
| Progressive rocker continuity | The rise is spread across consecutive frames and reads as continuous, with no up/down oscillation. The candidate preserves the requested micro-adjustment character rather than substituting a single step. | Pass |
| Rocker timing versus near-maximum extension | The causal phase is rocker onset `.45082`, rear-extension peak `.71311`, lead `.26230` cycle (about `0.534 s`, approximately `13` rendered frames). At onset the rear-extension measure is only `0.144 m` left / `0.075 m` right versus peaks `0.827 m` / `0.758 m`; visually the heel/metatarsal begins unloading around frames `23` / `48` while the limb is still materially short of maximum, and remains toe-only through roughly frames `36` / `60`. This is smooth, but it is an early and long heel rise relative to the requested “as extension gets near maximum” intent and the desired `.04-.10` lead (about 2-5 frames). | **P1 open: timing/semantic mismatch** |
| Toe articulation and release | Release is progressive after the loaded dwell; digits do not remain rigid. No whole-foot lift occurs before the distal release. | Pass |
| Post-release passive lag | After both releases (roughly frames `42-45` and `65-70`) the digits point down and continue with a short eased/free-weight lag before receiving/landing preparation. Exported evidence records eight passive keys and terminal toe pitches no higher than about `-9.3` / `-9.9` degrees. No immediate toe-up snap is visible. | Pass |
| Loop / action-repeat seams | Internal repeat boundaries around the action seam show continuous body and foot motion with no visible reset. Dense validation reports zero seam toe drift and effectively zero seam orientation difference. The ten-second clip ends mid-action, so this is not a claim that its final output frame equals frame one. | Pass |
| Posture, mass, framing | Full body remains readable and in frame. No catastrophic penetration, overextension, posture collapse, or camera/framing regression was found. Foot overlap and tan-on-floor contrast occasionally reduce visual certainty but do not create a new P1 contact failure. | Pass; minor P2 readability debt |

## P0/P1/P2 verdict

- **P0: 0.** No invalid media, crash, catastrophic body break, unusable framing, or unrecoverable penetration was observed.
- **P1: 1 — rocker timing.** The prior iteration-16 startup toe slide/pop is closed in this candidate, and the contact/release motion is continuous. However, the measured and visible rocker onset leads rear-extension peak by `.26230` cycle, not the desired `.04-.10`; the heel rises while the rear leg is still far from maximum extension and stays toe-only for an unnecessarily long interval. Under the user's strict “as extension gets near maximum” intent, this is a material approval blocker even though ordering and contact validators pass.
- **P2: 1 — readability/evidence.** Some overlapping foot frames still merge the tan toe patch with the floor/shadow, and a side MP4 cannot independently prove every hidden distal vertex. The brighter floor is materially better than iteration 16; this remains follow-up presentation debt, not the root failure.

**User-facing disposition:** do not present iteration 3 as approved yet. It is a credible approval candidate with the old slide/pop defect removed, but the rocker should be delayed so onset falls within approximately `0.04-.10` cycle before rear-extension peak (about `2-5` rendered frames), while preserving the current fixed toe patch, monotonic metatarsal rise, toe-down passive lag, and release order. If the `.04-.10` range is deliberately downgraded to advisory, then no new contact P1 is visible; that would be a changed acceptance decision, not evidence from this review.

## Supporting machine evidence

The relevant files are:

- `/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-21/respin-2-validation.json` — PASS for dense distal contact, monotonic metatarsal rise, toe-down passive keys, and seams.
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-21/base-validation.json` — top-level FAIL because legacy `long_front_reach` and broad `progressive_toe_contact_before_release` proxies remain false; this review does not reinterpret or waive that separate gate.
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-WALK-RESPIN-2/user-rejection-iteration-16/diagnostic-addendum.md` — prior P1 diagnostic and fail-closed contact contract used for direct comparison.

## Reproduction commands

```sh
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=index,codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_read_frames \
  -of default=noprint_wrappers=1 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-3/walk-relaxed-v8-1-respin-side.mp4

ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=index,codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_read_frames \
  -of default=noprint_wrappers=1 \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4'

shasum -a 256 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-3/walk-relaxed-v8-1-respin-side.mp4 \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4'
```

## Limitations

- The reference and captures have different cameras, crops, models, lighting, and floor calibration; screen-space observations are qualitative.
- A 24-fps MP4 cannot independently prove every exported 60-Hz adjustment or hidden weighted toe vertex; the dense GLB witness report is corroborating evidence.
- The iteration-3 render is ten seconds and ends mid-action; internal seam checks do not imply final-frame-to-first-frame equality.
