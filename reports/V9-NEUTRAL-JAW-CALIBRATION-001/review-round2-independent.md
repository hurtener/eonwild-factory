# Neutral jaw calibration round 2 — reviewer 2

Reviewed exact `f26cb9e4af2ac04130352ab5ef2911d7bd9d31d1` against round-1 freeze `b13efbdc48e174b2c7d9568fe61d086967cef5c6`. Scope was only the neutral-jaw postfix and shared frozen-source helper. The jaw worktree remained clean and unchanged.

## Result: CLEAN

The gain composition is now `gain * breathing_gape - neutral_close`, so neutral closure is retained at zero and partial transition gains while breathing alone scales. The direct composition test covers gain 0/.25/1. A separate actual start-transition source solve using the scaled adult source, adult grounded program and v7 performance returned gain `0.0` at the first frame and a jaw/rest angular distance of `50.039335650063755°`, matching receipt closure `50.03933635803102°` within float32 export precision.

`validate_frozen_source_with_uniform_scale` binds the raw SHA and binary; active scene roots/topology; normalized document; and detached cached nodes, parents, name mapping, and rest TRS. It admits only one common positive root-scale multiplier in `[.25,4]`. Independent probes rejected detached `nodes`, `parents`, and name-map mutations. The round-one P1 cached-node omission is closed by the `20b8bb2` helper delta.

Recursive semantic role traversal rejects head or lower-jaw aliases inside nested neck, spine, tail, leg and toe-chain containers. The source-space calibration uses raw height `2.657391579010845 m` and raw sampled gap `0.003986087368516689 m`, yielding `0.0015000000000001583 BH`; admitted uniform scale produces height `2.2841755838983118 m` and gap `0.0034262633758475047 m`, retaining the ratio. Receipt records raw/scaled heights, gaps and the admitted scale. These remain sampled engineering-clearance witnesses, not tooth contact, biological validation, visual approval, or Unity proof.

## Independent checks

- `uv run --frozen pytest -q tests/test_neutral_jaw_calibration.py tests/test_source_identity.py tests/test_phase_local_solved_pose.py`: **37 passed in 28.83s**.
- Ruff on shared identity and jaw source/tests: passed.
- `git diff --check b13efbd..f26cb9e`: passed.
- Profile SHA-256 reproduced as `b81d9c60dfe402e9e3f741591666d9517a8b7236992a5acb5f3cfc95890cf418`.

No P0, P1, or P2 finding. Native walking review, Unity parity, and production approval remain outside this source-only review.
