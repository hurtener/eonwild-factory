# Adult body transfer Candidate B

Status: **IMPROVED OVER V3 AND CANDIDATE A; WHOLE-BODY POLISH REQUIRED.**
Candidate B is the latest bounded body-response diagnostic. It preserves the
accepted adult-v3 leg recovery and improves visible lateral support transfer,
but it does not yet convey the requested several-ton effort across the whole
body. Biological validation is not established, Unity parity is not run, and
production approval is false.

## Change under review

Candidate B retains Candidate A's support-timed pelvis carrier and walking-style
kinematic height proxy. It changes only three art-directed performance values:

- pelvis sway rises from `0.006` to `0.018` body heights;
- pelvis roll rises from `0.6` to `1.5` degrees;
- `0.9` degree of upper-trunk counterroll is distributed progressively over
  the admitted semantic spine and chest on the same continuous support clock.

Pelvis yaw, gaze, neck, tail and height inputs remain unchanged. The v4 gait
profile is byte-identical to Candidate A, so stride, cadence, duty factor,
contacts, leg recovery, clearance, stance anchors and articulation inputs are
unchanged. These controls are a kinematic coordination hypothesis. They do not
model center of mass, ground-reaction force, torque, muscle capacity or a
mass-dependent response.

Reusable counterroll controls are commit
`02adf3831e5d308b2b0cf906c45b0fc83f52c82d`; versioned v5 inputs are commit
`329b150566d08c2a2ca19153aa844f8ae054855f`. Narrow review then found that a
malformed semantic rig could bind a leg chain as the trunk. Commit
`64dd6b4ae45e297eef968b116bbc2cca700617b8` closes that boundary by requiring a
typed, nonempty, cross-role-disjoint, contiguous semantic spine/chest chain.
The narrow P1 re-review is clean. Commit
`2199e7f2fb4040b4988a7a267f2b0a9b7eb5a2a5` adds v5 alongside retained v3 in
candidate and native-review CI matrices. The one-cycle recipe is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v5.json`.

## Reopened emitted evidence

The authoritative post-fix package is retained outside Git at
`out/continuation-adult-v5-body-counterroll-postfix-001/package`. Its 297
serialized keys span one 2.46-second cycle. `factory verify` reports integrity
and technical PASS. Key hashes are:

- manifest: `8408608975c8499a1676f91228c18650557ae71c0c46961bff72d0eb30332229`
- root-motion GLB: `6f7c6fb7ee79055c66f0f76be150a5c72cbe919fa9514c11ffb64915ee8fecf4`
- in-place GLB: `8dff0f9d4c92e73cda477e05ad554e536967b2c46a3df89748538fe0bfe4d086`
- plan: `76a92ae16caf5c5d03f2b1772aaf6f3d3878fd2bb84ec7b9b681a0ae83e30540`
- solver receipt: `b0f51ab50762a54a9369aded2d0e3200eb1ccb8aff699cd393f7d693a2938bfd`
- validation: `bacf5bc4025e87c9e93084e4a46bf1f4ab611e2afdd183fbde41ca28b06488bf`
- input lock: `3c08cfa5fec0daef9c50bfa0ca1e3e682b990fb96304c3002f593e6e96e5cd5a`

The original review package was generated at v5 input commit `329b150`. After
the semantic-binding fix, a fresh compile reproduced both GLBs, the plan,
solver receipt, runtime and validation byte for byte. Only the input lock and
manifest changed because the authoritative package truthfully locks the fixed
source. The exact comparison is in `host-postfix-equivalence.json`.

All 297 authored plan samples are exactly equal between A and B after excluding
compiler-owned skin-refinement offsets. The maximum change in those offsets is
0.000759 mm. Leg-local translations remain constant. Final full-patch
interior-swing clearance is 35.214 mm left and 40.603 mm right. Maximum hard
articulation violation and skin penetration are zero. Final contact, scalar
articulation, feasibility, serialized rotation-rate and cyclic-continuity gates
all pass. The maximum serialized rotation rate is 630.456 degrees/second under
the unchanged 1200 limit; solved foot-pitch rate is 470.661 degrees/second under
the unchanged 600 limit.

At the nearest emitted declared stance-midpoint samples, pelvis translation is
40.871 mm toward the support side and pelvis roll is 1.500 degrees toward that
side. The bilateral hip midpoint moves 36.195 mm left and 35.989 mm right. The
torso-surface proxy also lies supportward at both samples. At left support,
world roll progresses from 1.500 degrees at the pelvis through 1.410, 1.296,
1.158, 0.996 and 0.810 degrees over the semantic spine to 0.599 degrees at the
chest; the right-support response mirrors it. Head world orientation differs
from Candidate A by at most 0.001567 degree after gaze stabilization. Tail
inputs are unchanged; its emitted world response changes by at most 1.080
degrees because its parent pelvis response changed.

## Host visual boundary

The host inspected all 370 rendered review frames across five native-time views,
verified all films, clocks, cameras and hashes, and completed native-speed
browser playback for the four A/B/v3 comparisons plus the v3/B root-motion
pair. Candidate B shows clearer supportward weight-transfer direction and a
distributed torso response without disturbing the recovered legs. It remains
too level and even through the sagittal body, neck and tail profile to satisfy
the requested impression of a several-ton animal. This is `POLISH_REQUIRED`,
not a body-motion, art-direction, biological, Unity or production approval. No
third amplitude trial was made.

`audit-summary.json` is the tracked compact mechanical record. The full host
audit artifacts remain outside Git with SHA-256
`3499f467ed9aae5ebf981e8b548fdeea791e5eced7233047036fb68e50dd859d`
and `26034b89befca9ed0e4749e6edded066c3fc920ede760786f3f19f99837fab61`.
`candidate-a-host-review.json` preserves the causal baseline decision;
`host-review.json` records B's visual boundary. `review-round2.md` and
`review-p1-closure.md` preserve the exact finding and narrow closure.
`review-round2-mechanics.md` preserves the independent clean B mechanics review;
`candidate-a-review-mechanics.md` and `candidate-a-review-integrity.md` retain
both clean reviews of the causal A baseline.

The mandatory suite for exact head
`2199e7f2fb4040b4988a7a267f2b0a9b7eb5a2a5` passed 716 tests plus 21
subtests in 306.42 seconds with the pinned real Blender and Khronos tools.
`host-validation.json` records the exact command, toolchain, log/XML hashes and
the initial sparse-checkout collection error in which no tests ran before the
full tracked checkout was restored. Hosted CI remains pending.

`followup-sagittal-diagnosis.md` is a read-only diagnosis of the remaining
level side profile. It records that no authored support-timed sagittal carrier
exists and sets boundaries for a possible future experiment. It does not
authorize a third candidate, numeric tuning, a gate change or an anatomical
claim.
