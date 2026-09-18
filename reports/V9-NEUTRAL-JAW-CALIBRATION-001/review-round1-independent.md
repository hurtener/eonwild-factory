# Neutral jaw calibration — reviewer 2, round 1

Reviewed only `b13efbdc48e174b2c7d9568fe61d086967cef5c6` against `26ec06837cd03d59bd03d6bf948ae6e7d8cf4212`. No source, recipe, asset, package, renderer, threshold, or approval state was changed.

## Focused evidence

- `uv run --frozen pytest -q tests/test_neutral_jaw_calibration.py`: **14 passed**.
- `uv run --frozen ruff check src/eonwild_motion/planning/jaw_response.py src/eonwild_motion/solve/jaw_response.py src/eonwild_motion/solve/performance.py tests/test_neutral_jaw_calibration.py`: **passed**.
- `git diff --check`: passed; worktree remained at the exact frozen head.
- Profile SHA-256: `48441581b52ee1795ff82118820c29f52c3f903993fac684f6ac148377c76a87`; frozen source SHA-256 matches `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`.

The local-axis construction and ordering place the neutral/breathing rotation before head and gaze composition, so hierarchy carries the hinge. The transformed-source test and default-off/zero paths are useful evidence. The following findings prevent acceptance.

## P1 — neutral closure incorrectly fades with locomotion gain

**Location:** `src/eonwild_motion/solve/jaw_response.py:268`.

The implementation evaluates `gain * (breathing_gape_degrees - neutral_close_degrees)`. Thus the authored neutral closure is zero at gain zero and only half applied at gain `.5`; a start or stop returns toward the known open modeling pose as locomotion fades. Neutral posture must remain constant; only breathing should be gain-driven.

Compose `gain * breathing_gape_degrees - neutral_close_degrees` exactly once in the admitted jaw-local frame. Preserve the existing legacy breathing path when neutral calibration is omitted or explicitly zero. Add actual start/stop endpoint and partial-gain checks.

## P1 — raw-byte hash does not bind mutable current source state

**Location:** `src/eonwild_motion/solve/jaw_response.py:229-248`.

The raw source hash is verified, yet current cached `rest_*`, document/topology, and skin data are subsequently consumed with only a positive-gap condition. I changed only `source.rest_rotation[jaw]` by +5 degrees, leaving `source.raw` unchanged. The raw hash still matched the calibration and admission succeeded with current gap `0.04464113830666783 m`, rather than the calibrated source witness `0.003426263375848837 m`.

Admit only the intended current-state variation: the established uniform scene-root animal scale. Bind current topology, document/binary-derived state, local TRS, skin/accessor identity and jaw relation to the frozen source plus that allowed scale. Arbitrary local jaw, skin, hierarchy, accessor, or cached-state edits must require a new calibration. Test both stale cached state and valid uniform scaling.

## P1 — list-valued semantic aliases bypass the lower-jaw admission check

**Location:** `src/eonwild_motion/solve/jaw_response.py:48-59`.

`_semantic_jaw` rejects only duplicate *scalar* roles. A copy of the valid role map with `roles["neck"] = [roles["jaw_lower"], *roles["neck"]]` is accepted by `admit_neutral_jaw` and returns jaw node `24`; the same occurs for `tail` and `spine`. The requested contract explicitly requires strict malformed/alias calibration rejection. In profiles that use those semantic lists, such an alias can also make later body-response or gaze passes act on the jaw.

Recursively collect every semantic node name from role containers and reject head or jaw occurrence outside their dedicated roles; retain the valid head-to-jaw ancestry check. Add neck/spine/tail alias controls.

## P2 — declared normalized clearance mixes source spaces

**Location:** `src/eonwild_motion/planning/jaw_response.py:64-68`, calibration fields in `catalog/performance/heavy-biped.tarbosaurus-adult-walk.v7.json`.

The profile’s `measured_body_height_m=2.2841755838983118` is the scaled animal height while `measured_minimum_gap_m=0.003426263375848837 m` is the raw-source gap. Raw semantic height is `2.657391579010845 m`, so raw normalized clearance is `0.0012893332706067305`, not the declared `.0015`; uniform scaling retains `.001289333...`.

Measure and bind height and gap in the same source space; verify the ratio after permitted uniform scale. Recalibrate closure if `.0015` is the intended authored clearance, or record the changed ratio accurately. Refresh the versioned evidence/profile, without changing frozen source bytes.
