# Iteration 38 / iteration 4 final technical review

Candidate-only review; no accepted V8.1 or candidate asset was edited. This is
evidence for user approval, not release acceptance.

## Verdict

- **P0: 0**
- **P1: 0**
- **P2: 2** — stale validator method wording, plus two glTF portability
  warnings.

## Identity and delivery

| item | SHA-256 | result |
| --- | --- | --- |
| iteration-38 GLB | `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e` | exact match |
| iteration-4 MP4 | `8ef3d2c571e2ee317a431a66f8a031fabe53936d6bf256e9c091a9071ef48a20` | exact match |

The iteration-4 directory contains exactly that MP4 and `render-run.json`.
It is H.264/yuv420p, 960x540, 24 fps, 240 frames, and 10.000 s. Iterations
15, 16, and 21 plus their media have explicit quarantine markers; iteration
21 is rejected for its early `.26230` causal lead and is not an approval input.

## Final-skinned mechanics

The final validator uses dense world-space skinned distal witnesses and a
preserved shin/pelvis rear-extension landmark, rather than the prior
pivot/origin proxy.

| side/cycle | skinned onset | shin/pelvis peak | lead | release lead | loaded keys |
| --- | ---:| ---:| ---:| ---:| ---:|
| L0 | .65711 | .75410 | .09698 | .03279 | 15 |
| L1 | .65814 | .75410 | .09596 | .03279 | 15 |
| R0 | .65558 | .75410 | .09852 | .03279 | 16 |
| R1 | .65455 | .75410 | .09954 | .03279 | 16 |

All four satisfy final-skinned onset-to-peak `.04–.10`, peak-to-first-passive
release >=`.02`, and 15–20 loaded 60 Hz keys. Toe-only dwell is `.11475`,
passive lag is eight baked keys, and receiving separation is actual
exported-channel onset `.85246`, later than the `.78–.85` passive window.

Across all complete dense witness groups: X <=`.001098 m`, Z <=`.007524 m`,
Y <=`.006440 m`, versus `.01375/.00825/.00825 m` limits; maximum adjacent
movement is `.000789 m`; metatarsal rise is `.03151–.04745 m` with zero >1 mm
reversals. Passive terminal toe-down runs are 8 left and 7 right consecutive
keys at <= -4 degrees. The right eighth key becomes -1.97 degrees only after
the required seven-key run, so the >=5-consecutive-key condition passes.

The exported homogeneous passive mechanism records `activeTarget: null` and
monotonically decreasing mechanical energy and linear speed for every cycle,
before later receiving preparation. This is a physical final-channel
correction, not a waived proxy.

## All-key, seam, scale, and immutability

Both walk clips have 245 measured/exported keys and 4.069565 s duration.
Selected sole penetration is 0 root-motion / 0.000170 m in-place; worst
support quantile is 0.002984 / 0.006212 m. All-key support and joint
continuity pass. In-place seam witness drift is zero with effectively zero
toe-root orientation difference; startup adjacent witness jump is 21.22 mm
left and 2.53 mm right, within the 25 mm two-pixel cap.

Reference stride is 2.59999997 m, speed 4.59999986 km/h, and world hip height
2.75636 m. The single explicit 12 m wrapper remains. Derived reach passes:
left 1.14175 >= 1.13902 m and right 1.21099 >= 1.20408 m.

The base report's absolute-reach and broad toe-patch proxy checks remain false.
They are superseded by stride-scaled reach plus final-skinned witness/release
proof; no physical constraint has been waived.

Generation records identical before/after accepted tree hashes and
`immutableUnchanged: true`; source GLB and canonical-profile hashes match.
Independent manifest verification reports 285/285 accepted V8.1 files
matching with zero mismatches. Raw tree hashes are cache-environment volatile.

## P2 follow-up

1. `respin-2-validation.json` still says “zero passive foot translation.”
   Iteration 38 intentionally uses an untargeted homogeneous decaying pivot
   translation (up to 0.07970 m) and validates energy/no-target behaviour.
   Update the method text before release-facing reuse.
2. `gltf-transform validate` has no errors but retains
   `MESH_PRIMITIVE_GENERATED_TANGENT_SPACE` and
   `NODE_SKINNED_MESH_NON_ROOT` warnings.

## Evidence

- `candidates/v8.1-walk-respin-2/generated/iteration-38/respin-2-validation.json`
- `candidates/v8.1-walk-respin-2/generated/iteration-38/base-validation.json`
- `candidates/v8.1-walk-respin-2/generated/iteration-38/generation-report.json`
- `candidates/v8.1-walk-respin-2/scripts/validate_walk_respin_2.py`
- `reports/V8-1-WALK-RESPIN-2/plan.md`
