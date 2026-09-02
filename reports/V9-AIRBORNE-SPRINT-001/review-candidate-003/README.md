# Sprint review candidate 003 — conservative prototype ready for review

Authorized new Sprint candidate after Run006 anatomical correction. This directory supersedes neither the accepted Run baseline nor the historical rejected Sprint trials.

Profile-only work: cadence 11.5/24 seconds per engineering step, 2/11.5 flight fraction, lower pelvis, longer stroke. The source's approximately 0.406 body-length same-frame split remains a target with image/marker uncertainty, not a guaranteed reachable constraint. Hard hip/knee/ankle bounds, lengths and source floor remain unchanged. New Run007 buoyancy controls are explicitly disabled while Sprint feasibility is checked.

The shared-code author confirmed the corrected default path stable, including the exact-authored-pitch precision correction; subsequent Run007 additions are opt-in. Three adaptive profiles were tested, followed by **one explicitly authorized narrow conservative approach correction**. Failed trials were not rendered as viable motion.

## Selected checkpoint

`build/V9-AIRBORNE-SPRINT-001/review-candidate-003/trial-04-conservative-approach/`

Status: **focused kinematic and skin-floor gates pass; user acceptance pending**. This is a usable conservative Sprint prototype, not reference-parity completion. Stop here for user review; no further profile work is active.

- Step period 11.5/24 s (0.479167), same-foot engineering cycle 23/24 s (0.958333), flight fraction 2/11.5. These remain rounded design seeds from the corrected reference, not exact source limb-identity measurements.
- Travel 1.40 body heights, touchdown reach 0.43H, recovery clearance 0.10H, lift/lower fractions 0.20/0.22, pelvis crouch 0.11H. Accepted Run006 uses 1.33H, 0.32H, 0.26H, and 0.08H respectively. Sprint is therefore faster, modestly lower and longer-stroked, with a deliberately lower recovery path to preserve feasibility at the faster cadence.
- Compression 0.07H, flight height 0.035H, toe flex 32°, push-off pitch 60°, hip recovery target 60°, and all hard articulation/rate bounds remain unchanged from accepted006. Run007's opt-in buoyancy/response work is not automatically inherited.
- Same-frame split **3.650757 m / 0.305197 body lengths**, signed hip reaches −1.8385/+1.8122 m. Accepted Run006 is about 0.28260BL: this prototype is about 8% wider, but approximately 25% short of the source Sprint's 0.406BL proxy. The source and generated markers differ, and the source has uncertainty; do not label this a matched 0.406BL Sprint.
- Per-foot root-relative excursion is about 3.977 m / 0.33246BL, distinct from same-frame split. No biological stamina or physical COM validation is claimed. A shorter Sprint sustain envelope is still behavior-level future work, not the 1.9167-second preview duration.

## Focused evidence

`focused-gate.json` independently reopens output and source. No bone stretching or attachment translation was introduced (maximum local leg/toe translation difference 3.6e−9 m; scales unchanged). Reach error zero; maximum foot-target residual 5.34e−7 m; no anatomical branch flips; maximum engineering angle-envelope miss zero. Peak joint angular rate is **866.15°/s**, below the unchanged 1200°/s ceiling, and maximum joint loop seam is **0.021°**.

The narrow final correction specifically removes trial03's late approach extension corner. At t=0.875/0.883333/0.891667 s:

| Witness | Rejected trial03 | Selected trial04 |
|---|---|---|
| Left knee interior | 165.00 → 152.07 → 149.93° | 131.20 → 129.90 → 130.15° |
| Selected pitch | −19.62 → −14.71 → −11.43° | −15.25 → −12.69 → −10.14° |
| Main local knee change | 12.93° in 1/120 s | 1.30°, then 0.25° |

Trial04 does not approach the 165° extension boundary there. Its full left knee range is 72.57–149.24°; right is 66.19–145.24°. This is a local continuity improvement, not proof of physical dynamics.

`final-skinned-ground-receipt.json`: unchanged source floor −0.012001038 m; no foot penetration; no planned-stance misses under the existing proximity tolerance; 12 interior-flight samples without floor intersection. Actual ground-contact velocity remains **unknown/null**: across 94 stance pairs there are no persistent sole/toe points within 0.1/0.5/1 mm of the fixed floor. The relative-bottom-band deformation values (0.5987 m/s at 0.1–1 mm, 1.0007 m/s at 3 mm) occur about 9–20 mm above the floor, not at proven loaded contact. No no-skate/friction claim is made.

## Review media

Within the selected directory:

- `sprint-side-2cycles.mp4`
- `sprint-front-2cycles.mp4`
- `sprint-rear-2cycles.mp4`

Each is 1100×620, 24 fps, 46 frames, 1.916667 s: **two repeats of the same native 23-frame cycle**, with no speed stretch. Source PNGs and exact NLA source-time/camera receipts are in `side-native-cycle/`, `front-native-cycle/`, and `rear-native-cycle/`. Native source time is `(scene_frame−1)/24`; NLA presentation scale was checked equal to one. `media-receipt.json` records ffprobe verification. `*-frames-01-12.png` and `*-frames-13-23.png` cover every rendered frame for all views.

The worker inspected all 23 consecutive frames in all three views plus native frame10. No clipping or obvious old inverted knee/hip triangle was seen. Full-speed host/browser playback and user artistic review remain distinct gates. The side view intentionally shows the complete body and feet; front/rear views expose lateral leg behavior rather than hide it behind a side silhouette.

## Rejected bounded trials

| Trial | Stroke / reach / clearance / crouch (H) | Outcome |
|---|---|---|
| 01 long stroke | 1.70 / 0.53 / 0.24 / 0.14 | Reach passes, split0.3716BL; knee-envelope miss12.34°, peak rate1469.8°/s. Rejected. |
| 02 lower recovery | 1.65 / 0.53 / 0.17 / 0.14 | Split0.3603BL; knee-envelope miss8.00°, peak rate1324.5°/s. Rejected. |
| 03 bounded feasible geometry | 1.50 / 0.50 / 0.10 / 0.11 | Angle/reach gates pass, split0.3270BL; terminal knee extension corner produces1551.5°/s. Rejected. |
| 04 authorized conservative approach | 1.40 / 0.43 / 0.10 / 0.11 | Focused kinematic and floor gates pass. Selected for review, not accepted. |

No hard bound was relaxed to obtain the selected result. The prior historical Sprint folders and accepted Run006 remain untouched.

## Reproduction

Build into a **new unused name** (the wrapper refuses an existing directory):

```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-SPRINT-001/review-candidate-003/build_candidate.py \
  --name conservative-reproduction --travel 1.40 --reach 0.43 \
  --clearance 0.10 --crouch 0.11 --lift 0.20
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-SPRINT-001/review-candidate-003/check_candidate.py \
  build/V9-AIRBORNE-SPRINT-001/review-candidate-003/conservative-reproduction
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/evaluate_skin.py \
  --iteration build/V9-AIRBORNE-SPRINT-001/review-candidate-003/conservative-reproduction \
  --contact-profile build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json
```

Render with `render_views.py` using `--view side`, `front`, or `rear`, each to a new `VIEW-native-cycle` directory, at ground −0.01200103802869944. `make_media.py DIRECTORY` encodes the verified native two-cycle previews and sheets (system `python3` provides Pillow). Generic output GLB names retain `airborne-run-*`; the Sprint profile and containing directory identify this candidate, not a duplicated solver/clip rename.

No shared source/tests, accepted baseline, commit or remote state was changed by this profile/render task.
