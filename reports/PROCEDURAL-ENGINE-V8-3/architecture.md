# Permanent engine, profile, and channel model

## One engine, data-owned revisions

`eonwild-motion` remains one package at semantic version `0.1.0`. Animation
versions and iterations are not branches, copied engine folders, or Python
conditionals. They are release profiles and channel metadata.

The canonical state is `profiles/channels/state.json`:

- `stable` binds a profile path/hash, its explicit profile-lock SHA, an
  immutable release manifest, and the approved artifact path/hash.
- `working` binds a profile path/hash and explicit profile-lock SHA plus
  `iteration`, `revision`, and `basedOnStable` metadata.
- top-level `generation` changes only when stable is explicitly advanced.
- `engineVersion` must exactly equal the installed engine version.

The initial working channel deliberately points to V8.2 with iteration `0`,
revision `1`. This establishes the permanent mechanism without claiming a new
motion result.

## Resolution and lock identity

`--profile` accepts exactly three forms:

1. `stable`;
2. `working`;
3. an explicit profile path.

Channel resolution validates the state schema, engine version, profile hash,
explicit profile lock, working/stable ancestry, and—on stable—the release
manifest and artifact against the profile. The resolved channel lock hashes:

- the explicit profile-lock SHA;
- channel name;
- channel-state SHA;
- generation;
- iteration/revision;
- stable-history identity.

The filesystem location of an identical channel-state fixture is not semantic
lock input. This permits deterministic isolated verification while the runtime
record separately retains the exact resolved state path.

Explicit paths preserve the pre-channel resolved lock. Run reports and all
validation, render, comparison, and promotion evidence carry the channel,
state SHA, generation, iteration, revision, and history identity, or explicit
`null` values for direct paths.

## Mutation boundary

Build, validate, compare, and render are read-only with respect to channel
state and history. The only CLI mutation path is:

```sh
eonwild-motion promote ... --update-stable
```

It remains behind all existing clean-source, exact-hash, provenance,
independent-approval, validation, contact, render, media, and review gates. A
stable update additionally requires that the promoted run was built through
`working`, that channel state is byte-identical to the build lock, and that
working revision/generation have not moved.

The transition writes a new non-overwritable history record containing the
prior stable object and prior state SHA, then atomically writes the next state.
The new stable pointer is derived from the approved profile/release/artifact;
no caller-supplied release identity is trusted. A repeated history identity is
rejected. If the stable update fails after the new release directory has been
installed, promotion removes only that newly-created destination and reports
failure instead of leaving an apparently promoted but untracked release.

## Future working iteration

A future V8.3 profile is added beside V8.2, then `working.profile`,
`working.iteration`, and `working.revision` advance together. That channel
mutation changes the resolved lock even before motion bytes change. Hip balance
will later enter as a declared layer referenced by that profile; it does not
require an engine copy or branch-specific logic.
