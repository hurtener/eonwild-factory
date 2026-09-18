# Sprint Bone_016 handoff residual decomposition

Status: `DIAGNOSTIC_COMPLETE`. The unchanged production handoff remains
`BLOCKED`; this read-only diagnostic does not approve it or change a source,
profile, evaluator, phase, amplitude, or gate.

## Bound inputs

- Package trio: `/Volumes/m2-extended-disk/Repos/eonwild-factory/out/continuation-native-clock-7920c59-pairs/sprint`
- Exact source snapshot: `c43d426ca8e5a2610c37ad7ae235ef623cb3f3fa`
- All three `inputs.lock.json` engine maps are identical: 88 entries, canonical
  JSON SHA-256 `7a7b6517d43faa06d8a0216625e510d6f3f83c2b8fe624ff8724fd622b9a9b44`.
- The detached diagnostic source matches all 88 entries. Package inputs were
  hashed before and after and remained byte-identical. Full hashes are in
  `result.json`.

The main checkout advanced while this analysis was running. The final run uses
the exact package-bound detached source at
`/private/tmp/eonwild-engine-c43d426`, rather than the newer main checkout.

## Exact reconstruction

`analyze.py` reconstructs the Bone_016 node origin from the package plan,
body-response receipt, source rest TRS, solver operation order, and performance
formula. Casting the reconstructed local TRS to float32 reproduces the emitted
join residual within `3.1e-11 m/s` in all four cases:

| interface | emitted root / in-place | reconstructed float32 root / in-place |
| --- | --- | --- |
| start | 1.412795 / 1.493701 mm/s | 1.412795 / 1.493701 mm/s |
| stop | 1.202134 / 1.199715 mm/s | 1.202134 / 1.199715 mm/s |

The float64 source reconstruction is 1.868176 mm/s at start and 1.680998 mm/s
at stop in both modes. Float32 timestamp/TRS serialization therefore changes
the estimate and currently reduces it by about 0.37-0.48 mm/s; it is not the
root cause of the threshold miss. Evaluating the same samples on their plan
clock still yields 1.671044 mm/s at start and 1.677702 mm/s at stop.

## Causal allocation

The order-independent, two-control Shapley allocation is on the float64
finite-window mismatch. Vector components do not add by norm.

| component | start | stop |
| --- | ---: | ---: |
| driven sagittal tail response | 1.230343 mm/s | 1.140529 mm/s |
| authored tail yaw | 0.215223 mm/s | 0.012376 mm/s |
| baseline root/pelvis/centering/static elevation | 0.815672 mm/s | 0.542359 mm/s |

At start, the baseline vector is composed of a 0.611136 mm/s root term, a
0.549956 mm/s pelvis term, a 0.079747 mm/s other-tail term, and negligible
nonlinear allocation interaction. At stop those norms are 0.023677, 0.527910,
and 0.014029 mm/s. Bone_002 chest contributes exactly zero to this node-origin
witness because it is not an ancestor of Bone_016. Bone_016's own rotation also
does not move its own origin; its tail ancestors do.

The source endpoint itself is consistent. After only the declared root travel
alignment, reconstructed Bone_016 positions differ by at most `5.4e-15 m`,
path-local rotations by at most `3.8e-14 degrees`, driven tail angles by at most
`4.5e-16 degrees`, pelvis height by at most `2.3e-16 m`, and declared pelvis
vertical velocity by at most `1.6e-15 m/s`. Both sides resolve the same
0.11666666666666667-second phase and gain 1. The transition envelope has zero
first derivative at the handoff. The steady and transition driven response use
the same continuous periodic lag at that phase, while performance yaw uses the
same phase/gain sine. No source-level endpoint state or first-derivative formula
disagreement was found.

The remaining estimator mismatch already exists in local native derivatives.
For the full response, the largest Bone_016-moving tail-ancestor angular
mismatch is 0.003276 degrees/s at start (Bone_018) and 0.003083 degrees/s at
stop (Bone_017). Root/pelvis local translation mismatch norms are 0.304245 /
0.270960 mm/s at start and 0.011787 / 0.262824 mm/s at stop. Those small local
errors accumulate along the long tail hierarchy.

## Chain-rule assessment

As a bounded diagnostic only, the script propagates the unchanged three-sample
local TRS derivative estimates through an endpoint FK Jacobian. It reports
1.882185 mm/s at start and 1.665404 mm/s at stop, effectively the same failing
scale as differentiating world positions. This is distinct from the previously
rejected five-point world polynomial, but it does not solve this mechanism:
the local derivative estimates already differ before FK. Replacing them with
analytic authored derivatives would cease to be an emitted-animation witness
and could miss a real serialized discontinuity.

The evidence supports one-sided finite-window truncation plus float32
clock/TRS quantization on a long nonlinear hierarchy, rather than an authored
tail-yaw discontinuity or a source endpoint mismatch. No new motion shaping or
evaluator change is justified by this diagnostic. Preserve the truthful
`BLOCKED` result.

## Reproduce

```sh
cd /Volumes/m2-extended-disk/Repos/eonwild-factory
.venv/bin/python /private/tmp/eonwild-sprint-posture-v5/out/sprint-tail-handoff-causal-001/analyze.py
```

The script fails closed if the package files mutate or if the detached source
does not match the complete package engine lock.

## Independent reproduction

Root reran a copied `analyze.py` in
`out/continuation-sprint-tail-causal-001`. The reproduced `result.json` is
byte-identical, SHA-256
`90ee2ac13f8e7b8c0e1bbfee922b8dc02872c52cf57179c97c16604735233633`.

The Linux sprint job `101903802453`, run `34175445729`, used the same historical
`c43d426` engine source and matched all four emitted residual values within
`4.7e-14 m/s`. This reproduction binds the diagnosis to that historical source
and package trio; it does not claim that a later or final integration head has
been compiled or validated.
