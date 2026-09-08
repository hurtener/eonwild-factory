# Shared animal motion set: root review round 1

Complete implementation head: `38f14dd4142c161f2838d80210ee3a83be836a91`.
Tree: `3d0a3bb3aa7f7552b7667f877ee0f4a1e076c8e0`.
Diff base: published `945b189340f9d461373a1309bd06a7a7c3bcea8d`.
Scope: all 20 changed files, with the extracted response helper and its narrow solver-ownership correction also inspected at their frozen component heads before integration. This is the first complete implementation review, not release approval.

## P1: expected gait response is derived from unbound generated plan data

`src/eonwild_motion/factory/compiler.py:840` loads the expected grounded gait from `plan.parameters`. The new package saves set, baseline, intent, style and neutral-pose bytes, but not its locked program profile or transition's steady-gait profile. Consequently verification cannot compare these plan parameters with the immutable intent's actual gait.

The independent negative witness retains the real adult walk set, baseline, intent and exact `program_profile` binding (`271ccb833a8913d3dc6bd8281e798e54b9c7bebad2080136245cb7b5e5afa725`). The provenance checker accepts both the bound 1.23-second gait with coefficient `0.14519967609352594` and a substituted 0.8-second gait with coefficient `0.061423618679262736` when the plan and derived receipt are updated consistently. The test invokes the production provenance-checking function, without a new GLB compile; it does not claim that a complete mechanically revalidated substituted package was generated.

Retain and hash-check the exact program profile and, for transitions, its separate steady-gait profile. Derive expected gait response from these snapshots and compare the generated plan's authoritative gait parameters. Reject missing or rehashed substituted snapshots and contradictory generated gait data. Verification must still work after the original repository configuration is unavailable. This directly enforces the user's request that movement intent and the shared baseline remain authoritative.

## P2: a valid-looking movement name escapes the requested output directory

`src/eonwild_motion/factory/motion_set.py:70` only requires a nonempty name. `compiler.py:726` then appends it directly to the output path. The public selection API accepts `../escaped` and dispatches the child compilation to a sibling of the requested output folder. The reproducer intercepts compilation before geometry solving and asset writes, recording the actual escaped destination. The existing per-package overwrite guard does not confine a new destination.

This is a realistic, local, low-risk fix: require a portable single path component and validate all selected destinations before creating output directories. Cover parent traversal, absolute paths, separator-containing names and valid ordinary names.

## Checked boundaries

The baseline owns source/rig/animal/contact/articulation/frame, separate neutral calibration and shared style; intents reject these fields. Shared style rejects neutral calibration and solver flags. The response helper has no species or motion-name branch, preserves V10 reference parameters, and uses steady-gait cadence/stride/excursion. The initial explicit solve policy accepts only its supported CUBICSPLINE configuration; unsupported direct airborne/supported-action intents and LINEAR set requests reject. Legacy recipe behavior remains on its existing path. Handoff and connected schedules add baseline identity checks without weakening existing geometry/engine/interface checks.

The author's final focused run reports 132 passing tests. Root has not relabelled that as an independent full-suite result. Actual source-law equivalence and fast-walk mechanics are running separately; no new shared-set GLB or native visual approval is claimed here.

Reproducer: `diagnostics/shared-set-review1-repro-38f14dd.py`, SHA-256 `d8e7a05b88a5c84f0c620f275f6160dac7098bc5876adde36452be6e9079f5e6`.
Result: `audits/shared-set-root-review1-repro-38f14dd.json`, SHA-256 `d40bcb14d5bc3d3d6c3f43ea7c30d522c196694fb6d7ca2aeb4d3196e1ed53b7`.

Outcome: P0=0, P1=1, local P2=1. Fixes and exact release-head verification required; await the independent second review before one combined fix pass.
