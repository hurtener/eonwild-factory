# Exact emitted tangent validator — Sol adversarial review

## Scope and pins

- Base: `3726cb7fe4e620745f83d1e5ea7499561a1191ae`
- Round-one reviewed head: `6370df15d26c991b9c58dbf0a62c8699b31f16fc`
- Narrow closure head: `52e826ccd7e05dd2e82c37e889af8cf0a977c7a0`
- Worktree at closure: clean.
- Reviewed only the exact emitted tangent helper, handoff/cyclic consumers, and their focused tests. No source edits were made by this reviewer.

## Verdict

Round one found three P1 fail-open contract defects and two P2 reporting defects. The narrow fix at `52e826c` closes all five. **Narrow post-fix result: CLEAN (P0=0, P1=0, P2=0).**

## Round-one findings against `6370df1`

### P1 — cyclic acceptance checked only the last animation

`emitted_cyclic_continuity` accumulated the historical diagnostic over every animation, then passed the loop variable `animation["name"]` to the exact evaluator after the loop. A two-animation GLB therefore admitted a bad first clip when the last clip was smooth.

Concrete reproduction: the first clip had a `t^2` translation seam and a `45*t*(1-t)` rotation seam; the second clip had constant translation and rotation. `6370df1` returned `PASS`, exact linear/angular maxima `0.0`, while its own retained quadratic diagnostics reported `2.0 m/s` and `90.0000388 degrees/s`.

### P1 — nonconstant animated scale was outside cyclic acceptance

The exact FK helper differentiated scale, but `local_cyclic_tangents` admitted scale channels without checking them and reported only local translation/angular mismatch. A clip with flat translation/rotation and a final scale key changing from `[1,1,1]` to `[2,1,1]` returned `PASS`. There is no governed cyclic scale limit, so silently accepting this channel made the claimed final serialized TRS scope incomplete.

### P1 — handoff exact evidence was optional and could be undersized

`compare_boundaries` silently substituted sampled adjacent tangents whenever both `exact` dictionaries were absent. When exact dictionaries were present, it checked before/after array agreement but did not bind node or skin row counts to sampled position/skin correspondence, and did not require unique string labels. A two-node/two-skin boundary with one arbitrary exact row returned `PASS`. This allowed callers of the acceptance function to omit or forge the new FK/LBS evidence while retaining an exact-looking result.

### P2 — exact cyclic peak witnesses were not independently reproducible

The peak witness stored only the scalar mismatch in `incoming`; it omitted the incoming/outgoing vectors, their adjacent key times, and units.

### P2 — retained handoff quadratic diagnostics lost witness identity

The old quadratic maxima remained available, but their argmax indices were discarded, so a diagnostic regression could not be traced to the sampled node/material row.

## Narrow closure evidence at `52e826c`

- Cyclic validation now requires exactly one named emitted clip before evaluation (`quality.py:238-241`). The original two-clip fail-open now raises `ContractError: cyclic witness requires exactly one named emitted clip`.
- `local_cyclic_tangents` rejects every nonconstant animated scale channel (`emitted_tangent.py:251-256`) while admitting a constant animated scale channel. The original changing-scale input now raises `ContractError: cyclic tangent witness does not govern nonconstant animated scale channels`; the constant-scale control returns `PASS`.
- Exact handoff evidence is mandatory unless an explicit, boolean `test_only_allow_sampled_tangents=True` is supplied (`handoff.py:107-127`). The ordinary missing-evidence reproduction now raises `handoff requires exact emitted tangent evidence`.
- Exact names/labels must be unique strings, vector counts must match labels, and exact node/skin counts must match the sampled boundary (`handoff.py:129-146`). The original undersized witness now raises `handoff exact tangent shape differs`; duplicate-label coverage is tested as well.
- The sampled arrays themselves do not carry node/material names, so `compare_boundaries` cannot cross-check label text against a second sampled identity list. This does not leave the P1 open: production `_boundary` creates sampled node rows and exact node rows from the same `descendants` enumeration, creates sampled skin rows and exact skin rows from the same side/sole/toe/vertex selection order, and `verify_handoff` separately compares the named topology across packages. At the lower-level helper boundary, equal unique exact labels plus exact/sample count equality preserve before/after row correspondence; an arbitrary relabel cannot change any maximum or acceptance result. Treating every direct Python dictionary as hostile provenance would require redesigning the sampled payload to carry identities, rather than another validation check in this patch.
- Cyclic witnesses now include incoming/outgoing vectors, adjacent key times, and units (`emitted_tangent.py:261-269`). Quadratic handoff diagnostics now retain argmax indices (`handoff.py:97-106,164-165`).
- Cyclic scope remains explicitly local-channel translation/angular velocity. It does not claim full-world or skinned loop continuity (`emitted_tangent.py:251-252,270-272`). Handoff remains the FK/LBS consumer.

## Independent numerical cross-check

Against the retained packages under `out/continuation-final-9d6974d-pairs`, the production exact helper was evaluated for walk, reverse-walk, run, and sprint, at start and stop, in root-motion and in-place modes (16 comparisons). Its maxima matched the earlier independent SciPy Rotation/product-rule FK/LBS probe to at most:

- `3.4e-12 degrees/s` for local angular mismatch,
- `1.2e-13 m/s` for world velocity mismatch,
- `1.4e-13 m/s` for skinned material velocity mismatch.

That independent probe found zero scale animation channels in all 24 retained GLBs, so emitted scale derivatives there are exactly zero. The helper's animated-scale product rule is separately exercised by a nonuniform-clock FK/LBS test; cyclic validation now rejects nonconstant animated scale because no scale threshold is governed.

Motor velocity uses emitted float32 key times and adjacent serialized plan travel. Quaternion sign-equivalent encodings and the parent-world rotation composition are covered by focused tests and agree with the independent SciPy-frame probe. Existing strict position, rotation, linear, skin, and angular limits are unchanged. The historical quadratic estimates remain diagnostics only.

## Verification

- `git diff --check 6370df1..52e826c`: PASS
- `uv run pytest -q tests/test_exact_emitted_tangent.py tests/test_emitted_handoff.py tests/test_motion_contact_adversarial.py`: **70 passed in 2.36 s**
- Direct post-fix adversarial probe: missing exact evidence rejects; undersized exact evidence rejects; nonconstant scale rejects; constant animated scale passes; multiple clips reject.
