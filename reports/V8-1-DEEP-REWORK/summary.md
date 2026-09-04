# V8.1 deep rework — implementation handoff

## Outcome

V8.1 is a separate editable package. The imported V8 package was not intentionally edited. Its cache-excluding canonical tree hash remains `1eb9d5856873bf77e318bb301d2aacdc8930581761ad58c458e5a13222a9ad65`. The raw-tree hash is not a valid immutability oracle because read-only Python imports regenerated `__pycache__/*.pyc`; those cache files were not deleted.

The final V8.1 pack contains 47 clips. It preserves the V8 walk root track, timing, phase cycles, and mean speed; applies the accepted V5.5 asymmetric idle/support stance and neutral-chain posture; performs the accepted 90% lower-foot pivot correction before locomotion/sole/IK generation; fixes the jaw on a rest-local hinge; keeps the grounded normal attack distinct; and adds mirrored power attacks plus support-aware entry and feeding/walk handoffs.

## Canonical hashes

- Final/reproduced GLB: `ba321da21c20fce9fc2192efbcc40ae192303b06c2ccb856e0b8d7edeba2cc8a`
- Final/reproduced animation manifest: `8357304d09b0247339b471894eb34b742c56e0b40decd964c207daacfd465648`
- Canonical/resolved profile: `f128bd39cca62a674855ffbcce2e88226cec3b17048bf9a830bd158238240143`
- Canonical V8 tree excluding `.DS_Store`, `__pycache__`, and `*.pyc`: `1eb9d5856873bf77e318bb301d2aacdc8930581761ad58c458e5a13222a9ad65`

The clean-build report differs only in its absolute `output.animated_glb` path; the GLB, animation manifest, and resolved profile are byte-identical.

## Measured acceptance evidence

- V8.1 release validation: `PASS`.
- Actual baked-GLB ground validation: `PASS`.
- Geometry-derived flight duration from all 169 baked keys: `0.189828 s` / `0.190385 s`.
- Minimum sampled clear key inside that interval: `0.020699 m` / `0.021101 m`; maximum baked both-sole apex clearance: `0.072913 m` / `0.073312 m`, or `0.05313 h` / `0.05342 h` for a measured `1.372215 m` hip height.
- Maximum sampled power-attack penetration: `0.0 m` for both mirrored variants.
- Root vertical apex: `0.120755 m`; persistent forward delivery: `0.535164 m`.
- Launch-leg load: `0.72`; ordered lead landing and second-foot catch pass for both variants.
- Jaw off-hinge rotation: `1.28e-14 degrees`; maximum skull-space lower/upper midline error: `0.001526 m` against a `0.002 m` gate.
- Pivot change: independently measured IBM slots `[43, 56]` only; toe-root error `1.72e-16 m`; rest-skinned mesh error `2.24e-08 m`.
- V8 walk preservation: exact root-track maximum error `0.0 m`, with identical duration, samples, timeline, phase cycles, and mean speed. Allowed rotation differences are limited to the accepted neutral posture and pivot-driven foot/ankle/toe/IK seam.
- Browser contract: `PASS`, 47 clips, embedded GLB hash exactly matches the standalone GLB, no external URLs, and separate normal/power action queues are playable.
- Unit contract: 2 tests, 2 passed.
- Package attestation: 285 files verified by `SHA256SUMS_V8_1.txt`.

## Source files changed relative to V8

- `scripts/reproduce_v8_1.sh`
- `scripts/run_v8_1_tests.sh`
- `scripts/verify_package_v8_1.sh`
- `scripts/write_package_manifest_v8_1.py`
- `toolkit/v8/browser_demo/index-v8.1.html`
- `toolkit/v8/browser_demo/v8.1-viewer.js`
- `toolkit/v8/examples/profiles/tarbosaurus-v8.1.json`
- `toolkit/v8/scripts/build_v8_1_browser_html.py`
- `toolkit/v8/scripts/eonproc_v3/generator.py`
- `toolkit/v8/scripts/eonproc_v3/gltf_io.py`
- `toolkit/v8/scripts/eonproc_v4/locomotion.py`
- `toolkit/v8/scripts/eonproc_v7/actions.py`
- `toolkit/v8/scripts/eonproc_v8/actions.py`
- `toolkit/v8/scripts/eonproc_v8/generator.py`
- `toolkit/v8/scripts/eonproc_v8/locomotion.py`
- `toolkit/v8/scripts/eonproc_v8/pivots.py`
- `toolkit/v8/scripts/eonproc_v8/profile.py`
- `toolkit/v8/scripts/render_v8_1_validation.py`
- `toolkit/v8/scripts/reproduce_v8_1.sh`
- `toolkit/v8/scripts/run_pipeline_v8.py`
- `toolkit/v8/scripts/run_v8_1_tests.sh`
- `toolkit/v8/tests/test_v8_1_contract.py`
- `toolkit/v8/tests/validate_baked_ground_v8_1.py`
- `toolkit/v8/tests/validate_browser_contract_v8_1.py`
- `toolkit/v8/tests/validate_jaw_centering_v8_1.py`
- `toolkit/v8/tests/validate_v8_1_release.py`
- `toolkit/v8/tests/validate_walk_preservation_v8_1.py`

