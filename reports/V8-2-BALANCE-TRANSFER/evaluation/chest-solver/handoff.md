# Candidate-A chest balance solve handoff

## Result

Use a **world-relative rotation-vector solve**, not a local Euler roll tweak.
The safe deterministic coefficient is:

```text
chest_roll_gain = 0.3984375
```

Applied to iteration-b’s existing walk channels, it produces official
Candidate-A values:

| Gate | Measured | Requirement |
| --- | ---: | --- |
| Chest pitch envelope | `4.0816°` | within `.2°` of approved `4.1030°` |
| Chest yaw envelope | `2.6480°` | no regression from approved `2.6120°` |
| Chest roll envelope | `5.6179°` | `5.4–6.25°` |
| Chest/pelvis roll correlation | `-.9015` | `[-.95, -.70]` |
| Head pitch/yaw/roll | `2.5801° / 1.5288° / .9661°` | caps `2.9° / 2.1° / 1.2°` |
| Max chest local delta | `.96535°` | `≤ 1.0°` |
| Max neck local delta | `.29926°` | `≤ .75°` |

The current tail, pelvis, lower legs, and seam remain unchanged. The official
Candidate-A gate passes on the temporary evaluated variant.

## Exact per-key solve

For each existing exported walk key, using current iteration-b world rotations:

```text
P     = R_pelvis(t) * inverse(R_pelvis(0))
p_z   = log(P).z
Q     = R_chest(t) * inverse(R_pelvis(t))
q*    = log(Q) + [0, 0, -0.3984375 * p_z]
Rch*  = exp(q*) * R_pelvis(t)
```

`log`/`exp` are the shortest-path quaternion rotation-vector operations. This
is the same world-basis convention used by the frozen evaluator. It leaves the
official chest-relative pitch and yaw samples unchanged by construction and
adds only the required counterphase roll component.

Reconstruct the local chest key after all unchanged chest-parent transforms:

```text
q_local_chest* = inverse(R_parent_chest*) * Rch*
```

Then preserve the **iteration-b head world pose**, rather than its previous
neck locals. Let `D = Rch* * inverse(Rch_iteration_b)` and apply the following
residual world-delta fractions down the existing neck chain:

| Bone | Residual multiplier for `D` |
| --- | ---: |
| `Bone_041` | `.89` |
| `Bone_040` | `.74` |
| `Bone_039` | `.55` |
| `Bone_038` | `.31` |
| `Bone_037` | `0` |
| `Bone_036` | `0` |

For every row, calculate `R_bone* = D^residual * R_bone_iteration_b`, then
reconstruct the local quaternion from its already-updated parent. This makes
`Bone_036` world-exact to iteration-b and keeps the head caps intact.

Apply the identical new arrays to both existing relaxed-walk clips. Preserve
quaternion sign continuity and set the duplicated final key equal to key zero.

## Bounds and search

The temporary solve used a monotonic bisection on the coefficient and the
official 120-phase evaluator. The local chest bound becomes active at about
`gain = .4127`; do not exceed `.410` in an implementation. The recommended
`.3984375` leaves about `.03465°` chest-local margin while avoiding a
barely-valid edge value.

Required post-write proof:

1. Candidate-A official gate passes.
2. `Bone_000`, `Bone_001`, all lower-leg/foot/toe channels, and tail channels
   remain byte-identical to iteration-b.
3. Both walk clips receive the same upper-body arrays.
4. Existing structural/contact validation passes unchanged.

## Reproduction

```sh
blender --background --python-exit-code 1 \
  --python reports/V8-2-BALANCE-TRANSFER/evaluation/chest-solver/solve_chest_balance.py -- \
  --candidate candidates/v8.2-balance-transfer/generated/iteration-b/tarbosaurus_procedural_v8_2_balance_transfer.glb \
  --approved candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb \
  --target-roll 5.618 \
  --output reports/V8-2-BALANCE-TRANSFER/evaluation/chest-solver/solve-result.json
```

The solver creates only temporary variant GLBs and does not mutate either
input.
