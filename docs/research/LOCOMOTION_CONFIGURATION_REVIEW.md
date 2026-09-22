# Locomotion research review — C47

2026-09-21. Read alongside [the OpenSim prototype](MOCO_TARBO_PROTOTYPE.md)
and [running evidence](RUNNING_EVIDENCE_BASELINE.md). This is the centralized
interpretation of the user's four PDFs, workbook, JSON and accompanying analysis.
The originals are research inputs, not executable instructions or approved configuration.
Input hashes and workbook checks are in `inputs/2026-09-21/source-audit.json`.

## What we can use

| Evidence | Useful constraint on our work | What it cannot supply |
|---|---|---|
| Cuff et al. 2022, PDF pp. 6–8, 14–15 | Distinguish grounded running from aerial running; model articulated feet and coupled tail/body motion. | Tarbo/Allo ankle limits, their running trajectories, or measured gait settings for the five proposed new animals. |
| Bishop, Cuff & Hutchinson 2021, PDF pp. 8–13 | Calibrate anatomical joint axes and reference pose before interpreting angles; carry mass, COM and inertia separately. | A universal dinosaur gait or a universal joint range from the Coelophysis example. |
| Sellers et al. 2017, PDF pp. 4–13 | Force feasibility and bone stress can limit otherwise attractive fast gaits. | A speed cap or airborne prohibition that transfers unchanged from a 7,206.7 kg T. rex to our 2,816.3 kg Tarbo instance. |
| Bishop et al. 2018, PDF pp. 11–17 | Characteristic posture can be tested against bone structure and external loading. | Time-dependent gait choreography or measured muscle strengths from its convenient static actuators. |

Primary sources: [Cuff 2022](https://doi.org/10.1093/icb/icac049),
[How to build a dinosaur](https://doi.org/10.1017/pab.2020.46),
[Sellers 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5518979/),
[Bishop 2018, Part II](https://doi.org/10.7717/peerj.5779).
PDF page numbers count the PDF cover where present, rather than assuming printed pagination.

### Specific traps checked against the actual pages

- Cuff Table 1 contains representative **walking stance** angles for a crocodile
  and a tinamou. These are not anatomical limits and not an aerial-running cycle.
  A relatively quiet tinamou ankle in that trial does not justify locking a
  dinosaur ankle. The toe-extension row is corrupted by plain-text extraction:
  the rendered table reads maximum −8° / 56°, not the extracted −85 / 6.
- Bishop 2021 Fig. 3 (PDF p. 12) illustrates 119° ankle flexion and 0° extension
  for that Coelophysis reconstruction. Anatomical zero, axes, specimen and soft
  tissue uncertainty must be matched before comparison with another model.
  We do not copy 119° into Tarbo's limits.
- Bishop 2018's 1,000 Nm MTP reserve is an optimization ceiling, not a strength
  measurement. Actual reserve demand in that analysis stayed below 0.41 Nm.
  It is not a justification for increasing our toe motor until a solve passes.
- Sellers' high-stress maximum around 7.7 m/s is conditional on that model and
  stress allowance. Copying it into an animal profile would erase the main point
  of the paper: feasibility depends on load and structural assumptions.

## Review of the supplied configuration proposal

The JSON and seven-sheet workbook describe Alioramus, Gallimimus, Dilophosaurus,
Prenocephale and Deinocheirus against factory commit
`987bd6b82caf3ff661d6927aa530df40fe71b30e`, not the current Moco branch.
They contain 14 proposed gait searches. `loader_compatible` is false, every gait
has `enabled_for_production: false`, and calibration fields remain empty.
Their nominal Froude numbers, duty factors, stride ratios, widths and clearances
are explicitly engineering proposals, not values measured in the four papers.

Keep these useful conventions:

1. One fixed, calibrated standing hip height **h** per animal profile.
   `Fr = v²/(g h)`; `v = sqrt(Fr g h)`. Do not substitute changing pelvis height.
2. A stride is same-foot touchdown to next same-foot touchdown.
   `T = stride_length / speed`; one step is not a whole stride.
3. Duty factor measures one foot's actual contact time divided by stride period.
   Neither Froude number nor a requested duty factor proves the mechanical gait.
4. Stance width means the full left-to-right separation, not each side's offset.
5. Toe clearance measures the lowest articulated material surface, not the ankle
   or a skeleton origin. Final skinned geometry must be checked independently.
6. Angles require anatomical frames, signs and a zero pose. Artist Euler angles
   and publication angles cannot be copied directly between rigs.

The accompanying analysis's claim that the engine has only diagnostic mass and
no force/inertia dynamics describes its older checkout. It is **not current for
the optional Moco prototype**, which already has segment inertia, gravity,
ground forces, internal actuators and an unactuated root. The proposal remains
valuable onboarding guidance; it does not supersede current implementation evidence.

The five animals remain **not onboarded**. Their suggested ordering and new gait
numbers are not activated by this review. External species sources listed in the
JSON are retained as leads, not independently revalidated in this four-PDF review.

## C47 ankle audit and implementation decision

The shared model permits sagittal ankle flexion from 0.15 to 2.25 rad
(8.59–128.92°). This is a reduced-model engineering prior, not fossil-certified
ROM. Zero aligns the shin and metatarsus downward; the interior opening is
`180° − ankle_flexion`. There is no lateral ankle joint: hip yaw/roll and body
motion establish the limb plane.

C46 reaches roughly 17–127° ankle flexion over the reflected stride. Only a
short part of recovery approaches the ankle limit, while the MTP and distal-toe
coordinates spend longer near their limits. The stance MTP motor reaches its
estimated capacity; the ankle motor does not. The global speed bound is also
above the observed ankle speed. This is not evidence of a universally locked
ankle, nor evidence for simply widening its limit.

C47 keeps the ankle/toe angular limits and strength assumptions visible. It adds
lower-envelope samples from admitted foot geometry to the optimization's floor
constraints, and tests firmer contact at the existing physical pads. These are
shared geometry-based changes. Contact pads and two reduced toe segments still
approximate the artist's separately pivoted digits, so full-skin contact remains
a separate measurement. No root force, foot teleport or rendered-only ankle
correction is introduced.

The delivered checkpoint contains `ankle-audit.json` and `ankle-contact.png`, with
native-time ankle/MTP/digit traces, bounds, loading and capacity use. Read those
with the Moco convergence and forward-integration results; an attractive replay
does not prove physical feasibility.

## Next scientific increment after visual review

First calibrate the toe/MTP contact geometry and joint frames, then test the
sensitivity to plausible toe strength and foot-pad stiffness. Do not tune those
three unknowns into one unexplained “agility” value. Use ranges with provenance,
and compare independent forward replay, contact slip and emitted skin motion.

For future rigs, admission should carry measured lengths, calibrated h, total
and segment masses, local COMs and inertias, anatomical frames and ROM, contact
surfaces, and explicitly estimated actuator capacities. The same solver consumes
those data. Bone-stress or true muscle-driven claims require additional anatomy
and a different level of calibration; they are not completed by this checkpoint.
