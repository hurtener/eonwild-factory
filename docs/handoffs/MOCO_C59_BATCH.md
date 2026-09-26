# C59: four finite movement tasks on both animals

Status: **GENERATED AND FRAME-INSPECTED; USER REVIEW PENDING**. Physical acceptance: **NOT CERTIFIED**. Full Moco convergence: **false for every take**.

The user requested a longer batch experiment and one combined review. This pass was implemented directly, without subagents. Eight 12-second takes use one shared OpenSim finite whole-body coordinator. This is the existing Moco research pipeline's reduced-coordinate inverse-dynamics path, not a newly converged Moco predictive solution. Foot placements, durations and attention targets remain authored task intent. Do not describe this batch as muscle-driven prediction or production-ready gameplay.

## Review

Main reel: principal game repository `game/Evidence/moco-c59-batch/c59-review-all.mp4` (96 seconds, 2304 frames, 24fps, 2560×720). Side view is left, quarter view right. Original individual views and eight dual-view clips are beside it. All source views were inspected in chronological frame sheets (4608 rendered frames total), with a closer Tarbo pivot check at 7.25–7.54 seconds. This is frame inspection, not a claim of direct video perception or user approval. Small lighting warm-up is visible at the beginning of some captures.

| Reel interval | Animal | Task |
| --- | --- | --- |
| 00–12 s | Tarbo | Outside-first stepping pivot, 60 degrees |
| 12–24 s | Allo | Outside-first stepping pivot, 60 degrees |
| 24–36 s | Tarbo | Two lateral outside/inside step pairs |
| 36–48 s | Allo | Two lateral outside/inside step pairs |
| 48–60 s | Tarbo | Faster short backward retreat variation |
| 60–72 s | Allo | First C59 backward retreat |
| 72–84 s | Tarbo | Planted alert/look-around |
| 84–96 s | Allo | Planted alert/look-around |

Pivots use six placements, a 10% wider final stance, unloaded foot reorientation and head/neck lead. They are stepping turns with moving support, not fixed-center spins. Lateral travel is 0.5796m Tarbo / 0.4764m Allo; backward travel is 1.3157m / 1.1316m. Alert intent reaches ±40 degrees under the central animal attention profiles. These are finite start/end takes, not seamless locomotion loops or arbitrary moving-state handoffs.

The fixed-camera option was added to the Unity review viewer because pelvis tracking concealed lateral travel. Both lateral takes were recaptured and reinspected using it. Motion bytes were unchanged. The other takes use the existing tracking camera.

## Shared implementation and boundaries

- Factory `src/eonwild_motion/solve/moco_placement_task.py` builds all four tasks from semantic contact geometry and animal body scale. No species branch or literal bone-name choreography.
- `tools/sequence_moco_retreat.py` selects this optional task path, applies root yaw before IK, and allocates attention through the central profile using projected skull heading. The original retreat path is preserved.
- `moco_finite_coordination.py` permits forward/lateral/yaw search envelopes to follow the task seed. Envelope widths are unchanged. Anatomical bounds remain absolute. These root search penalties are not hard physical constraints.
- All admitted limb, trunk, neck and tail coordinates enter the shared finite coordinator. Body motion nevertheless reads restrained, especially Allo's alert. Participation in an objective does not guarantee expressive or physically sufficient motion.
- Existing C56 support-edge pads expand 14 contact sites to 34, dividing nominal stiffness across them. Mass, segment data, actuator capacities and joint limits are unchanged from each source. Contact topology differs from the forward source; this is explicit.
- Sources provide anatomy and a rest state (frame zero); periodic gait timing is not copied. This does not establish general moving-state handoff support.
- Every finite optimization stopped at its six-evaluation budget. No success/convergence is inferred from an exported trajectory.

## Mechanics and inspection

