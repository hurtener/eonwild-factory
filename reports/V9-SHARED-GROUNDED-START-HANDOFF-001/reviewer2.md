# Handoff contact-floor calibration reviewer 2

Reviewed exact clean head
`1f783f87d3604b7a2fe6ae5acb1998569ed6582f` (tree
`19dd976747bbe66071bd24a28c8e238545d0b503`) against parent
`215588c75c5e64f5ce9f9dbbe3fa5fcfdfca03a4`. The review was limited to the
two-file handoff calibration diff.

The handoff reader now derives the contact profile from the same hash-locked
animal instance and uniform geometry scale used by compilation. The animal
loader binds the calibration to the recipe source SHA before scaling, the
contact scaler returns a detached profile, and the existing handoff pair gate
already requires equal animal bindings. Both boundary readers therefore keep
their existing strict runtime-ground equality check against one calibrated
profile. Recipes without an animal still return the locked legacy profile
unchanged. No package bytes, contact tolerance, or comparison threshold is
changed.

All 54 emitted-handoff tests passed independently in 0.83 s, including the
actual V10 scale, legacy omission, source-substitution, immutable-input, floor
equality, pair-binding, exact tangent, and malformed timeline cases. The
two-file diff check passed. The test file retains pre-existing style findings
outside this narrow diff; the changed production file introduces no Ruff
finding.

P0: 0. P1: 0. Local actionable P2: 0. Actual start/steady handoff and native
acceptance remain separate execution evidence owned by the author and root.
