# Blender cubic playback narrow compatibility closure — reviewer 2

Reviewed exact head `527d27467c57c116041907976b36aa8728592b8b`
against parent `f5207ca3a83718f21f0c8fb1bd25d891be6a4a8f`.

**PASS — no P0/P1 findings.**

The detector now inspects every serialized animation sampler before invoking
the exact CUBICSPLINE adapter. Genuine multi-clip LINEAR content remains on
Blender's stock import path, while any CUBICSPLINE sampler still enters the
existing strict one-animation/common-timeline adapter and its render-time
action-detachment checks.

Evidence:

- The approved immutable V8.2 asset SHA-256
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`
  has two LINEAR clips, imports through stock Blender playback, returns no
  adapter, preserves both actions, and remains byte-identical.
- The prior real Cycles CUBICSPLINE proof remains PASS at
  `2.3496518960810366e-6 m` in-place and
  `2.4421291038418187e-6 m` root-motion after render evaluation.
- Author receipt
  `audits/blender-cubic-playback-001/narrow-527d274/receipt.json`
  SHA-256
  `507970116a37951bbbca50486475393889a9c92aba892462827aaf3d7e1169f3`
  records 43 focused tests plus 10 subtests and Ruff PASS.
- Reviewer-local focused run:
  `test_blender_native_playback.py` and
  `test_showcase_acceptance.py`: 20 tests plus 10 subtests PASS in 0.59 s.

The change does not alter GLB bytes, source interpolation, recipes, native
curve claims, or FBX support.
