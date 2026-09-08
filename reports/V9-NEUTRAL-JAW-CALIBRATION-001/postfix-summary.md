# Neutral jaw round-1 postfix — frozen `f26cb9e`

The consolidated round-1 postfix is frozen at `f26cb9e4af2ac04130352ab5ef2911d7bd9d31d1` in the isolated neutral-jaw worktree. Its round-1 parent is `b13efbdc48e174b2c7d9568fe61d086967cef5c6`; published base remains `26ec06837cd03d59bd03d6bf948ae6e7d8cf4212`. The worktree is clean. No recipe or full adult candidate was added.

A reusable frozen-source admission validator was isolated as commits `9a4c583770a935daa4ff36901e5ce5bdf4956a56` and `20b8bb2a0a5189da0d1231ca54bdbb68ab22d7c8`. It verifies the raw source SHA, current binary and document, complete active-root topology, and cached nodes, parents, names and rest TRS. The only admitted state difference is one common positive scene-root scale multiplier in `[0.25, 4]`. Detached cached-node state, cached pose changes, binary/document changes, nonuniform scale and out-of-range scale reject.

The jaw response now applies `gain * breathing_gape - neutral_close`: the authored neutral closure remains constant through start/stop gains while only breathing follows gain. Recursive semantic-role traversal rejects the head or lower jaw masquerading anywhere in spine, neck, tail, leg or nested role containers. Admission uses the shared frozen-source validator and reports both raw-source and admitted body height/gap plus the verified uniform scale.

The versioned behavior calibration was re-solved in one raw-source coordinate space. Frozen raw source height is `2.657391579010845 m`, authored closure is `50.03933635803102 deg`, and sampled gap is `0.003986087368516689 m` (`0.0015000000000001583` body heights). With the admitted uniform animal scale `0.8595555137374769`, height is `2.2841755838983118 m` and sampled gap is `0.0034262633758475047 m` (`0.0015000000000000163` body heights). These remain engineering calibration witnesses, not tooth contact or biological evidence.

Validation:

- 157 focused tests passed in 48.08 s: neutral jaw, frozen-source identity, airborne gait, performance, phase-local solve context, and adult bind catalog.
- 12 direct frozen-source identity tests passed in 1.02 s after the detached-node-cache closure.
- Ruff passed on all new/touched modules except the airborne module, whose pre-existing unrelated F401 remains outside this change; `git diff --check` passed.
- Frozen source asset remains exact SHA-256 `2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f`.
- Updated v7 performance profile SHA-256 is `b81d9c60dfe402e9e3f741591666d9517a8b7236992a5acb5f3cfc95890cf418`.
- Recalibration JSON SHA-256 is `b5d0727f359ed32b2525b4205ebe5cf746405be1306b39aa0f40694d50e2f743`; its script SHA-256 is `4aa34df7b9f18292cf6ea8e6c0e32c390e814d0320e61e287e176a43ae13ff54`.

This head closes the two P1s and one P2 in `root-neutral-jaw-round1-review.md` and the corroborating recursive semantic-role P1 in `neutral-jaw-round1-reviewer2-b13efbd.md`. Two independent round-2 reviews remain pending. The prior static diagnostic review does not constitute animated behavior, native, Unity, or production approval.
