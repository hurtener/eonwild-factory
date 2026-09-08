# SourceMotionQuery + neutral-jaw compatibility integration — independent review 2

Date: 2026-09-08

## Reviewed boundary

- Exact head: `b31bcf655d72883d98e899e70f86213d3cec9730`
- Base closed axial+jaw head: `2c433df17fd7f8241565692b428c3e8a0fb82fe4`
- Previously closed SourceMotionQuery head used only as a comparison authority: `1deac52c8f31012b18cbb7c08a5c4ce718dfd651`
- Worktree: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-source-query-jaw-integration`
- Review scope: the new compatibility seam only: deep detached GLB cloning with frozen raw identity, the extracted airborne solve-context builder's neutral-jaw fields/admission/receipt path, the one-admission provisional/final context split, and the production scaled-adult union regressions. The closed SourceMotionQuery stage was not re-audited.

## Result

**CLEAN: no P0, P1, or reachable local P2 finding in the reviewed compatibility seam.** No reviewed source or test file was edited.

The head's final commit changes three files relative to its parent: `airborne_gait.py` (+13/-6), `source_motion_query.py` (+7/-2), and `test_source_motion_query.py` (+119/-2). The query clone now preserves the frozen `Glb.raw` identity while deeply detaching the current document, topology maps/lists, and rest caches. Immutable byte strings retain equal contents. The admitted scaled source revalidates against the frozen original and one uniform scale.

The emitting solver validates the plan override, removes only `performance` from its geometry-only provisional context, then builds the final context from the complete validated plan. Instrumentation at the exact head observed one neutral-jaw admission during SourceMotionQuery construction and one during a complete `solve_airborne_gait` invocation, rather than two in either operation. The emitted receipt agreed with the final context on source SHA, jaw node, local hinge axis, close angle, and admitted scale.

## Adversarial evidence

A production adult-v7 query was built from source `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f` with admitted uniform scale `0.8595555137374769`. Exact imports resolved to this worktree's `src/eonwild_motion/solve/source_motion_query.py` and `src/eonwild_motion/solve/airborne_gait.py` under `PYTHONPATH=src:tests`.

The detached clone retained raw SHA-256 `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f` and current re-encoded SHA-256 `5c3e12218bb7d3c24eb0649e5b8733e2f2a1ae49bb1a71ba880fb575c3e1bcfc`. Its document/nodes, parents, name map, and rest translation/rotation/scale containers were distinct from the caller. After independently corrupting every corresponding caller-owned family and replacing its binary bytes, the clone snapshots remained exact and the retained phase-local pose remained equal.

The full adult-v7 solve emitted 45,491,736-byte root-motion and 45,491,732-byte in-place GLBs. Its jaw receipt retained source SHA `2cdd901…`, jaw node 24, and close angle `50.03933635803102 degrees`. The stale-current-document corruption regression rejects rather than silently changing source identity.

## Focused checks

All commands explicitly used the external task environment and `PYTHONPATH=src`.

- SourceQuery/source identity/phase-local/neutral-jaw set: **48 passed in 53.82 s**.
- Explicit production payload and jaw composition selections: **5 passed in 26.00 s**. This is a targeted subset and overlaps the broader set; counts are not aggregated.
- Airborne breathing semantic-jaw selection: **1 passed, 29 deselected in 1.03 s**.
- Scoped Ruff over both integration modules and focused tests: **All checks passed**.
- Author's retained log `out/source-query-jaw-integration/focused-final.log` records **53 passed in 33.75 s**, SHA-256 `140364fe48b72de29b98d7b506c0e30e8c50f6391b96fdd4adfa1eb95a811643`. Its Ruff log SHA-256 is `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`.

The tracked worktree was clean after review and `git diff --check 2c433df..b31bcf6` passed.

## Exact file hashes

- `src/eonwild_motion/solve/airborne_gait.py`: `2a562d3ab72435ed1b467e9f42c4b6023149148fe1702bc60e52994f7a730773`
- `src/eonwild_motion/solve/source_motion_query.py`: `51a1f2e84e2231a1853e866f7813ec84f5550a453c97c3ef86119fe45df62279`
- `src/eonwild_motion/factory/source_identity.py`: `1a5a3f94489212080735e8838cb718cdf3906d3c5ad2601a06e4e366fb3b3728`
- `src/eonwild_motion/solve/jaw_response.py`: `cf992494f56a5e969a0584dff3ba5c79f33c5b14e22bf8c47b9c15f55e235835`
- `tests/test_source_motion_query.py`: `15d5eb27ddcb477c21a19768167d81a598c7eda1742de971163597273b565542`
- `catalog/rigs/heavy-biped.v9.json`: `c3de770bf7dcc68219a28fb9851e9b75f3d3eebe2c2c0c7deb0078850100fd7e`
- `catalog/programs/heavy-biped.tarbosaurus-adult-walk.v4.json`: `271ccb833a8913d3dc6bd8281e798e54b9c7bebad2080136245cb7b5e5afa725`
- `catalog/performance/heavy-biped.tarbosaurus-adult-walk.v7.json`: `b81d9c60dfe402e9e3f741591666d9517a8b7236992a5acb5f3cfc95890cf418`
- `catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v2.json`: `53ffeba22e24a87504d3dcc310bedacf6db94d60a25ffe56ad028b03f41e849d`
- Adult source GLB: `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`

This is a focused compatibility review. It does not alter or extend the closed diagnostic's derivative authority, emitter status, motion thresholds, or production/visual/Unity claims.
