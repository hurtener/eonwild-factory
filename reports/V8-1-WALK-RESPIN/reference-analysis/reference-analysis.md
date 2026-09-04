# V8.1 relaxed-walk respin — reference analysis

Status: ready for a walk-only V8.1 respin. This is an adjustment of V8.1, not a V5.5 rollback. No engine or media files were modified.

## Bottom line

The difference is not only the rendered video. The current V8.1 profile is shorter and has a faster cycle than the user-preferred V5.5 feel:

- V8.1: `cycle_hz=0.64` (`1.5625 s` cycle), `stride_length_m=1.58`, `stance_fraction=0.66`.
- V5.5: `cycle_hz=0.45` (`2.2222 s` cycle), `stride_length_m=1.90`, `stance_fraction=0.70`.
- The V8.1 preview is also 20 fps while the V5.5 preview is 60 fps, so frame sampling changes the read, but it cannot explain the underlying short stroke and fast cadence.

At the requested reference scale, the direct kinematic constraint is:

`forward_speed_mps = stride_length_m × cycle_hz`

The 12 m nose-to-tail length is useful scale context, but it does not determine stride by itself; cadence and forward speed are the quantities that set the same-foot stroke.

Using the user’s `4.5–4.8 km/h` (`1.25–1.333333 m/s`) and keeping the cadence near the source/V5.5 feel gives the bounded center candidate:

`cycle_hz=0.465`, `stride_length_m=2.75` → `1.27875 m/s = 4.6035 km/h`.

With two cycles retained, the walk-only clip is approximately `4.3011 s`. This lengthens the same-foot stroke while keeping a relaxed, readable cadence; it does not copy the V5.5 posture or action layers.

## Evidence and method

The relaxed reference was decoded at native 24 fps: `672×448`, `241` frames, `10.041667 s`. The older walk was also decoded at native 24 fps: `736×400`, `193` frames, `8.041667 s`. All frames were decoded; full-frame sheets and dense hind-leg contact crops were inspected at roughly `0.08–0.17 s` spacing. The four user captures were inspected as stills and are listed in `metrics.json`.

The strongest repeatable timing cue in the relaxed reference is approximately `2.0 s` left-to-left (or right-to-right) cycle, with alternating contacts about `1.0 s` apart. A conservative visual range is `1.85–2.15 s` (`0.465–0.541 Hz`). Camera/framing translation, changing crop, shadows, occlusion, and the lack of a metric floor marker make image-space foot travel unsuitable as a calibrated metre measurement.

Frame-level qualitative sequence in the relaxed reference:

1. Broad sole support is established.
2. In late stance, the visible heel/metatarsal (“bead”) rises while the distal toe patch remains on the floor.
3. Toe-only support persists briefly, then the toes release and the leg folds into swing.
4. The opposite leg reaches, flattens, and accepts load before the next rocker.

The user captures make the rocker cue clearer than the video: the forward planted foot is broad/flat, while the rear foot is behind the hip with the heel/metatarsal lifted and only the digits retaining ground contact. The exact frame order and per-digit timing are not supplied.

## Measured/estimated gait cues

| Cue | Estimate | Confidence and use |
|---|---:|---|
| Relaxed source same-foot cycle | `~2.00 s` (`0.50 Hz`), plausible `1.85–2.15 s` | Medium; repeatable timing, but no calibrated event labels |
| Alternate contact spacing | `~1.00 s` (`0.50` cycle) | Medium; visual side-view sequence |
| Leading toe reach in user stills | roughly `0.5–0.8 H` ahead of the approximate hip | Low/medium; static image-space estimate, `H` is hip height |
| Trailing loaded toe relation | near the hip to roughly `0.3 H` behind it | Low/medium; hip landmark and stance phase are ambiguous |
| Apparent toe-to-toe support span | roughly `0.8–1.2 H` in the stills | Low; perspective and different poses dominate |
| Heel/metatarsal rise | late stance, beginning in the last `~0.18–0.22` cycle fraction | Medium for the qualitative cue; low for exact onset |
| Toe-only contact | final `~0.08–0.12` cycle fraction before release | Low/medium; inferred from visible rocker, not a tracked marker |
| Individual digit release order | unresolved | The references do not resolve this; do not hard-code an unobserved order |

The reach numbers are visual bounds, not fossil measurements and not a request to force pixels into metres. In the generator, `contact_lead_stride` is a touchdown placement offset, not the visible front-to-rear span by itself. With alternating contacts, the simultaneous support span is approximately half the same-foot stride before foot geometry and phase-dependent offsets. Validate rendered toe/heel landmarks in 3D rather than judging this from the profile scalar alone.

## V8.1 respin handoff

Use these as the center candidate, with the bounded envelope shown for one controlled visual search:

