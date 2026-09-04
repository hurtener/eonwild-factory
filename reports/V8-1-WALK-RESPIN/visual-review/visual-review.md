# V8.1 relaxed-walk respin — independent visual review

**Review status:** user-approval candidate only; not a final-release approval  
**Review date:** 2026-08-28  
**Scope:** read-only review of the supplied walk-only approval MP4, the supplied relaxed-walk MP4, and the five available user captures. No source, GLB, profile, engine, showcase, or media files were changed.

## Inputs and verification

Candidate MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin/iteration-2/walk-relaxed-v8-1-respin-side.mp4`

SHA-256 (verified during this review): `92f7bf9da1a6ef56655391161547f15a5aef78f9d36f044d05fceb8f24160e62`.

`ffprobe` reports H.264 High, `960×540`, `yuv420p`, `24/1` fps, `10.000000 s`, and `240` decoded video frames. The film contains the approximately `4.3011 s` two-cycle source sequence repeated through the ten-second render; the repeat boundaries are around decoded frames `103→104` and `206→207`.

Reference MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4`

SHA-256: `b0401fc76a202d6ed5dc9a5515f1054eab8bed8075c04f6167ff426fd603f5ae`.

`ffprobe` reports H.264 High, `672×448`, `yuv420p`, `24/1` fps, `10.041667 s`, and `241` decoded video frames. The reference model, background, crop, and contact shadow differ from the candidate, so it is used as a qualitative gait reference rather than a pixel- or metre-calibrated target.

The four earlier captures listed in the reference-analysis bundle were available and inspected, along with the new mid-stroke capture:

- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-7ef6cc22-6ee4-4b26-8546-467effc3f044.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-746b7f42-f1b3-4358-b8c5-e5b117c56a37.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-dd138643-625f-432f-b6a5-cfea59a62ea9.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-b47a569f-bee0-4c49-9b95-084dad087791.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-872f7632-1584-4ecd-a70e-bfbfe60c2eeb.png` (new capture; SHA-256 `005459c938c85aa6b5afe7c6dc312e739443f332fd2fa2833c7424fd10841890`)

## Method

I decoded every candidate frame and every reference frame at native 24 fps, inspected full-body and hind-foot contact sheets, then inspected the transfer, rocker, release, and repeat-boundary ranges at individual-frame resolution. The normal-rate impression is smooth: the candidate has no obvious judder, frozen interval, or one-frame pose jump. An `ffmpeg` `freezedetect` scan produced no freeze/unfreeze events. The candidate was reviewed across both source-cycle passes, not only the first still.

The candidate frame sheets and crops used for this review are retained in `/tmp/v81-walk-review.DrIavf/` and are intermediate review evidence, not delivery media.

## Findings by criterion

| Criterion | Observation | Disposition |
|---|---|---|
| Relaxed, heavier cadence | Native 24 fps reads calm and substantially less short/fast than the old V8.1 preview. Pelvis/body bob is restrained; the mass transfer is more subtle than in the bright reference, but it does not read as a run or a frantic hop. | Pass with the P2 presentation caveat below |
| Longer forward/rear stroke | Frames `021–031` and the mirrored `140–150` range show a long forward reach and a folded trailing leg without an obvious rear kick or overextension. | Pass |
| Hip–knee–ankle chain | The leg chain remains cohesive through reach, load, fold, and exchange. No knee/ankle collapse, inversion, or persistent stretch was seen. | Pass |
| New mid-stroke transfer capture | The capture shows the pelvis/COM stacked over one loaded foot, the opposite leg folded and passing close beneath the body, and a level head–tail axis. Candidate frames `041–047` and `140–150` show the same qualitative transfer: one support foot under/near the pelvis, the opposite leg folded close, a nearly level head–tail line, and no persistent split/stretch. The same stacked pose is also visible at the `001/104/207` repeat-start equivalents. | Pass |
| Late stance rocker | In the frame-level foot sheets, the rear/metatarsal segment rises before distal digits release. The ordering is bilateral and matches the reference cue; no whole-foot pop was visually proven. | Pass, but the cue is not equally legible on both sides at this presentation contrast |
| Digit release | Digit branches remain coherent through release; no visible digit snap or obviously wrong individual release order was found. Exact per-digit order remains unresolved by the captures. | Pass / evidence-limited |
| Sliding, penetration, hover | No persistent sliding, mesh penetration, or gross airborne foot was visually confirmed. The candidate validation reports zero selected-sole penetration and low support error, but the MP4 itself has too little contact contrast to independently prove the exact sole/toe support in every frame. | P2 readability finding |
| Full-body posture and framing | The entire nose-to-tail silhouette remains in frame with no clipping. Head, torso, and tail stay coherent and near-level; no posture collapse was found. | Pass |
| Loop seam | Frames around `103→104` and `206→207` are visually continuous; the reset is not an obvious jump at normal 24 fps. | Pass |

## Iteration-2 baseline P0/P1/P2 verdict

- **P0: 0.** No crash, invalid media, catastrophic geometry, or unusable framing.
- **P1: 0.** No major visual correctness blocker was found. In particular, the new capture's stacked mid-stroke transfer is present, and no persistent split/stretch, rear overextension, or whole-foot lift is visible.
- **P2: 1.** The dark floor/stage has no readable contact line or useful contact shadow. This makes the required broad support → metatarsal rise → toe-only hold → distal release cue substantially harder to verify than in the supplied bright reference, especially for the shorter right-side toe-loaded interval. This is a presentation/evidence debt, not a proven kinematic failure; the machine-readable validation separately reports the bilateral progressive-rocker ordering.

**Disposition:** visually suitable to return to the user as an approval candidate with the P2 disclosed. If the approval bar requires the toe-only contact to be self-evident from this editorial MP4 alone, rerender the same walk with a readable ground/contact value or shadow and recheck the two seams. This review does not approve a final release.

## Iteration-3 brighter-stage recheck (superseding status)

This bounded recheck covers only the brighter editorial render; the motion input is unchanged.

- MP4: `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin/iteration-3/walk-relaxed-v8-1-respin-side.mp4`
- MP4 SHA-256: `4a654cad0878dcb710090b44d7647644215b0c3b9a696566c1638ecf347145dc`
- Unchanged input GLB SHA-256: `96bf5c37402bd784b23785173fbb9a45cd8cbbed33ea2fd0675bdfd11c48a5a1`
- `ffprobe`: H.264, `960×540`, `24/1` fps, `10.000000 s`, `240` decoded frames.
- `freezedetect` produced no freeze/unfreeze events. Native-rate playback remains smooth across both passes.

The neutral gray-green floor materially raises foot/ground separation relative to iteration 2. At representative rocker frames (`008`, `025`, `034`, `051`, `080–089`) the loaded forefoot and the rear/metatarsal rise are readable against the floor; the distal toes remain visibly ordered through the late-stance release. The mid-transfer range (`041–047`) remains cohesive, and the repeat ranges (`101–105`, `204–208`) show no new seam jump. No new whole-foot lift, gross hover/penetration, posture collapse, or framing defect was introduced. Exact weighted toe contact is still not independently provable from a side MP4 alone, but the prior dark-floor readability blocker is closed for this presentation.

### Final iteration-3 recheck verdict

- **P0: 0.**
- **P1: 0.** No new major visual correctness blocker was introduced.
- **P2: 0.** The prior dark-floor/contact-readability finding is closed by the brighter stage treatment.

**Updated disposition:** appropriate to return to the user as a user-approval candidate. This remains a visual candidate review and is not final-release approval.

## Reproduction commands

```sh
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=index,codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_read_frames \
  -of default=noprint_wrappers=1 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin/iteration-2/walk-relaxed-v8-1-respin-side.mp4

ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=index,codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_read_frames \
  -of default=noprint_wrappers=1 \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4'

ffmpeg -hide_banner -loglevel info -i \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin/iteration-2/walk-relaxed-v8-1-respin-side.mp4 \
  -vf 'freezedetect=n=-60dB:d=0.08' -an -f null -

shasum -a 256 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin/iteration-2/walk-relaxed-v8-1-respin-side.mp4 \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4' \
  /var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-872f7632-1584-4ecd-a70e-bfbfe60c2eeb.png
```

## Limitations

- The source videos and still captures have different cameras, crops, models, lighting, and no shared metric floor calibration.
- The captures have no known frame rate or temporal order; they establish pose/contact cues only.
- A visual MP4 cannot prove hidden weighted toe vertices or exact 3D sole distances. The validation JSON was used as context, never as a substitute for the frame review.
- The candidate MP4 currently hashes to the value recorded above; this is the verified file hash for this review.
