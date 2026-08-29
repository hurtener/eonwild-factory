# V8.3 foot-artifact and V9 narrow-gauge gait audit

Status: **independent read-only audit; no V8.3 promotion decision**

## Result

The suspected V8.3 foot-adjacent artifact is not reproduced as a
candidate-only deformation. The counter-solve changes the leg pose within its
declared limits, but the toe-dominant geometry remains nearly coincident with
V8.2 and the fixed-camera evidence shows no new crossing, toe explosion, or
knee/ankle pop.

There are two separate issues that should not be conflated with a V8.3
skinning failure:

1. Both V8.2 and V8.3 have a real, small inherited toe-tip/ground-plane
   interpenetration. The render plane is fixed from the rest/bound-box minimum,
   while the animated sole/toe tip moves lower in some contact frames.
2. The three-quarter evidence camera exposes the finite matte-plane boundary.
   That is an evidence-layout defect and can be mistaken for a ground or foot
   artifact.

The dark strip beside the far hock is lighting/occlusion. It appears in the
same V8.2 and V8.3 phases, remains attached to a continuous limb silhouette,
and is not detached dark geometry.

## Pinned inputs and evidence

| Item | Exact value |
|---|---|
| V8.3 HEAD | `195a8b4707997b3309f86f8821217ed1d7e9c22a` |
| V8.3 GLB | [`b5fc...17d03.glb`](/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb) |
| V8.3 SHA-256 | `b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03` |
| V8.2 GLB | [`tarbosaurus_v8_2_approved.glb`](/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-2-release/procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb) |
| V8.2 SHA-256 | `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5` |
| Imported mesh | 59,169 vertices, 102,258 polygons, one skinned mesh; rest/inverse-bind structure matches V8.2 |
| Action range | `[0, 97.66957092285156]` frames |
| Evaluation | Blender 5.2.0 LTS, direct GLB import, common integer frames `0..97` |
| Media | [`media-manifest.json`](/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/reports/PROCEDURAL-ENGINE-V8-3/evidence/media-manifest.json): side/front/three-quarter, 960x540, 24 fps, 240 frames, 10 seconds, finite non-looping |
| Phase crops | 18 total: nine full-body and nine feet crops |

The media was inspected independently of the existing PASS wording. The
side, front, three-quarter, full-body, and feet phase images were reviewed at
corresponding V8.2-left/V8.3-right phases.

## Exact V8.2 versus V8.3 findings

### Counter-solve and motion

The declared V8.3 layer sequence is
`pelvis_balance_pre_ik@1 -> leg_contact_resolve@1 ->
chest_tail_head_stabilization@1`.

The serialized layer metrics report:

- Pelvis added lateral P2P: `0.021 m`.
- Pelvis added vertical P2P: `0.009993370713473285 m`.
- Pelvis added roll P2P: `1.7 degrees`.
- Maximum foot target position error: `2.5823128856601336e-15 m`.
- Maximum foot target orientation error: `0.000005454337916859027 degrees`.
- Maximum foot-pivot translation: `4.867755750919621e-8 m`.
- Maximum leg local delta: `2.1284536214200096 degrees`.

These are real pose changes, not a mesh corruption. They are smooth in the
sampled frames and remain below the declared 3/3/4-degree leg-chain limits.
The lower-leg region can therefore move several millimetres relative to V8.2
without being a toe deformation.

### Dense final-skinned comparison

The sparse final-skinned witness report covers only three vertices per side.
An additional direct Blender evaluation compared all vertices with meaningful
foot/toe-chain weights and the six witness vertices.

| Mask | Vertices | Maximum V8.3 minus V8.2 | Interpretation |
|---|---:|---:|---|
| Left toe, any toe weight `>1e-8` | 3,737 | `5.848941655474254e-3 m` | Contaminated by ankle/shin spill-through weights |
| Right toe, any toe weight `>1e-8` | 3,459 | `5.518935709896333e-3 m` | Same spill-through issue |
| Left foot, any foot/toe weight `>1e-8` | 4,063 | `7.88823985760007e-3 m` | Includes upper contact-chain vertices |
| Right foot, any foot/toe weight `>1e-8` | 3,943 | `1.4342410290023037e-2 m` | Maximum at an ankle/shin-dominated vertex |
| Left toe, toe weight `>=0.75` | 1,395 | `0.0003832554835665211 m` | Toe-dominant geometry; no explosion |
| Right toe, toe weight `>=0.75` | 1,386 | `0.00038674751184692384 m` | Toe-dominant geometry; no explosion |
| Six repository witness vertices | 6 | `3.155676150813735e-5 m` | Direct 98-frame check |

