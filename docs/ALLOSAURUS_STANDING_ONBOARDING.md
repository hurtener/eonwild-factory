# Allosaurus standing-pose onboarding

An imported A-pose or T-pose is rig-binding input. It is not the animal's living standing baseline and its joint angles are not posture evidence. The factory keeps the imported bind geometry available for deterministic skinning, then creates an explicit, hash-bound derived source for the calibrated standing neutral used by locomotion. Every articulation or posture value must carry cited scientific evidence or be labeled as an authored estimate with confidence, provenance, and limitations.

The onboarding order is fixed:

1. **Admit the original source and prepare the rig.** Fit the semantic pivots and deformation ownership first. Preserve the original asset, and record the prepared source hash, node hierarchy, rest transforms, skin joints, inverse-bind matrices, vertex attributes, and influence normalization.
2. **Create an explicit standing source.** `prepare_standing_pose` in `eonwild_motion.factory.standing_preparation` applies the declared engineering standing calibration to a new derived GLB. The current candidate requests a 30-degree hip, 125-degree knee, and 25-degree metatarsus posture. The ankle world orientation changes with the metatarsus direction; the metatarsophalangeal joint, pad, and toe world orientations are preserved, and a root translation restores the bilateral full-skin plantar floor. Their horizontal positions may change as the leg pose changes. Those angle values are authored engineering estimates with provisional confidence; they are not inferred from the imported A-pose and are not measured anatomy, biological optima, or range-of-motion claims. The derived GLB contains no animation.
3. **Measure the derived standing geometry.** Reopen the exact derived bytes and compute body height, bilateral full-weight skin floor, contact masks, semantic segment lengths, and neutral-support/touchdown geometry. A measurement from the earlier A-pose is stale for this source even when the mesh, weights, and inverse-bind matrices are unchanged.
4. **Bind the shared motion baseline.** A future Allosaurus animal/baseline version binds the derived source and every recalculated calibration by path and SHA-256. Walk, fast walk, and their transitions can then reuse that animal standing source. Motion intents own timing and choreography; they do not carry private standing offsets. This preparation stage does not recompile or rerender those motions.
5. **Reopen emitted motion.** Validate the final root-motion and in-place GLBs against the bound floor, complete skin influences, contact ownership, support geometry, joint and reach limits, interpolation, loop continuity, and package provenance. Rendering starts only after these gates report their real status.

The standing derivation must not rewrite the imported source under its old hash or reinterpret its inverse-bind matrices. It may change the derived source's default joint transforms because that change is the purpose of the new asset. The receipt must state the input and output hashes, declared joint rotations, changed ankle orientation, preserved metatarsophalangeal/pad/toe world orientations, measured full-skin floor translation, and all preserved structural fields. It must not claim that distal world positions are preserved.

The reproducible command shape is:

```bash
python -m eonwild_motion.factory.standing_preparation \
  --source <prepared-source.glb> \
  --rig <semantic-rig.json> \
  --contact <contact-profile.json> \
  --config <standing-preparation.json> \
  --output <new-empty-output-directory>
```

The configuration is `catalog/standing-preparation/allosaurus-engineering-standing.v1.json`, with schema `eonwild.motion.standing-pose-preparation.v1`, model `bilateral_semantic_sagittal_standing.v1`, and explicit `hip_sagittal_degrees`, `knee_interior_degrees`, and `metatarsus_sagittal_degrees` inputs. The public function is `prepare_standing_pose(source, *, semantic_roles, contact_profile, config)`. The command must write a new output rather than replace the input source; the output directory contains `geometry.glb` and `receipt.json`.

The initial implementation is bound to commit `8ab72cdd99e4f531308704815e991ecf344973ca`. Its derived candidate geometry has SHA-256 `b6be08e94f5ba3a24e83023669393c7eba922c02afd22e97d518170a4739027e`; this identity records an engineering candidate rather than visual or production approval.

Tarbosaurus is outside this calibration. Its source, animal configuration, shared baseline, emitted packages, and reviewed media remain byte-identical unless a separate versioned change is explicitly made.

This stage establishes a reproducible engineering standing pose. It does not establish fossil joint centers, soft-tissue volume, mass dynamics, muscle capacity, digit anatomy, or production approval.

## Standing and behavior roles

The derived source in this stage is only the **calibrated standing neutral**. It does not yet implement usual-standing, resting, ready, or balance-recovery behaviors. Those roles require separate, versioned behavior policies and contact choreography.

The intended configurable defaults are a staggered usual stance with one foot behind, rear-foot initiation when leaving that stance, a wider support base during balance recovery, and a narrower track during locomotion. These are authored design defaults pending their own evidence and validation; they are not universal dinosaur behavior claims. A behavior must move between them through continuous, declared foot-contact phases. It may not teleport the skeleton, hide offsets in rest transforms, or silently slide an anchor.

Floor, contact, reach, interpolation, and full-skin constraints run after each posture or stance change. Shared solvers consume semantic calibration and behavior data, with no Allosaurus-specific solver branch.

## Evidence boundary

[Gatesy et al. (2022), “A proposed standard for quantifying 3-D hindlimb joint poses in living and extinct archosaurs”](https://pmc.ncbi.nlm.nih.gov/articles/PMC9178381/) supports keeping a reference coordinate pose distinct from a posed Allosaurus. It does not prescribe the candidate's standing angles. [Bates, Benson, and Falkingham (2012), “A computational analysis of locomotor anatomy and body mass evolution in Allosauroidea”](https://www.cambridge.org/core/journals/paleobiology/article/abs/computational-analysis-of-locomotor-anatomy-and-body-mass-evolution-in-allosauroidea-dinosauria-theropoda/149D0DB9E3574ACD4106E2B04F65AD1C) evaluates a spectrum of estimates rather than establishing one standing posture. Neither source establishes a universal staggered rest stance. The configured posture and stance defaults therefore remain explicitly authored engineering estimates until stronger source-specific evidence is bound.
