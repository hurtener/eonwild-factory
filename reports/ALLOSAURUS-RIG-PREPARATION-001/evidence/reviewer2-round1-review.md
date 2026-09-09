# Rig preparation reviewer 2 — round 1

Reviewed exact commit `f941fe9b1b3e9eceb897dd5541c0a0af83730888`
(parent `00de4845f59ef283ce9cd00d97e90c6218f326c5`). This is a read-only
review of the three-file source/config/test stage. The author's working tree
began its separate postfix while this review ran, so the exact committed module
and test were archived under `exact-source/` and the probes import that module.

## Findings

### P1 — selected-skin rewrite can corrupt an unselected skin

`prepare_rig` accepts a source with multiple skins and validates/rebuilds only
the selected skin's inverse-bind accessor. The probe adds a second mesh and skin
over the same hierarchy, backed by an independent inverse-bind accessor. Its
input skin reconstruction error is `0.0000011353242509093592 m`. Preparation is
accepted, but the unchanged second skin has `1.0466473631570283 m` reconstruction
error afterward. Hierarchy changes are global, so the selected-skin proof does
not protect other skins.

Fail closed on unsupported multi-skin inputs, or enumerate every affected skin
and preserve it independently. The current stage should use the smaller exact
one-skin boundary because the implementation and evidence are single-skin.

### P1 — input neutral preservation is not established

The function reconstructs only the prepared output against stored `POSITION`.
It never checks that the incoming skin reconstructs that same neutral surface.
Independently shifting every incoming inverse-bind x translation by 0.01 m gives
an input skin error of `0.020087094131633104 m`; preparation accepts it and then
reports only `0.0000008672800672062335 m` output error. The operation therefore
silently replaces a noncanonical incoming neutral rather than preserving the
actual input. This reproduces the first root finding with a separate driver.

Require the admitted source's full selected skin to reconstruct its `POSITION`
surface within the declared preservation tolerance before changing hierarchy or
inverse binds. Also reject a selected mesh node used as one of its own joints.

### P1 — declared jaw branch does not isolate the moving lower jaw

The production articulation validates node ancestry, but not whether weighted
skin outside the intended lower-jaw surface is owned by that branch. Root's
native +8°/-8° diagnostic shows the upper snout and upper tooth row moving with
the declared lower jaw. The report's cranium subset excluded suspected
jaw-weighted vertices, so its stability number could not disprove that leakage.
This is a concrete source-weight admission failure, not an animation approval
question. Require an independently defined source-space upper/lower region and
either reject leakage or apply a declarative, source-bound transfer with a full
neutral/reopened and articulation deformation proof.

### P2 — duplicate articulation authority is accepted

Two articulation rows can repeat the same role and node with opposite axes.
The exact head accepts and emits the contradictory receipt. Roles and controlled
nodes should be unique; descendant names should also be unique within a row.
This is local metadata hardening because the current preparation step does not
yet consume the articulation rows as motion commands.

## Verification

- Exact f941 test file contains seven cases. Root's pre-edit exact-head run was
  `7 passed in 3.46s`. A later local `9 passed in 6.31s` run used the author's
  in-progress postfix working tree and is not evidence for f941.
- `git diff --check f941fe9^..f941fe9`: clean.
- `probe.py` executes the two P1 corruptions and duplicate-authority P2 against
  the archived exact module. `result.json` contains finite JSON and binds the
  fixture, reviewed head, accepted output hashes, and measured residuals.
- Candidate remains non-promoted. The static views do not approve hands/pedal
  digits, animation behavior, biological fit, Unity parity, or production use.

## Evidence hashes

- Exact committed module: `160adf93e33606b3c2477c122887a600b8ba764ef2260a365406228ccb9170d0`
- Exact committed test: `585729fcb648867a5d1fc5561480ce4b998026741c4c56540cf024f1eb2a1eaa`
- Root round-1 report: inspect retained `../rig-preparation-root-review/README.md`
- Production candidate GLB cited by root: `0fe715fe38aeca125d3ecda873d4575eb151690c4b759cbfdfbaa0f0ef8ec04f`
