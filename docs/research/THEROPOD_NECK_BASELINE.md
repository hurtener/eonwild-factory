# Theropod neck and attention baseline

Adopted 2026-09-14 from the user's investigation. This is an editable animation
baseline with explicit evidence classes, not a claim of measured dinosaur limits.
The [original investigation](user-notes/2026-09-14-theropod-neck-investigation.md)
is preserved verbatim as user-supplied research, including proposals not implemented.
This document resolves its overlapping ranges for the engine.

## Evidence and interpretation

- **NECK-TREX-60 — published model estimate.** Snively & Russell (2007),
  *Craniocervical feeding dynamics of Tyrannosaurus rex*, DOI 10.1666/06059.1,
  Materials and Methods / Specifying Skeletal Geometry, explicitly models a
  skull heading 60 degrees from the midsagittal plane. The reconstruction uses
  at least 50% articular overlap, no bony collision, and muscle/tendon spans no
  longer than 130% of neutral. Verified against the
  [primary-paper transcription archived by Plazi on Zenodo](https://zenodo.org/records/3809066).
  This is one modeled posture under assumptions, not a measured habitual range
  or proof of a universal hard stop. The extra 5 degrees in our rig is authored.
- **NECK-ALLO-LATERAL — published qualitative model result.** Snively et al.
  (2013), DOI 10.26879/338, Results / Kinematics and Figure 11, reports maintained
  joint contact in its lateral pose and possible further range. It compares
  anterior intervertebral mobility favorably with T. rex. No total yaw maximum
  is published. [Primary paper](https://www.palaeo-electronica.org/content/2013/389-allosaurus-feeding).
  Our Allosaurus numeric ranges are user-proposed reconstruction estimates.
- **NECK-TARBO-PROXY — comparative inference.** Transfer the tyrannosaur posture
  baseline to Tarbosaurus as a provisional related-animal prior. No equivalent
  Tarbosaurus full-neck quantitative result was verified. Do not relabel this
  as direct Tarbosaurus evidence or infer it from body mass alone.
- **NECK-REGIONS — authored rig approximation.** More even Allosaurus bend and
  a stiffer Tarbosaurus base are the adopted visual direction. The numerical
  weights are authored, not measured vertebral contributions. Allosaurus has
  only two admitted neck controls; these are not two anatomical vertebrae.

Reviewed sources on 2026-09-14. Other papers linked in the original investigation
remain leads for field-of-view, regional mobility and coupled rotation. Its
visibility-by-angle table is not admitted as a sensing or occlusion model.

## Operational values

All angles are degrees **per side**, measured as skull heading relative to torso
heading in the horizontal plane. They are cumulative across the neck and head,
not a rotation assigned to the atlas, or permission to turn the head backward.

| Admitted profile | Ordinary target | Scan target | Strong / soft onset | Routine cap | Exceptional cap | Request body follow after |
|---|---:|---:|---:|---:|---:|---:|
| Allosaurus | 40 | 55 | 70 | 80 | 85 | 70 |
| Tarbosaurus | 35 | 45 | 55 | 60 | 65 | 45 |

These values have low confidence as precise biological degrees. They are useful
artistic defaults pending actual-rig review. In the current implementation,
commands stay unchanged through the strong range, then saturate smoothly toward
the routine cap. Exceptional motion requires explicit selection. Never treat
maximum-range demonstration as evidence of a comfortable repeated pose.

83% of yaw goes through the neck and 17% through the head. Ordered base-to-head
neck weights are [0.48, 0.52] for Allosaurus and [0.06, 0.10, 0.18, 0.28, 0.38]
for Tarbosaurus. The solver reads semantic roles and numbers, never species names.
Add neck controls during admission if more detailed curvature is needed; do not
pretend adding rotations creates missing articulation.

## Current and future movement use

The canonical profile's attention.envelope is the numeric authority. Python
validates it; the directional baker bounds attention before contact corrections.
The Unity consumer receives the same profile and numerical reference vectors.
New reverse recipe v2 uses the profile's ordinary target; `none` keeps attention
forward, and scan/strong intents are explicit choices. Existing v1 recipe and
approved motion bytes remain available as historical inputs.

Attention target choice is separate from retreat: face a threat while backing
away, or inspect a flank when choosing space. A sideways snout direction does
not establish what the animal can see; eye orientation and body occlusion matter.

The envelope returns requested body follow and unfulfilled yaw. It does not
rotate the chest, pelvis, root or planted feet. A grounded turn behavior/motor
must fulfill that request with its own support choreography. Full automatic
body following is pending, as are coupled regional yaw/roll/pitch and anatomical
soft-tissue or joint-surface verification. The original suggested 5–10-degree
roll is retained as a future authored trial, not silently treated as research.

Historical compilers without embodiment inputs retain their original envelopes;
they are not retroactively certified. Feeding, attacks, running and future
families must adopt this shared profile layer and reopen their emitted motion
before claiming coverage. Prevent a runtime overlay from doubling baked gaze.

## Future onboarding priors

The user's T. rex 60–65, Daspletosaurus 60–70, albertosaurine 55–65,
Carnotaurus 55–65, dromaeosaur 60–70 and ornithomimid 75–90-degree proposals
are retained in the original note. They are unadmitted reconstruction leads,
not production presets. A new model needs evidence classification, explicit
regional controls, a chosen routine/exceptional envelope, source identity,
actual-rig review and contact checks. Do not scale neck ROM automatically from
mass, agility index or phylogenetic labels, or copy a profile's confidence.

## Review status

Checkpoint 19 applies this baseline to a new backward candidate on both rigs.
Checkpoint 18 remains preserved and unapproved. Earlier approved walking and
turning exports are unchanged. New range settings and source research are
adopted implementation inputs; animation approval remains a separate review.
