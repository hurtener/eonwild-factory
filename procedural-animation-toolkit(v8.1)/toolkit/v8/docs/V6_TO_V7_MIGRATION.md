# V6 → V7 Migration

## Breaking correction

V6 locomotion clips must not be promoted as production walk assets. Their pelvis translation was not consistently part of the final leg/contact solve. V7 regenerates locomotion rather than filtering or retargeting those broken tracks.

## API changes

- Use `BipedV7Profile`.
- Use `TarbosaurusV7LocomotionGenerator`.
- Exporter now emits the exact contact-solved pelvis translation.
- Turn diagnostics are available at `diagnostics.turn_mass_lead`.
- Browser runtime accumulates root-cycle displacement.
- Mirrored power bite is a first-class action and sequence.

## Runtime clip renames

All `_V6` suffixes become `_V7`. The catalog remains forty clips: twenty-two base/action clips plus eighteen authored transitions.

## Mandatory regression tests

- Re-skin the baked relaxed walk and measure mesh/sole height.
- Play at least two loops of root-motion walk in the browser.
- Play both turns from side and overhead views.
- Queue walk → action → recovery → walk sequences.
- Verify active button and queue status.