The broad-mask maximum is vertex `44873` at frame `0`, with weights
`Bone_013=0.8183919`, `Bone_014=0.1801905`, and `Bone_012=0.0014176`. It is
not a toe vertex in any meaningful weighting sense. The left broad-mask
maximum is likewise a `Bone_009`-dominated lower-leg vertex. The toe-dominant
maximum is below the proposed `0.5 mm` candidate-vs-baseline toe regression
gate.

The committed witness evidence is also recorded for comparison:
`977` samples, worst axis regression `0.0001039505 m`, Euclidean regression
`0.0001193097 m`, against limits `0.0005 m` and `0.002 m` respectively. Sparse
witnesses remain insufficient as the only proof; the dense mask should be the
normative check.

### Floor contact

The render script creates the plane at the primary mesh bound-box minimum
minus `0.012 m` ([`render_comparison_blender.py`](/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/reports/PROCEDURAL-ENGINE-V8-3/tools/render_comparison_blender.py)).
The independently measured imported plane level is
`z = -0.01200103802869944`.

At cycle frame `38`, toe-tip vertex `50291` (`Bone_045`, 100% toe influence)
reaches:

- V8.2 gap: `-0.005567486898201423 m`.
- V8.3 gap: `-0.005569492967027145 m`.

At cycle frame `11`, the corresponding right toe-tip vertex `42208`
(`Bone_054`, 100% toe influence) reaches approximately `-0.005431 m` in V8.3.
The candidate-minus-baseline displacement at the worst named tip is only about
`2.0e-6 m`. This is an inherited sole/target-plane mismatch, not a
counter-solve regression. The existing visual crops do not make the few
millimetres legible, so this must be handled by a sole-level metric and an
explicit legacy exception or by correcting the baseline contact setup.

### Visual classifications

| Observation | Classification | Finding |
|---|---|---|
| Dark far hock/lower-leg strip | Lighting/occlusion | Present in both versions; attached silhouette; not detached geometry |
| Toe silhouette and toe articulation | Normal motion plus bounded skinning | No candidate-only toe explosion; toe-dominant delta <= `0.383 mm` |
| Knee/ankle compensation | Intentional motion | Smooth 1–2-degree local changes; no visible pop or split |
| Foot crossing | No defect observed | Front and three-quarter phases retain alternating, non-crossed feet |
| Lateral stance | Motion/design signal | Narrow stance is visible, but it needs normalized state-aware measurement |
| Toe-tip floor intersection | Inherited motion/target mismatch | Both versions penetrate fixed plane by up to `5.57 mm` |
| Three-quarter floor boundary | Evidence-only defect | Finite plane edge enters bottom of the camera crop |

## Coordinate-contract risk

The semantic rig declares `upAxis: Y` and `forwardAxis: X`, while the V8.3
thresholds declare `x=lateral`, `y=vertical`, `z=sagittal`. The exported root
translation and rendered body travel are predominantly along the sagittal
axis, not the declared semantic forward field. A V9 heading metric that reads
`forwardAxis: X` literally can report a 90-degree error. Define the local
travel tangent from measured root displacement/ground velocity and derive the
lateral axis from it; either reconcile or explicitly version the semantic
coordinate field before using it for acceptance.

## Primary-source verification

The following claims are source-bounded, not used as Tarbosaurus hardcodes:

