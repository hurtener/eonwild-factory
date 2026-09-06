# Motion quality continuation: draft, not an animation release

The `quality-01` walk is **REJECTED**. Neither successful generation nor a
passing skeleton proxy is sufficient to replace the accepted V9 motion. The
requested motion-quality and breadth work is not finished.

## Source and recovery

- Merged factory baseline: `712708652b1035526b38d06fa7d487fe3c919117`.
- Original continuation point: `582ad85078bd80172dc694a2eaf4b6f46ffe4239`.
- Remote work found on resumption: `4d82b3d8e1a7ba5f7a0b448e4d9c6d442c8070d7`.
  Continue that work; do not reset to the older handoff.
- `reports/MOTION-QUALITY-AND-BREADTH-002/recovery/receipt.json` records a
  **partial** recovery (part 0 available; parts 1-3 missing). It is not proof
  that every earlier local edit was recovered.
- This continuation could not inspect `/mnt/data/eonwild-factory`: even a
  container echo, Python health check and image read failed with ClientError.
  No local work was overwritten, deleted or declared clean.
- Main, the original Spark branch, immutable capsules and approved assets are
  unchanged by these continuation commits. The temporary, self-committing
  `motion-source-recovery.yml` has been removed. CI has read-only contents
  permission and cannot rewrite this branch.

## What already exists on the recovered branch

The active compiler dispatches grounded gait, airborne gait, gait transitions
and persistent-support actions. The catalog includes forward/fast/reverse walk,
run/sprint, idle/alert/call, bite-miss recovery, feeding, and forward/reverse/
run/sprint start-stop recipes. Those are implemented candidates, **not a claim
that their final skinned motion has been accepted**. Renamed synthetic fixtures
are not evidence of successful transfer to a second real species.

## Walking comparison authority

Use this preserved V9 narrow-gauge take, never quality-01 or an arbitrarily
selected older walk:

```
build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb
SHA-256 b54e3740ea451927b3b812c1be3f4ca6146cc369ad1313be7f08edd5ca741cd3
Clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION
```

The historical clip name retains V8_1; that does not change the identity of
this V9 artifact. Its adjacent `candidate-contact-profile-root_motion.json`
records the original floor. Do not lower that floor, retime the reference,
change its animation channels, or infer that its contact metadata and the
new admitted geometry share an axis convention without measuring them.

`tools/prepare_motion_reference.py` prepares a hash-checked, read-only
comparison package. The caller must provide the appropriate explicit forward
axis. It cannot be passed to the factory as a neutral generation source.

## Corrections made in this continuation

1. The permanent workflow runs the full test suite, including the historical
   integration fixture. The old integration/Blender exclusions are gone.
2. The catalog job compiles **and invokes strict verification** for 18 current
   recipes. A mechanically blocked recipe makes the job fail.
3. The showcase now returns a nonzero exit for missing integrity evidence,
   mechanical rejection, a failed/missing requested camera view, a failed
   reference view or a rendering timeout. It still renders rejected candidates
   for diagnosis; a video is not a successful acceptance result.
4. The showcase supports side/front/rear/three-quarter native-time review and
   root-motion ground presentation. A single-recipe reference comparison locks
   each camera using the reference first and then reuses it for the candidate.
5. Blender build errors include the captured error tail in the run report;
   the full log is preserved separately. Temporary fixture cleanup can no
   longer leave only an inaccessible `see /tmp/...` path as the diagnosis.
6. Regression tests were added for these failure modes. They have **not run
   in this continuation**. No animation thresholds or approved hashes changed.

Example commands (use fresh output directories):

```sh
python -m pytest tests -q --tb=short
python tools/build_showcase.py --output out/review-walk --recipes walk.v2 \
  --render --views side front rear three-quarter --mode root_motion --fps 60 \
  --reference-package out/prepared-v9-walk
python tools/build_showcase.py --output out/review-behaviors \
  --recipes idle.v1 alert.v1 bite-miss.v1 feeding.v1 --render \
  --views side three-quarter --mode root_motion --fps 60
```

Exit 2 from the showcase means mechanical rejection, even if diagnostic media
were successfully produced. Exit 0 never grants visual approval or Unity parity.
The four-view CI job similarly preserves candidate rejection after rendering.

## Verification record and external execution block

The last inspected full-suite run is
`https://github.com/hurtener/eonwild-factory/actions/runs/34046652734`, testing
`807b4f2b92eb4251094d1219eb9d791562331f73`: **289 passed, 9 errors, 4 subtests
passed**. All nine integration setup errors report a Blender build failure;
the actual cause was not exposed in the captured report. Do not relabel this
as a passing full suite, skip the fixture, or change its expected output hash.
Four camera jobs in that same run completed, but their media have not been
visually approved in this continuation. The committed verification/run.json
is an artifact inventory, not a claim that every listed media file is present
in the checkout.

The existing recovery job was retried once and failed without any runner
steps or downloadable logs. The new read-only verification run
`https://github.com/hurtener/eonwild-factory/actions/runs/34049334607` likewise
failed before its first execution-health step (`contracts` job 101529987493,
steps null); downstream acceptance was skipped. This rules out neither an
account, policy nor runner-service issue; the available response does not
identify the cause. No billing, spending limits, runner settings or repository
visibility were changed to work around it.

## Merge / motion acceptance still required

- Diagnose and pass the entire regression suite on the final source.
- Correct and measure the actual forward/reverse stroke, ankle/metatarsal/toe
  articulation and narrow lanes against the specified V9 reference.
- Validate alternating lateral tail response and forward sprint gaze in the
  emitted skinned animal, not only the planner's parameters.
- Pass final material contact, cyclic pose/velocity continuity and limb limits
  without offsetting the floor, relaxing limits or discarding seam witnesses.
- Generate and inspect native-time comparisons from all four views. Review
  transitions, bite recovery and feeding support/grip/release in actual motion.
- Preserve successful reference bytes and supply final source-bound receipts.

**Unity validation: NOT_RUN. Visual approval: PENDING. Production promotion:
NOT_GRANTED.** Keep the PR draft until the requested motion and verification
work is genuinely complete.
