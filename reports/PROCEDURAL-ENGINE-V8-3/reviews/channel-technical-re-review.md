# Channel P1 narrow re-review

## Verdict

- Commit reviewed: `42f5fe6eb00597b589d697b8ddf4fc2f90dd13dc`
- Parent: `1676f03f3343deac0b260dc7c8dc5e09987c0c96`
- Scope: the two P1 findings in `channel-technical.md`
- P0: **0**
- P1: **0**
- P2: **0**
- Recommendation: **PASS for the P1 closure scope**

## P1-1 closure: stable binds the installed promoted release

The stable-update path now requires its destination below repository-owned
`releases/`, schema-validates the installed `manifest.json`, and binds its
release ID, engine, profile, working-channel identity, artifact path, artifact
hash, and approved output (`src/eonwild_motion/pipeline/channels.py:27-68`).
The next stable object is populated from those installed manifest/artifact
bytes rather than the working profile's source capsule
(`src/eonwild_motion/pipeline/channels.py:204-255`). Stable resolution validates
that repository release and replaces the resolved approved-output path with
the promoted artifact (`src/eonwild_motion/contracts/resolve.py:244-283`).

Independent temporary reproduction used a distinct destination under
`releases/` and confirmed:

- stable manifest path exactly equaled the installed destination manifest;
- stable artifact path exactly equaled the artifact inside that destination;
- both state hashes equaled the installed bytes;
- `resolve_profile("stable")` returned that promoted artifact path.

The temporary release was removed after the check; no `releases/` residue was
left.

## P1-2 closure: injected failures roll back and retry

History and state are staged as fsynced sibling files. Installation checks the
exact prior state and history nonexistence, installs history without overwrite,
then replaces state. The exception path restores exact prior-state bytes,
removes only the just-installed history after verifying its hash, cleans staged
files/directories, and verifies the rollback
(`src/eonwild_motion/pipeline/channels.py:75-178`). Promotion still removes its
new destination if the channel transition fails
(`src/eonwild_motion/pipeline/promote.py:281-297`).

Independent failure injection at all four exposed boundaries produced the
same result:

| Boundary | Raised | Exact state restored | No history residue | Identical retry |
|---|---:|---:|---:|---:|
| `history-staged` | yes | yes | yes | generation 2 PASS |
| `state-staged` | yes | yes | yes | generation 2 PASS |
| `history-installed` | yes | yes | yes | generation 2 PASS |
| `state-installed` | yes | yes | yes | generation 2 PASS |

The integration test additionally injects failure after history installation
through the full promotion path and verifies destination removal, exact state
restoration, no history directory, and successful identical retry.

## Focused verification

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_channels -v
Ran 6 tests in 1.019s — OK
```

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest \
  tests.test_integration.VerticalSliceTests.test_nonpromotion_commands_leave_source_status_unchanged \
  tests.test_integration.VerticalSliceTests.test_promotion_gates_and_no_overwrite -v
Ran 2 tests in 30.671s — OK
```

Exact preservation checks also passed:

- V8.2 GLB SHA-256:
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`
- V8.2 release-manifest SHA-256:
  `51f493aaae13fe46d8b6d3600ec1a8de117c2ee39beb6e05159398cacb21fada`
- canonical channel-state SHA-256:
  `d895da0d02cea27805153677d9bff34d2372c6066076024887772a05d9b9ac67`
- no V8.2 toolkit, profile, or canonical channel-state path changed in the fix
  diff;
- `git diff --check` passed;
- the exact commit has a valid SSH signature for
  `117486687+hurtener@users.noreply.github.com`, fingerprint
  `SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`.

No engine, schema, profile, release, channel state, or media file was modified
by this reviewer. Per instruction, this report is not committed.
