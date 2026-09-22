**Yes—these papers can provide the scientific backbone for Eonwild’s movement configuration. The useful outcome is not a universal “dinosaur walk,” but a set of distinct, evidence-linked locomotion profiles for the bodies we actually have.**

I verified the requested branch, `feat/motion-quality-and-breadth`, at commit **`987bd6b`**. Its `assets/animals/Models` directory contains exactly five models: **Alioramus, Gallimimus, Dilophosaurus, Prenocephale and Deinocheirus**. The configuration below covers those five—not the Tarbosaurus and Allosaurus benchmarks elsewhere in the repository.

### Configuration files

**[Download the configuration workbook](sandbox:/mnt/data/eonwild_locomotion_research/Eonwild_Locomotion_Configuration_Research.xlsx)** · **[Download the research configuration JSON](sandbox:/mnt/data/eonwild_locomotion_research/eonwild_locomotion_proposals.v1.json)**

The workbook contains **seven sheets**, including the model catalog, **14 proposed gait experiments**, body controls, calibration inputs, integration requirements and an evidence register. Entering a calibrated hip height calculates speed, stride length and cycle duration automatically.

The JSON is explicitly a **research proposal**, not a file that the current production loader accepts. No repository files were changed, and this pass did not measure or anatomically validate the GLB geometry.

## 1. What the papers actually give us

The main Cuff paper is valuable because it connects anatomy, experimental observations of living archosaurs and predictive simulations. However, **none of our five species appears in its Table 2 of musculoskeletal models**. Its quantitative examples therefore need to remain reference evidence, not silently become species-specific measurements.  

| Paper                                                           | What we should take into the factory                                                                                                                                                                         | What we should not copy directly                                                                                                                                            |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Cuff et al., 2022 — Walking, Running and Jumping**            | Distinguish grounded from aerial running; coordinate the body with stance; treat ankle, metatarsus and toes as functionally different; investigate tail–leg coordination.                                    | Its crocodile and tinamou walking angles are representative trials—not universal dinosaur joint limits. Its Coelophysis results are not measurements of our five species.   |
| **Bishop, Cuff & Hutchinson — How to Build a Dinosaur**         | Establish anatomical coordinate systems, joint centers, mobility constraints, segment mass, center of mass and inertia before making dynamic claims. Treat reconstruction as a range of plausible solutions. | A rig’s neutral pose is not its living standing pose. Bone-only movement limits are not necessarily the limits available with cartilage, ligaments and flesh.               |
| **Sellers et al., 2017 — T. rex stress-constrained locomotion** | Add loading constraints rather than optimizing only for speed. Keep fast grounded movement available as a distinct possibility.                                                                              | Do not apply this particular adult T. rex model’s conclusions, mass or stress thresholds to every biped—including immature Alioramus.                                       |
| **Bishop et al., 2018 — Cancellous Bone, Part II**              | A method for constraining plausible posture from bone architecture, with validation against a chicken. Useful for posture research and understanding methodological limitations.                             | This is not a complete gait reconstruction. Its equal-strength actuators and large toe-joint reserve are modeling devices, not biological muscle settings.                  |

### Three findings that directly affect our animation work

**“Erect” does not mean rigid, straight legs.** Cuff distinguishes erect posture partly through the orientation of the hip and ankle articulations. Meanwhile, the straightened limb shown in the modeling workflow establishes a coordinate reference. Neither is a reason to give an animal locked knees in its resting or walking pose. This distinction matters directly to our standing calibration.  

**Running does not necessarily require both feet to leave the ground.** The paper describes tinamous changing from walking mechanics to bouncing, running mechanics without an aerial phase. Sellers likewise distinguishes contact-based gait definitions from center-of-mass energy behavior. Our configuration should therefore separate **requested speed**, **contact schedule** and **measured gait mechanics**.  

**The tail is part of whole-body coordination, not an ornamental sine wave.** The Coelophysis simulations described by Cuff produced lateral tail motion **toward the retracting hindlimb during its stance**, contributing to angular-momentum coordination. That is an excellent mechanism to investigate in our theropods—but not a universal amplitude or phase curve to paste onto every animal. 

## 2. The five model profiles I would establish

The anatomical evidence below comes from the supplied papers plus additional species-focused literature. The **engineering families and movement identities are proposals**.

