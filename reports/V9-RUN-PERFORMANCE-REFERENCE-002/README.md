# Run performance reference 002 — sustained Run polish analysis

Scope: all 145 consecutive decoded frames of `running-sustained-left.mp4` (736×400, 24 fps, 6.041667 s), compared with the user-accepted Run006 `feasible-recovery` native 30-frame cycle. No Sprint implementation, baseline change, or engine edit.

The corrected prior timing authority remains `reports/V9-AIRBORNE-RUN-SPRINT-REFERENCE-ANALYSIS-001/events.json`: V07 clear-flight windows 8–12, 25–26, 39–44; 14–17-frame visible-event spacing, a 15-frame/4-flight-frame engineering seed, not a certified same-foot cycle. This analysis does not resurrect the superseded exact-period assertions.

## Outcome

Keep accepted Run006 as the baseline. Its remaining forceful/Sprint-like impression is mainly **concentrated recovery articulation plus weak whole-body follow-through**, not an incorrect nominal Run cadence. The reference looks buoyant because support extension, body rise, floating leg exchange, neck stabilization and tail-curvature reversal form one phrase. Adding an independent body oscillation would not reproduce this.

All 145 consecutive source frames were inspected in dense sheets, including native individual checks at 10, 19, 20, 24 and 27. The detailed phase comparison covers 1–72 (more than two repeated left/right visual sequences); 73–145 confirm recurring shape/timing variation, rather than being discarded. Overlapping limbs prevent claiming exact same-foot cycle boundaries. All 30 native baseline frames were inspected; its two-cycle movie repeats those same 30 frames, so it is not independent second-cycle evidence.

## Evidence and method

New independent lossless decode: `build/V9-RUN-PERFORMANCE-REFERENCE-002/reference-frames/frame-001.png` through `frame-145.png`. Source hash and decode metadata are in `source.json` in that build directory. `reference-001-012.png` through `reference-145-145.png` are every-frame sheets; `baseline-001-012.png`, `baseline-013-024.png`, and `baseline-025-030.png` show the entire accepted native cycle. The baseline is cropped for visibility, not spatially registered to reference pixels.

`screen-space-contours.csv` tracks native-pixel dorsal contour medians in fixed x windows (pelvis region 300–349, chest 230–264, neck 175–199), plus the colored tail endpoint. `baseline-contours.csv` uses a gray-silhouette dorsal window at x390–439. These are **surface/image proxies**, not joint coordinates or physical COM. `whole-sequence-contours.png` shows all 145 frames, with only the prior audited contact labels shaded. `metrics-summary.json` records numerical witnesses and reopened-GLB baseline leg samples.

Allow approximately ±3 px per dorsal endpoint (up to ±6 px on an excursion), ±5 px for the tail endpoint, and ±1–2 frames on visual phase landmarks. Fixed windows are susceptible to small tracking shifts, surface deformation and camera projection. The reference ground line remains near y298 in the detailed sequence (about ±2 px); that supports a visible relative rise, but not world reconstruction. Different render cameras prevent converting the reference-to-baseline pixel ratio directly into a pelvis amplitude multiplier. No angular velocity or acceleration is estimated by differentiating noisy video keypoints.

## Phase-aligned observations

Compare **events**, not equal file frame numbers: baseline f1 is a touchdown, approximately corresponding to reference landing f13 (or f28/f46); baseline f5 is its early-support trough, comparable to reference f17–18; baseline f12 is toe-off, comparable to reference f24 boundary; baseline f13–15 is flight, comparable to reference f25–27; baseline f16 is the next touchdown, comparable to reference f28. These are approximate visual alignments, not a retiming of the reference.

