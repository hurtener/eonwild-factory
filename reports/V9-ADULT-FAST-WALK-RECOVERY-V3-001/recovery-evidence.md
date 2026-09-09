# Fast-walk world-metatarsus recovery C3

- Source commit: `f53782e060d38554879cbd25a65d0d62c72d44f4`
- Frozen package: `worktrees/eonwild-fast-walk-recovery/out/tarbosaurus-adult-fast-walk-recovery-v3-f53782e`
- Technical result: PASS; visual review PENDING; Unity parity NOT_RUN.

## Cause evidence

The prior `.80` release profile failed on its return branch at 720.7416 degrees/s. Extending release to `.90` reduced that branch, but moved the maximum to the independent onset branch: 666.1362 degrees/s at left `1.091666698 -> 1.100000024` seconds, with solved foot pitch `35.023162 -> 40.574292` degrees and world-recovery gain `.3008156 -> .3577705`. During that same interval the baseline metatarsus direction changed `22.240988 -> 17.234733` degrees from down.

The 1.6-second cycle has a .608-second swing. The historical full-branch quintic has maximum phase slope `1.875/d`: `7.3426/s` over the .42 onset and `6.4248/s` over the `.42 -> .90` return. A release/peak shift cannot lengthen both under the fixed .90 release; it transfers the witness instead of fixing it.

## C3 correction

The profile keeps the `.42` peak, `.90` release, `-20` degree world target, cadence, stride, duty, clearance, contact schedule, and guardrails. It alone opts into `rate_limited_c2`. On each normalized branch, its `.25` quintic velocity ramp and constant-slope middle give values `0, 1/6, 5/6, 1`, velocities `0, 4/3, 4/3, 0`, and zero acceleration at the endpoints and internal joins. Maximum phase slope is `1/(.75*d)`, versus `1.875/d` historically (32/45 of the historical peak). Omission preserves the historical serialized plan.

## Frozen emitted evidence

- Solved foot pitch: `575.5990272512696` degrees/s, limit `600`.
- Witness: left `1.0916666984558105 -> 1.100000023841858` seconds, `37.28616952896118 -> 42.082823514938354` degrees.
- Global serialized rotation: `972.7097813640545` degrees/s, limit `1200`.
- Extension/articulation violation: `0` / `0`.
- Final skinned-contact gate: PASS.
- `in_place.glb`: `0215d73f22f45e1897afa8d6336caea8bd2072a57679e63e05ce735fe32717cf`.
- `root_motion.glb`: `4416c91ea3629f638949139c5c7a9c1d1e0ed062b518822d024dbd313670e2a7`.
- `validation.json`: `6c68095a2056a15b074d1580b33bc8132f583b3d1e48d73afbbe70318695dd0c`.

Focused regression gate: `15 passed` (`tests/test_world_metatarsus_recovery.py`, `tests/test_grounded_recovery_direction.py`, and `tests/test_adult_fast_walk_recovery_catalog.py`). Full cross-behavior gates and native visual review are root-owned.