For life stage, I would preserve the known immature reference for Alioramus and use adult authoring targets for the other four, pending a proper comparison between each mesh and its intended specimen or reconstruction.

| Model                        | Evidence that should shape its configuration                                                                                                                                                                                                                                    | Proposed configuration family    | Movement identity to author                                                                                                                                                                                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Alioramus altai**          | The holotype, MPC-D 100/1844, is an immature individual; the published mass estimate reported in the literature is **369 kg**. That is a specimen reference, not a measured mass for our GLB or a full-adult value. ([ResearchGate][1])                                         | **Gracile tyrannosauroid biped** | A relatively lightly committed predator: planted walking, controlled acceleration, deliberate braking and coordinated reorientation. Investigate running without importing the assumptions of a multi-tonne adult tyrannosaur.                                          |
| **Gallimimus bullatus**      | Ornithomimid anatomy includes elongated distal hindlimbs and a long metatarsus. Importantly, the ornithomimid foot lacks the hallux retained in some earlier ornithomimosaurs. These anatomical distinctions do not establish an exact maximum speed. ([ResearchGate][2])       | **Cursorial ornithomimid biped** | The broadest initial relative-speed exploration in this proposal. Distinct walking, faster grounded movement and aerial-running experiments; clear ankle/toe recovery and stable attention through the long neck.                                                       |
| **Dilophosaurus wetherilli** | Marsh and Rowe’s redescription treats it as a large-bodied early theropod with differentiated axial anatomy, not a coelophysoid. Coelophysis is therefore a useful mechanics reference—not an equivalent body that merely needs enlarging. ([Jackson School of Geosciences][3]) | **Medium early-theropod biped**  | A longer-bodied predator with visible coordination between pelvis, neck and tail. Begin with a convincing walk, then investigate more forceful acceleration and faster gaits without copying Coelophysis trajectories.                                                  |
| **Prenocephale prenes**      | This is a pachycephalosaurian **ornithischian**, not a theropod. Its holotype includes a nearly complete skull and partial postcranial remains, but the accessed literature does not supply a dynamically calibrated gait. ([ResearchGate][4])                                  | **Compact ornithischian biped**  | Compact, planted movement and readable changes of direction. Fast locomotion is an authoring hypothesis to test. Do not inherit a theropod muscle map or assume high-speed headbutting from the skull alone.                                                            |
| **Deinocheirus mirificus**   | The 2014 description identifies a heavily built, **non-cursorial** ornithomimosaur with relatively short hindlimbs, an expanded pelvis and broad-tipped pedal unguals. ([Nature][5])                                                                                            | **Giant ornithomimosaur biped**  | High-support walking, controlled whole-body repositioning and a faster grounded candidate. Keep aerial running and jumping outside the initial authoring set. “Non-cursorial” should not become “motionless,” but it should prevent a scaled-up Gallimimus performance. |

**The most consequential split is Gallimimus versus Deinocheirus.** Their relationship can help organize anatomical research, but their documented body plans argue against sharing one locomotion profile with a different scale multiplier. My proposal gives them different contact timing, speed exploration and body-response treatment. ([ResearchGate][2])

There is also a concrete asset-review check here: **Gallimimus should not inherit a generic theropod’s raised inner toe simply because the shared rig supports one.** Check the actual mesh and semantic bindings before treating that digit as present. ([ResearchGate][2])

## 3. Initial numerical configuration table

These are **proposed first-pass authoring targets**, not numbers extracted from fossils or the papers.

I normalized them to a calibrated reference hip height because it would be misleading to prescribe absolute speed from a GLB whose physical scale and standing posture have not been established.

The definitions are:

$$
Fr=\frac{v^2}{g\,h},
\qquad
v=\sqrt{Fr\,g\,h}
$$

Here, \(h\) is a **fixed, calibrated standing hip-height reference** for the animal profile. It is not the mesh’s bounding-box height, and it should not fluctuate with each frame of pelvis movement. Hip-height assumptions materially affect this calculation; Dececchi et al., for example, explicitly use and discuss a particular limb-length-based proxy. ([PLOS][6])

Duty factor, \(\beta\), is the proportion of a complete same-foot cycle during which that foot contacts the ground. 

### Proposed nominal targets

In the gait columns, each pair is **`Froude number / duty factor`**.

