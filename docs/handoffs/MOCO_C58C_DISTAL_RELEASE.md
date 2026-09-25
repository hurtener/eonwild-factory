# C58C — unloaded forefoot relaxation

Status: **DIAGNOSTIC READY FOR USER REVIEW**, paused at the visual checkpoint.
C58B walking received positive feedback with one remaining request: a brief
relaxed metatarsal/forefoot hang before preparing for contact. This is not an
approval of C58B running or of physical acceptance.

## Change and scope

The optional shared `moco_distal_release` refinement uses admitted toe/digit
mass, gravity moment and rotational inertia to integrate a reduced damped
forefoot response during unloaded walking recovery. A C2 envelope releases it
and prepares the reviewed contact pose before loading. Only `mtp_l` and `mtp_r`
change: maximum added downward hang is 9.51 and 9.98 degrees. All other sampled
coordinates remain identical within 1e-9 radians/metres. Zero loaded samples
were changed. No animal-name branch, anatomy limit expansion, contact mechanics
change, renderer-only rotation or running modification was introduced.

Frequency (2 Hz), damping ratio (0.65), release (0.06 s) and preparation
(0.14 s) are **authored estimates**, recorded in
`catalog/behaviors/moco-unloaded-forefoot-compliance.v1.json`. The admitted
physical geometry supplies gravity and inertia. This is a reduced response
around a saved diagnostic trajectory, not a complete forward simulation,
identified muscle physiology, or newly converged Moco gait prediction.

## Evidence and limitations

- Sixteen native seconds, 24 fps, side and quarter; 384 frames each.
- All 768 frames inspected chronologically in contact sheets. The added hang
  and preparation read as a small distal change; no obvious new strike or
  frozen articulation. Native-speed timing remains for user review.
- Five focused compliance/posture tests pass.
- Anatomical bounds, masses, forces and contacts unchanged. Reopened joint
  limits show no violations. Skin floor minimum remains -3.978 mm.
- Ankle peak speed remains 162.30 / 135.65 deg/s. MTP peak speed is
  150.76 / 112.12 deg/s; the added motion increases distal speed, not decreases it.
- Root residual 0.143825 BW/BWL; peak command 6.23463; loaded-slip P95
  0.090978 m/s. Inherited physical contact/effort acceptance remains **FAILING**.
- Full Moco convergence: **false**. No production acceptance or approval inferred.

## Saved output and reproduction

Principal game repo: `game/Evidence/moco-c58c-distal-release/` contains both
`c58c-allo-walk-side.mp4` and `c58c-allo-walk-quarter.mp4`, comparison and visual
receipts, model/trajectory, compressed replay, retarget receipt, exact generation
arguments/environment, render commands/logs, policy and SHA-256 manifest.
Unity review assets: `game/Assets/Eonwild/MocoAllo58CWalk/`.

Working research: `/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c58c-distal-release`.
`generation.json` records generation; use a new output directory because the
tool refuses an existing output. `render.sh` records replay, retarget, Unity
build, native captures and encoding. Existing C58B source replay is archived in
its evidence directory (decompress if needed); source solution hash is pinned
in `walk-a/distal-release-receipt.json`. Do not use the exported zero parameter
placeholder (`coefficients.npy`) to regenerate the trajectory: the returned
`solution.sto` is authoritative for replay of this refinement.

Stop here for user review. Do not modify running or launch further solves.
