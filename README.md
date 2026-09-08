# Eonwild Motion Factory

**Python authors reusable motion; Unity is the intended consumer.** This work
continues V9 and the merged factory baseline, not another numbered toolkit.

PR #2 is still a draft: **quality-01 is rejected** and new candidates do not
inherit the approval of the preserved V9 takes. Execution is restored. Read
[the final local continuation evidence](reports/V9-CONTINUATION-FINAL-4AE0FE9-001/README.md)
and [the current motion/evidence status](docs/MOTION_QUALITY_STATUS.md) for the
verified improvements and remaining transition/handoff acceptance work.

## One active generation path

```
admitted geometry + semantic rig + versioned behavior recipe
    → behavior-owned placement, attention and contact plans
    → shared articulated limb/body/skin constraints
    → reopen final GLBs and measure
    → immutable candidate + source identity + runtime metadata
    → native-time review → Unity parity → explicit future promotion
```

Generation never imports historical `build/`, `reports/` or retired toolkits.
Read-only review may inspect a specifically hash-bound historical asset; its
animation is not an input to new choreography. Species differences belong in
geometry, semantic bindings and profile data rather than literal bone names.

## Install and generate

Use Python 3.12 or newer and the existing pinned dependencies:

```sh
uv sync --frozen --group test
uv run python -m eonwild_motion.factory compile \
  --recipe recipes/heavy-biped/walk.v3.json --output out/walk-v3
uv run python -m eonwild_motion.factory verify out/walk-v3
```

An output directory must be new; earlier takes cannot be overwritten.
Compilation is not approval. Verification exits nonzero for blocked technical
acceptance. Missing evidence is not a zero-error pass.

The current adult Tarbosaurus benchmark candidate is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v3.json`.
It adds specimen-specific mass evidence and measured geometry calibration to
the grounded walk. See [animal configuration](docs/ANIMAL_CONFIGURATION.md)
for the reusable data contract and its current biomechanical limits.

The latest body-response review candidate is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v9.json`. It preserves the
reviewed V8 bind geometry, gait, legs, contacts, articulation, travel and
configured amplitudes, then combines the support-timed axial clock with the calibrated
neutral jaw. The host inspected all 370 rendered frames across five locked
cameras; native-speed playback remains pending. The exact LINEAR local-channel
loop is `BLOCKED` at 3.231 mm/s against the unchanged 1 mm/s limit.
Body timing is authored kinematics; mass-response physics is unavailable.
See [the combined V9 report](reports/V9-ADULT-AXIAL-JAW-V9-001/README.md).
The final SourceMotionQuery union passed 907 tests plus 21 subtests; see the
[integration report](reports/V9-SOURCE-MOTION-QUERY-V9-INTEGRATION-001/README.md).

Current explicit review candidates are `walk.v3`, `reverse-walk.v4`, `run.v4`,
`sprint.v4`, `fast-walk.v2`, `tarbosaurus-pin-552-1-adult-walk.v9`,
`tarbosaurus-pin-552-1-adult-fast-walk-recovery.v3`, `feeding.v2`, and
`bite-miss.v2`, alongside `idle.v1`, `alert.v1`, and `call.v1`. Historical
adult v3 and body diagnostics v5/v6/v7/v8 remain in CI as regression witnesses.
The eight start/stop recipes are now `.v3`, bound to those exact sustained gait/performance
inputs. All remain candidates, not automatically accepted animations. Passing
the individual start, steady-gait and stop clips is insufficient: the permanent
transition-pair jobs independently check both actual
serialized joins. See [the transition interface](docs/TRANSITION_INTEGRATION.md).

```sh
uv run python tools/verify_catalog.py \
  --recipes walk.v3 reverse-walk.v4 feeding.v2 bite-miss.v2 \
  --output out/review-candidates
```

The compiler supports grounded gait, airborne gait, gait transitions and
persistent-support actions. Metatarsal articulation is separate from pad
contact and digit recovery. Forward attention is calibrated from the admitted
rostrum. Feeding coordinates a feasible initial brace and bounded common pelvis
accommodation before oral constraints; the mouth anchor and floor do not move
to conceal failed reach. These are geometric/art-directed controls, not claims
of simulated muscles or reconstructed dinosaur optic axes.

## Review actual motion

With Blender and ffmpeg installed:

