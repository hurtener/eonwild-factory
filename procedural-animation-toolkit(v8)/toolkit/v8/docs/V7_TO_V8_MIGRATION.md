# V7 → V8 Migration

V8 is additive over V7. The lower-body locomotion/contact architecture is retained. Runtime clip names advance from `_V7` to `_V8`.

## Runtime changes

- Load `animation-manifest.v8.json`.
- Use the V8 state graph and event markers.
- Do not add a runtime crossfade after authored transition clips.
- Accumulate root-motion loop deltas.
- Bind attack effects to `bite_contact`, not clip start.
- Bind feeding effects to `feeding_bite_contact`, `feeding_pull`, and `feeding_chew_swallow`.

## Behavioral changes

- Turn clips carry larger head/neck lead and overshoot.
- Bite clips are longer and contain two support changes.
- Feeding loop duration is 10.8 seconds and contains three irregular events.
- Existing V7 relaxed walk remains the regression baseline but has V8 names.
