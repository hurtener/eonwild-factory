# Evidence-bound animal configuration

Animal instances bind scientific estimates to a particular admitted geometry.
The first instance is adult Tarbosaurus bataar PIN 552-1. Its grounded walk is
a candidate for evaluating a large animal at a documented scale; its mass
does not yet drive a force-based locomotion solver.

## Current adult benchmark

| Quantity | Value | Basis |
| --- | --- | --- |
| Body mass | 2816.3 kg | PIN 552-1 volumetric model, Snively et al. 2019, Tables 2–3 |
| Summed hindlimb length | 2.415 m | PIN 552-1 femur, tibia and central metatarsal, Dececchi et al. 2020, Table 1 |
| Study hip-height proxy | 1.932 m | Study assumption, 0.8 times hindlimb length |
| Source semantic hindlimb | 2.809591584 m mean | Independently reopened left and right neutral rig chains |
| Applied uniform scale | 0.8595555358917822 | Published hindlimb divided by measured mean chain |

Primary sources: [Snively et al. (2019)](https://doi.org/10.7717/peerj.6432)
and [Dececchi et al. (2020)](https://doi.org/10.1371/journal.pone.0223698).
The 2249.1 kg estimate in Snively et al. belongs to a different adult specimen,
ZPAL MgD-I/4. It is not the lower endpoint of a PIN 552-1 uncertainty interval.
The study hip-height proxy is not a measured standing posture or a target that
the solver should reach by compressing the legs.

Dececchi supplement S4 contains taxon-level segment lengths of 0.940, 0.945
and 0.535 m, without a specimen identifier. Their 2.420 m sum differs from the
PIN 552-1 Table 1 total. The instance records these as comparison evidence;
the existing rig's segment proportions differ. Uniform scale preserves those
proportions, so anatomical fit remains `UNVERIFIED`.

```sh
uv run python -m eonwild_motion.factory compile \
  --recipe recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v1.json \
  --output out/tarbosaurus-adult-walk
uv run python -m eonwild_motion.factory verify out/tarbosaurus-adult-walk
```

## Configuring another supported biped

1. Admit neutral geometry and provide its semantic rig and contact bindings.
   Measure the full neutral skin and both semantic hindlimb chains in metres.
   Preserve the geometry hash, measurement method and rig identity.
2. Create a versioned instance under `catalog/animals/`, using
   `tarbosaurus-bataar-pin-552-1.adult.v1.json` as the schema example. Supply
   taxon, specimen, life stage, units, evidence type, confidence classification,
   citation and source locator for each quantity. Keep measured geometry,
   published estimates and derived posture proxies distinguishable.
3. Bind the instance path and SHA-256 in a new recipe's optional `animal`
   field. Existing recipes retain their exact bindings. For transitions,
   start, steady and stop must bind the same instance and source profiles.
4. Compile into a fresh directory and verify the package. Inspect `animal.json`,
   `biomechanics.json`, the emitted geometry, native multi-view films and
   close contacts. Review one complete cycle and actual start/stop sequences.
   A data schema pass cannot establish anatomical or motion credibility.

Version 1 supports the existing semantic biped chain and the explicitly named
`uniform_hindlimb_match` policy. Its hip proxy is fixed at `0.8 * hindlimb`.
Another posture model, different chain topology, missing specimen evidence or
another scaling policy needs an explicit schema/policy extension. Do not fill
missing evidence with Tarbosaurus values to make another animal load.

## What the mass currently does

The compiler applies the uniform scale to the actual scene roots and the
declared contact-floor level before solving. Source calibration is independently
remeasured against the bound rig and skin. Packages retain the animal snapshot
and report root speed/acceleration, planned pelvis motion, Froude values using
two labeled height definitions, body weight, and mass-times-acceleration proxies.

Body mass currently enters those diagnostics. It does not infer segment masses,
inertia, muscle limits, tissue stress or contact-force distribution. Pelvis
acceleration is not whole-body center-of-mass acceleration, and its mass product
is not ground reaction force. The report explicitly identifies these missing
calculations. A mass-dependent solver and a second independently skinned animal
remain necessary before claiming biomechanical or production family transfer.

The prior sprint keeps its authored stride, period and flight as an engineering
benchmark. It is not the biologically accepted default for this adult instance.
Neck posture, stance loading, foot release, recovery clearance, torso/tail
coordination and acceleration/deceleration must be assessed from actual motion,
even when the configured joint and contact limits pass.

## Adult walking direction

The adult recipe binds its own gait and performance profiles. Its 1.23 s step
period, 0.62 duty factor and 0.6 reference-height step length produce a grounded,
conservative walking candidate. The current profiles author 28° push-off,
36° recovery pitch, 30° toe flex, and a 16° tail-yaw response with 0.16-cycle lag.
These are animation controls selected from emitted-motion comparison; they are
not fossil measurements or mass-derived physiological limits. The solver may
adjust targets to satisfy the actual rig/contact constraints, so inspect emitted
poses rather than assuming those values are achieved exactly.

The first 36° recovery-pitch polish was visually rejected: the emitted foot tucks
upward/forward while the supplied walking reference lets the distal chain hang
downward beneath a flexed knee. These current values are under correction and
must not be reused as an accepted animal configuration.

Forward head carriage is also an authored criterion. Inner-ear reconstructions
in related tyrannosaurids concern alert head posture and describe a somewhat
downturned head; they do not establish an exact habitual angle for Tarbosaurus.
See [Witmer and Ridgely (2009)](https://doi.org/10.1002/ar.20983). The neutral-relative
gaze correction therefore removes unwanted upward compensation without labeling
the rig's bind pose or its 3° relative attention cue as a fossil-derived posture.

[EXAMPLE_VIDEO_REVIEW.md](EXAMPLE_VIDEO_REVIEW.md) records the supplied reference
clips, frame-by-frame coverage and the criteria used to judge legs, tail, neck,
torso and start/stop staging. Profile metadata locks the selected visual-reference
identities and labels their role. The compiler does not import their animation.