```sh
uv run python tools/review_compiled_candidate.py \
  --package out/review-candidates/walk.v3 --output out/walk-review \
  --views side front rear three-quarter --fps 30 --compare-v9-walk
```

On macOS pass
`--blender /Applications/Blender.app/Contents/MacOS/Blender` when needed.
The command renders an existing immutable package without regenerating or
repairing it. To serve retained review pages and seekable media locally with
single-range HTTP support, run:

```sh
uv run python tools/serve_review.py --root . --bind 127.0.0.1 --port 8877
```

The review server uses the explicit document root and loopback binding; it is a
local evidence viewer, not a production or multiplayer server. The renderer uses the explicit floor, keeps native timing, locks each camera
from the preserved V9 reference before drawing the candidate, and checks the
candidate again after rendering. Review outputs contain actual MP4s, timing,
camera and render receipts; FBX transport is **not** Unity validation.

The older `tools/build_showcase.py` is also available; pass explicit `--recipes`
for the current candidates rather than relying on its initial-catalog defaults.
Both tools retain mechanical rejection even when diagnostic rendering succeeds.

## Verification and toolchain

```sh
uv run python -m pytest tests -q --tb=short
```

The 2026-09-08 v7 and CUBICSPLINE-consumer Stage A integration head
`3b1f55602ba2d8d177c42ec15ccb02d401f92b7d` passed 788 tests plus 21
subtests in 237.65 seconds with the pinned real tools. Hosted CI for the
publication head is pending; the local result does not approve motion or
authorize merging draft PR #2. The receipt and bounded review closure are in
[the Stage A integration report](reports/V9-CUBICSPLINE-CONSUMER-STAGE-A-001/README.md).

The earlier 2026-09-08 final continuation head
`4ae0fe92ec3ffd49dfeca14085756cc7cbe7d852` passed 683 tests plus 21
subtests in 212.65 seconds. Its receipts and final review closure remain tracked
in [V9-CONTINUATION-FINAL-4AE0FE9-001](reports/V9-CONTINUATION-FINAL-4AE0FE9-001/README.md).

The complete mandatory suite includes historical integration, exact duplicate
builds, promotion rejection and real rendering. Its canonical CI is macOS
arm64 + Blender 5.2.0 + genuine Khronos glTF validator 2.0.0-dev.3.10. The
preserved release reproduces exactly there. Linux differs by two float32
rounding values; the approved hash is not changed to hide that portability
boundary. Current V9 candidate mechanics run independently on Linux.

CI is read-only, runs one job per recipe, retains failed receipts, and generates
native multi-view reviews. There are no self-committing recovery workflows,
production imports of staging scripts, or omitted integration tests. A green
test suite is not itself a green motion catalog or a visual approval.

The integration validates actual exported LINEAR/SLERP tangents and now shares
a strict CUBICSPLINE-capable reader across contact and tangent consumers.
Generic gait joins and local steady loops remain outside their unchanged
governed velocity limits. Stage A does not add a CUBICSPLINE emitter or interval
rate authority, so it grants no CUBICSPLINE technical pass. Earlier quadratic
finite-difference values remain diagnostics only; this head makes no exact
runtime C1 claim and changes no motion representation.

## Preserve what worked

Approved Run010, Sprint006, Feeding003 and V9 walking references remain
unchanged. See `catalog/baselines/approved-takes.json` and the exact walk identity
in `docs/MOTION_QUALITY_STATUS.md`. The inherited V8_1 name inside the V9 walk
GLB is not a reason to select a different asset.

V8 and V8.1 are retired from the active tree but recoverable through Git
history. `legacy/capsules/v8.2` is immutable compatibility/provenance material.
V5/V5.5 remain breadth-recovery references, never the active generation path.
Prior partial-recovery records remain honest about missing source fragments.

## Runtime boundary

One runtime motor owns final movement. Animation contacts are cues, not
unconditional gameplay damage, grip, yield or feeding facts. The Python factory
emits the planned motion and versioned metadata; the Unity adapter must still
prove imported/compressed trace parity, terrain and target adaptation, event
handoff and device cost. A second real independently skinned species is also
still required to establish production family transfer.

See [the factory roadmap](docs/FACTORY_ROADMAP.md),
[the Unity contract](docs/UNITY_MOTION_CONTRACT.md), and
[the current status](docs/MOTION_QUALITY_STATUS.md).

**Unity: NOT_RUN. Visual approval: PENDING. Production promotion: NOT_GRANTED.**
