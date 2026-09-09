# Allosaurus rig preparation — reviewer 2 narrow closure

## Scope

Read-only, diff-only closure review of
`f941fe9b1b3e9eceb897dd5541c0a0af83730888..55cd2b64bcfd1e315277d025f78cecf6927274e1`
(tree `f1307185e741060a198deb257f70273feb2a6a4d`). I reviewed only the
previously reported noncanonical-input, multi-skin, duplicate-articulation,
and jaw-weight-ownership fixes plus the frozen production candidate. This is
not another whole-stage review.

## Result

**CLEAN: P0=0, P1=0.** No concrete local P2 was found in the narrow patch.

The three executable corruption witnesses now fail closed with the expected
typed contract errors:

- a 10 mm inverse-bind translation change is rejected because the neutral
  source skin is not canonical POSITION geometry;
- a second skin is rejected before mutation because preparation supports
  exactly one skin;
- a second articulation declaration for the same node is rejected because
  articulation roles and nodes must be unique.

The exact Allosaurus source and committed configuration regenerate the frozen
candidate byte-for-byte. Input SHA-256 is
`91d9816b6bbaeb1037f3e9cbf253261799d8a4121efd91e0e2185f76908a6bf7`;
candidate and regenerated SHA-256 are both
`c56772d63045d3410b8efe81eb45f7ee06ad97307fa076a32033553dab372c41`.
The receipt reports input neutral-skin error `7.774061190383236e-07 m`,
reopened output neutral-skin error `3.749428662070317e-07 m`, and reopened
world-matrix error `1.0374803127710663e-08`. The declared upper-skull transfer
selects 6,672 vertices and changes 6,132 with source-world halfspaces recorded
in the receipt.

The tracked candidate report's complete `SHA256SUMS` inventory verifies. The
focused rig-preparation suite passes: `11 passed in 10.16s`. Root separately
owns the native neutral/jaw visual judgment; this closure does not promote the
candidate or assert Unity, animation, biological, or production approval.

## Reproduction

Run from an exact checkout of the reviewed head with the repository source on
`PYTHONPATH`:

```sh
source "$ARC/task-env.sh"
PYTHONPATH=src /Volumes/m2-extended-disk/Repos/eonwild-factory/.venv/bin/python \
  "$ARC/audits/rig-preparation-reviewer2-55cd2b6/probe.py"
PYTHONPATH=src /Volumes/m2-extended-disk/Repos/eonwild-factory/.venv/bin/python \
  -m pytest -q tests/test_rig_preparation.py \
  --basetemp="$ARC/worktrees/eonwild-shared-motion-set-release-validation/out/pytest-rig-prep-reviewer2-55cd"
```

`probe.py` and `result.json` are the exact independent reviewer artifacts.
