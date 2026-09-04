# V8.1 walk respin 2 — iteration-16 independent visual review

**Status:** user-approval candidate only; not a final-release approval  
**Review date:** 2026-08-28  
**Scope:** read-only visual review of the iteration-16 approval MP4 against the supplied relaxed-walk reference and the available user captures. No engine, GLB, profile, showcase, or media files were changed.

## Inputs and verification

Candidate MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-2/walk-relaxed-v8-1-respin-side.mp4`

SHA-256: `c973ebfa6d2411a1c660627608cae42f7c2761ef16b0ce950cc6af6604757ed6`.

`ffprobe` reports H.264/yuv420p, `960×540`, `24/1` fps, `10.000000 s`, and `240` decoded frames. The render manifest identifies the iteration-16 input GLB as:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-16/tarbosaurus_procedural_v8_1_walk_respin.glb`

GLB SHA-256: `8d878d7a6cbecfc1cfd5193b3889b640e82f445df4583d38c1c146d371f63d2c`.

Reference MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4`

SHA-256: `b0401fc76a202d6ed5dc9a5515f1054eab8bed8075c04f6167ff426fd603f5ae`. The reference is `672×448`, `24/1` fps, `10.041667 s`, and `241` decoded frames. Its camera, model, lighting, and contact shadow differ, so it is a qualitative gait reference rather than a metric or pixel target.

The available captures were inspected, including the mid-transfer capture `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-872f7632-1584-4ecd-a70e-bfbfe60c2eeb.png` and the earlier relaxed-walk contact examples under `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-*.png`.

## Method

All candidate and reference frames were decoded at native 24 fps. I inspected full-body and hind-foot sheets plus individual phase frames across both passes. The candidate was checked at native playback cadence through the rocker/release sequences and repeat boundaries; an `ffmpeg` `freezedetect` scan produced no freeze/unfreeze events, and the decode completed at all `240` frames.

The candidate validation is context only: it reports the intended `2.60 m` stride, `4.60 km/h` reference-scale speed, rocker onset before rear-extension peak, 15/18 loaded-rocker samples, and a seven-sample passive toe/ankle lag. The visual verdict below is based on the MP4, not on those diagnostics alone.

## Findings

| Criterion | Observation | Disposition |
|---|---|---|
| Relaxed cadence and mass | The native-rate sequence reads as a calm, heavy walk rather than a run or hop. Pelvis/body bob is restrained and the head–tail line stays close to level. | Pass |
| Shorter stride | Relative to the earlier 2.75 m candidate, the side-view stroke reads modestly shorter while retaining a relaxed cadence and useful forward reach. It does not read as a cramped shuffle or a rear-leg overextension. The visual impression is consistent with the validated 2.60 m target, but the camera is not metric-calibrated. | Pass |
| Rocker before maximum extension | In the first-side phase sequence around frames `016–032` and the mirrored sequence around `116–140`, the rear/metatarsal segment begins rising while the leg is still extending, then extension eases rather than continuing into a rear kick. The cue is gradual, not a single-frame foot pop. | Pass |
| Loaded adjustments | Consecutive native-rate phase sheets (`012–047` and `056–091`) show smoothly changing foot/ankle poses through the loaded interval. No 15–20-sample stepped staircase is visible at the exported 24 fps presentation; the 60 Hz loaded counts remain validation evidence. | Pass |
| Toe loading and release | The distal toe patch stays down while the metatarsal/rear segment rises, then the digits articulate into release. The toes do not remain rigidly locked to the shank, and no whole-foot lift is visible. | Pass |
| Passive/free-weight lag | Post-release frames in the roughly `034–044` transition show a short unloaded follow-through before the receiving/precontact leg becomes the clear support. The foot/digit silhouette continues with a small eased lag rather than snapping directly into the next planted pose. | Pass; exact hidden toe weighting remains evidence-limited |
| Centered support transfer | Full-body frames around `040–052` and their repeat equivalents show the pelvis/COM stacked over the loaded foot, the opposite leg folded and passing close beneath the body, and no persistent split/stretch. | Pass |
| Contact, slide, penetration | No visible foot pop, persistent slide, mesh penetration, or gross hover occurs in either pass. The lighter neutral floor gives usable sole separation; exact 3D sole distance cannot be proven from a side MP4. | Pass; evidence limitation only |
| Posture and framing | Nose-to-tail silhouette remains in frame. Hip–knee–ankle chains stay coherent; no posture collapse, camera crop, or mass regression was found. | Pass |
| Loop seam | Frames `101–105` and `204–208` are continuous at native cadence. The repeat does not introduce an obvious pose, root, or foot jump. | Pass |

## P0/P1/P2 verdict

- **P0: 0.** No invalid media, catastrophic geometry, crash, or unusable framing.
- **P1: 0.** No major visual correctness blocker. The requested pre-peak rocker, continuous loaded adjustments, articulated toe release, brief passive lag, centered transfer, and shorter stride all read without a visible regression.
- **P2: 0.** No actionable residual presentation defect was found. Exact weighted toe contact remains a limitation of the side-view MP4 rather than a visible failure.

**Disposition:** appropriate to return to the user as an approval candidate. This review does not approve final release.

## Reproduction commands

```sh
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=index,codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_read_frames \
  -of default=noprint_wrappers=1 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-2/walk-relaxed-v8-1-respin-side.mp4

ffmpeg -hide_banner -loglevel info -i \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-2/walk-relaxed-v8-1-respin-side.mp4 \
  -vf 'freezedetect=n=-60dB:d=0.08' -an -f null -

shasum -a 256 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-2/walk-relaxed-v8-1-respin-side.mp4 \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4'
```

## Limitations

- The source reference and user captures use different cameras, crops, models, lighting, and floor calibration.
- A 24 fps MP4 cannot independently prove every exported 60 Hz micro-adjustment or hidden weighted toe vertex.
- The candidate validation JSON is corroborating context, not a substitute for this visual review.
