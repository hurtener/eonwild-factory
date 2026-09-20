# Alioramus motion refresh: kinematic bridge candidate 01

Status: **review candidate; not predicted gait, anatomical approval or production admission**.
Original `assets/animals/Models/Alioramus-altai.glb` remains unchanged. The requested
source is on `codex/animal-profile-housekeeping`, Git blob
`58bb677040ef9d28ce06494c5adf23ab3a80c21d`, SHA-256
`51c15f798071c28fcaebe7ab3da769404294c30c797433e982a70089edb62bc1`.

## What this applies

The exact source has 76 skin joints, 15,952 vertices, three influence sets and no
animation. A separate semantic profile binds the existing pelvis, legs,
metatarsals, three multi-joint toe chains per foot, neck, tail, arms and jaw.
The animation emitter preserves the original mesh, skin, materials, textures,
source nodes and every original binary accessor. Nothing is rebound or reduced.

Three new clips are emitted: `Alioramus_Walk_RootMotion`,
`Alioramus_Walk_InPlace` and `Alioramus_Standing_Calibrated`. The last name means
an explicitly authored geometric standing calibration, **not fossil-validated
joint placement**. It is separate from the untouched bind pose. The walk is a
1.4-second authored cycle, 0.98 m nominal stride, 0.70 m/s. All numerical motion
intent is an engineering estimate, not a measured animal gait.

This is an opt-in experiment under `src/eonwild_motion/biomechanics`, not a new
factory toolkit or a replacement for the existing admitted motion compiler.
Existing FK, full-influence skin evaluation, glTF sampling and emission utilities
are reused. No prior animated take supplies this experiment's trajectories.

## Actual OpenSim boundary

A rig-shaped 76-body / 231-coordinate kinematic proxy and an authored state table
are written as `.osim` and `.sto`, reopened in OpenSim 4.6, and evaluated using
`getTransformInGround`. Reference-frame calibrated body transforms are mapped
back to local artistic-rig quaternions and baked into the final GLB. Missing
coordinates, wrong frames, changed source identity and incompatible topology
fail rather than silently dropping motion.

The proxy has zero gravity, dummy inertias/masses and unrestricted spherical
internal joints. **Do not use it for dynamics, muscle forces, biological limits
or speed claims.** This proves a self-consistent kinematic transport path, not
retargeting from an independent published dinosaur or a contact-force prediction.
The walking seed is authored with fixed-length IK, heel/digit articulation,
small secondary motion and final skinned-floor correction.

An independently solved Moco minimum-effort slider confirms the optimizer runs.
That test is not an Alioramus solve. A licensed, calibrated source model and a
physically solved gait remain the next research gate described in
[the OpenSim feasibility study](research/OPENSIM_DINOSAUR_FEASIBILITY.md).

## Reproduce

Use an isolated Python 3.13 environment; the review dependency file records the
versions used in this experiment without changing the main project's lock.

```sh
python -m pip install -r tools/requirements-biomechanics-review.txt
PYTHONPATH=src python -m pytest tests/test_alioramus_refresh.py -q
python tools/build_alioramus_refresh.py \
  --output out/alioramus-refresh --sample-hz 60 --moco-smoke
blender -b -t 4 --python tools/render_biomechanics_review.py -- \
  --package out/alioramus-refresh --output out/alioramus-review \
  --views side three-quarter front --width 1280
ffmpeg -framerate 30 -i out/alioramus-review/side/%04d.png \
  -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart \
  out/alioramus-review/side.mp4
```

The builder refuses an existing output directory. Source-code and dependency
identities are recorded in `build-manifest.json`. Review media uses actual
Blender-imported geometry and native timing; Workbench textured renders are
geometric review evidence, not a claim of final game/PBR lighting. The Blender
source and full-rig FBX are emitted separately. FBX is reopened to check bone
count, action count and durations. Blender pose comparisons are not Unity tests.

## Initial local measurements

The delivered GLB SHA-256 is
`0d57cabb6c1152de919b7a538acafee89f2b6253263c9135962f1a7241e43427`.
The actual receipts, rather than this summary, bind each generated/exported file.

| Check | Result / boundary |
|---|---|
| Focused actual-rig tests | 26 passed, including genuine OpenSim replay |
| OpenSim body-transform samples | 85 across the complete cycle |
| Maximum source/target frame positional discrepancy | approximately 0.00250 mm |
| Original source accessors and skin hierarchy | preserved byte-for-byte |
| Reopened full-skin floor samples | 169 keys and midpoints |
| Lowest vertex above the zero floor in those samples | approximately 0.544 mm |
| Reopened Blender joint comparisons | nine poses, approximately 0.0022 mm maximum |
| FBX reopen | 76 bones; three actions; 1.0 / 1.4 / 1.4 second durations |
| Physics-predicted Alioramus gait | NOT_RUN |
| Complete material no-slip and continuous contact | NOT_CERTIFIED |
| Native Unity/Animator parity | NOT_RUN |
| Human visual approval and production promotion | NOT_GRANTED |

These are finite-sample geometric checks. Existing source skinning can still
show limb deformation under motion; anatomy, contact appearance and gait quality
need human review. A first frame or unchanged skin weights cannot certify them.
This experiment does not supply starts/stops, stand-to-walk transitions, slopes,
reactive control, running or sprinting. Do not crossfade the standing clip into
walking and call the handoff contact-correct.

## Unity handoff

Use the Generic path in [the existing Unity contract](UNITY_MOTION_CONTRACT.md).
The root role is `Bone_000`. Choose root-motion ownership OR the motor-reconciled
in-place clip, never both. Preserve more than four weight influences where the
importer permits; the source uses three four-slot sets and the inspected FBX has
up to nine active influences on a vertex. Reducing to four is a changed skinning
configuration and must be measured again.

`runtime.json`, `contacts.json` and `reference-poses.json` provide coordinate,
cycle, planned-contact and nine-pose landmark evidence. Factory glTF positions
are right-handed +Y-up/+Z-forward. The documented Unity adapter reflects X for
positions and Y/Z for axial vectors; do not apply a second conversion blindly
on top of FBX import. Verify actual imported landmarks and root travel before
calling this Unity-ready. Unity does not need OpenSim at runtime.
