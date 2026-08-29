# V9 contact/gauge evidence commands

Commands were run from:

`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`

The slice is uncommitted on `codex/procedural-engine` at the pinned
implementation head below. `PYTHONDONTWRITEBYTECODE=1` was used for Python
checks. No incoming evidence video was read.

## Repository identity

```sh
git branch --show-current
git rev-parse HEAD
```

```text
codex/procedural-engine
85de1f2ceaa75427f74090a47d2b6a1ca3c6022a
```

## Strict focused checks

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  python3 -m unittest -v tests/test_v9_contact_gauge.py tests/test_contracts.py
```

```text
Ran 27 tests in 8.496s
OK
```

The twenty-four contact/gauge tests cover strict policy admission, generic
synthetic measurement, yaw-axis invariance, zero-travel rejection, immutable
root-motion extraction, in-place rejection, accessor bounds and malformed
container rejection, repository path admission, irregular timestamp travel,
finite-difference contact velocity, hip-derived lateral semantics,
canonical-H normalization, step-width policy admission, unsupported turns,
nonzero timeline bounds, simultaneous-touchdown step rejection, end-to-end GLB
timeline bounds, and skin-weight normalization. The three existing
contract tests also confirm that the canonical engine has
no release-specific literals and that its existing profile/channel contracts
remain valid.

## Full regression

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  python3 -m unittest discover -s tests -v
```

```text
Ran 76 tests in 75.643s
OK
```

No tests were skipped. The suite includes the existing V8.2/V8.3 pipeline and
negative checks plus the 23-test V9 contract-gateway suite and twenty-four
contact/gauge tests.

## Report generation and deterministic double run

The checked-in machine report was generated with the callable API:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
from eonwild_motion.contact_gauge import analyze_glb

root = Path('.')
result = analyze_glb(
    root / 'procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb',
    root / 'profiles/v9/contact-gauge-v8.2.json',
    root / 'reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json',
    repository=root,
)
result.write(root / 'reports/V9-CONTACT-GAUGE-001/contact-gauge-report.json')
print(result.report_sha256)
PY
```

The generated report has canonical JSON hash
`04debe04ab7e4c27cb58824d7ab7e1a7d3b972432229fa50b0822a293ad20be6` and file
SHA-256
`1357d48d152e457bebe47ec474fa8e24ae390b4b7a975b5521dc29ad93a87f46`.

Two independent calls to the same API produced:

```text
first_canonical_sha256  04debe04ab7e4c27cb58824d7ab7e1a7d3b972432229fa50b0822a293ad20be6
second_canonical_sha256 04debe04ab7e4c27cb58824d7ab7e1a7d3b972432229fa50b0822a293ad20be6
first_file_sha256       1357d48d152e457bebe47ec474fa8e24ae390b4b7a975b5521dc29ad93a87f46
second_file_sha256      1357d48d152e457bebe47ec474fa8e24ae390b4b7a975b5521dc29ad93a87f46
byte_equal              True
canonical_equal         True
finite                  True
```

## Input and release-witness hashes

```sh
sha256sum \
  'procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb' \
  assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb \
  profiles/v8.2/profile.json profiles/v8.2/profile.lock.json \
  profiles/v8.3/profile.json profiles/v8.3/profile.lock.json \
  profiles/channels/state.json \
  reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json \
  profiles/v9/contact-gauge-v8.2.json \
  reports/V9-CONTACT-GAUGE-001/contact-gauge-report.json
```

```text
a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5  procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb
b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03  assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb
37a26e006700350bc42d40eeb50f93bb4fa63dae98c98db2423a8eb3c9157c9b  profiles/v8.2/profile.json
6e4a740605d8b06feb33d318bafc65bbd75f64a8df19210f00031f5fbeffa228  profiles/v8.2/profile.lock.json
d222e1159db92928a442c1fa0c048ac1c8c733a3dfc3e7a18731a9416cd96815  profiles/v8.3/profile.json
0419a7612337d911ac88286f31916345d6d5d76151943b4b74bcd1fdda2632cf  profiles/v8.3/profile.lock.json
0fb80ed42b0b53e91e6fd55af272c2f4a0c1a9f724c2d6263b6f74a8af543b8a  profiles/channels/state.json
9c1a142867b46c19b5f5c8f45677ecae86e50918e56562f86702cc10c085c89f  reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json
b1235eae91ec033fe4e7c2a475b7a2ab666fb5aae758d860eb5cae02e4425cd6  profiles/v9/contact-gauge-v8.2.json
1357d48d152e457bebe47ec474fa8e24ae390b4b7a975b5521dc29ad93a87f46  reports/V9-CONTACT-GAUGE-001/contact-gauge-report.json
```

The V8.2 profile lock declares `lockSha256` `eba6d05608e5b34c408dfeed5f9440ac85444b441d380c9279688e76d5c280ec`; the V8.3 profile lock declares `lockSha256` `4b506eb9145ccdeb21bebbb58d8fd40aa3a0048c1625be927655c012f989abc9`.

## Scope check

```sh
git diff --check -- src/eonwild_motion/contact_gauge.py \
  tests/test_v9_contact_gauge.py profiles/v9/contact-gauge-v8.2.json \
  reports/V9-CONTACT-GAUGE-001
```

The check passed. The working tree still contains unrelated user-owned
changes/untracked evidence outside this task; they were preserved and are not
part of this report.

The final machine evidence file SHA-256 is:

```text
49ffa3a74119d0e297f7c5584ab02eff4a1d1196ec9ff1b5b6bf40aba8aa48ce  reports/V9-CONTACT-GAUGE-001/evidence.json
```
