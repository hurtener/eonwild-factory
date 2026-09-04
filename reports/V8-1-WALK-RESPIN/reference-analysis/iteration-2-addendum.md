# V8.1 walk respin — iteration-2 motion-direction addendum

Status: bounded read-only handoff for the next walk-only MP4. This responds to the
rejected iteration-3 render. It is an 8.1 correction, not a return to V5.5. No engine,
source asset, generated GLB, or media file was edited.

## Direct handoff

Use one foot's normalized cycle phase `φ`, where `φ=0` is that foot's receiving
contact and `φ=1` is its next receiving contact. The opposite foot remains half a
cycle out of phase. The target is:

```
same-foot stride       2.60 m
speed                  4.60 km/h = 1.277777778 m/s
cycle_hz               0.4914529915 Hz (center; T = 2.034782609 s)
alternate contacts     1.017391304 s apart
two-cycle approval MP4 4.069565217 s before frame-rounding
```

The 12 m nose-to-tail length and 2.75 m hip height establish reference scale; they do
not determine the stride without the speed/cadence product. `2.60 × 0.4914529915`
is the required `1.277777778 m/s`.

### Required phase ordering

The implementation should preserve the V8.1 body/head/tail behavior and change only
the walk timing/rocker state in this approval pass.

| State | Phase target | Bounded range | Required read |
|---|---:|---:|---|
| Load continuity / loaded micro-sample window | `.40–.72` | fixed window | 18 internal monotone control knots; allow 15–20 valid loaded samples per side |
| Rocker onset | `.46` | `.44–.48` | begin before full rear extension; use the foot/metatarsal rocker, not a late swing pop |
| Rear-extension soft maximum | `.56` | `.54–.58` | measured pelvis-to-rear-foot extent peaks softly, then is alleviated |
| Toe-only loaded dwell begins | `.64` | enforce release minus `.08–.12` | bead/metatarsal is rising while selected distal toe patch remains loaded |
| Toe-patch release | `.72` | `.70–.74` | release only after rocker; no whole-foot lift or sole snap |
| Passive/unloaded lag | `.75` | `.72–.80`, duration `.05–.08` | no active toe/ankle receiving arm; residual distal motion is free-weight/damped |
| Receiving toe/ankle arm starts | `.82` | `.80–.86` (never before `.78`) | only now begin active preparation for the next contact |
| Receiving flatten / precontact | `.90` | `.88–1.00` | progressively flatten toward broad contact at `φ=1` |

The hard ordering gate is `φ_rocker_start <= φ_rear_extent_peak - 0.06`.
The center values provide approximately `0.10` cycle of lead. At the target period,
the rocker onset is about `0.936 s` after contact, release about `1.465 s`, and the
passive interval lasts about `0.102–0.163 s`.

Do not let rear extension continue to its maximum while the rocker is already active:
after `φ=.46`, rear extent should plateau and then shorten smoothly. The maximum is a
soft kinematic turning point; it is not a hard knee stop.

### Curve and control-shape requirements

- Generate `18` internal phase knots across `.40–.72` (bounded `15–20`). The first
  knots maintain loaded continuity; the monotone rocker ramp is visible by `.44–.48`.
  This is a control-sample count, not a request to lower the 24 fps render rate.
- Use C2 minimum-jerk or no-overshoot cubic-Hermite interpolation. Do not use a step,
  linear snap, or a second rear-extension overshoot.
- From `.40–.48`, increase metatarsal lift shallowly. From `.48–.60`, lift
  monotonically while rear extent velocity falls through zero. From `.60–.68`, hold
  the distal patch loaded while the bead rises. From `.68–.72`, use a short smooth
  release ramp.
- During `.72–.78` (or `.72–.80` at the upper bound), remove the active toe/ankle
  target arm. Preserve residual angular velocity/angle as passive lag, then damp it;
  do not immediately reverse it into the receiving pose.
- Begin the receiving arm only at `.80–.86`, and reserve the final `.88–1.00` for
  low-amplitude precontact flattening. The receiving contact must be broad and nearly
  flat, not a toe-first slap.

### Bounded angular and passive response values

These are bounded tuning values for the existing 8.1 rig semantics, not new anatomy
claims:

| Control | Center | Bound / gate |
|---|---:|---:|
| loaded bead/metatarsal pitch | `9°` | `8–10°`, do not exceed `12°` |
| loaded toe push | `12°` | `10–14°`; keep distal patch down |
| broad contact foot pitch | `1°` | `0–2°` |
| active receiving ankle arm | `8°` | `8–10°`, starts only at `.80–.86` |
| passive toe/ankle residual excursion | `≤2°` typical | `≤4°`; no active target edit in lag |

If the implementation exposes a time-domain passive spring, use a critically damped
or very lightly underdamped response (`ζ=.85–1.00`) over `.05–.08` cycle, with no more
than one small lobe and no rebound large enough to re-extend the rear leg. A useful
seconds-domain starting band is `ω_n≈18–28 s⁻¹` for this `T=2.0348 s` cycle, selected
so the residual distal angle is at most `25–30%` when the receiving arm starts. If
the rig is phase-keyed rather than simulated, implement the same behavior as a C2
decay to the receiving target; do not invent a separate dynamics system for this
approval MP4.

