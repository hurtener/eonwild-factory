# V8.3 machine-gate blocker — frozen upper locals versus pelvis world roll

## Status

`BLOCKED_BY_CONTRACT_CONFLICT`. No V8.3 artifact is eligible for selection,
rendering, channel update, or promotion. Stable remains the exact approved
V8.2 release.

## Reproduced conflict

The required pelvis layer changes pelvis orientation in the frozen evaluator's
world basis. With V8.2 spine/chest/tail local tracks frozen, the same world
delta left-multiplies every descendant. The official relative matrices become

```text
R_chest_relative' = D * R_chest_relative * inverse(D)
R_tail_relative'  = D * R_tail_relative  * inverse(D)
```

Their rotation-vector components therefore rotate whenever `D` produces the
required larger pelvis roll. The vector norms remain invariant, but the
contract gates individual pitch/yaw/roll components. This makes the demanded
pelvis progression conflict with the simultaneously frozen upper local tracks
and tight component envelopes.

The implementation search used the independent 120-phase evaluator pinned at
`/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-2-BALANCE-TRANSFER/evaluation/tools/evaluate_balance.py`.

| Candidate | Pelvis roll P2P | Chest-relative pitch P2P | Result |
| --- | ---: | ---: | --- |
| scale .5, phase -60 deg, scale-one roll 1.70 deg | 3.298 deg | 4.257 deg | pelvis roll below 3.5 |
| scale .5, phase -58 deg, scale-one roll 2.05 deg, pulse .30 | 3.591 deg | 4.491 deg | chest pitch above 4.282 |
| scale .5, phase 120 deg, scale-one roll 1.70 deg | 3.899 deg | 5.433 deg | chest pitch above 4.282 |
| chest-axis conjugation-preserving solve | 5.003 deg | 4.082 deg | pelvis pitch/yaw become 8.261/8.840 deg |

The fixed-axis X/Y coupling grids did not produce an intersection. For the
3.591-degree pelvis-roll candidate, pitch coupling from -1.0 through +1.0 did
not reduce the 4.491-degree chest-pitch envelope; yaw coupling sufficient to
reduce it violated pelvis yaw and/or chest roll. Tail-relative yaw also moved
by substantially more than the allowed 0.25 degree when pelvis roll passed.

## Successful executable portion

The three-layer canonical pipeline executes in the mandated order. At scale
0.5 the numeric bilateral leg solve restored the V8.2 foot world transforms
to approximately `1e-15 m` translation error and `5.5e-6 deg` orientation
error, with sub-millimetre pivot compensation in the world-basis variant.
Untouched toe local tracks therefore retain the approved rocker/passive/
receiving parent-space behavior. Neck distribution remained below `0.382 deg`
and restored head world orientation to numerical precision.

These results do not override the failed upper-body gates and are not release
evidence.

## Required contract-owner decision

One of the following must be explicitly authorized before implementation can
continue:

1. permit a declared upper-spine counter-compensation channel in
   `chest_tail_head_stabilization@1` while keeping the chest and tail bones'
   own local tracks exact; or
2. replace the tight component-wise chest/tail world-relative envelopes with
   a conjugation-invariant metric appropriate to frozen descendant locals; or
3. reduce the required pelvis world-roll progression.

Option 1 is the smallest biomechanical implementation change, but the current
contract says the final layer may use only neck/head compensation and cannot
reopen chest/tail solving. The repository constitution forbids changing that
ownership or weakening the evaluator merely to obtain PASS.

## Preserved boundaries

- no stable-channel state/history change;
- no V8.2 artifact/profile byte change;
- no selected V8.3 artifact or visual media claim;
- no technical or visual self-approval;
- no signed release commit from a failing candidate.
