# Acquired-reference seam reviewer 2 — R1 and descriptor-authority closure

## Scope and identity

This bounded independent review covers the acquired-reference configuration,
compiler, package-replay, and provenance stage from base
`bf2979d` through review head
`efef02fe2638eb6b534e5cb2af7e3ae74a19b014`, followed only by the narrow
descriptor-authority correction at exact final head
`f51431a61ce6b42b1bb64ab97af65437780f6c2e`, tree
`f93e8573612e72c8cd5d113361d87e9f2851ec3f`.

The exact final source was tested from the immutable archive
`ARC/tmp/reviewer2-acquired-reference-f51431a-exact`. The registered author
worktree was not used as source authority after it resumed moving.

## Verdict

- **P0: 0**
- **P1: 0 at final head**
- **P2: 1 local malformed-input validation inconsistency**

The R1 head admitted one concrete P1: descriptor bytes could be captured from
document A while a second parse selected source/capsule B, and package-local
construction did not require payload digests to match its descriptor snapshot.
The original exact-`5828625` witness admitted both the interleaved resolution
and an A-descriptor/B-payload package.

The narrow final change parses only the captured descriptor bytes and enforces
source/capsule digests in frozen `AcquiredReferenceInputs.__post_init__`.
The independent closure replaces the live descriptor with B immediately after
decoding captured A: resolution remains bound to A. Both package-local and
direct-constructor A/B substitutions now fail with `ContractError`. This closes
the P1 without changing the adapter, motion law, or emitted assets.

The reviewed stage also keeps raw licensed source and the derived motion
capsule outside tracked Git paths; only the admitted prepared geometry and
descriptor are tracked. Focused tests cover direct-recipe rejection, transition
rejection, ordinary baseline clearance-policy packaging, detached payloads,
package replay from the original pre-emission source plan, and retention of
baseline-owned policy provenance for ordinary non-reference intents.

## Local P2 follow-up

`validate_clearance_policy` checks that the body-height fraction is positive
but does not check finiteness. Python JSON decodes `1e999` as positive infinity,
so the factory-level validator admits that malformed numeric value. The
authored-material adapter independently rejects it when consumed, and this
review found no emitted-output corruption. Add the same finite numeric check at
the factory validation boundary in a later local patch; this does not reopen
the acquired-reference stage.

## Independent execution

From the exact final archive with the primary shared Python environment and
`PYTHONPATH=<archive>/src`:

```text
pytest -q tests/test_acquired_reference.py tests/test_authored_material_contact.py tests/test_motion_set.py tests/test_motion_set_v2.py
61 passed in 18.18s
```

The author's final focused result is separately reported as 92 passing tests in
20.92 seconds with Ruff clean; it is not relabelled as independent execution.

## Evidence hashes

- Original R1 split-authority probe: `descriptor-snapshot-repro.py`
  `bc8db83a47ae37ac5b533ab7fc90c787a7d65fe9efe2a93428a69964495364c7`;
  result/log `4e355020df4efb0ae61c223acb5898eb6d77eb6230f723827d30b0b85ce47af5`.
- Final closure driver:
  `75152144df82fcfd6b34a5a544ccddc9367485493b5c93d7a39c5753a695a838`.
- Final closure result:
  `7aed5e41194a866a11777a6c2a2ef201d0f35823e4328d471112ca7fed66f2b2`.
- Non-finite local-P2 driver:
  `446e55ee889a3cf3e05be9694f1ebba1253cb5256165d49b44046dc831477138`.
- Non-finite local-P2 result:
  `6d2902fb1a3221b44dd8701d5f9f0023141f9a445cbcfd24c030d0d101cb145f`.
- Independent focused log:
  `137e769181edd783b37b7f5828c0c091e43cb31b372cb47651d622da2bcf2be1`.

No export, native render, visual approval, Unity acceptance, primary edit, push,
or merge is claimed by this review.
