# PROCEDURAL-ENGINE-V8-3 — implementation summary

## Result

The repository now has a permanent schema-validated stable/working channel
model on the single `eonwild-motion` engine. Stable and working initially point
to the exact approved V8.2 profile; working is iteration `0`, revision `1`.
No motion layer, GLB, release capsule, or reviewed report changed.

CLI examples:

```sh
eonwild-motion build --profile stable --work-root /external/work
eonwild-motion build --profile working --work-root /external/work
eonwild-motion build --profile profiles/v8.2/profile.json --work-root /external/work
```

Every resolved lock and run/evidence profile binding now records channel,
channel-state SHA, generation, iteration, revision, and history identity.

Stable changes only through an explicitly approved promotion with
`--update-stable`. The tested temporary transition retained prior state in a
non-overwritable history record and advanced generation/revision. Ordinary
commands left canonical state byte-identical and created no history directory.
An injected stable-update failure also proved that the newly-created release
destination is rolled back.

The full suite passed 26 tests in 43.218 seconds, including two exact builds,
two byte-identical canonical renders, the retained P1 negatives, stale channel
and stable-artifact rejection, immutable history, and installed CLI discovery.

## Exact identities

- Engine: `0.1.0`
- Channel state SHA-256:
  `d895da0d02cea27805153677d9bff34d2372c6066076024887772a05d9b9ac67`
- Stable resolved lock:
  `ebd3305dad6064f359d5a2ffd2a351169f6df092da3ee75f293cc9a39256d419`
- Working resolved lock:
  `4198300a8a34e93f56f2235f1555b4024f42fc1b10cee5cb5cf01009f83a3bb3`
- Explicit V8.2 resolved lock:
  `eba6d05608e5b34c408dfeed5f9440ac85444b441d380c9279688e76d5c280ec`
- Approved artifact remains:
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`

## Deferred

- No V8.3 profile or motion exists yet.
- No hip-balance channel or layer was added.
- Working-channel mutation is intentionally not exposed as a casual build
  side effect; a future bounded profile-management command must preserve the
  same schema/hash discipline.
