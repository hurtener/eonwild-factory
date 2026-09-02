# V9 Airborne Run/Sprint Reference Analysis 001

Frame-level screen-space analysis of the admitted V06/V07/V08 videos. This is a frozen reference artifact, not a motion solver, physical reconstruction, or visual acceptance decision.

## Results

- **V06 — combined start/run/stop:** 193 frames at 24 fps. No decoded frame is fully airborne. Broad choreography bounds are start/acceleration frames 1–73, sustained frames 74–136, stop/deceleration frames 137–173, and settle frames 174–193. The tracked camera and changing silhouette do not support a cadence-ramp or acceleration measurement; V06 acceleration is explicitly **not measured**.
- **V07 — representative Run audit (frames 1–48):** clear flight windows are 8–12, 25–26, and 39–44. Frame 24 is near-ground ambiguous, frame 27 is a near-ground transition, and frame 43 is clearly still flight (the former landing label at 43 was wrong). Visible-flight timing gives 14–17-frame boundary spacing in this evidence set, with a rounded 15-frame control-design seed and approximately 4 flight frames; it is not an exact opposite-foot step or 30-frame same-foot cycle.
- **V08 — representative Sprint audit (frames 1–52):** clear flight windows are 13–14, 24–25, 36, and 47–49. Frames 26 and 35 are boundary-ambiguous; frames 29–30 are visibly planted support. Visible-flight timing gives 11–12-frame spacing (median 11.5), with a 2-frame flight seed; it supersedes the old 16-frame/32-frame assertions. Frames 53–145 remain decoded but are excluded from exact timing claims after the left-edge/camera-ground reframe.
- **Signed reach correction:** V07 and V08 travel left, so leading-foot x is lower than the pelvic proxy and trailing-foot x is higher. The reproducible fore-aft separation is `trailing_x - leading_x`, not `110 - 20` or `150 - 100`. Coordinate witnesses and uncertainties are recorded in `measurements.json`.

## User design direction

Sprint should have a lower body/centre-of-gravity posture, faster strokes, and a shorter sustainable-duration envelope than Run. Run carries a longer visible flight fraction in the audited evidence; Sprint's identity comes from its much longer normalized leg separation and stronger limb action, not simply more flight. These are animation/control requirements, not physical centre-of-mass or biological-stamina measurements.

### Historical interpretation (superseded)

Sprint should read with a lower body/centre-of-gravity posture and faster individual limb strokes. Here, “faster strokes” means traversing the materially larger Sprint excursion with more aggressive limb action; it does not overwrite the measured 16-frame Sprint step period or imply a higher step cadence than Run. At the behavior-engine level, Sprint must also have a shorter sustainable-duration envelope than Run. These are animation and control-design requirements, not claims that the reference video measures physical centre of mass, biological stamina, or metabolic capacity.

The paragraph above is an earlier assistant interpretation, not a verbatim user statement. Its “16-frame” and no-higher-cadence assertions are superseded by the bounded visual audit in `events.json`.

## Current implementation-facing design note

For this engine iteration, use the bounded observed timing as a calibration seed: Run visible-flight event spacing is 14–17 frames (15-frame seed, approximately 4 clear-flight frames), while Sprint is 11–12 frames (11.5-frame seed, approximately 2 clear-flight frames). This supports a higher bounded visible-event cadence for Sprint alongside its larger fore-aft limb excursion and lower/compressed posture. It is an engineering seed from the audited windows, not a universal gait-cycle or physical-speed claim; the shorter Sprint sustain-duration behavior remains a separate design requirement.

The measured grammar is: landing → compression/support → long push-off with distal digit flex → flight/exchange → next opposite-foot landing. Contact and airborne ranges, confidence, and ambiguity are in `event-labels.json`; numeric inputs, explicit source coordinates, and uncertainty are in `measurements.json`. No exact same-foot stride period is asserted because limb identity is not tracked through overlap.

## Reproduce and verify

From the repository root:

```bash
./.venv/bin/python reports/V9-AIRBORNE-RUN-SPRINT-REFERENCE-ANALYSIS-001/analyze_reference.py --skip-extract
./.venv/bin/python reports/V9-AIRBORNE-RUN-SPRINT-REFERENCE-ANALYSIS-001/validate_analysis.py
```

The first command regenerates dense/focused contact sheets, freezes source hashes and anchor copies, computes the V06 diagnostic screen-space trace, and redraws the diagnostic plots. The V06 trace is retained for reproducibility only and is not an acceleration result. The second checks frame counts, inclusive/exclusive timing arithmetic, visual witness labels, signed-coordinate arithmetic, and required artifacts.

## Artifact map

- `sources.json` — exact filenames, hashes, metadata, anchor hashes.
- `event-labels.json` — bounded provisional contact/push-off/flight/landing classifications with confidence, rejected old labels, and ambiguity witnesses.
- `events.json` — bounded airborne windows and visible-flight timing proxies; exact step/stride fields are deliberately null.
- `measurements.json` — explicit screen-space landmark coordinates, signed reach/separation, posture observations, and uncertainty.
- `screen-space-proxy.json` — reproducible V06 tracked-frame diagnostic envelope with a strict non-acceleration validity limit.
- `frames/`, `contact-sheets/`, `plots/`, `anchors/` — frozen visual evidence.

No metres-per-second, force, impulse, physical centre-of-mass, biological-capacity, or exact same-foot-stride claim is made.