| Animal            | Walking candidate | Faster grounded candidate | Optional aerial-running probe | Walking stance width / \(h\) | Walking toe clearance / \(h\) |
| ----------------- | ----------------: | ------------------------: | ----------------------------: | ---------------------------: | ----------------------------: |
| **Alioramus**     |   **0.15 / 0.66** |           **0.55 / 0.57** |               **1.20 / 0.44** |                     **0.12** |                      **0.07** |
| **Gallimimus**    |   **0.20 / 0.63** |           **0.60 / 0.55** |               **1.50 / 0.42** |                     **0.10** |                      **0.08** |
| **Dilophosaurus** |   **0.15 / 0.67** |           **0.50 / 0.58** |               **1.00 / 0.46** |                     **0.13** |                      **0.07** |
| **Prenocephale**  |   **0.12 / 0.69** |           **0.40 / 0.59** |               **1.00 / 0.46** |                     **0.16** |                      **0.06** |
| **Deinocheirus**  |   **0.08 / 0.74** |           **0.25 / 0.64** |   **Disabled in initial set** |                     **0.18** |                      **0.05** |

**These values define experiments—not certified capabilities or a species speed ranking.** In particular, the Prenocephale aerial probe is a low-confidence research option, not a finding that this animal ran that way.

The workbook also contains bounded search intervals around the nominal values. Those are engineering search ranges, **not statistical confidence intervals**, and not every combination should be assumed feasible.

A few conventions are important:

**Stance width** means the full distance between the left and right stance lanes—not the offset of each foot from the centerline. The actual pelvis, limb geometry and self-collision constraints must govern whether a proposed width works.

**Toe clearance** means the lowest articulated toe or pad surface above a flat support plane at midswing—not the ankle’s height. A high ankle can still leave a toe dragging.

**“Faster grounded” is deliberately not named “grounded running.”** The requested contact schedule keeps support on the ground; the resulting center-of-mass mechanics determine whether it should actually be described as grounded running. 

### Stride and timing

I would also make stride length explicit rather than speeding up an existing cycle until it reaches the desired velocity:

| Animal        | Walking stride / \(h\) | Faster-grounded stride / \(h\) | Aerial-probe stride / \(h\) |
| ------------- | ---------------------: | -----------------------------: | --------------------------: |
| Alioramus     |                   1.20 |                           1.70 |                        2.50 |
| Gallimimus    |                   1.40 |                           1.90 |                        2.80 |
| Dilophosaurus |                   1.20 |                           1.65 |                        2.30 |
| Prenocephale  |                   1.05 |                           1.40 |                        2.10 |
| Deinocheirus  |                   0.90 |                           1.25 |                           — |

These are also **engineering seeds**. A stride means one foot’s touchdown to its next touchdown. Once \(h\) is calibrated:

$$
L_{\text{stride}}=(L_{\text{stride}}/h)\,h,
\qquad
T_{\text{stride}}=\frac{L_{\text{stride}}}{v}
$$

For illustration only, a hypothetical \(h=1.5\) m, \(Fr=0.15\), and stride ratio of 1.20 gives approximately **1.49 m/s**, a **1.80 m stride**, and a **1.21 s cycle**. That is an arithmetic example, not a measurement of Alioramus.

The resulting combination still needs to pass geometry, contact and—when available—dynamic feasibility checks.

## 4. Body configuration: where these animals should stop looking like reskins

The numerical table is only the starting point. I would pair it with the following **authoring directions**, keeping exact amplitudes and joint limits subject to calibration.

