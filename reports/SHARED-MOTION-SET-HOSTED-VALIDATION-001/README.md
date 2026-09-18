# Shared motion-set hosted validation

This stage adds a dedicated pull-request and manual GitHub Actions job for the
current Tarbosaurus shared locomotion set. It compiles `walk`, `fast-walk`,
`walk-start` and `walk-stop` together through
`catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v2.json` using the
existing `compile-set` CUBICSPLINE path. It then reopens all four emitted
packages and calls the existing native-time `verify_handoff` implementation for
`walk-start` to `walk` and `walk-stop` to `walk`.

The reviewed implementation is
`af1aeb1ce0b00e4758fdbc193288abbc22ca4019` (tree
`64d97f19716f1cdc9fdaa3b9c87a06fbeff4d828`), based on documentation checkpoint
`a406500459e1d13b7e328c7a1f70330e12f92115`. The current motion-set input at
that head has SHA-256
`1c3d071a5e638ab02a31688102e295647573be2a99f7c28e388307b249ca8d90`.

The new helper consumes existing package directories; it does not compile,
repair, retime or approve them. It preserves complete handoff receipts, hashes
those receipts into its combined result, retains errors, and returns nonzero
unless all four package integrity/technical checks and both joins pass. Package
names, selected handoff membership, output immutability and evidence filename
uniqueness fail closed.

The hosted job runs on Ubuntu 24.04 with Python 3.13 and a 180-minute limit.
It records the checkout commit/tree, clean-status observation, motion-set hash,
Python environment, compiler log and compiler exit. It uploads those records,
all generated packages and the complete handoff evidence even when a step
fails. Pull-request path filters cover the workflow, source engine, catalog,
bound source assets, package metadata and helper. Manual dispatch remains
available. This path performs no rendering; native visual review and Unity
validation remain separate gates.

## Review and local checks

Round 1 reviewed `c87fccad6b36fb7ffd9bd0bf9a56368c440dbddc` and found one P1: the first
workflow revision selected historical `adult-grounded.v1` instead of current
`adult-locomotion.v2`. It also found two local evidence-hardening issues: the
GitHub Bash step inherited `errexit` before it could save a failed compiler exit,
and distinct handoff pairs could collide in a derived evidence filename. Exact
head `af1aeb1` changes the two workflow bindings to v2, explicitly suspends and
restores `errexit` around compiler exit capture, and rejects ambiguous labels
before output creation. The external reviewer-2 R1 receipt is
`ARC/audits/shared-motion-set-hosted-validation-reviewer2-c87/README.md`, SHA-256
`e6783363336c51348cdf698a991b03054163b408f2694d799074c365a35b1080`.

At the fixed head, 99 focused helper, v1/v2 motion-set and emitted-handoff tests
passed in 3.05 seconds. Ruff lint and format checks, Python compilation, YAML
parsing and `git diff --check` passed. A shell probe invoked with inherited
`bash -e` confirmed that a failed pipeline records exit code 1. Root's narrow
closure ran six changed-path checks in 0.20 seconds and passed.
Reviewer 2 independently reran six narrow checks in 0.18 seconds and closed the
fixed head with P0=0, P1=0 and P2=0. Its receipt is
`ARC/audits/shared-motion-set-hosted-validation-reviewer2-c87/narrow-closure-af1aeb1.md`,
SHA-256 `cb0ca8c1a178eaa79b6467b99c95bfa9de12f777c679bd4b43e150bd9d86032b`.

## Acceptance boundary

Hosted execution of the new job is **PENDING**. No hosted package or handoff
result is claimed by this report, and no expensive compile was run before code
review. The existing `factory-baseline.yml`, including its legacy candidate
matrix and truthful failures, is unchanged. This stage does not claim that the
catalog is all green, that visual review passed, that Unity parity ran, or that
any generated motion is production approved.
