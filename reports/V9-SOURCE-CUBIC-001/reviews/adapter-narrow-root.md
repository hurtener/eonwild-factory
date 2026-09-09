# Blender legacy compatibility: root narrow closure

Reviewed only `f5207ca3a83718f21f0c8fb1bd25d891be6a4a8f..527d27467c57c116041907976b36aa8728592b8b`. PASS, remaining legacy multi-clip LINEAR P1 closed; no new P0/P1 in this narrow correction.

The detector now scans serialized samplers without imposing the exact cubic adapter's single-animation/common-timeline contract. The strict adapter contract runs only after cubic is found. Explicit cubic rejection in unsupported consumers remains in place.

Root independently imported the unchanged approved V8.2 GLB in actual Blender 5.2.0 LTS: detector accepts the stock path, adapter is None, both original named LINEAR actions remain, and source SHA is unchanged. All eight dedicated playback tests pass. The author also reran the real adult cubic Cycles regression at this final head; the local conversion and detachment code are unchanged from root's full post-render parity pass at f520.

This is the exceptional narrow closure after two full review rounds, not a third full review. Combined integration/full suite, new movies, body-weight visual review, Unity and production remain separate.

- `root-blender-cubic-narrow-527d274-native.json`: SHA-256 `f5956e16878f2e579e35d570176fbff7ad3cf78009639ebb8658928994765dd0`.
- `root-blender-cubic-narrow-527d274-native.py`: SHA-256 `75d74a9bb5cb0bdd6ca846a41679521d007df9593adcaed60e8207badd506fba`.
- `root-blender-cubic-narrow-527d274-pytest.log`: SHA-256 `7675afcbf0656da4d29291a330ffc7200eb716c466b0dd4338f6eecaa12bf6a4`.
