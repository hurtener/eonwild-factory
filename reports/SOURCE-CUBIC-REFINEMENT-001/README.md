# Source CUBIC refinement and reverse-walk review

The shared exporter now inserts a source-derived key when its serialized
CUBICSPLINE interpolation violates an articulation limit between valid source
poses. The actual Tarbosaurus reverse-walk package passes after one insertion
at 0.737500011920929 seconds. No joint limit, contact allowance, source pose,
stride, or playback clock was relaxed.

## Implementation and bounded review

Initial reviewed implementation: `d90521003281767480f7523ccb346f08838c35be`.
Narrow cache correction: `43cdcdda32dba76e01df9bc16304dd5d0d108b6c`.
Integrated implementation: `c24bf69601a4069a4338df21d2f984c7cb17e865`.
The integrated src/catalog/tests match the corrected reviewed head exactly.

The exporter rechecks both output modes after each refinement, inserts at
most eight source keys, and retains the final failure if that budget cannot
close the violation. Checked values are reused to avoid redundant solves.
Passing curves retain their animation bytes. A cross-revision synthetic
articulated fixture confirms identical root-motion, in-place and plan bytes
against the preceding exporter when no key is inserted.

Reviewer two identified one P1: nested mutable cache values could be changed
after source validation and then serialized. The correction stores detached
immutable row/pose snapshots and checks the bound law integrity on every
reuse, including reuse needing no new source queries. The original corruption
probe now raises TypeError. Both narrow closure reviews pass; no P0/P1/P2
finding remains in this delta. No additional whole-branch review was opened.

Author focused checks: 202 passed at the initial implementation. Root initial
checks: 52 passed; both narrow closure checks passed 11 tests. The integrated
implementation passed the same 52 focused checks in 5.90 seconds. Ruff and
diff checks pass. These are focused results. The preceding published
`6f6b8e2` hosted contracts passed 1,135 tests plus 21 subtests in 723.50 seconds
and source evidence passed; that result is not attributed to this new head.
At published `9a7e20983b8bce4bfcc3fbbf2ae34c3e92280f82`, hosted contracts
passed 1,140 tests plus 21 subtests in 606.17 seconds (job 102354496950),
and source evidence passed. Broader catalog acceptance still has failures;
the overall workflow is not claimed green.

## Actual candidate evidence

Candidate 006 root-motion SHA-256:
`9c9d6685d29374dfc750ec6784a7f39f91e957716d2f56bb113e2f046de34f5d`.
In-place SHA-256:
`441962cbeb21f74fc85545ee46bd79250b6f3e16316936036c3e48bed19d7aae`.
Manifest SHA-256:
`b181f4704dadf401c50f248cba2be6765bdbbe5667a305222ea709df7634524a`.
Root independently reopened and verified the complete package: integrity and
technical status PASS. The exact integrated implementation then rebuilt
release candidate 008 in 432.55 seconds and independently verified PASS.
Root-motion, in-place, plan and midpoint-plan bytes are all identical to the
reviewed 006 artifact. Release manifest SHA-256:
`36f3849793b18ae6850a5f5fe6c74720bd3da20b9b94c0ce81d8655fbcb9c61c`. The initial between-key ankle departure was
0.064762056 degrees; after refinement it is approximately 0.0017537 degrees,
within the unchanged 0.01-degree numerical allowance.

Root inspected every frame in two source-bound views: side and front,
60 frames each at 30 fps over the unchanged 2-second cycle. Enlarged recovery
poses were also reviewed. No gross limb inversion or new contact/body jump
was observed. Four-sample 640-pixel renders limit fine skin assessment; the
known proximal thigh concern remains. Browser playback was unavailable
because its policy check could not be verified. No native-speed user
acceptance, reverse Unity parity, or production approval is claimed.

The retained source-law preflight for reverse start and stop passes all native
rows, contact, reach and sampled rate checks. Candidate 007 final start and
stop exports now independently verify integrity and technical PASS, as do
their actual serialized joins with steady 006/byte-identical release 008 in
both modes. Start manifest SHA-256:
`c636c3519b56ec66b0dd9771b1b31bf7b1cbda0a0f05d78b4ccd744544701451`.
Stop manifest SHA-256:
`d2ef5af9be365ecc754e6e04333b7b324e18bcd33e2c4f7decbeba3b6fc444bb`.

Connected review 009 uses the matching d905 generating fingerprints for
007 start, 006 steady and 007 stop. The separate 006/008 byte-equivalence
receipt binds this review to corrected steady output without claiming that
the older packages were regenerated at 9a7e209. No segment is blended or
retimed. The sequence lasts 13.6 seconds and moves backward 7.052392 m.
Root reviewed all 816 frames across root-motion side and in-place
three-quarter views, plus enlarged exact join and recovery panels. No new
gross limb inversion, body jump or join discontinuity was found. Independent
frame hashes, source manifests, 408-frame/30-fps clocks and full video decode
pass. Native-speed aesthetic acceptance, fine skin assessment and Unity
remain open. These are review candidates, not production-approved animals.

## Allosaurus and remaining scope

Acquired Raptor reference timing is independently verified at 24 fps with
31 intervals (1.291667 seconds). The Allosaurus transfer now closes its loop
and solves skeletal targets, but is still rejected for material footing:
independent evaluated-mesh checks of diagnostic 003 find floor penetration
of approximately 289 mm left and 274 mm right. The foot-head adapter used
negative transferred heights and bypassed the canonical skin-target law.
Source foot-surface contact/clearance and final target contact correction are
being implemented. Neither the rejected transfer nor a successful bone-head
residual establishes an accepted Allosaurus animation.

V10 walk and shared fast walk remain the working baselines. Sprint/run
coverage, their transitions, broader Allosaurus onboarding and Unity runtime
acceptance remain unfinished. PR #2 remains draft. Do not merge.

Local source-bound evidence stays on the external SSD under task storage:
`audits/reverse-shared-006-root-native/`,
`audits/reverse-cubic-key-refinement-reviewer2-d905/`,
`audits/tarbosaurus-reverse-shared-001/`, and
`audits/allosaurus-wholebody-003-root-review/`.
The connected extension is recorded under
`audits/tarbosaurus-reverse-shared-007-transitions/` and
`audits/reverse-connected-native-009/`, including independent
`root-start-verification.json`, `root-stop-verification.json` and
`root-review.json` receipts. The full-suite log is
`audits/ci-contracts-9a7e209.log`.