| Take | Root residual RMS (BW/BWL) | Peak normalized command | Loaded slip P95 (m/s) |
| --- | --- | --- | --- |
| Tarbo pivot | 0.12367 | 4.0140 | 0.0247 |
| Allo pivot | 0.08834 | 1.1003 | 0.0175 |
| Tarbo lateral | 0.05312 | 1.9122 | 0.0231 |
| Allo lateral | 0.08241 | 0.7232 | 0.0164 |
| Tarbo retreat | 0.05154 | 1.1244 | 0.0183 |
| Allo retreat | 0.08149 | 0.7562 | 0.0145 |
| Tarbo alert | 0.03628 | 2.0613 | 0.0026 |
| Allo alert | 0.06986 | 0.8547 | 0.0023 |

Reopened skin exports report no sampled knee/ankle angle-limit violations and positive minimum skin clearance (4.3–12.5mm). This does not certify support forces, all coordinates, stability or controller integration. Rest support-force deficits and root residuals remain. Commands below one do not alone establish physical feasibility.

Tarbo pivot is the weakest numerical candidate: peak ankle speed 381.4 degrees/s at 7.4375 seconds, plus command excess. Adjacent rendered frames show a fast planted-leg adjustment without a gross mesh jump. Keep it flagged for native-time judgment; do not promote it merely because angles stay within bounds. The other takes have short, restrained steps and quiet body/tail behavior; no gross crossing or sudden mesh jump was found in the inspected frames.

The legacy sequence `distance_m` field measures backward/forward travel only and is misleading for lateral or turning tasks. Use archived `displacement-audit.json` for signed world forward/lateral displacement, heading change and horizontal path length. Original replay bytes are preserved.

Focused checks: **13 passed** across placement, finite coordination, retreat task and distal release. Unity builds/captures exited zero. Media frame counts, rates and durations were verified with ffprobe. No full gameplay/parity or biological validation claim.

## Reproduce and continue

Factory worktree: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/worktrees/stride-hip-visual-iteration`.
Game repository: `/Volumes/m2-extended-disk/Repos/eonwild`.
Research workspace: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c59-batch`.
Base factory commit: `465ac09b3d15262d1b2aff0204890fcdfb33b01b`.
Base game commit: `0240f981e2e4c8cf5e4cad75cbb161a62d1bea59`.
Review branches: `codex/moco-c52-walk-turn` and `codex/moco-c52-walk-turn-review`.

Archived evidence includes expanded plans, process commands/logs, model.osim, solution.sto, coefficients, receipts, compressed replay JSONs, source rest inputs/hashes, semantic embodiment data, generation-source snapshots, render scripts and videos. Animated GLBs/profiles live once in `game/Assets/Eonwild/Moco59{Animal}{Task}/`. Raw PNG captures remain on the external research drive, not duplicated into Git.

Canonical family configuration: factory `catalog/behaviors/moco-c59-batch.v1.json`. `batch.json` contains each source, profile and motion-set path. For a deliberate rerun, adapt these absolute paths if necessary, use a new output directory, and inspect existing receipts before launching:

1. OpenSim Python: task-storage `research/opensim-2026-09-20/moco-venv/bin/python`; NumPy/retarget/test Python: `venvs/contact-mass/bin/python`.
2. Run archived `generate.py <take-id>` from the factory: it calls sequence generation, physical replay, then actual-rig retarget. Exact argv and exits are in each process receipt. Environment: `PYTHONPATH=src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`. Do not accidentally rerun completed outputs.
3. `render.py <take-id>` imports the GLB/profile and builds the existing plain-stage Unity viewer (6000.3.23f1). `render-fixed.py` adds fixed-camera capture for lateral takes. Both save 288 frames per view and encode at native 24fps. The scripts overwrite their named outputs: choose a new checkpoint directory first.
4. Inspect every frame and important joint velocity events. `compact-sheets.py`, `audit.py`, and `assemble.py` archive the review procedure. `solution.sto` is from finite coordination, not a converged full Moco solve.
5. Keep physical receipts separate from visual decisions. Do not weaken joint limits or silently retime footage. Record each accepted/changed take after the user reviews the batch, then select the next family.

Stop here for the requested batch checkpoint. C59 approval is not inferred. Sprint, impacts/stumbles, knockdown/get-up, feeding/drinking, lying/rest, attacks, terrain adaptation and robust moving-state joins remain outside this pass.