| Animal            | Feet and support                                                                                                                    | Tail and torso                                                                                                                                             | Head, neck and forelimbs                                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Alioramus**     | Preserve separate ankle, metatarsal, MTP and toe behavior. Make load transfer and release readable without rigid block-foot motion. | Test the Coelophysis-inspired stance/tail relationship as a weak prior, then evaluate the whole body. Avoid a large adult-tyrannosaur response by default. | Separate gaze stabilization from neck carriage. Keep arm motion restrained rather than adding human-like running swings.                 |
| **Gallimimus**    | Emphasize clean distal-limb recovery and toe release. Use its own foot anatomy and support footprint.                               | Retain a long-tailed body model; do not substitute the dynamics of a short-tailed ostrich.                                                                 | Distribute neck movement while preserving attention. The head should neither wobble freely nor look welded to the world.                 |
| **Dilophosaurus** | Start from its own joint-center calibration, not a uniformly enlarged Coelophysis skeleton.                                         | Refit tail and trunk response to the actual body proportions.                                                                                              | Coordinate head carriage through the neck; give the forelimbs their own restrained response and separate interaction behavior.           |
| **Prenocephale**  | Fit the contact footprint and limb configuration independently of the theropods.                                                    | Begin with restrained continuity and turn response; do not label a copied theropod muscular mechanism as established anatomy.                              | Neutral attention comes first. Head lowering and bracing should be separate actions, not its permanent walking posture.                  |
| **Deinocheirus**  | Use broad support geometry, longer support intervals and gradual transfer between contact regions.                                  | Treat trunk, neck, tail and arms as contributors to mass distribution—not just visual appendages.                                                          | Changes of attention and reach should involve distributed whole-body response, rather than fast neck movement over an unaffected pelvis. |

The supplied research itself warns that reducing the foot to one toe joint misses important behavior. Cuff discusses coordinated phalangeal motion and explicitly identifies simplified feet as a weakness in predictive simulations. **We can simplify the physical model initially without accepting a visually rigid foot in the final skinned animation.** 

### Joint configuration I would use as the starting architecture

For a reduced physics model, the published Coelophysis setup offers a useful initial pattern: a hip with three rotational degrees of freedom, with the knee, ankle and metatarsophalangeal joint simplified to flexion–extension. The paper presents those distal one-axis joints as modeling simplifications, not complete anatomy. 

My proposed implementation would preserve that distinction:

| Configuration element    | Initial treatment                                                                                                                              |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Root and pelvis**      | Free whole-body motion; no hidden support or balancing force.                                                                                  |
| **Hip**                  | Separate flexion–extension, abduction–adduction and long-axis rotation in calibrated anatomical frames.                                        |
| **Knee and ankle**       | A one-axis model can start a reduced solve, but additional motion must remain possible when anatomy, retargeting or task behavior requires it. |
| **Metatarsus and toes**  | Separate the ankle-to-foot segment from toe articulation. Preserve the render rig’s meaningful digit chains.                                   |
| **Neck and tail**        | Use explicitly modeled or declared response behavior; do not mistake locked segments for validated infinite strength.                          |
| **Jaw and interactions** | Separate task configuration. A head reaching a target is not automatically a complete bite or feeding action.                                  |

I have not supplied universal knee, ankle or neck angle limits. Those fields remain calibration inputs. Source joint angles depend on their anatomical axes, rotation order and zero pose; they cannot be pasted directly into artistic bone rotations. 

## 5. What is still needed before calling these physical configurations

There are two different kinds of completeness here: a useful authoring proposal and a calibrated biomechanical model.

For these five assets, the following quantities still need to be established:

| Quantity                                        | Why it matters                                                                      | Configuration treatment                                                                                                        |
| ----------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Physical scale and standing hip height**      | Converts normalized movement into meters and seconds.                               | Measure the calibrated pose and retain the method and source identity.                                                         |
| **Segment lengths and joint centers**           | Determines reachable motion and whether the apparent leg follows the animal’s body. | Measure both sides; distinguish artistic landmarks from fossil-derived centers.                                                |
| **Body and segment masses**                     | Determines translational loading and weight distribution.                           | Use a documented specimen/reconstruction basis. Do not infer mass from file size or polygon volume without a defensible model. |
| **Segment centers of mass and inertia tensors** | Determines balance and resistance to turning or pitching.                           | Reconstruct and test explicitly; a single total-mass value is insufficient.                                                    |
| **Joint mobility and actuator capacity**        | Determines which motion can actually be produced and supported.                     | Keep anatomical assumptions and engineering motor limits separately labeled.                                                   |
| **Contact geometry and compliance**             | Determines support, slip, toe release and impact behavior.                          | Calibrate against the actual foot and substrate model.                                                                         |

These requirements follow the modeling workflow in *How to Build a Dinosaur*, including its explicit “mass set” of mass, center of mass and inertia tensor.  

For Alioramus, **369 kg is a useful literature anchor**, but the workbook deliberately does not automatically place it in the “applied body mass” input. First establish that the asset’s intended scale and life stage correspond to that reference. ([ResearchGate][1])

