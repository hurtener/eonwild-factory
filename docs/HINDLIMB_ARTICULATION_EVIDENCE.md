# Hindlimb articulation evidence and current limits

This note records the evidence used to assess the Tarbosaurus motion
candidates. It does not establish a measured Tarbosaurus joint range. No
published specimen-specific range of motion for PIN 552-1 was found in this
review, and values from *Tyrannosaurus rex* or living birds remain explicitly
comparative.

## Angle conventions

Numbers are comparable only after their zero pose and sign are stated.

- The factory recovery audit reports the smaller geometric angle between
  adjacent segment directions: `0 degrees` is folded and `180 degrees` is
  straight. It is a descriptive scalar derived from the emitted rig, not a
  complete anatomical joint coordinate system.
- [Hutchinson et al. (2005)](https://doi.org/10.1666/04044.1) use a straight
  reference at `0 degrees`; positive knee values are flexion and the model
  permits `-10 to 90 degrees`. Their stated conversion gives a geometric knee
  interior of `180 - model angle`, or `90 to 190 degrees`. The negative endpoint
  represents modeled hyperextension and is not a value to transfer to this rig.
- [Gatesy, Bäker and Hutchinson (2009)](https://doi.org/10.1671/039.029.0213)
  use `0 degrees` fully flexed and `180 degrees` fully extended for the knee and
  ankle, matching the geometric-interior direction used here. Their hip and MTP
  conventions differ. An author-hosted copy is available from the
  [Royal Veterinary College](https://www.rvc.ac.uk/Media/Default/Structure%20and%20Motion/Documents/23_000.pdf).
- [Rubenson et al. (2007)](https://doi.org/10.1242/jeb.02792) use positive
  flexion from a straight segment-coordinate reference for the knee and ankle,
  so their plotted knee and ankle values convert approximately as
  `geometric interior = 180 - flexion`. Their MTP zero places the phalanges
  perpendicular to the tarsometatarsus and cannot use that conversion.
- [Gatesy et al. (2022)](https://doi.org/10.1111/joa.13635) provide the preferred
  reproducible archosaur convention: anatomical coordinate systems on the
  proximal and distal segments, with flexion-extension, abduction-adduction and
  long-axis rotation defined by a joint coordinate system. Future evidence
  records should state this coordinate basis or a complete equivalent.

## What the studies constrain

The two *T. rex* models do not yield one interchangeable knee limit.
Hutchinson et al. (2005) selected the `90 to 190 degree` geometric-interior
range for a three-dimensional muscle moment-arm exploration. Gatesy et al.
(2009) began a two-dimensional mid-stance search with morphology-derived
geometric ranges of `30 to 180 degrees` at the knee and `90 to 180 degrees` at
the ankle. After ground and kinetic exclusions, 2,391 slow-running-capable
loaded mid-stance poses occupied `108 to 141 degrees` at the knee and
`132 to 168 degrees` at the ankle. Only one in thirteen combinations inside
those scalar subranges remained viable. The authors also describe their
geometric mobility estimates as potentially liberal. The loaded mid-stance
subset is not an unloaded swing range, and neither paper measures Tarbosaurus.

Rubenson et al. (2007) measured running ostriches with surface-marker motion
capture and related the measurements to anatomical specimens; it was not an
XROMM study. Their figures show knee and intertarsal flexion increasing after
toe-off, reaching their most flexed region around mid-swing, and then extending
toward toe strike. Approximate readings from the published plots put the knee
near a `65 degree` geometric interior and the ankle near `75 degrees` around
mid-swing. These are plot readings from a derived living bird, not numeric
Tarbosaurus limits. The reported functional axes and out-of-plane rotations
also show why a lateral-view interior angle cannot describe the full joint
pose.

[Schaller et al. (2009)](https://doi.org/10.1111/j.1469-7580.2009.01083.x)
measured passive ostrich intertarsal motion and found a much wider passive range
than the near-extended angles used during loaded stance. Preparation and
measurement method changed the reported extrema. Passive mobility, loaded
support and unloaded recovery therefore require separate evidence labels.

Three-dimensional studies further limit what scalar gates can claim.
[Kambic, Roberts and Gatesy (2017)](https://doi.org/10.1111/joa.12680) found
strong coupling among flexion-extension, abduction-adduction and long-axis
rotation in intact avian hindlimb joints; axis-aligned minima and maxima include
many poses outside the measured mobility envelope.
[Manafzadeh and Gatesy (2021)](https://doi.org/10.1111/joa.13513) showed that
osteological simulations can overestimate total mobility while still missing
real local poses when joint translations are omitted.
[Manafzadeh, Gatesy and Bhullar (2024)](https://doi.org/10.1038/s41467-024-44832-z)
used articular-surface interaction to distinguish plausible locomotor poses,
including a small set of highly flexed, fast mid-swing exceptions in living
birds. These methods provide pose plausibility and uncertainty evidence; they
do not supply a Tarbosaurus scalar range.

[Manafzadeh et al. (2025)](https://doi.org/10.1038/s41586-024-08251-w) infer that
early theropod knees were restricted to more hinge-like motion before fibular
reduction enabled the extreme long-axis rotation of modern birds. This supports
anatomically registered local hinge axes for non-avian theropod candidates. It
does not justify copying modern avian long-axis rotation or assigning a numeric
Tarbosaurus envelope.

## Factory interpretation

The present scalar engine cannot represent a coupled three-dimensional
articulation envelope or an articular-surface score. Source-bone translations
remain disallowed. Six-degree-of-freedom studies therefore bound the strength of
our biological claims; they do not describe functionality already implemented
by the compiler.

The current `65 degree` knee-interior floor should not be lowered merely to make
a candidate feasible. The ostrich plot reaches approximately that value during
unloaded recovery, while the two *T. rex* modeling studies disagree too strongly
to establish a more-flexed Tarbosaurus endpoint. The Gatesy et al. (2009)
`90 degree` ankle floor is useful as a *T. rex* model-derived sensitivity check,
not as a measured Tarbosaurus gate. A candidate below it requires explicit
review rather than automatic biological approval.

Any future limit change should be versioned with the animal evidence record and
must identify taxon or specimen, source, coordinate convention, modeled or
observed status, and applicable phase: passive osteological mobility, loaded
stance or unloaded recovery. Scalar limits remain conservative engineering
exclusions. They cannot by themselves establish anatomical correctness, and a
candidate must still pass emitted-skin, clearance, rate, contact, bilateral and
native-time visual review.