| Parameter | Current V8.1 | Center candidate | Bounded envelope | Intent |
|---|---:|---:|---:|---|
| `reference_hip_height_m` | `2.75` | `2.75` | fixed | Keep the requested adult scale |
| `cycle_hz` | `0.64` | `0.465` | `0.46–0.48` | Return to readable relaxed cadence |
| `stride_length_m` | `1.58` | `2.75` | derive from speed: `v/hz` (`2.60–2.90` over the envelope) | Restore the long same-foot stroke |
| `stance_fraction` | `0.66` | `0.72` | `0.70–0.74` | Increase high-duty support and readable overlap |
| `contact_lead_stride` | `0.54` | `0.54` | `0.52–0.55` | Keep V8.1 contact placement; do not use V5.5’s `0.40` |
| `load_ramp_fraction` | `0.18` | `0.20` | `0.18–0.22` | Make load transfer gradual at both stance ends |
| `toe_off_window_fraction` | `0.16` | `0.20` | `0.18–0.22` | Start the rocker early enough to read; preserve toe support |
| `toe_off_foot_deg` | `7` | `9` | `8–10` | Raise the bead/metatarsal visibly, without a foot pop |
| `toe_push_deg` | `8` | `12` | `10–14` | Keep the distal toe patch down through push-off |
| `contact_foot_deg` | `1` | `1` | `0–2` | Broad, nearly flat touchdown |
| `swing_lift_hip_fraction` | `0.058` | `0.055` | `0.050–0.060` | Keep lift readable but relaxed; do not add V5.5’s higher hop |
| `swing_advance_start_fraction` | `0.08` | `0.08` | keep | Retain fold-before-advance timing |
| `swing_advance_end_fraction` | `0.89` | `0.89` | keep | Retain early pre-contact extension |
| `precontact_window_fraction` | `0.25` | `0.25` | `0.22–0.28` | Flatten progressively before touchdown |
| `supercycle_count` | `2` | `2` | fixed for approval MP4 | Show two complete cycles |

The center rocker timing is approximately:

- heel/metatarsal lift begins around phase `0.52` of that foot’s cycle (`stance - toe_off_window`);
- distal toe-only support occupies roughly the final `0.08–0.12` cycle fraction;
- at `0.465 Hz`, that toe-only interval is about `0.17–0.26 s`.

Implementation requirement: the proximal foot/bead must rise progressively while a weighted distal toe patch remains within the existing sole-contact tolerance. Do not translate or vertically lift the whole foot proxy at the stance/swing boundary. The observable order is support loss at the proximal/rear foot, toe patch retention, then distal release. Per-digit staggering is a hypothesis only; if used for readability, keep the central weight-bearing digit last by a small amount and verify that no digit visibly floats or penetrates.

## Approval checks for the walking MP4

1. Read the actual walk manifest/root track, not only the profile: reference-scale `stride_length_m × cycle_hz` must be `1.25–1.333333 m/s` (`4.5–4.8 km/h`), with scale conversion documented if the GLB is rendered at approximately half reference size.
2. Confirm two cycles, approximately `4.17–4.35 s` over the allowed cadence band, with alternate contacts half a cycle apart.
3. Confirm same-foot contact-to-contact advance is approximately `2.60–2.90 m` at the 2.75 m hip-height reference, while the side view reads as a long but relaxed stroke.
4. In a slow inspection, verify broad touchdown → progressive bead/heel rise → toe-only hold → distal release → folded swing → progressive pre-contact flattening.
5. Keep V8.1 contact/sole gates and the existing neutral body/head/tail behavior; approve or reject this walk MP4 before generating other animations.

## Uncertainties and limits

- The supplied videos are rendered side views with camera/framing changes and no metric calibration. Pixel reaches are therefore only normalized visual estimates.
- The four PNGs are static captures with no known frame rate, camera intrinsics, rig scale, or temporal ordering.
- The stated adult speed range is user input for this respin, not independently sourced here; it should not be presented as a newly established scientific result.
- No trackway stride, force-plate, or direct soft-tissue evidence was available. Exact toe joint order, metatarsal pad geometry, and toe-only dwell are hypotheses to be visually approved.
- Current V8.1 reports raw root speed in the half-scale asset coordinate system (`0.504575826 m/s` over `1.576799456 m` in `3.125 s`); it must not be compared directly to the full-scale target without the profile/hip-height scale conversion. The current profile intent itself is `1.58 × 0.64 = 1.0112 m/s` (`3.64032 km/h`), below the user’s target envelope.

## Provenance

- Relaxed walk input: `/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4`, SHA-256 recorded in `metrics.json`.
- Older walk input: `/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-walk-reference-older.mp4`, SHA-256 recorded in `metrics.json`.
- Current V8.1 profile/report: `/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/reproduced_result/v8.1-final/`.
- Current V8.1 walk preview: `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1/site/v8_1_walk_side_20fps.mp4`.
- User captures and their SHA-256 values are listed in `metrics.json`; they are treated as user-supplied visual references, not project-generated assets.
