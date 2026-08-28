# Independent channel/version technical review

## Verdict

- Commit: `1676f03f3343deac0b260dc7c8dc5e09987c0c96`
- Diff: `829fff1a10d89d9f5f0c2f6ab902930956f8076f..1676f03f3343deac0b260dc7c8dc5e09987c0c96`
- P0: **0**
- P1: **2**
- P2: **0**
- Recommendation: **FAIL / do not accept the stable-update path yet**

Stable, working, and explicit resolution are deterministic and exact V8.2 is
preserved. The blocking defects are both in the promotion-only state
transition: the new stable pointer does not reference the promoted release,
and a state-write failure leaves an orphan immutable history record that makes
the same valid transition permanently non-retryable.

## Findings

### P1-1: stable advancement does not point to the promoted release

`promote_run` installs and validates the new release at the requested
destination, then passes its manifest path to `update_stable_channel`
(`src/eonwild_motion/pipeline/promote.py:278-290`). The channel updater hashes
that manifest only for the history record
(`src/eonwild_motion/pipeline/channels.py:48-60`). When it constructs the new
stable pointer, it ignores the promoted manifest and promoted artifact paths
and instead writes `resolved.source_manifest_path` and
`resolved.approved_output_path`
(`src/eonwild_motion/pipeline/channels.py:63-84`).

That means successful `--update-stable` does not make stable resolve to the
release that promotion just created. In the current same-V8.2 fixture the bug
is masked because the working profile already points to the existing V8.2
capsule and approved GLB. A controlled update using a distinct promotion
manifest produced generation 2 while the new stable object still contained:

- manifest: `procedural-animation-toolkit(v8.2)/RELEASE_MANIFEST.json`
- artifact: `procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb`

The new promotion manifest appeared only as an unresolvable SHA in history; no
stable path referenced it. This contradicts the transition contract that the
new stable pointer is derived from the approved promoted release
(`reports/PROCEDURAL-ENGINE-V8-3/architecture.md:57-69`) and prevents the model
from advancing correctly when working targets an actual later profile.

Required closure: derive stable release manifest and artifact references from
the installed promotion destination, require those paths to live in the
repository-owned immutable release area, bind their hashes to the promoted
manifest, and add a test where the promoted destination is deliberately
different from the working profile's source release.

### P1-2: state replacement failure strands history and prevents retry

The updater checks that the history path does not exist, then writes history
and channel state as two separate operations
(`src/eonwild_motion/pipeline/channels.py:44-47` and
`src/eonwild_motion/pipeline/channels.py:87-89`). Each individual JSON write is
atomic, but the two-file transition is not. `promote_run` removes the newly
installed release directory if the updater raises
(`src/eonwild_motion/pipeline/promote.py:291-295`), but it does not remove or
quarantine a history record already written by the failed transition.

Controlled failure injection made the first history write succeed and the
second state write raise `OSError`. The result was:

- channel state remained byte-identical to generation 1;
- `history/stable-0002-a2cf73a3c7d1.json` remained present;
- retrying the same otherwise-valid transition failed with `ValidationFailure:
  stable history already exists`.

This is a partial commit: history claims a replacement that never became
stable, while rollback makes the approved release destination disappear. It
violates the stated rollback/no-overwrite boundary and converts a transient
write failure into a permanent manual-repair condition.

Required closure: make the history/state transition recoverable as a unit.
For example, stage both records, atomically install state, then finalize an
idempotently verifiable history record, or explicitly roll back a newly-created
history file when state replacement fails while never deleting pre-existing
history. Add failure injection after each filesystem operation plus a retry
test proving state/history/release consistency.

## Passing evidence

### Resolution and lock binding

The canonical state schema validates and all three selectors resolved with the
declared identities:

- stable lock: `ebd3305dad6064f359d5a2ffd2a351169f6df092da3ee75f293cc9a39256d419`
- working lock: `4198300a8a34e93f56f2235f1555b4024f42fc1b10cee5cb5cf01009f83a3bb3`
- explicit V8.2 lock: `eba6d05608e5b34c408dfeed5f9440ac85444b441d380c9279688e76d5c280ec`
- channel-state SHA: `d895da0d02cea27805153677d9bff34d2372c6066076024887772a05d9b9ac67`

Stable and working bind the state SHA, generation, revision, history identity,
and channel name; working additionally binds iteration. Explicit resolution
retains null channel metadata and the prior exact profile lock. Missing,
schema-invalid, profile-hash-stale, stable-artifact-stale, engine-mismatched,
and working-base-mismatched states fail closed in implementation/tests.

### Focused verification

The documented focused suite passed:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_channels -v
Ran 5 tests in 0.402s — OK
```

The two relevant integration checks also passed after two real builds/renders:

```text
test_nonpromotion_commands_leave_source_status_unchanged ... ok
test_promotion_gates_and_no_overwrite ... ok
Ran 2 tests in 29.083s — OK
```

These prove ordinary-command channel/history immutability, the successful
fixture transition, existing-destination refusal, and the currently covered
pre-update rollback injection. They do not cover either P1 above.

An isolated installed-package smoke succeeded:

```text
pip install --no-deps .
eonwild-motion --help
usage: eonwild-motion [-h] {build,validate,compare,render,promote} ...
```

### V8.2, legacy, signature, and source hygiene

- Approved V8.2 GLB remains SHA-256
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
- Existing V8.2 release manifest remains SHA-256
  `51f493aaae13fe46d8b6d3600ec1a8de117c2ee39beb6e05159398cacb21fada`.
- V5, V5.5, and V8.2 toolkit tree IDs are unchanged from the review base:
  `dedabea120c3e2e7c82758eb351521fee8417e75`,
  `aff45b0dc8da9dbf28343c0cc9715c9a6a0e255a`, and
  `0ef600321dfef270b5d29aa501b0a2674c9ce5f2`.
- `git diff --check` passed and the implementation worktree was clean before
  this report was written.
- The commit is a direct child of the requested base and has a valid SSH
  signature for `117486687+hurtener@users.noreply.github.com`, RSA fingerprint
  `SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`.

## Disposition

No implementation, schema, profile, release, or media file was modified by
this reviewer. Because P1 is nonzero, this report is intentionally uncommitted.
