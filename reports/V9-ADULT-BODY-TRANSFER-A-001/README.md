# Adult body transfer Candidate A

Status: **MECHANISM CORRECT; WHOLE-BODY POLISH REQUIRED.** This is a bounded body
coordination diagnostic. It does not replace or approve the current adult v3
candidate. Biological validation is not established, Unity parity is not run,
and production approval is false.

## Change under review

Candidate A preserves the adult v3 source, rig, animal, contact, articulation,
stride, cadence and full leg-recovery program. The new v4 gait profile opts into
`stance_vault_proxy`, which shifts the existing 0.016 body-height pelvis-height
wave without changing its range. The proxy is highest at each declared stance
midpoint and lowest at each double-support midpoint. It is a kinematic pelvis
proxy, not a center-of-mass, force, or energy-conservation model.

The v3 performance profile retains the existing 0.006 body-height sway, 0.6
degree roll, 2 degree yaw and tail/head settings. It opts into
`support_directed_pelvis_carrier`, a continuous clock derived from duty factor
and semantic bilateral hip geometry. Pelvis translation and top lean point
toward the declared support side and pass through the center at double-support
midpoints. Yaw, chest, neck, head and tail control laws are unchanged.

Reusable controls are commit
`73fd34f44efd6a917831565be9451556ffc3989e`; versioned candidate inputs are
commit `9d5ae0fe873507e6088714727943dfd8b293b2c2`, based on published commit
`63b87b3e140314c051c92ffa901eb407b79a986a`. The one-cycle recipe is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v4.json`.

## Reopened emitted evidence

The immutable package is retained outside Git at
`out/continuation-adult-v4-body-carrier-001/package`. Its 297 serialized keys
span one 2.46 second cycle. `factory verify` reports integrity and technical
PASS. Key hashes are:

- manifest: `3b26f33d3cc1f248775c861b84153d51bfb5db3c211822a37f15a8747ee4d7d9`
- root-motion GLB: `fa6e3a11b9d1d017c3945758d976e97cfe4812960e087dad00eb37436a7840d6`
- in-place GLB: `8adbe7f17434fb8a9fe8d4956a46ff8d78e803495a10690722514659783a5e3b`
- plan: `b771a4f37ca29db67739215c37601438e8e5e59f20a59f0c191d233ce1bfe6f8`
- solver receipt: `05a253927cb0415e65f015e82a99c87d0be44e904fe7f62d27398e66bf1dbb2a`
- validation: `686119815ab92dc118a7209cd520cfab5bfdf0c8c9c3ecfaf184e2bbab0b3a7c`

At the nearest emitted left and right declared stance-midpoint samples, the v3
pelvis translated 12.642 mm away from support. Candidate A translates 13.624 mm
toward support; the bilateral hip midpoint moves 10.100 mm left and 9.962 mm
right respectively. Pelvis top lean follows the same support side. At the
nearest double-support midpoints, lateral pelvis displacement is within 0.070
mm of center. Height is within 0.001 mm of the proxy maximum at declared stance
midpoints and at the -36.330 mm minimum near double-support midpoints.

All authored foot/contact/recovery sample fields are identical to v3. The
largest difference in pre-solve skin-refinement target offset is 0.000427 mm.
Final full-patch interior-swing clearance is 35.214 mm left and 40.603 mm right,
matching v3 within 0.000030 mm. Final contact, skin, rotation-rate, cyclic and
scalar articulation gates pass; maximum skin penetration and hard articulation
violation are zero. Peak serialized rotation rate is 620.509 degrees/second
under the unchanged 1200 limit.

The torso-only uniform-vertex surface centroid remains asymmetric and is not a
center-of-mass estimate. At the left declared stance midpoint it remains 16.611
mm to positive lateral while pelvis and hip proxies move supportward. The spine
still follows the pelvis rigidly. Candidate A therefore establishes a clean phase/sign correction. Host review of
the front and three-quarter native playback still found a largely rigid torso
carried by active legs. Candidate A is retained as the causal baseline and is
not accepted as the whole-body correction. Candidate B may add a bounded axial
response without changing the accepted leg program.

The structured summary is `audit-summary.json`. Its source comparison artifact
is retained on the host with SHA-256
`bfb765ada2fa74d895ffd367941458224e37a0800bfa15a6d150d9e427b4463f`.
