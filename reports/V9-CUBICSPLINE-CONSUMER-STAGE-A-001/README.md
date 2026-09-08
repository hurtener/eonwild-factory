# CUBICSPLINE consumer Stage A integration

Status: **READER AND VALIDATOR INTEGRATED; CURRENT MOTION BLOCKED; CUBIC
EMISSION NOT IMPLEMENTED.** This stage makes existing consumers interpret glTF
TRS channels consistently. It does not change a recipe, key time, emitter,
acceptance threshold or retained package.

## Integrated behavior

The shared reader now validates and samples LINEAR and CUBICSPLINE translation,
rotation and scale tracks. CUBICSPLINE values use the glTF three-record layout,
Hermite interval scaling and normalized quaternion curve. LINEAR rotations use
true shortest-path SLERP at every finite angle. Contact sampling, exact local
loop checks, world/FK/LBS endpoint witnesses and direct handoff validation share
the reader.

Malformed accessors, clocks, paths, duplicate channels, non-finite values,
zero quaternions and unsupported interpolation reject. Animated nonconstant
scale remains outside the exact cyclic witness. The factory's interval rotation
rate authority still supports LINEAR only, so a CUBICSPLINE export cannot obtain
a technical pass in Stage A. There is no CUBICSPLINE emitter in this change.

Original implementation commits
`b87c591954c5c5f313d22cad334471f825b62b0d`,
`534ff53eb6cf7133864e713fb33968828d944774`, and
`76219543f5bc5982a77df1435fe1668e39de821a` were integrated as
`17cb08bbfd5435db7a5f6e84d539350b9d860d63`,
`6c7f804a01db39af467f22abc877a405b5aa80d7`, and
`efa1825fcf60317437b403792dd18b0ab6e7b3bf`.

## Review closure

Independent and host review reproduced and closed three material failure
modes: translation-only CUBICSPLINE bypassing the technical block, invalid
negative accessor indices, and LINEAR rotation sampling that used normalized
linear interpolation instead of SLERP. The final small-angle counterexample
used `0.06 rad` over `1/120 s`; sampler, derivative helper and analytic SLERP
now agree at exactly `7.2 rad/s`, including genuine quarter-time checks. No
P0/P1 remains in this bounded stage.

The preserved receipts are:

- `review-independent-round1.md`: SHA-256
  `5bf5db7a003061af76de3a55c4a31adb578354660b3e175346f27ec20052796b`
- `review-independent-round2.md`: SHA-256
  `2e52bc99fa7153ca5f177f73bf8683002cbc56dc390f347b6f30d74eb651ba6c`
- `review-independent-slerp-closure.md`: SHA-256
  `0429140536f9115ca93bd21901457d15629c3635671d664de5f423705ad80e0b`
- `review-root-round1.json`: SHA-256
  `91905a7cc483f8319c2c74091ebe9226ee831b571d102259abe0d89846fa2f04`
- `review-root-slerp-reproduction.json`: SHA-256
  `17019d361443bf9cea434ed6863d5b0be8a5afc7669b54800b964a545ab443f9`
- `review-root-slerp-closure.json`: SHA-256
  `5139489780111e840e7c875a55bdbff3f9b962a6c251eaefcc303f68f308c2ce`

## Combined verification

The code and CI head
`3b1f55602ba2d8d177c42ec15ccb02d401f92b7d` combines Stage A with the
reviewed adult v7 support-speed diagnostic. The complete mandatory suite passed
788 tests plus 21 subtests in 237.65 seconds from a full external-SSD checkout,
using Blender 5.2.0 LTS and Khronos glTF Validator 2.0.0-dev.3.10. There were no
exclusions. `host-validation.json` records the command, identities and hashes;
its SHA-256 is
`a49c810f07637c2269fb0ae9571016978f0df16aabeb0516ec420e5f65795672`.

The first version-probe command stopped before pytest because the Khronos
executable prints its version and usage but exits nonzero for `--version`.
That setup result is retained in the receipt. The unchanged suite then ran to
completion with the already verified executable.

The adult v7 diagnostic was compiled once at the combined head. Its exact
local-loop result remains `BLOCKED`: linear mismatch is
`0.0032116449766123154 m/s` against `0.001 m/s`; angular mismatch is
`3.6520318154983844 degrees/s` against `10 degrees/s`. The shared reader changes
eight emitted hindlimb rotation tracks at float precision through skin
refinement; all translation and scale tracks are exact. Across all 297 keys,
the maximum all-skin displacement from the visually reviewed package is
`1.753765605561636e-7 m`. See the
[adult v7 report](../V9-ADULT-SUPPORT-SPEED-V7-001/README.md) for the scoped host
decision and numerical equivalence receipts.

Hosted CI for the publication descendant is pending. Unity parity is `NOT_RUN`,
body polish remains required, biological validation is absent, and production
approval is false.
