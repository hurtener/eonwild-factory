# Adult sagittal body response independent review

- Reviewed head: `7e90292c4bd92c35bd40906537371d072a4c2899`
- Base: `3726cb7fe4e620745f83d1e5ea7499561a1191ae`
- Scope: five-file feature delta only
- Result: **one P1; no P0**

## P1 — forged semantic root is accepted by the new hierarchy validator

`src/eonwild_motion/solve/performance.py:280-323` describes typed, disjoint
body chains following the actual hierarchy. It validates pelvis→trunk,
trunk→neck→head, and pelvis→tail, but never connects the declared semantic root
to the pelvis. An unrelated existing node therefore passes as `roles["root"]`.

Reproduction against the exact bound source and rig:

1. Load
   `assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb`
   and `catalog/rigs/heavy-biped.v9.json`.
2. Replace `roles["root"]` (`Bone_000`) with unused existing node `Bone_060`.
3. Call `_sagittal_body_chains(source, forged_roles)`.
4. Observed: returns all chains successfully (`FORGED_ROOT_ACCEPTED Bone_060`).

The actual pelvis `Bone_001` has parent `Bone_000`. Upstream neutral admission
only requires that the declared root name exist, and the gait solver validates
leg/toe topology but not root→pelvis. The forged root consequently owns emitted
root travel while the sagittal carrier continues rotating the original pelvis
tree. This breaks the semantic binding the new feature says it validates.

Narrow closure: require the actual pelvis parent to equal the declared root and
add an actual-rig regression for an existing unrelated root masquerade.

## Other evidence

- All seven recipe bindings resolve to their declared SHA-256, including the
  new performance v5 profile.
- Legacy omission, strict option/amplitude validation, grounded-only behavior,
  body-chain disjointness, leg/neck masquerade rejection, transition interface,
  and emitted actual-rig response are covered by meaningful focused tests.
- `31 passed, 48 deselected` in the targeted body and catalog gate.
- `git diff --check 3726cb7..7e90292c`: PASS.
- No source or checkout state was changed by this review.

## Narrow closure

- Fix head: `4ea2ad2a9e2e73fdb7bfc2b0cd34445c044c1ae4`
- Reviewed diff only: `7e90292..4ea2ad2`
- Result: **P1 CLOSED; no new P0/P1**

The two-file fix resolves the declared root node and requires it to be the
actual parent of the pelvis before any carrier mutation. The regression uses
the production GLB and the original `Bone_060` masquerade. Independent replay
now reports `FORGED_REJECT sagittal body semantic roles must follow actual
topology`, while the unmodified production mapping returns trunk/neck/tail
chain lengths `6/5/9`.

Targeted closure gate: `3 passed, 73 deselected`, covering the forged-root
rejection and both signed valid production-rig responses. Diff check passed,
and the body checkout remained clean at exact fix head `4ea2ad2`.
