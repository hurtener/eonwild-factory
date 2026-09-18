# Canonical support-anchor provider: root round 1

Exact head: `7b584f21cff3197d8afcba9fbd109ee9f29e5026`, parent `b31bcf655d72883d98e899e70f86213d3cec9730`. Scope is the six-file optional provider, compiler/skin integration and focused tests. The closed SourceMotionQuery/axial/jaw source is not reopened.

Decision: **CHANGES REQUIRED — one P1 binding finding**. No recipe activates this implementation yet.

## P1: bind the provider to the consuming source and material contract

`CanonicalSupportAnchorProvider` retains only the gait-family hash, side/event information and material arrays. Its public constructor accepts those arrays without a source-context binding. `solve_with_skin_targets` checks only `isinstance` before copying their origins. It does not verify the provider belongs to the actual source/current scale, semantic roles, solver and locomotion contracts, performance/gaze/articulation inputs, coordinate frame or contact material indices/order of the request being solved.

The executable root probe builds a genuine provider with the sole/toe region declarations exchanged, then consumes it with the original contact profile. The two references retain equal counts (left 1564, right 1417) but different vertex ordering, with origin-array pointwise differences of 1.046226m/0.790528m. The solver accepts this provider and records its mismatched origins without a binding rejection. The probe uses zero refinement iterations to inspect API acceptance; it does not claim that this corrupted case passes final contact or candidate acceptance. A separately built provider also accepts a solver with twice the bound locomotion cadence and reports the same gait-family identity.

Preserve a complete, immutable source/contact/solve-context identity at construction and validate compatibility before consumption, including exact material order. Fail early for an incompatible solver cadence. Retain shared sustained-family event anchors across legitimate start/steady/stop requests; do not solve the issue by inferring a gait from rows or selecting a replacement material point. Cover wrong source/scale, roles, frame, contact ordering/profile, solver/performance/articulation and mutable-anchor payloads. The optional mode must not silently fall back to first-loaded anchors if its required provider is missing.

## Verification

Root inspected all six changed files and ran provider plus legacy phase-local payload regressions: **11 passed in 5.46s**. Existing legacy/default payload behavior is preserved by those checks. A preliminary probe attempted unsupported 12 Hz and rejected before exercising the finding; the corrected probe uses admitted 24 Hz.

Reproducer: `root-canonical-anchor-round1-probe.py`; result: `root-canonical-anchor-round1-probe.json`, SHA-256 `85fb2fcca8867816f3957b1382d74702557e159240d331135443b22597e39dce`.

This review does not establish emitted continuity, dynamics, scientific mass distribution, native quality or production acceptance. No thresholds, generated candidates or approved references were changed.
