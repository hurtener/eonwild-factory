# Authored material adapter narrow closure — `8d78946`

Verdict: **PASS** (`P0=0`, `P1=0`). This is a diff-only closure of the touchdown-classification and loaded/unloaded material-floor discontinuity reported against `706c226`; it is not a new whole-branch review.

## Frozen scope

- Head: `8d789469435e44277b19e06f35b57e35de8f3bad`
- Tree: `6cb8a11b671a3991e06da0dce5a8b6b474a0bd80`
- Parent: `706c22691e03480799e87a36382d2d7591c38b81`
- Clean author worktree: `ARC/worktrees/eonwild-shared-locomotion-regime-v2`
- Delta: `src/eonwild_motion/solve/authored_material_contact.py`, `src/eonwild_motion/solve/source_motion_query.py`, and the direct adapter regression only.

The adapter now classifies values within `1e-12` of a declared key as that exact event before selecting the contact interval, derives touchdown metadata from the current cycle, and applies the same minimum material-floor solve and final material/reach gate to loaded and unloaded feet. The code does not lower the `100 µm` material gap, `1 mm` target-residual limit, or the existing sampled rate limits.

## Original reachable witness

At `706c226`, the retained right-touchdown pair `1.1903225806451612` and `1.1903225806451614` changed contact `false→true`, material minimum `100.000001→78.756559 µm`, and Bone_028 by `0.02893717°`. The finite sampled grid maximum was `893.854981°/s`, so this was a contact/source-continuity defect rather than a demonstrated `1200°/s` gate failure.

At `8d78946`, the independent 133-row reproduction evaluates both floats as loaded. Their right-foot requested height is `21.243400582032→21.243400582704 µm`, their material minima are `100.000001303245→100.000001304248 µm`, the maximum quaternion-component difference is `4.7808978997920804e-14`, and the maximum local translation delta is `2.220446049250313e-16 m`. This closes both the classification jump and the below-floor loaded endpoint. The cycle-end left touchdown metadata is also the current endpoint (`2.46 s`).

## Checks

- Reviewer direct test: `pytest tests/test_authored_material_contact.py -q` — `12 passed in 16.68s`.
- Reviewer log: `narrow-8d-tests.log`, SHA-256 `d45ba6a4a1bd5dfee250e72451f25a055f31540306e3f615295d6d8c0819c4ba`.
- Independent 133-row result: `ARC/audits/authored-material-adapter-root-r1/dense-8d78946.json`, SHA-256 `a3871434619154bff20edb11ce18f4e61c3e2523ce6aa0af8e0ba3d43bd9203a`.
- Independent 133-row log: `ARC/audits/authored-material-adapter-root-r1/dense-8d78946.log`, SHA-256 `ba919c3705f56ff6fbd2378a747edb0dd63ad20a6a317336a8b0280ee9b0b6af`.
- Root narrow-closure receipt: `ARC/audits/authored-material-adapter-root-r1/narrow-closure-8d78946.json`, SHA-256 `eb2b4d62afa8734e9cb253fe85665053007f80874cf29d24306c7044b0580b6c`.
- Actual-package dense receipt: `ARC/audits/free-dinosaur-pack-investigation-001/actual-package/allosaurus-raptor-material-contact-preflight-975a-002/receipt.json`, SHA-256 `a6feae20b0191f84c70fa56a1d2f787a60442b2983b876b763388b819c889e8d`.
- Actual-package result: same directory, `result.json`, SHA-256 `8c911a3d03fe5207af6f74f69c69058ea9d7b86287069418d3aad2e2cc0e6ddb`.
- Actual-package inventory: 71 unique keys, midpoints, and event ±1 ms samples are `AVAILABLE`; maximum sampled local-joint secant `835.814138°/s < 1200°/s`, foot-pitch secant `462.054610°/s < 600°/s`, with requested material clearance preserved.
- `git diff --check 706c226..8d78946` passed and the frozen worktree was clean.

## Boundary

This closes the concrete event-neighborhood P1 for the non-emitting source query. The sampled secants are not continuous derivative authority. Emitted package, native visual, body-animation transfer, Unity, and production acceptance remain outside this narrow review.
