# V5.5 motion-reference analysis

## Evidence and limits

The side-walk reference is `procedural-animation-toolkit(v5)/inputs/tarbosaurus_reference_walk_side_v02.mp4`: 736 x 400, 24 fps, 193 frames, 8.041667 seconds, SHA-256 `7f981e34a38955b44df799069693c57a5b5c881083ae4cbd62419e5cdc7d3ea5`. It is byte-identical to `assets/examples/tarbosaurus/Tarbosaurus#walk_side_v02.mp4`. The existing fitter identifies stable walking after about 2.25 seconds and a repeat lag of 54 frames / 2.25 seconds.

The tracked attack/eat reference is `assets/examples/tarbosaurus/attack-eat.mp4`: 736 x 400, 24 fps, 289 frames, 12.041667 seconds, SHA-256 `4103fb155c44d880494c7a3cfb7c113238a45b107ed93e44189db9348ea58781`.

All conclusions below are silhouette- and camera-derived animation hypotheses. They are not biological measurements, force or center-of-mass evidence, calibrated motion capture, or a scientific claim. Side-view leg overlap creates approximately plus or minus two frames of uncertainty around near/far contact boundaries. The attack/eat reference is stylized and changes camera heavily; its feeding section does not support reliable joint-angle extraction.

## Side-walk cycle

A representative apparent cycle was inspected from original 24 fps frames 54 through 114:

| Phase | Frames | Time | Visible relationship |
| --- | ---: | ---: | --- |
| Precontact reach | 54-59 | 2.250-2.458 s | Hip advances the limb; knee stays flexed; ankle and foot unfold late; digits approach ground without an early straight chain. |
| Contact | 60-64 | 2.500-2.667 s | Foot lands ahead of hip; digit tips and sole settle over several frames rather than switching as a rigid unit. |
| Load acceptance | 65-71 | 2.708-2.958 s | Pelvis advances while knee and ankle remain flexed; metatarsus rotates relative to planted digits; torso does not dive with the head. |
| Midstance | 72-87 | 3.000-3.625 s | Foot stays grounded while hip passes over it; knee and ankle change together under load; limb does not become a locked straight column. |
| Terminal stance | 88-97 | 3.667-4.042 s | Hip moves ahead of support, trailing reach remains bounded, and foot roll increases. |
| Toe-off | 98-102 | 4.083-4.250 s | Metatarsus lifts before digit tips; toes are the last apparent contact; knee fold begins as support unloads. |
| Swing/recovery | 103-113 | 4.292-4.708 s | Hip starts forward recovery, knee folds, ankle follows, then knee and ankle open into the next forward placement. Next apparent contact is near frame 114 / 4.750 s. |

Across frames 60-113 the back line is comparatively level, chest excursion is modest, skull remains near the horizon with small residual bob, pelvis vertical motion is restrained, and proximal tail follows the pelvis with limited whip while the distal tail lags softly.

## Attack and feeding cues

- About 0.375-0.875 s: body lowers, loads, and pivots before the forward motion; hips and legs organize first.
- About 0.875-1.500 s: propulsion begins with changing support beneath the pelvis; neck/head extension follows whole-body acceleration.
- About 1.500-3.750 s: the source shows a multi-step charge, not a static torso-only lunge. V5.5 remains a bounded one-shot bite clip, so it adopts the rear-load/drive ordering without claiming to reproduce that full charge.
- About 8.500-10.250 s: the animal transitions down to feeding. The feet appear wider/planted and hind limbs stay flexed as neck/head descend, but the changing front camera prevents reliable angles.

## Implemented V5.5 hypotheses

- Shorter spatial reach and capped hip extension before changing the high-support duty factor drastically.
- Swing target advances earlier and finishes before final precontact; knee/ankle preferences remain staggered and transition into placement rather than being pulled forward at once.
- Contact settles at a small foot angle; foot roll leads a stronger toe push over the final stance window.
- Neutral body pitch moves toward level with a restrained pelvis pitch and horizon compensation.
- Attack adds an explicit rear/down brace before root drive, delays the strongest neck thrust until the drive, caps torso pitch, and uses the tail as a counterbalance.
- Eating moves the pelvis back and down, preserves planted support, and assigns the majority of reach to neck/head with increased tail counterbalance.
