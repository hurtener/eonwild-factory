# Allosaurus pedal physical-alias narrow closure

- Head: `f0a08c8c481bb27e5f00080d5b46dba39e3a20f3`
- Parent: `db0adb6518898ae651eb999f1003590f97ee3b20`
- Tree: `bd96e277560f8490d8ac38936e0702d8ff17db5a`
- Scope: exceptional diff-only re-review of the remaining physical-accessor alias P1
- Verdict: **PASS** (`P0=0`, `P1=0`, local actionable `P2=0`)

The fix keys physical skin rows by byte layout and accessor schema rather than accessor index. Duplicate descriptors of the same physical POSITION/JOINTS/WEIGHTS rows are therefore processed once. A descriptor whose rows overlap an already-owned layout without identifying the same complete bundle fails closed. The comparison includes start, count, stride, item byte size, component type, accessor type, and normalized state.

The regression duplicates each accessor descriptor while retaining the same underlying byte regions and proves unchanged weights. Its overlap regression shifts a weights buffer view into a partial physical overlap and requires rejection. The retained root reproducer reports `affected_vertices=0` and `maximum_weight_difference=0.0`; raw source regeneration remains byte-identical at SHA-256 `3613b67c9513c4ed5b88665c7606e0c15791bb922b01a72e7223aa112546ec89`.

Independent focused execution:

```text
PYTHONPATH=src .venv/bin/python -m pytest tests/test_rig_preparation.py -q --tb=short
25 passed in 19.93s
```

This supersedes the retracted reviewer receipt at `reviewer2-db0adb6`. It closes only the original duplicate-physical-layout defect. The separate Allosaurus motion preflight remains mechanically blocked; this review makes no gait, pose, contact, or motion-acceptance claim.
