# Bind-pose accessor exceptional narrow closure — reviewer 2

Status: **CLEAN — no open P0/P1**

Reviewed only `ef1c3055e83d4d2ec84a9c31de902c8ccf662a78..4fc8c9cb9e6f48a266c516f1c4328ad91a19b1a5`,
the one-line vertex-accessor alignment correction and its exact regression.
No source or test file was edited during review.

The final rule requires a four-byte-relative offset for the VEC3/VEC4
accessors used as skin vertex attributes while retaining component-size
alignment for MAT4 inverse binds. This closes the value-preserving
`JOINTS_0` counterexample: moving the view back one byte, enlarging it one
byte, and setting accessor `byteOffset=1` leaves every decoded joint value
unchanged but now raises `ContractError`.

The complete independent accessor receipt rejects:

- short inverse-bind and POSITION views;
- short, Boolean, and fractional declared buffer lengths;
- a missing required buffer-view buffer index;
- cancelling misaligned inverse-bind offsets;
- four bytes beyond the allowed embedded-buffer padding;
- a losslessly repacked `JOINTS_0` accessor at five-byte stride; and
- the value-preserving one-byte vertex accessor offset.

The unchanged valid source still emits byte-identically as
`2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`
with maximum reopened skin error
`1.1353242509093592e-06 m`.

## Evidence

- Full accessor closure receipt:
  `bind-pose-accessor-final-closure-4fc8c9c.json`,
  SHA-256 `24e7b816b9c7bd559c650ba6375a871e152cd9972b530b62f91a6c7e4a539452`.
- Exact vertex-offset closure:
  `bind-pose-vertex-offset-final-4fc8c9c.json`,
  SHA-256 `3b1b7f87a3bd9275f912654eafb62b4a0098c900057eb7c61126180feecfcc92`.
- `34 passed in 7.30s`: bind recovery, adult bind catalog, and public
  admission tests, using external-SSD temporary storage.
- Ruff and `git diff --check`: pass.
- Frozen tree:
  `92593198cafa02e4ea9aa7f135db2374383c7d4f`.
- Recovered source SHA-256:
  `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`.
- Admission evidence SHA-256:
  `3f50f1de1021c08229e0b611d692779208aaaddf4eeebdbc2c76382bc3154007`.

This closure covers only the bind-recovery accessors that provide inverse-bind
matrices and full-skin POSITION/JOINTS/WEIGHTS evidence. It does not replace
whole-file Khronos validation or expand into unused glTF attributes. Existing
visual, Unity, biological, and exact-continuity status remains unchanged.
