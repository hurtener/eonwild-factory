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
