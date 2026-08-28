# V8.3 technical dispatch final re-pin

## Verdict

- Exact commit: `2232daa0a15debe5e0a1080b31789fd8ca6fb19a`
- Diff base: `ba302d7cdb715a7c1161fb7d8cc8cede3e43f6d2`
- Scope: dispatch P1 from `technical-final-re-review.md` only
- P0: **0**
- P1: **0**
- P2: **0**
- Recommendation: **PASS for the exceptional dispatch-closure scope**

## Dispatch closure

V8.3 now declares the exact evaluator capability and evidence schema in its
profile:

```text
normative-evidence@1#eonwild.motion.v8_3_evaluation.v1
```

`contact_inheritance_facts` resolves dispatch from that profile declaration,
rejects duplicate/malformed/unsupported declarations, and requires a normative
declaration for every proof contract other than the explicit legacy
`protected-channel-byte-equivalence` contract
(`src/eonwild_motion/pipeline/validate.py:41-74`). The evaluator then validates
the document against the normative schema and requires its `schema` value to
match the profile declaration
(`src/eonwild_motion/pipeline/normative_evidence.py:152-167`). It no longer
infers evaluator selection from optional evidence keys.

Independent deletion tests against the exact V8.3 profile produced:

| Deleted top-level field | Result |
|---|---|
| `artifactSha256` | rejected: required normative schema property |
| `selectedScale` | rejected: required normative schema property |
| `metrics` | rejected: required normative schema property |
| `evidence` | rejected: required normative schema property |

Independent profile-declaration mutations produced:

| Declaration mutation | Result |
|---|---|
| normative declaration removed | rejected: declaration required |
| `normative-evidence@999#wrong.schema` | rejected: unsupported |
| `normative-evidence@1` | rejected: malformed |
| `normative-evidence@1#` | rejected: unsupported |
| `normative-evidence@1#wrong.schema` | rejected: schema mismatch |
| two supported declarations | rejected: multiple declarations |

A malformed V8.3 report therefore cannot reach the legacy selector path.
Conversely, explicit `profiles/v8.2/profile.json` validation still passes with
proof `protected-channel-byte-equivalence` and
`normativeEvaluation = None`, confirming intentional legacy compatibility.

The two committed focused corruption tests also passed independently:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest \
  tests.test_integration.VerticalSliceTests.test_normative_evidence_fails_closed_on_controlled_corruption \
  tests.test_integration.VerticalSliceTests.test_normative_evidence_rejects_cross_document_corruption -v

Ran 2 tests in 38.466s — OK
```

Authentic working validation passed and reported:

- status `PASS`;
- candidate SHA-256
  `b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`;
- sweep winner `0.5`;
- normative evaluation `PASS`;
- media binding `PASS`.

## Minimal diff and frozen identities

The functional dispatch diff is limited to the evaluator declaration,
dispatch/schema enforcement, and focused tests. The V8.3 profile changed only
its validator capability; deterministic re-locking changed only its profile
SHA/lock SHA and the corresponding working-channel hashes:

- V8.3 profile SHA:
  `d222e1159db92928a442c1fa0c048ac1c8c733a3dfc3e7a18731a9416cd96815`;
- V8.3 profile lock:
  `4b506eb9145ccdeb21bebbb58d8fd40aa3a0048c1625be927655c012f989abc9`;
- channel-state SHA:
  `0fb80ed42b0b53e91e6fd55af272c2f4a0c1a9f724c2d6263b6f74a8af543b8a`.

The stable object is data-identical to `ba302d7`; top-level generation remains
`1`; working iteration/revision/base remain `1`/`2`/`stable-0001`. No catalog,
motion, layer, artifact, media, or evidence payload changed in this dispatch
commit. Exact artifact identities remain:

- V8.3:
  `b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`;
- stable V8.2:
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.

`git diff --check ba302d7..2232daa` passed. The exact commit is a direct child
of `ba302d7` and has a valid SSH signature for
`117486687+hurtener@users.noreply.github.com`, fingerprint
`SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`; author and committer are
`Santiago Benvenuto <117486687+hurtener@users.noreply.github.com>`.

No implementation, profile, catalog, asset, evidence, or media file was changed
by this reviewer. Per instruction, this report is not committed.
