# Task-owned Blender cubic playback: root round one

Reviewed exact `4823fa8cc3813fa07a06e670f7b344e8321908ec` against published `170617beda89b1836aabebd983b7891549e03d65`, seven changed files. Disposition: CHANGES REQUIRED.

P1: Exact sampled pose is overwritten during native rendering. The local TRS conversion matches the installed Blender importer and all 18 requested source times in each adult mode pass the independent full-skin check (59,169 same-index vertices; maximum 4.399 micrometres). However, the same pose after an actual one-sample Cycles still diverges by 1.566769 mm in-place and 2.291010 mm root-motion, exceeding the unchanged 0.5 mm limit. The renderer retains the imported approximate animation; render dependency-graph evaluation can restore it. Ensure the actual render graph uses the exact pose, without modifying exported channels or claiming native curve/FBX support. A post-render reapply alone cannot prove rendered pixels were correct. Preserve and rerun the source-bound root reproduction, including evaluation inside the render graph if needed.

P1: The standard compiled review wrapper requests FBX through build_showcase.render_view on the first view. The new deliberate CUBIC FBX rejection therefore prevents the otherwise supported native review from completing. Author identified this integration failure during root review. Detect cubic before requesting the unsupported optional export, record its unsupported status explicitly, and retain LINEAR behavior.

Local P2: Direct invocation of the existing render_walk_review.py script now raises ModuleNotFoundError before argument handling because the new package import has no source-path bootstrap. Reproduced with PYTHONPATH removed and Blender --python-exit-code 1 --python src/eonwild_motion/blender/render_walk_review.py -- --help. Add the same local source bootstrap pattern used by the other Blender entrypoints.

Root focused tests: 41 passed in 0.33 s (native playback, preview clock, review timing). The sampled local coordinate conversion and strict finite/clock bounds are sound in this benchmark. Both connected and candidate rendering call sites were read. FBX rejection is appropriate; the wrapper must represent it rather than prevent native review. This review does not establish biological, visual, Unity, or production acceptance.

Consolidate these local changes for one post-fix exact-head review. Do not reopen the already closed curve reader or exporter implementation.

- `root-blender-cubic-round1-4823fa8-pytest.log`: SHA-256 `8150cf4fe0d85c2cf49401c21ce452afcd361aa0aa47a66eceb9e23e6a587a30`.
- `root-blender-cubic-round1-4823fa8-junit.xml`: SHA-256 `596f9c4486f6963f2c94d72c10a1d0ce7dc93094d8efbc5c8ab6aa05542f2905`.
- `root-blender-cubic-round1-4823fa8-legacy-cli.log`: SHA-256 `0ae66eadd473d0fb19d2d663ec7308750c172e1c8ac4e54105e7867946dae797`.
- `root-source-cubic-adult-v9-67a6756-001/native-result.json`: SHA-256 `5eb31e5890161360a7366f9ab9a8ac50cc56c302a5c05a250a177a1af226273c`.
- `root-source-cubic-adult-v9-67a6756-001/verify_native.py`: SHA-256 `2505e5bbc2dcc8631f3b6e01c28074995d86e63e977c095f4256acf00fdac05c`.
