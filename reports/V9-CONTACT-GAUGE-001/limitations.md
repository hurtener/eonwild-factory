# V9 contact/gauge slice limitations

Status: **bounded PASS for a read-only pre-solver measurement path**. This is
not a physical-feasibility result and is not V9 completion.

The implementation evaluates the declared, immutable V8.2 root-motion clip
through the generic `src/eonwild_motion/contact_gauge.py` path. It also runs a
synthetic body-frame fixture through the same code path. The in-place clip is
intentionally rejected because measured travel is zero; this slice does not
pretend that a static clip supplies a travel tangent.

The report's contact, support-width, heading, crossover, floor-gap and
penetration values are measured geometry/animation bookkeeping under the
checked-in masks, ground level, sampling rule and thresholds. The thresholds,
mask cutoffs and narrow-gauge bands are engineering-envelope inputs. They are
labelled separately and are not fossil measurements, scientific claims, or
acceptance of physical support.

All height-normalized support, track and step widths use the analyzed-window
median hip height `H`; the optional width-normalized view uses the corresponding
window-median hip width `W`. Step width is only measured from adjacent,
chronologically ordered, alternating contralateral touchdown contact
centroids whose elapsed time is strictly greater than `1e-12 s`; simultaneous
bilateral onsets cannot form a step pair. If that pair is unavailable, the
report marks it `UNEVALUATED` and never substitutes bilateral support width.
Turn state is explicitly
`UNEVALUATED_UNSUPPORTED` because this slice does not provide local curvature,
changing tangents or inner/outer contact roles.

The implementation does not perform support-polygon or friction checks,
impulse/dynamics or whole-body solving, curve adjustment, promotion, GLB
mutation, CLI wiring, or runtime playback. The inherited toe penetration is
reported rather than corrected. No fixed-camera renderer was added because
this pre-solver slice is fully evidenced by deterministic machine output and
adding a renderer would not change the measurement contract.

The ten newly uploaded evidence videos in the source checkout were not
copied, renamed, ingested or analyzed. They remain outside this slice pending
their owner's stable-set confirmation.
