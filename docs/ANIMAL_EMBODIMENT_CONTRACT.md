# Animal embodiment profile v1

Canonical files: `catalog/embodiment/allo.v1.json` and `tarbo.v1.json`. These consolidate the approved consumer mappings and settings without changing approved locomotion packages. The shared code stays in `src/eonwild_motion`; there is no new versioned toolkit.

## Authority

An animal profile is the editable entry point for semantic bindings, calibrated axes, sequence timing, attention and secondary-motion settings. `authoring` preserves the original animal-instance evidence, approved emitted gait parameters and original intent references. Historical recipes remain reproducibility inputs, not editable game copies. This checkpoint does not replace every historical compiler configuration format or automatically admit new topology.

`tools/export_embodiment.py` validates required/unique roles, available nodes, finite values, explicit unit axes, sequence intervals and the motion SHA-256, then exports exact profile bytes and Python numerical reference vectors. Consumers receive files; they do not import Factory Python at runtime. Keep profile version, asset hashes and evidence together.

## Frame and law

Profiles describe admitted metre/second glTF assets, right-handed +Y up/+Z forward, xyzw quaternions. Joint `axis` is a local right-handed angular vector. Unity position reflection negates X; angular-vector reflection negates Y/Z. New source frames must be normalized during admission.

The `eonwild.secondary.v1` state is elapsed time, walk intensity and one response value per configured joint, initially zero. Each nonnegative finite time step:

- Walk intensity approaches clamped speed/full-walk-speed with exponential response `1-exp(-dt*walkBlendRate)`.
- Each arm response approaches clamped foot-separation signal times its authored sign, with `1-exp(-dt/max(0.03,responseSeconds))`.
- Jaw/arm breath contribution is `0.5-0.5*cos(elapsed*2*pi/breathPeriod+phase)`.
- Local angular offset is rest + breath contribution + (for arms) walk range × walk intensity × response.
- Apply the offset after source sampling; restore previous offsets before the next source sample. Pausing advances no state. Jaw rhythm intentionally continues through stops.

`src/eonwild_motion/embodiment.py` is the reference evaluator. Unity's numerical adapter must pass the exported reference vectors, including variable time steps, pauses and settling. The scene adapter binds transforms; it does not contain animal names or derive articulation from bone naming patterns. Attention target choice remains a game responsibility and is outside the secondary preview bake.

Arms may be empty. `hasJaw: false` disables the jaw layer. Required grounded-biped and attention roles remain mandatory; unsupported families require explicit shared implementation rather than silent fallback.

## Blender and new animals

`tools/bake_secondary_preview.py` takes an immutable exported clip plus a profile and produces a NEW preview GLB. It retains all non-secondary animation channels and adds the Python-evaluated local rotations for configured joints. Blender can import/play that GLB. This is an offline consumer preview, never source material for generating locomotion and never a production-contact certificate.

New animals require admitted geometry, skinning and semantic mappings; measured local joint axes; documented stride/proportion evidence; authored limits; a compatible shared locomotion family; an immutable generated motion package; profile export; and native-time review of that real rig. A renamed fixture proves naming independence only.

Focused checks: `PYTHONPATH=src python -m pytest tests/test_embodiment.py -q`. Export/bake tools expose their arguments with `--help`. Runtime/Blender evidence and the detailed onboarding guide are maintained in the principal Eonwild game repository under `docs/ANIMAL_PROFILE_ONBOARDING.md` and `game/Evidence/animal-profile-housekeeping/`.


## Locomotion capabilities v1 — checkpoint 11

The optional `locomotion` section extends the same embodiment profile. The approved walk source, stride intent, rig bindings and secondary-motion law remain intact. `planning/locomotion_capabilities.py` resolves explicit-unit values and provenance to effective motion limits. Changing an animal name has no effect; changing its numerical inputs does.

| Input | Resolution / use | Evidence status |
|---|---|---|
| Existing body mass | Effective horizontal force / mass gives acceleration and braking limits | Published estimate already in animal instance |
| Yaw inertia | Effective torque / inertia gives angular acceleration and braking; also drives tail response time | Published specimen/composite estimate; mesh correspondence remains unverified |
| Ilium area / yaw inertia | Separate research turning proxy | Published-model proxy, never converted directly into playback speed |
| Forward, braking, lateral force; yaw driving/braking torque | Independent control budgets, multiplied by selected effort | Authored effective budgets, not reconstructed muscles |
| Preferred / maximum grounded speed and maximum step frequency | Resolve speed and cadence while preserving step and same-foot stride | Authored low-speed intent, not sprint-speed claims |
| Traction coefficient | Caps horizontal acceleration; lateral budget also limits yaw rate at speed | Authored flat-ground assumption |
| Effort, turn cadence multiplier, heading per step, attention lead | Select a response within capability; add support steps when needed | Authored style |

Each input has value, unit, classification and source. The dimensionless agility components summarize linear acceleration/braking/lateral capacity relative to g and turning relative to g/(1 metre). These are engine summaries; the published area/inertia index is kept separately and retains its cm²/(kg m²) convention. Never merge these into one universal agility score.

`resolve_walk` returns requested/resolved speed, preserved stride and cadence. `advance_walk_speed` applies separate forward/braking budgets. `yaw_rate_at_speed` provides the speed-dependent lateral limit. `plan_directional` uses the same choreography and fits travel/heading rates and accelerations to these budgets, before actual-rig IK and contact correction. It regenerates poses rather than retiming an existing clip. Foot anchors and outside-first stepping remain behavior-owned.

Scope: the fit constrains the **locomotion path**, excluding the additional local support/pelvis accommodation. It is NOT final whole-body COM dynamics, segment force balance, muscle/tissue stress validation, or final material contact locking. Those remain the next polishing work. Walking capability resolution is implemented and tested; the approved straight-walk packages are unchanged and have not been regenerated with these profiles.

The current Allosaurus proxy uses the 1512 kg composite row, yaw inertia 2303.25 kg m² and ilium area 1131.5 cm². Tarbosaurus uses PIN 552-1, 2816.3 kg, 4486 kg m² and 2977 cm². Source: [Snively et al. 2019, Table 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC6387760/). Force/torque settings are independently authored; they are not inferred from the research index. [Dececchi et al. 2020](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0223698) informs the distinction between locomotor economy, body size and top speed. No Tarbosaurus sprint speed is claimed.

Export with `tools/export_embodiment.py`; it now adds resolved capability JSON to the existing profile and secondary vectors. Directional generation accepts `--profile catalog/embodiment/allo.v1.json` (or another admitted profile), binds the source geometry/calibrated height, and emits the profile snapshot, resolved limits, fit receipt and motion hashes alongside the GLB. `source-animal.profile.json` is the original authoring snapshot, whose source hash still identifies the approved walk; `resolved-capabilities.json` binds the new directional GLB explicitly. Unity consumes this immutable export; its review player displays the resolved budgets and does not add another root movement owner. Live gameplay control integration is a later checkpoint.

### Future animals

Start with an admitted rig/profile, documented mass, limb dimensions and step/stride. `tools/seed_locomotion_capabilities.py --target TARGET --reference REFERENCE --output NEW_PROFILE` generates an explicitly unreviewed similarity prior. Length comes from hindlimb measurements; inertia scales by mass ratio × length ratio², force by length ratio², and torque by length ratio³. All inherited/scaled values are relabeled derived estimates with reference hashes. These assumptions are a starting point, never new biological measurements. Replace them with specimen evidence or deliberate calibration, regenerate both the new animal and a reference animal, inspect every rendered frame, and review native-time motion. Unsupported body families still require shared implementation.