Repository-level authored files are `docs/V5_TO_V5_5_CHANGES_AND_V8_1_TRANSFER_GUIDE.md`, `docs/V8_TO_V8_1_DEEP_REWORK.md`, `reports/V5-V5-5-TRANSFER-GUIDE/plan.md`, this report bundle, and `showcase/v8.1/`. Generated package files are attested in `procedural-animation-toolkit(v8.1)/PACKAGE_MANIFEST_V8_1.json` rather than repeated here.

## Reproduction and verification commands

From `procedural-animation-toolkit(v8.1)/`:

```sh
./scripts/reproduce_v8_1.sh reproduced_result/v8.1-final
./scripts/run_v8_1_tests.sh
python3 scripts/write_package_manifest_v8_1.py
./scripts/verify_package_v8_1.sh
```

The clean runner refuses a non-empty output directory, constructs its Python dependencies with `uv`, requires the explicit `tarbosaurus-v8.1.json` profile, builds every artifact, and runs release, actual-baked-ground, jaw-geometry, browser-contract, and V8-walk-preservation validators.

V8 preservation was recomputed with:

```sh
find 'procedural-animation-toolkit(v8)' -type f ! -name '.DS_Store' ! -name '*.pyc' ! -path '*/__pycache__/*' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256
```

Blender evidence was produced with `/opt/homebrew/bin/blender --background --python-exit-code 1 --python showcase/v8.1/render_v8_1_blender.py -- ...`. The renderer imported the final GLB directly and did not edit animation channels. Blender version was `5.2.0 LTS`; the final ten-second side and three-quarter sequences are `720×406`, `24 fps`, 240-frame H.264 films, and both render reports identify the GLB hash above. A project-owned abstract target primitive and contact shadow mark the contact/feeding point for review only; they are not part of the GLB.

## Exact artifact paths

- Final GLB: `procedural-animation-toolkit(v8.1)/validated_result/v8.1/tarbosaurus_procedural_v8_1_animation_pack.glb`
- Offline runtime review: `procedural-animation-toolkit(v8.1)/validated_result/v8.1/OPEN_ME_tarbosaurus_v8_1_3d_browser.html`
- Release/baked/jaw/walk/browser evidence: `procedural-animation-toolkit(v8.1)/validated_result/v8.1/*.json`
- Clean reproduced bundle: `procedural-animation-toolkit(v8.1)/reproduced_result/v8.1-final/`
- Editorial comparison page: `showcase/v8.1/site/index.html`
- Ten-second Blender power sequence: `showcase/v8.1/blender-final-side/films/power-sequence-side.mp4` and `showcase/v8.1/blender-final-threeq/films/power-sequence-threeq.mp4`
- Final film SHA-256: side `f624c8637d1584842da4ff127fe6f60349465c56014c7abf9af5879099161b8b`; three-quarter `fdd5f5d5879653f5b5ab06b0edc3a7718e02377456f945e3d3a4a09d2fd78d4d`
- Blender idle/walk comparison: `showcase/v8.1/blender-final-comparison/films/`
- Blender front jaw review: `showcase/v8.1/blender-final-jaw/`
- Fixed-frame contact sheets: `reports/V8-1-DEEP-REWORK/blender-review/`
- Full reference-video frame analysis: `reports/V8-1-DEEP-REWORK/reference-analysis/attack-eat-reference-v8.1-visual-analysis.md`

## Limitations and review boundary

- Automated and fixed-camera evidence passes, but the motion remains subject to perceptual review in the local browser page; this is intentionally not labeled unconditional visual acceptance.
- The source reference keeps the jaw visibly open during much of the post-landing charge. V8.1 models the user-requested bite as a distinct contact/clamp event and then hands off into feeding, rather than copying the source’s exact extended gape.
- `showcase/v8.1/blender-side/` and `showcase/v8.1/blender-threeq/` are earlier noncanonical diagnostic renders. Only `blender-final-*` uses the final GLB and is linked by the page.
- No commit or push was performed.
