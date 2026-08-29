# Verification commands and results

All commands ran from `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`
with `PYTHONDONTWRITEBYTECODE=1` for Python checks. No command changed V8.2 or
V8.3 release state.

## Source and scope checks

```text
git rev-parse HEAD
195a8b4707997b3309f86f8821217ed1d7e9c22a

git status --short --branch
## codex/procedural-engine...origin/main [ahead 10]
```

The worktree had pre-existing untracked handoff/audit directories; they were
preserved. `git diff --check` passed, and
`git diff --name-only -- 'procedural-animation-toolkit(v*)/**' -- profiles/v8.2 profiles/v8.3 profiles/channels assets/sha256`
returned no paths.

## Contract and planner checks

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_v9_contract_gateway -v
Ran 23 tests ... OK

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
Ran 52 tests in 98.928s
OK
```

The focused suite covers both fixtures, strict schema admission, missing and
unknown fields, stale family/axis aliases, ambiguous units, the provisional
absolute-dynamics guard, finite-number and exponent-overflow rejection,
body-frame COM/topology checks, named source-hash manifests bound to each
embedded input, body/contact substitution rejection, cross-document contact
mismatch, explicit migration, report reload, nested-plan tamper rejection, and
deterministic double-run hashes. The full suite includes the existing 29-test
V8.3 regression coverage.

The emitted report was validated and reloaded through the V9 gateway:

```text
reports/V9-EXTENSION-CONTRACTS-001/evidence.json
plan_sha256     828f59439732de0de8b287b688284afdb0ab4d60ee5caae45c755f2178866629
evidence_sha256 9120adbbfa66330c909de0402fb48c9cedb235ee6f5bc233501ab638713ed8d0
canonical_report_sha256 ad3b687e0888676c6ea400f5390f3709885454d34acb26c2af3beb4c09832f6a
```

## Immutable baseline hashes

```text
a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5  procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb
bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2  procedural-animation-toolkit(v8.2)/input/tarbosaurus_v8_2_iteration_b_base.glb
51f493aaae13fe46d8b6d3600ec1a8de117c2ee39beb6e05159398cacb21fada  procedural-animation-toolkit(v8.2)/RELEASE_MANIFEST.json
37a26e006700350bc42d40eeb50f93bb4fa63dae98c98db2423a8eb3c9157c9b  profiles/v8.2/profile.json
6e4a740605d8b06feb33d318bafc65bbd75f64a8df19210f00031f5fbeffa228  profiles/v8.2/profile.lock.json
d222e1159db92928a442c1fa0c048ac1c8c733a3dfc3e7a18731a9416cd96815  profiles/v8.3/profile.json
0419a7612337d911ac88286f31916345d6d5d76151943b4b74bcd1fdda2632cf  profiles/v8.3/profile.lock.json
0fb80ed42b0b53e91e6fd55af272c2f4a0c1a9f724c2d6263b6f74a8af543b8a  profiles/channels/state.json
b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03  assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb
```
