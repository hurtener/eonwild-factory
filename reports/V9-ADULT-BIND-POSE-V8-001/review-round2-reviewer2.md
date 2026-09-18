# Bind-pose admission reviewer 2 — round 2 and narrow accessor closure

Status: **P1 OPEN at `2d6b5e6506c14231f2a87b593bd8897ae0143519`**

Scope was limited to the bind-pose recovery changes from
`16aab6232698c6f641c34624c0ea246c67f1684e` through
`1b5a13e9c703a67470288901291aff65aa9faa4a`, followed by the narrow accessor
fix at `2d6b5e6506c14231f2a87b593bd8897ae0143519`. No source, input, package,
threshold, or recipe was modified during review.

## Finding

### P1 — recovery still admits four invalid embedded-buffer/accessor layouts

`_accessor_index` now proves the accessor span against the buffer view and
declared buffer, closing the originally reported short-view/short-buffer cases.
Four schema-invalid layouts still preserve the decoded values, pass the full
59,169-vertex reconstruction witness at
`1.1353242509093592e-06 m`, and are emitted unchanged:

1. A used buffer view with the required `buffer` member removed is treated as
   buffer zero through a default.
2. An inverse-bind view shifted back one byte and enlarged one byte, combined
   with accessor `byteOffset=1`, preserves the absolute data start but violates
   the individual component-alignment requirements.
3. Four extra BIN bytes beyond the declared buffer length are accepted, beyond
   the GLB allowance of at most three padding bytes.
4. All `JOINTS_0` values repacked losslessly at `byteStride=5` are accepted,
   although vertex stride must be a multiple of four.

This is the same local authority boundary as the first span failure. A bounded
fix is to require an explicit exact integer `bufferView.buffer == 0`, validate
the accessor offset and buffer-view/absolute offsets under the applicable
alignment rules, require an explicit vertex stride to be a multiple of four,
and require `0 <= len(binary) - declaredByteLength <= 3`.

Exact reproduction:

- `bind-pose-accessor-closure-2d6b5e6.json`
  SHA-256 `18e526fb1ec2f4274def08d250f68c06f662ba5ed4a56270f6a4ec3229a47097`
- Probe source `bind-pose-accessor-closure-2d6b5e6.py`

## Closed round-1 findings

- Boolean and fractional skin joints and a negative inverse-bind accessor now
  raise `ContractError`.
- NaN and positive/negative infinite POSITION values now raise
  `ContractError`; the reconstruction maximum cannot fail open.
- The original short inverse-bind view, short POSITION view, short declared
  buffer, Boolean declared buffer, and fractional declared buffer all raise
  `ContractError` at `2d6b5e6`.
- A rotated and translated non-skin helper inserted between recovered joints,
  with the skinned mesh reparented beneath that helper, is accepted while
  preserving the source binary. Reopened mesh-world element error is
  `4.148690181116077e-07`, joint-world error
  `9.436075576324532e-07`, and skin error
  `1.2727535122402942e-06 m`, all inside the unchanged limits.

Supporting receipts:

- `bind-pose-postfix-round2-probe.json`
  SHA-256 `357d8bf5f4bbbd1f9a7d6b69afd6c4d1e2a009a7776e9bedaa2e00a10184ab32`
- `bind-pose-postfix-hierarchy-probe.json`
  SHA-256 `acdfe8c8c44817dd7d99531d7114a93fca959a2230e6c7cd6b1c6408fc872b76`

## Verification

- `30 passed in 3.89s`: bind recovery, adult bind catalog, and public
  admission tests, with temporary data on the external SSD.
- Ruff on the two changed source/test files: pass.
- `git diff --check 16aab62..2d6b5e6`: pass.
- Recovered source SHA-256 remains
  `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`.
- Admission evidence SHA-256 remains
  `3f50f1de1021c08229e0b611d692779208aaaddf4eeebdbc2c76382bc3154007`.
- Valid recovery output remains byte-identical at
  `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`.

The worktree contained host/author evidence files as untracked files during the
final check; tracked source and tests matched the frozen commit. This review
does not assess visual motion, Unity parity, biological validity, or the
already blocked exact-continuity status.