| Phrase | Reference sequence evidence | Accepted baseline contrast | Polish implication |
|---|---|---|---|
| Landing and compression | f13–18, f28–32, f46–50: the receiving leg yields over several frames, body sinks, neck continues settling, tail tip rises. | Compression timing is already plausible: trough about 3.5 frames after touchdown. Rear recovery quickly approaches the tight knee envelope while the body stays comparatively quiet. | Keep touchdown/flight schedule and compression landmark initially; soften concentrated leg recruitment, not simply slow the whole clip. |
| Support extension and launch | f19–24 and f33–39: body visibly rises before separation; leading recovery foot emerges from under the torso; rear support extends progressively. Tail tip curves downward during the rise. | Planner returns compression to nominal height with **zero vertical speed at toe-off**, then starts a separate flight bump. | Join compression recovery, launch and flight as one continuous body trajectory with carried-through upward speed; do not restart lift after release. |
| Flight and leg exchange | f8–12 and f39–44: body near its high region, legs exchange in comparatively open arcs; distal segments continue changing, rather than holding a deeply tucked shape. f25–26 is shorter clear flight, not a different exact cadence contract. | Right knee remains essentially at its 65° minimum around f6–8 while hip swings rapidly through under-body recovery; leading thigh remains high into late recovery. | Reduce recovery compaction and avoid dwelling on an active articulation limit; preserve stable bend plane and ankle coordination. |
| Approach and catch | f10–13, f25–28, f42–46: leading limb opens and lowers progressively; body descends into the receiving leg. Tail continues its upward recovery into support. | Baseline late recovery releases a high thigh and lowers the distal foot within a compact final interval. No inversion remains, but the concentrated angle change reads more forcefully. | Allocate more of recovery to opening/lowering and less to a high-clearance/strong-hip-lift dwell; preserve floor contact and foot-speed boundary continuity. |

### Quantified buoyancy, without inventing COM

Repeated reference dorsal excursions are about **20–30 native px**, or **0.036–0.053** of the existing 561.5 px visible-body-length witness. For the detailed first three events:

| Low / first clear flight / apex witness | Rise by first clear flight | Full rise | Nominal fraction |
|---|---:|---:|---:|
| f3 / f8 / f9 | 26 px | 28 px | 93% |
| f18 / f25 / f25 | 24 px | 24 px | 100% |
| f32 / f39 / f41 | 26 px | 30 px | 87% |

The percentages are approximate shape-timing witnesses with the uncertainty above, **not precise launch physics**. The robust observation is that most rise is already complete by clear flight. Across the complete clip the contour spans y120–150, with successive rise/settle phrases rather than high-frequency alternating jitter. The reference's small changes from phrase to phrase should not be replaced with fake random variation.

The baseline rendered dorsal contour spans 16 px over a median 926 px silhouette extent (about 0.017 body lengths). This confirms that the presented baseline body looks quieter, but the contours/cameras are not anatomically equivalent. In the exact plan, compression amplitude is 0.07 body heights and additional flight height 0.035: two-thirds of low-to-apex rise is compression recovery, one-third is the independent flight lift. A first test should change their **phase continuity/allocation while holding total low-to-apex excursion**, before any amplitude increase.

### Leg smoothness is a sequence property

The reference f13–18 rearward recovery, f19–21 under-body overlap/passing, and f22–27 opening/approach occupy roughly 6, 3 and 6 displayed frames respectively (about 0.25, 0.125 and 0.25 s, ±2 frames). The exact foot is occluded at f19; these are visible shape windows, not a certified continuously identified limb track. Native f19/f20 make that limit explicit. Similar open passing recurs around f31–35, f49–53, f63–68 and later phrases.

Exact baseline right-foot/hip samples show a rearward foot from f1–7, passing the hip between f7–8, and reaching maximum forward distance around f12–13 before descending to f16 touchdown. Thus gross time allocation is not wildly faster than the reference: the aggressiveness is **how much angular change is packed into that interval**. From f5 to f8, right hip sagittal angle moves −9.2° → 43.3° in 0.125 s while knee interior goes 72° → 65° and dwells at approximately 65° across f6–8. Then knee opens to 83.7° by f10; hip peaks near 74.2° at f13. These are exact candidate geometry witnesses, not reference anatomical measurements.

Current clearance ramps occupy only the first/last 22% of swing, leaving a nominal **56% height plateau**. The coordinated foot placement changes actual emitted foot height, so this is not a claim that the rendered toe is literally stationary. Together with the 60° hip recovery target, it recruits a compact high leg while the toe moves forward. The clearance curve has continuous position/velocity but changes second derivative where its sine-squared ramps join the plateau. The body trajectory likewise has zero-speed joins at toe-off/landing between separate pieces. Those structural timing facts can concentrate apparent acceleration without any branch flip or excessive peak-rate violation.

The reference does not show a matching sustained deep tuck at the passing phase. Its hock/distal segment appears to trail, swing through lower, and progressively open; the knee/thigh does not need to snap to create a long Run silhouette. A precise reference knee-angle or acceleration curve is **not recoverable** from the occluded, textured side-view limb. The correct comparison is consecutive path/pose spacing and reversals, not a fabricated derivative chart.

### Chest, neck and tail

