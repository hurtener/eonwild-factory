# V8.1 walk respin 2 — iteration-38 / iteration-4 independent visual review

**Disposition:** visual approval candidate; no final-release approval.
**Review date:** 2026-08-28
**Scope:** read-only review of the exact iteration-4 MP4 at native 24-fps cadence, with dense frame inspection of startup, both toe-offs, post-release lag, and internal repeat boundaries. No engine, GLB, showcase, or media file was changed.

## Inputs and identity

Candidate MP4:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4`

SHA-256: `8ef3d2c571e2ee317a431a66f8a031fabe53936d6bf256e9c091a9071ef48a20`.

`ffprobe` reports H.264/yuv420p, `960x540`, `24/1` fps, `240` decoded frames, and `10.000000 s`. The render manifest identifies the iteration-38 GLB:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb`

GLB SHA-256: `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`.

The five user captures were inspected directly:

- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-da9a8952-56d3-4797-b190-96bd0b6a1f94.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-1d1a8cfb-577d-4cac-90ce-590bb646a6ec.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-69bddfde-74d4-43ca-8067-1917cd2cc536.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-c17c9fd3-7eb1-471b-8384-0bbde0637436.png`
- `/var/folders/qf/9hz3q9b55xb9hjwg0w478_h00000gn/T/codex-clipboard-6f98d490-7de4-4416-a013-d453153b7df1.png`

They have no embedded phase timestamps. They were used for qualitative side-view morphology and contact language. The supplied relaxed-walk reference was used for cadence and mass, not camera or pixel matching.

## Method

I decoded the candidate at native 24 fps, reviewed the first 20 frames individually and as a lower-foot sheet, then inspected every frame across the first toe-off window (approximately render frames `23-45`) and the bilateral repeat (approximately `47-70`), with enlarged foot crops. Full-body sweeps and internal repeat boundaries were checked for posture, support transfer, framing, and seam continuity. This is a visible-motion judgment; the iteration-38 respin validator is cited only as corroboration.

## Findings

| Criterion | Observation | Disposition |
|---|---|---|
| Startup / first 20 frames | The initially loaded toe patch stays visually fixed through roughly frames `1-17`; the feet merge gradually around `18-20` with no witness reset or old iteration-16 first-20-frame pop. The dense report's startup jumps (`21.22 mm` left and `2.53 mm` right) remain below its `25 mm` cap and do not read as a visible discontinuity. | Pass |
| Relaxed heavy cadence and mass | Native-rate sequential playback reads as a slow, heavy, relaxed walk. Pelvis bob is restrained, head-tail axis remains level, and the 2.60 m stroke does not become a run, hop, rear kick, or overextended split. | Pass |
| Support transfer / chain | Mid-transfer frames keep the pelvis/COM over the loaded foot; the opposite leg folds and passes close beneath the body. Hip-knee-ankle chains remain cohesive with no persistent stretch or support ambiguity. | Pass |
| Loaded distal toe patch | In both toe-off windows, the same forward toe patch remains down and slightly weighted while the metatarsal/rear foot rises. The visible patch does not slide across the floor, jump back, or detach as a whole foot. No gross penetration or hover is visible. | Pass; prior P1 contact defect closed |
| Rocker timing and continuity | The prior iteration-21 visual defect was a heel rise beginning about `.26230` cycle before extension peak and lasting too long. In iteration-4, the rendered metatarsal cue begins around frames `33` / `57`, reaches the rear-extension maximum around `37-38` / `61-62`, and therefore leads by about `4-5` frames. It reads as a short near-peak rocker, not an early long toe-only hold. The rise is smooth over consecutive frames with no up/down reversal or single-frame step. | Pass |
| Ankle-channel versus visible cue | The upstream baked ankle-change phase is `.58197`, but the effective skinned metatarsal onset is `.65455-.65814` against a `.75410` extension peak: `.09596-.09954` cycle, within the desired `.04-.10`. The earlier channel change is not accompanied by an early visible heel lift in the inspected MP4; the acceptance judgment follows the rendered foot cue. | Pass |
| Loaded adjustments | Dense native-rate sequences show 15-16 small loaded adjustments across the rocker rather than a rigid hold or staircase. At 24 fps the transitions remain fluid and continuous. | Pass |
| Toe articulation / release order | Digits articulate progressively after the loaded dwell; they do not stay rigid and the whole foot does not lift early. Release follows the near-peak rocker. | Pass |
| Passive/free-weight lag | After release, both feet and digits point down and continue with eased passive follow-through before receiving preparation. The visible sequence has no immediate toe-up snap; the dense export records 8 passive toe-down keys on the left and 7 on the right before the later receiving channel. | Pass |
| Seams | Internal repeat-boundary frame sheets show continuous body, foot, and shadow motion with no visible pop or witness reset. The ten-second clip ends mid-action, so this does not claim final-frame-to-first-frame equality. | Pass |
| Posture, framing, penetration | Full body remains readable and in frame. No posture collapse, camera crop, gross overextension, or visible mesh/floor penetration was found. The neutral floor is brighter than the rejected dark-floor review, although some overlapping foot frames remain low-contrast. | Pass; minor P2 readability note |

## P0/P1/P2 verdict

- **P0: 0.** No invalid media, crash, catastrophic body break, unusable framing, or unrecoverable penetration was observed.
- **P1: 0.** The iteration-16 planted-toe slide/reset and startup pop are not visible. The iteration-21 early/long rocker is also closed in the rendered motion: visible metatarsal rise occurs only about 4-5 frames before maximum extension, while the toe patch stays loaded and the later release/passive lag remains articulated. No new P1 was introduced.
- **P2: 1.** Some overlapping foot frames still blend tan toes with the floor/shadow, so the MP4 is not a perfect visual witness for every hidden distal vertex. This is a presentation/evidence limitation, not a visible contact failure. Separate technical-review P2 items (validator wording and glTF portability warnings) are outside this visual verdict.

**User-facing disposition:** appropriate to return as a user-approval candidate, with the explicit caveat that this is not final-release approval. The visible motion satisfies the requested near-peak rocker, fixed toe loading, articulated release, passive toe-down lag, centered transfer, and startup/seam behavior in this bounded review.

## Corroborating machine evidence

`/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-38/respin-2-validation.json` reports dense world-space distal-witness lock, zero metatarsal reversals over 1 mm, effective skinned onset-to-peak lead `.09596-.09954`, 15-16 loaded keys, passive toe-down runs, and zero seam toe drift. The separate base report remains top-level `FAIL` because legacy absolute-front-reach and broad toe-contact proxy fields are false; this visual review does not waive that gate.

## Reproduction commands

```sh
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=index,codec_name,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_read_frames \
  -of default=noprint_wrappers=1 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4

ffmpeg -hide_banner -loglevel info -i \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4 \
  -vf 'freezedetect=n=-60dB:d=0.08' -an -f null -

shasum -a 256 \
  /Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-4/walk-relaxed-v8-1-respin-side.mp4
```

## Limitations

- The captures and reference differ in camera, crop, lighting, model, and floor calibration; screen-space contact observations are qualitative.
- A 24-fps MP4 cannot independently prove every exported 60-Hz key or hidden skinned toe vertex; dense GLB evidence is corroborating.
- The render is ten seconds and ends mid-action; internal seam continuity is not a final-frame-to-first-frame loop proof.
