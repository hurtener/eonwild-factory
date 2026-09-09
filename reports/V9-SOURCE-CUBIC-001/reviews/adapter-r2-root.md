# Task-owned Blender playback: root round two

Reviewed exact `f5207ca3a83718f21f0c8fb1bd25d891be6a4a8f` against `4823fa8cc3813fa07a06e670f7b344e8321908ec`. CHANGES REQUIRED: one remaining reachable legacy compatibility P1; all original round-one findings closed.

Render overwrite is closed. Root reran the unchanged source-bound Cycles reproduction in a new directory. All 18 sampled source times and all 59,169 vertices per adult mode pass. Post-render maximum same-index errors are 0.002349652 mm in-place and 0.002442129 mm root-motion; overall sampled maxima are 0.004398812 and 0.004128426 mm. The exact adapter detaches imported approximate action bindings while retaining datablocks for timing; no post-render reapply hides a failed render. Old failed evidence remains intact.

The showcase now omits unsupported optional FBX only for cubic, records the unsupported transport status, and preserves requested LINEAR FBX. The legacy direct Blender script import bootstrap is fixed; root reproduced --help success with PYTHONPATH removed. Root focused checks passed 53 tests plus 10 subtests in 1.15 s.

Remaining P1: canonical legacy LINEAR rendering now rejects the approved immutable V8.2 asset (SHA a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5), which has two named LINEAR clips. The new reject_stock_cubic_playback detector calls a helper requiring exactly one animation, so it blocks this previously supported canonical render path before Blender import. Restrict single-animation admission to the actual exact cubic adapter; detection and genuine LINEAR stock playback must preserve this multi-clip case. Add a bound legacy compatibility regression. This concrete P1 gets one narrow diff-only closure after round two, not a third full audit.

Native pose reproduction is established only at the checked times and render evaluation. Body-weight visual acceptance, biological/physical certification, Unity, and FBX cubic support remain open or explicitly unsupported.

- `native-result.json`: SHA-256 `20ef785a4af2e5e5a49731b853895dbaf4d8025b76bd07508b9052e2b424d474`.
- `verify_native.py`: SHA-256 `2505e5bbc2dcc8631f3b6e01c28074995d86e63e977c095f4256acf00fdac05c`.
- `request.json`: SHA-256 `7601cfd92678c0c3c25f0079f71a96cf599e00568b6dd6719e61eb6ba509b637`.
- `pytest.log`: SHA-256 `9afad341ae90bf85c9a9c61dd5c807ee83eed60044d4eb51580074c76dbc46e6`.
- `junit.xml`: SHA-256 `a6940bb87557e2eb18a16d64a780c5453d45fe45429bbc8237482c77e3da8757`.
- `legacy-cli.log`: SHA-256 `c6dd102a0bf708dfaf77a6062d82594d29e14df9d6cd21db3aab3831235d19e1`.
- `legacy-multiclip-probe.json`: SHA-256 `a4cd2710e4022048aea270f0b9bea8380ea02be24e097dc8eaab4ffefc2372c6`.
