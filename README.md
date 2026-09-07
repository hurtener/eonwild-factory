# Eonwild Motion Factory

**Python authors reusable motion; Unity is the intended consumer.** This work
continues V9 and the merged factory baseline, not another numbered toolkit.

PR #2 is still a draft: **quality-01 is rejected** and new candidates do not
inherit the approval of the preserved V9 takes. Execution is restored. Read
[the current motion/evidence status](docs/MOTION_QUALITY_STATUS.md) for the
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

The explicit adult Tarbosaurus benchmark is
`recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v1.json`.
It adds specimen-specific mass evidence and measured geometry calibration to
the grounded walk. See [animal configuration](docs/ANIMAL_CONFIGURATION.md)
for the reusable data contract and its current biomechanical limits.

Current explicit review candidates are `walk.v3`, `reverse-walk.v4`, `run.v4`,
`sprint.v4`, `fast-walk.v2`, `feeding.v2`, and `bite-miss.v2`, alongside `idle.v1`,
`alert.v1`, and `call.v1`. The eight start/stop recipes are now `.v3`, bound to
those exact sustained gait/performance inputs. All remain candidates, not
automatically accepted animations. A passing start, steady gait and stop are
insufficient: the permanent transition-pair jobs independently check both actual
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
repairing it. It uses the explicit floor, keeps native timing, locks each camera
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