- McCrea et al. report the first tyrannosaurid trackways as narrow, with slight
  inward pes rotation and footprints near or overlapping the trackway midline;
  their pace/stride observations are specific to the described ichnotaxon and
  trackways. The paper also uses the trackways to discuss concurrent walking
  and possible gregariousness, not COM targets.
  [PMC4108409](https://pmc.ncbi.nlm.nih.gov/articles/PMC4108409/)
- Wilson et al. report that most known theropod trackways are narrow-gauge and
  digitigrade, while wider stance occurs in some low-speed/rest contexts. Their
  uneven-surface example is an early-theropod context and does not justify a
  universal brace or turn rule.
  [PMC2752196](https://pmc.ncbi.nlm.nih.gov/articles/PMC2752196/)
- Bishop et al. measure step width as the mediolateral distance between
  successive footfalls and find a continuous decrease with increasing stride
  length/speed in their non-avian theropod trackways. Faster placement can
  approach the midline, and crossover is a possible high-speed behavior. The
  paper does not supply a universal dinosaur support-width ratio or COM target.
  [PMC5550975](https://pmc.ncbi.nlm.nih.gov/articles/PMC5550975/)

The numeric bands below are therefore explicitly engineering starting priors
with uncertainty, not paleobiological measurements.

## Species-neutral narrow-gauge contract

The full machine-readable proposal is [`narrow-gauge-contract.json`](/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json).
Its core definitions are:

- `H`: median hip/pelvis-to-ground height over valid samples.
- `T`: measured local ground travel tangent; `L`: normalized ground lateral
  axis derived from `up x T`.
- `C_left`, `C_right`: deterministic weighted centroids of sole/toe contact
  vertices, never ankle origins.
- `stanceSupportWidth/H = abs((C_left - C_right) dot L) / H`.
- `stepWidth/H`: lateral distance between successive contralateral contact
  centroids divided by `H`; do not conflate it with simultaneous stance width.
- `psi`: signed angle between the projected foot axis (foot root toward the
  toe-contact centroid) and `T`.
- `m/H`: signed distance of the horizontal COM projection to the active
  support-polygon boundary, divided by `H`. For moving states also evaluate a
  capture-point target using `COM + velocity / sqrt(g/H)`.

Initial low-confidence engineering envelopes:

| State | `stanceSupportWidth/H` | `abs(psi)` | COM/support rule |
|---|---:|---:|---|
| Straight walk | `0.00–0.10` | `<=15°` | Positive static margin; no unintended crossover |
| Slow/cautious | `0.05–0.18` | `<=20°` | `m/H >=0.02`; allow more double support |
| Brace | `0.12–0.30` | `<=30°` | `m/H >=0.05`; retain both contacts |
| Attack | `0.05–0.25` | `<=25°` | Dynamic capture-point margin; no fossil narrow-gauge claim |
| Turn | outer `0.10–0.35`, inner `0.00–0.20` | `<=45°` from local tangent | Explicit inner/outer role; crossover only if declared |

Each band must be stored with family median, p10, p90, and measurement
uncertainty. Attack, brace, and turn ranges are gameplay/engineering
hypotheses, not claims from the three papers.

## Acceptance gates

1. Evaluate 120 common phases and dense 240-Hz playback, with deterministic
   sole/toe masks and q05/q50/q95 output for width, heading, COM margin, gap,
   and contact velocity.
2. Preserve the existing V8.3 gates: foot target error `<=0.00035 m`, local
   solve limits, foot-pivot limit `<=0.015 m`, witness Euclidean regression
   `<=0.002 m`, and worst-axis regression `<=0.0005 m`.
3. Add dense toe-dominant candidate-vs-baseline regression `<=0.0005 m`; report
   broad-mask motion separately rather than failing on ankle/shin vertices.
4. Report absolute sole penetration. The current inherited `5.57 mm` result
   must either be corrected in the baseline/render plane or carried as a
   named, review-approved legacy exception; it must not be hidden by shadows.
5. Straight/slow/brace states must have no unintended crossover. High-speed
   crossover is allowed only in a state that explicitly declares it.
6. The fixed top view must show contact centroids, foot-heading vectors, COM
   projection, support hull, travel tangent, frame/phase ID, and synchronized
   V8.2/V8.3 panes. The plane boundary must remain outside every crop.

## Recommended implementation order

1. Correct the evidence setup: enlarge the ground plane or use a shadow
   catcher, then add the locked top-view and foot macro evidence.
2. Implement species-neutral contact/sole masks and normalized measurements.
3. Add family profiles and gait-state classification with p10/p50/p90
   uncertainty; derive headings from measured travel, not the conflicting
   semantic forward field.
4. Make dense final-skinned toe/sole regression normative and keep sparse
   witnesses as a secondary guard.
5. Re-run straight, slow/cautious, brace, attack, and turn fixtures across
   multiple families before accepting any numeric envelope as stable.
