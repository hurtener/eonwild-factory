# Canonical support anchor provider narrow P1 closure — reviewer 2

- Reviewed head: `f847630b901d86b4aeb895fe50fd9523b13d79e6`
- Parent: `f36b1eeb9af059f006000106624b8ae3ea143c8f`
- Scope: only the two-file postfix that validates every consuming plan row against the canonical `SourceMotionQuery` source law and rejects caller-owned `target_offset_m` before skin refinement.
- Outcome: **CLEAN** — no remaining P0/P1 or concrete local P2 in this narrow diff.

## Review evidence

The implementation reuses the already admitted source, semantic roles, solver gait, locomotion gait, transition, coordinate frame, articulation profile, contact profile, and complete consuming plan. `SourceMotionQuery` then regenerates each supplied sustained or transition row at its declared time and requires exact structured agreement within its existing numeric contract. This closes the prior acceptance of mutated root and foot rows without binding the canonical anchor identity to a particular output grid. An explicit pre-refinement guard rejects `target_offset_m`, including a zero offset, so caller corrections cannot be normalized away by the shared query comparator.

Focused tests:

```text
PYTHONPATH=src:tests uv run --frozen --group test pytest -q \
  tests/test_canonical_support_anchors.py tests/test_source_motion_query.py \
  --basetemp out/provider-r2-p1-closure/pytest
20 passed in 45.41s
```

Additional exact-head adversarial probe:

- canonical sustained consumption: PASS
- canonical start consumption (1,034 rows): PASS
- canonical stop consumption (788 rows): PASS
- interior sustained root-forward corruption: REJECTED
- interior sustained right-foot forward corruption: REJECTED
- interior sustained left-foot contact corruption: REJECTED
- zero caller-owned target offset: REJECTED before refinement
- interior start and stop root-forward corruptions: REJECTED

Probe receipt: `out/provider-r2-p1-closure/adversarial.json`, SHA-256 `83320cd1fd3597accb59080a22b84500795917a3cb5d60ce4abed936b9ef1ebb`.

Static checks:

```text
git diff --check f36b1eeb9af059f006000106624b8ae3ea143c8f..f847630b901d86b4aeb895fe50fd9523b13d79e6
uv run --frozen --group test ruff check \
  src/eonwild_motion/solve/support_anchors.py \
  tests/test_canonical_support_anchors.py
All checks passed!
```

Reviewed file hashes:

- `src/eonwild_motion/solve/support_anchors.py`: `e66e906d59fae0f3a996abaf703fc603684b15c36b3a3a11f4bf2fb229f675a9`
- `tests/test_canonical_support_anchors.py`: `28d8b7bdd8c3ec823c23cd0a505c1926c9b0059c4949f75a731ef4a17d3d000f`

This review does not reopen the provider's two completed whole-stage rounds or make emitter, source-law continuity, gate, or approval claims.
