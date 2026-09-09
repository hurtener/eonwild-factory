# V9 factory baseline and next acceptance gates

## Shared animal motion sets

A versioned motion set binds one animal baseline and an ordered list of portable
motion intents. The baseline owns admitted source geometry, semantic rig,
animal scale, contact and articulation limits, coordinate frame, neutral-pose
calibration, shared body style, gait-response policy, and solve policy. An
intent owns only its program and gait/timing profiles. Unknown fields and body
overrides fail closed.

`python -m eonwild_motion.factory compile-set` resolves every selected intent
from one immutable baseline snapshot. Each package retains a canonical flat v1
`recipe.json` for existing consumers plus the authored set, baseline, intent,
style, and neutral-calibration snapshots. Verification reconstructs the recipe
and effective performance from those package-local bytes. Grounded gait and
grounded transitions are the initial supported capability; other programs must
be admitted explicitly rather than inheriting grounded controllers.

Source: `feat/spark-muse` / `8c1f5c2bfea481a56916ee6e0bfa74961ca0d141`.
This document supersedes historical instructions that made Babylon the fixed
consumer or treated a numbered experiment as the public factory interface.
The product's embodiment, scientific-honesty and reproducibility principles
remain. Unity is the intended runtime; it has not been implemented here.

## Baseline scope

The baseline adds a neutral-geometry admission boundary, locked recipe inputs,
an immutable candidate compiler, a genuine grounded reverse-walk planner,
reopened final-channel checks, skinned-contact evaluation, runtime sidecars,
corruption tests, and reproducible review tooling. It extracts the already
reusable V9 locomotion emitter rather than rewriting it.

The old reproduction/promotion pipeline remains for approved-byte regression.
It must not be confused with candidate creation. V8/V8.1 are recovered through
Git history; the V8.2 release capsule moves intact into legacy/capsules. Do not
mistake a retired engine folder for permission to discard an approved take.

## Status is multi-dimensional

| Dimension | Evidence | Meaning |
|---|---|---|
| Generation | compiler completed and emitted inventory | A candidate exists |
| Integrity | final file hashes match manifest | Files are the recorded files |
| Skeleton mechanics | reopened FK and plan witnesses | Proxies satisfy declared checks |
| Skinned contact | actual serialized sole/toe vertices | Contact at the declared floor |
| Perceptual quality | native-speed multi-view comparison and human decision | Looks convincing |
| Unity parity | imported/compressed motion and live controller checks | Survives the engine boundary |
| Device budget | measured target devices | Fits the shipped runtime |

Integrity is not approval. An animation may look useful while remaining
mechanically blocked; retain the evidence instead of relaxing the threshold.
A missing skin measurement is NOT_MEASURED, not zero drift. The compiler's
manifest never claims production approval. A future publisher must require
all applicable approvals and cannot be the candidate generator itself.

## Work sequence

### 1. Consolidation and invariant regression (this baseline)

Preserve the approved checkpoints; stop new code imports from experiment
folders; separate geometry from choreography; add candidate/input identity.
Keep exact legacy solver behavior as the default API path during extraction.
Prove repeat compilation and negative tests before changing performance.

### 2. Final contact authority and gait seam acceptance

Fix actual final skin contact, not just toe-joint proxies. Audit contact masks,
initial pose/floor calibration, stance roll versus slip, and duplicate terminal
loop samples. A loop-seam evaluator must unwrap root motion and preserve the
same contact phase across cycles; never simply omit a failing physical phase.
Test the validator with lifted feet, slipping feet, phase shifts, corrupted
geometry, and final post-solve edits. Use normalized/physical tolerances with
explicit provenance; no broad proximity band masquerading as ground contact.

Exit: accepted run and sprint contact witnesses on their final GLBs, with the
same criteria applied before and after Blender/Unity import.

### 3. Extract persistent-support feeding

Recover Feeding001 support and Feeding003 oral anchoring into a typed behavior
module, not a wrapper that imports their historical Python files. The input
must declare semantic spine/neck/mouth roles, articulation envelopes, target
frame, grip windows, resistance/yield, and performance curves. State belongs to
one compilation instance, never a monkey-patched module or mutable rig cache
shared across simultaneous builds. Remap different neck chain lengths through
normalized chain coordinates rather than slices such as neck[:3].

Feeding004 remains an experiment. Do not migrate its hardcoded bone lists,
post-validation tremor, relaxed rate thresholds, or moving anchors on solver
failure. A yielding target is an explicit interaction state; infeasibility
must trigger a documented regrip/reposition/failure branch.

Exit: reproduce the accepted Feeding003 performance; vary target height,
resistance and duration; validate oral and foot contact on final serialized
motion; compile two requests in reversed order and prove no cross-run state.

### 4. Temporal performance and signed response

Add reference-backed, versioned performance curves and temporal objectives.
Carry prior pose/velocity through related phases; preserve intention instead
of independently solving every frame. Replace unsigned head-rate magnitude in
momentum-related paths with a correctly framed signed quantity, or explicitly
classify that path as an artistic response. Do not change the approved runs
while fixing a different dynamics path. Test mirrored impulses and reversals.

Review silhouette, load/response ordering, stance compression, head attention,
neck curvature and distributed tail response. Random noise is not a substitute
for coherent performance. Variants in this baseline are candidates, not proof
that this workstream is complete.

### 5. Unity validation scene (begin before the full world)

One animal, flat floor, slope, obstacle, adjustable food target, and scripted
resistance/yield. Test play/pause, speed changes, start/stop, turns, and contact
handoff. Compare world-space traces against the factory reference. Confirm
animation event delivery at frame zero, exact loop boundary, large frame jumps,
pause/resume and interruption. See UNITY_MOTION_CONTRACT.md.

### 6. Real family transfer

Admit a second independently rigged and skinned compatible biped with different
segment proportions. Change data, not shared Python behavior. Synthetic
renamed/scaled tests remain useful but do not certify this. Then test a third
holdout body. An incompatible topology should reject with a capability reason,
not silently stretch a limb or reuse an unrelated gait.

Exit: locomotion, feeding and transitions pass mechanical and perceptual
review on more than one real body without per-species branches.

### 7. Breadth and production release

Use the V5.5 catalog to recover missing actions in dependency order: idle and
attention, starts/stops/turns, feed/drink, committed bite/recovery, injury and
rest. Add different engineering families only after the first family proves
reuse. Publish a motion package with source identity, approved review,
Unity parity, runtime envelope and rollback reference.

## Integrated quality benchmark

A one-minute controlled sequence: notice something to the side, shift support,
start walking, accelerate, turn, sprint briefly, brake, approach food, grip and
pull, react to yield, retract, and return to an attentive idle. Repeat with
another support foot, target height and player input. This benchmark is a
planned acceptance test, not a cinematic already delivered by this baseline.