## Measurable approval gates

1. **Kinematics:** manifest/root track at reference scale reports same-foot stride
   `2.60 m ±1%` (`2.574–2.626 m`), center cadence `.491453 Hz ±.005 Hz`, and mean
   speed centered at `4.60 km/h`; the accepted envelope remains `4.50–4.80 km/h`.
2. **Timing:** two complete cycles last `4.0696 s` within frame-rounding tolerance;
   alternate contacts are `1.0174 s` apart.
3. **Ordering:** measured rear extent maximum is in `.54–.58`; rocker onset is in
   `.44–.48` and at least `.06` cycle earlier. After onset, rear extent has no second
   maximum larger than `5%` of the first.
4. **Loaded rocker:** each side has `15–20` valid loaded control samples (center
   `18`) across `.40–.72`; toe-patch contact remains within the existing `0.008 m`
   quantile tolerance while the metatarsal lift is at least `0.004 m` and preferably
   `0.006–0.012 m`. No sole penetration exceeds the existing `0.002 m` gate.
5. **Toe-only sequence:** toe-only dwell duration is `.08–.12` cycle; release lies in
   `.70–.74` and occurs after the bead/metatarsal lift. No selected distal patch loses
   load early, and no whole-foot vertical hop substitutes for the rocker.
6. **Passive lag:** release to active receiving arm is `.05–.08` cycle; target arm
   contribution is zero during the lag, residual angle decays to `≤25–30%`, passive
   excursion is `≤4°`, and angular velocity has no sharp sign reversal or rebound.
7. **Receiving contact:** first active receiving toe/ankle control is `≥.80`; flattening
   begins `≥.88`; the next support reads broad/flat before load transfer. Existing
   angular caps (`390°/s`, `9000°/s²`) and support/no-hover checks remain in force.
8. **Editorial review:** approve only the isolated side walk MP4, ideally at 24 fps
   plus a 0.5× frame review and a close foot crop. Do not generate the remaining
   animation set until this walk passes the gates.

## What was inspected and what it supports

- The relaxed source was decoded at native 24 fps and shows broad support, late
  bead/metatarsal rise with distal toe retention, brief toe-only support, release,
  folded swing, and progressive receiving flattening. Its same-foot timing is about
  2.0 s, but exact event labels are not calibrated.
- The four user captures consistently show the forward broad planted foot and the
  rear foot behind the body with the bead raised and distal digits retained on the
  floor. They provide the qualitative rocker cue, not temporal or metric calibration.
- The iteration-3 side render reads as too late/abrupt at the rocker relative to rear
  extension and does not visibly separate toe release from a short passive lag before
  the receiving arm. This is a visual diagnosis, not a tracked joint measurement;
  floor shading and the editorial camera make exact contact pixels uncertain.
- The render provenance says the iteration-3 MP4 is a walk-only editorial output, but
  its `render-run.json` imports the iteration-15 candidate GLB. The MP4 is therefore
  the visual truth for this rejection while the profile/validation values are only
  supporting implementation context. Keep that distinction in the handoff.

## Uncertainties

- User speed (`4.5–4.8 km/h`, with this pass centered at `4.60`) is a tuning input,
  not independently established in this report.
- Still images have no temporal ordering, camera intrinsics, ground calibration, or
  rig scale. Exact digit release order remains unresolved; do not hard-code a
  scientifically asserted per-digit sequence.
- “15–20 samples” is interpreted as loaded control/validation samples in the phase
  curve. A 24 fps editorial file may show fewer visible frames in a `.40–.72`
  window; that does not justify reducing the underlying knots.
- The passive spring values are implementation bounds. If the existing generator has
  no dynamics state, a phase-keyed C2 decay is the bounded equivalent for this respin.

## Provenance

- Rejected iteration-3 side MP4:
  `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin/iteration-3/walk-relaxed-v8-1-respin-side.mp4`
  SHA-256 `4a654cad0878dcb710090b44d7647644215b0c3b9a696566c1638ecf347145dc`;
  H.264, `960×540`, `24 fps`, `240` frames, `10.000 s`.
- Relaxed source:
  `/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8.1)/inputs/v8/tarbosaurus-relaxed-walk-reference.mp4`
  SHA-256 `b0401fc76a202d6ed5dc9a5515f1054eab8bed8075c04f6167ff426fd603f5ae`;
  H.264, `672×448`, `24 fps`, `241` frames, `10.041667 s`.
- Iteration-3 `render-run.json` records iteration-15 input GLB SHA-256
  `96bf5c37402bd784b23785173fbb9a45cd8cbbed33ea2fd0675bdfd11c48a5a1` and a
  walk-only editorial policy; no source/engine/media file was changed here.
- Existing four still-capture hashes and observations remain in
  `metrics.json`; their static evidence is not reinterpreted as timing data.