- **Chest:** dorsal chest and pelvis largely rise together in the first phrase (approximately 6 px contour difference), with small shape/pitch changes later. This does not justify a large thorax rocking angle. The chest should participate in the compression/launch phrase, rather than look attached to a nearly static horizontal carrier.
- **Neck/head:** dorsal neck reaches its high region around f11 versus pelvis f9–10, and f42–43 versus pelvis f41. This is a rough 1–3-frame visual lag/settling response, not a fitted oscillator. Mouth opening changes the jaw silhouette and must not be misread as head pitch. Maintain head stabilization while allowing distributed neck response to the solved body motion.
- **Roll/yaw:** side-view overlap and changing visible torso width are insufficient to recover independent roll/yaw magnitudes. Do not add arbitrary roll/yaw for “life”; another view or an explicit artistic decision would be needed.
- **Tail:** this is the clearest absent follow-through. Reference tip y224.5 at f7 versus y150.5 at f16 gives about 74 px vertical endpoint change over 0.375 s. Relative to dorsal pelvis, the tip changes from approximately 98.5 px below it to 4.5 px below it: this is curvature change, not merely the entire body moving. At f36–48 the same relationship repeats (tip relative-back about 76.5 → 0 px). The second intervening phrase has a smaller swing, so a perfectly repeated fixed-amplitude tail sine is not measured by the source. The tip is generally down during launch/early flight, then rises through approach and support. Baseline sheets mostly preserve the same downward-curved tail silhouette, making its body feel more rigid.
- **Damping/phase:** the tail's spatially distributed bend and continuing recovery are visible; a numerical damping ratio, stiffness or physical angular momentum is not. Tip excursions larger than base excursions reflect chain leverage as well as bending, so they cannot be read directly as joint-angle amplitudes.

## Small parameterized polish pass (proposal only)

1. **One continuous launch/flight/landing carrier.** Keep step 0.625 s, the existing contact schedule, stride, floor, crouch and initial total low-to-apex height. Replace the independent zero-speed toe-off lift restart with a constrained C2 trajectory: trough during early support, positive rise through release, one apex, descending approach and smooth yielding after catch. A launch-height-fraction knob around 0.80–0.90 of total rise is an engineering test bracket informed by the projected sequence, not a copied physical measurement. Solve endpoint velocities/accelerations consistently; do not independently ease every key to zero. Recheck reach throughout support before accepting a larger launch height.
2. **Less compact recovery, same anatomical safety.** Test a softer desired hip-lift target (e.g. 45–50° versus 60°, an artistic/engineering bracket), with a rounder clearance profile that removes/reduces the 56% plateau without increasing the accepted 0.26-body-height maximum. Shift opening/lowering earlier instead of holding the thigh high and releasing late. Treat clearance shape and ankle/hip coordination together, keeping the feasible pitch range connected. The earlier rejected margin-only trial is not a viable shortcut. Do not relax the knee/ankle/hip limits or raise clearance back to the disconnected 0.30 case.
3. **Driven torso/tail response, not an ornamental oscillation.** Use the actual solved support/compression/launch state, pelvis trajectory derivatives and signed limb-recovery motion as kinematic drive signals. Parameterize modest chest-response gain, head-stabilization gain, tail counter-response gain and response time. Distribute tail curvature over its semantic chain and permit bounded lag/decay; drive it from the body's change of motion rather than from elapsed-time sine waves. If a physical model is not available, label this an engineering response model—not conservation of angular momentum or force balance. Keep roll/yaw zero/unmodified until supported.

Produce one body/leg timing candidate first, then one candidate adding the driven chest/neck/tail response. Compare both against the unchanged accepted baseline at native speed, including opposing-side recovery and full-body playback. No broad parameter sweep is needed.

Acceptance for this polish: no branch flips, no new tight-envelope dwell, no disconnected pitch branch, unchanged limb translations/lengths, contact/flight and floor checks retained; check adjacent-frame angle increments and their changes, especially under-body passing and landing, plus loop continuity of body **and response state**. Lower peak rate alone is not visual acceptance. Actual ground-contact velocity remains unknown in the accepted candidate's evidence; this analysis does not turn its proximity metrics into no-skate proof.

## Reproduce

From repository root, with Python/Pillow available (the system `python3` has Pillow; this checkout's `.venv` does not):

```sh
python3 reports/V9-RUN-PERFORMANCE-REFERENCE-002/analyze_sequence.py
python3 reports/V9-RUN-PERFORMANCE-REFERENCE-002/summarize_metrics.py
```

These scripts write only `build/V9-RUN-PERFORMANCE-REFERENCE-002/`. No engine, baseline artifact, profile, mesh, weights or timing authority was changed.
