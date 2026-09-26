# C62 — interactive encounter foundation

Status: **IMPLEMENTED PROTOTYPE; REVIEW PENDING; NOT AA/PHYSICAL ACCEPTANCE**.
This is the first interactive checkpoint of the AA-readiness plan. It does not
complete that plan or promote the C60/C61 floor candidates to approved motion.

## Review and controls

The review is a native-time, 24 fps, two-minute Unity encounter on a plain stage.
Both animals share one runtime consumer, with admitted geometry, semantic bone
bindings, existing motion clips and separate attention profiles.

Video: `game/Evidence/moco-c62-encounter/encounter-native-120s.mp4`.
Scene: `game/Assets/Eonwild/Encounter62/Encounter.unity`.
Local player: `game/Builds/Eonwild Encounter.app` (generated, not committed).

- G switches autonomous/manual; Tab selects the animal.
- W walks, Shift+W runs, S retreats, A/D steer.
- H requests a knockdown; R requests a rise once body support is present.
- Space pauses; Escape quits. Run without `-evidence-dir` for manual exploration.

The recording uses a reproducible decision policy, not live player input.
Proximity and speed trigger the encounter response; severity and clip choice
are authored. This is not a validated collision impulse, injury or damage system.
Initial placement admits side impacts; arbitrary impact direction is not solved.

## Implemented

`EncounterMotionMotor` owns actor travel and heading. Imported root travel is
consumed once. Competing Animation/Animator components are disabled. Requests
adopt the current local pose, carry outgoing velocity, choose a compatible
contact phase, and decay pose offsets into the destination. Start and braking
clips retain the available take's articulation. Fall, get-up and retreat can
join without returning the actor to a fixed scene origin.

Contact projection uses current skin weights and bind matrices, a persistent
sole witness during support, existing knee/ankle engineering ranges, and final
full-skin measurement. Root/body support and limb accommodation are bounded
kinematic corrections. They do not simulate muscle forces. Burst jobs accelerate full-skin
evaluation during projection; no sparse contact subset substitutes for the skin.
Post-render BakeMesh comparisons independently check coordinate/scale parity.

Attention targets the other animal and consumes the canonical neck envelope.
It corrects the existing head direction rather than stacking the full requested
yaw onto an already-turned source pose. Authored breathing, jaw response and tail
countermovement supplement the imported body motion; floor choreography retains
its source axial motion. No species-specific solver branch was added.

The builder references original imported clips directly. It does not duplicate
hundreds of megabytes of curves or alter their approved source bytes.

## Acceptance and unfinished work

Read `game/Evidence/moco-c62-encounter/REVIEW.md` for exact capture, contact,
rendered-skin parity, performance, checks and observed defects.

| AA-readiness work | C62 outcome | Still needed |
| --- | --- | --- |
| Shared contact and recovery | Runtime support accommodation over C61 poses | Deep-pose support/traction, muscle capacity, self-collision and credible force transfer |
| Responsive controller | Pose/velocity adoption and support-aware joins on both rigs | Broader interruption coverage, momentum-aware braking, arbitrary terrain/directions |
| Purposeful life | Threat-directed attention, breathing/jaw and tail response | Richer behavior decisions, distraction, fatigue and context beyond this encounter |
| Hybrid production pipeline | Existing offline trajectories consumed with bounded runtime correction | Optimized contact proxies/LOD, authored polish workflow and physical admission |
| Playable encounter | Keyboard control plus reproducible autonomous review | Robust body collisions, gameplay damage authority, varied terrain and production budgets |

The recording visibly overlaps the animals during recovery and spends too long
backing away. The maximum support-witness mismatch is about 20 cm; body
corrections reach 49 cm. These remain open defects, despite low final floor
penetration. The separate M4 test reports 16.93 ms median / 31.53 ms p95, so
locked 60 FPS is not established.

A smooth pose join is not a smooth force transfer. A low penetration number does
not prove correct support force or eliminate slip. C61 inverse-dynamics failures
remain failures; **no new full Moco solve was run or converged for C62**. Runtime
corrections require their own acceptance and cannot inherit source approvals.
The approved main branches and source animation files remain unchanged.

## Reproduce

Run from the principal repository, `/Volumes/m2-extended-disk/Repos/eonwild`.
Unity executable:
`/Volumes/m2-extended-disk/Unity/Editors/6000.3.23f1/Unity.app/Contents/MacOS/Unity`.

1. Build with `-batchmode -quit -projectPath "$PWD/game" -executeMethod EncounterReviewBuilder.Build -logFile "$PWD/game/Evidence/moco-c62-encounter/build.log"`.
2. Check actual-rig state adoption with the same Unity command but `-executeMethod EncounterRuntimeChecks.Run` and a separate log.
3. Run `game/Builds/Eonwild Encounter.app/Contents/MacOS/Eonwild Floodplain` with `-duration 120 -seed 62 -capture 1 -evidence-dir "$PWD/game/Evidence/moco-c62-encounter/candidate-final" -logFile "$PWD/game/Evidence/moco-c62-encounter/candidate-final-player.log"`.
4. Run `sh game/Evidence/moco-c62-encounter/scripts/encode-review.sh`.
5. Run a separate uncaptured process (`-capture 0`) for performance. Do not run a capture/build/optimizer simultaneously or infer FPS from offline capture.

Never overwrite an existing review capture; choose another directory for a new
candidate. Recipe, source hashes, contact traces, runtime event receipt, focused
checks and media travel together. Only explicit task-owned paths are committed.
Factory review branch remains `codex/moco-c52-walk-turn`; game review branch is
`codex/moco-c52-walk-turn-review`. Stop here for user feedback.
