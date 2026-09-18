# Adult axial clock — reviewer 2, round 1

Reviewed only `483e006b1ddd20617b75e32b2e660b31e5ed0853` against parent `26ec06837cd03d59bd03d6bf948ae6e7d8cf4212` in `src/eonwild_motion/solve/performance.py` and `tests/test_motion_performance.py`. This was code review only; no recipe, asset, package, renderer, threshold, or approval status was changed.

## Focused evidence

- `uv run --frozen pytest -q tests/test_phase_local_solved_pose.py tests/test_motion_performance.py`: **105 passed**.
- `uv run --frozen ruff check src/eonwild_motion/solve/performance.py`: **passed**.
- Exact default-off payload pins passed for a renamed/frame-transformed fixture and the actual heavy-biped fixture.
- A shifted `handoff_phase_fraction=.125` start and stop each ended at the same `locomotion_time_s=.3075`, `performance_gain=1`, and axial clock value as the matching steady source clock.

The signed carrier uses semantic hip positions projected on the declared lateral frame; its grounded-source double-support admission does not inspect finite plan rows. I found no P0/P1 issue in leading-side sign, canonical steady clock construction, gain, start/stop phase carry-over, centered-tail order, malformed gait/frame rejection, or omitted-profile serialization.

## P2 — carrier does not bind the semantic hips to the yawed pelvis

**Location:** `src/eonwild_motion/solve/performance.py:280-308`, followed by the pelvis mutation at `:595-603`.

The helper admits bilateral hip positions but does not establish that either hip descends from the semantic pelvis whose world yaw carries the advertised leading hemipelvis. I rebuilt the renamed upper-body test fixture with both hips reparented from the pelvis to root while preserving their world rest positions. At the first double-support event the exact helper still returned `(-1.0, -pi/2, 1.0)`, yet after `apply_performance` both hips had `forward_shift_m=0.0`.

Require two distinct semantic hip nodes to be descendants of the semantic pelvis before enabling this option. Intervening structural helpers can remain valid. Add the reparented negative control and a valid transformed/helper hierarchy control.

## P2 — omitted axial option reassociates legacy tail arithmetic

**Location:** `src/eonwild_motion/solve/performance.py:651-655`.

When `axial_clock is None`, historical `-gain * amplitude * weight * sin(angle)` is now evaluated as `-amplitude * weight * (gain * sin(angle))`. These are mathematically equal but not necessarily binary64-identical. A deterministic scalar witness found: gain `0.1087256783870183`, amplitude `9.994991664328396`, weight `0.6567248622905973`, angle `4.8046281311806345`; old result `0.710637126127495`, new result `0.7106371261274951`.

Retain the original expression verbatim in the `axial_clock is None` branch and isolate the new formulation to opt-in axial behavior. Add a partial-gain omitted-option rotation-array equality regression. This is a compatibility P2; the existing float32 payload pins passed here and no emitted artifact difference was demonstrated.