Likewise, neither the **2 BW force assigned to every actuator** nor the **1,000 Nm toe-joint reserve** in the chicken study belongs in our default physical configuration. Their purpose was to make a particular quasi-static analysis tractable.  

## 6. How this fits the factory we already have

The requested branch already separates the source geometry, semantic rig, animal instance, contact profile, program profile, performance profile and articulation profile. That is the right structure to preserve.

However, the inspected `catalog/animals` directory contains **Allosaurus and Tarbosaurus instances, not instances for these five new source models**. The tables are therefore a proposal for their onboarding—not a report that they are already configured.

| Proposed information                                            | Factory destination                                                           |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Taxon, specimen, life stage, physical measurements and evidence | **Animal instance**, with source-bound calibration                            |
| Joint roles, anatomical frames and source hierarchy             | **Rig binding**                                                               |
| Foot surfaces, contact regions and toe roles                    | **Contact profile**                                                           |
| Gait timing, stride and phase targets                           | **Program profile**                                                           |
| Head, torso, tail and forelimb response                         | **Performance profile**                                                       |
| Calibrated motion constraints                                   | **Articulation profile**                                                      |
| Mass distribution, inertia, actuation and force evaluation      | **Physics-model configuration**, separate from the kinematic authoring inputs |

Two adapter details need particular care. Our proposed distances use **standing hip height**, while existing program fields use names such as `step_length_body_heights`. Our timing uses a **same-foot stride cycle**, while the current profile contains `step_period_s`. Those conventions must be reconciled with the implementation—not assumed equivalent from their names.

The repository also explicitly documents that mass currently contributes to diagnostics, **not a force-based locomotion solve**. It does not yet produce segment inertia, muscle limits or contact-force distribution; pelvis acceleration multiplied by mass is not a ground-reaction-force measurement. Merely adding the new animal values will not change that boundary.

### Acceptance should remain independent of the requested targets

For this integration, I would require separate checks for actual skinned-foot contact, ground-relative slip, toe clearance, joint behavior, whole-body dynamic balance, cycle continuity and starts/stops. In a periodic level-ground physics solve, the total vertical contact impulse should balance body weight integrated over the cycle; a pleasing pelvis curve alone is not that check.

Jumping should remain disabled initially. The supplied paper’s jumping results concern a particular tinamou model and include substantial landing loads—they do not establish a safe jump height for any of our five animals. 

## Recommended starting point

**I would begin with Alioramus walking, then use Gallimimus and Deinocheirus as the two contrasting transfer tests.** That is my proposed experiment order, not a ranking of biological capability.

Alioramus gives us a focused first candidate. Gallimimus tests whether the factory can produce a distinctly more cursorial movement identity. Deinocheirus tests whether shared infrastructure can handle a very different body without merely enlarging the same animation.

Dilophosaurus should then receive its own early-theropod calibration, and Prenocephale should enter through an explicitly ornithischian profile.

**The target is five recognizably different ways of supporting weight, recovering the feet and changing direction—not five skins playing the same gait.**

[1]: https://www.researchgate.net/publication/381887965_Mandibular_force_profiles_of_Alioramini_Theropoda_Tyrannosauridae_with_implications_for_palaeoecology_of_this_unique_lineage_of_tyrannosaurid_dinosaurs "https://www.researchgate.net/publication/381887965_Mandibular_force_profiles_of_Alioramini_Theropoda_Tyrannosauridae_with_implications_for_palaeoecology_of_this_unique_lineage_of_tyrannosaurid_dinosaurs"
[2]: https://www.researchgate.net/publication/289845348_Ornithomimosauria "https://www.researchgate.net/publication/289845348_Ornithomimosauria"
[3]: https://www.jsg.utexas.edu/txvp/dilophosaurus/ "https://www.jsg.utexas.edu/txvp/dilophosaurus/"
[4]: https://www.researchgate.net/publication/240625747_A_taxonomic_review_of_the_Pachycephalosauridae_Dinosauria_Ornithischia "https://www.researchgate.net/publication/240625747_A_taxonomic_review_of_the_Pachycephalosauridae_Dinosauria_Ornithischia"
[5]: https://www.nature.com/articles/nature13874 "https://www.nature.com/articles/nature13874"
[6]: https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0223698 "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0223698"
