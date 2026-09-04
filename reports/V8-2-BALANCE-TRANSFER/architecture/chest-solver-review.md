# Candidate-A chest solver adversarial review

## Verdict

The constraints are feasible without changing the frozen pelvis or any
lower-body channel. A bounded numeric solve over the six spine rotations can
meet the official chest roll, pitch, yaw, and counterphase gates. The current
failure is not an overconstraint; it is a representation mismatch.

The current analytic pass authors a roll in an intrinsic-Euler representation,
then the official evaluator measures components of
`Log(R_chest_world * R_pelvis_world.T)`. Finite rotations do not commute, so an
Euler-only roll changes all three components of the evaluator's rotation
vector. That is why the current artifact reaches roll `5.407666 deg` while
pitch falls from `4.102972` to `3.445999 deg` and yaw from `2.612021` to
`2.167328 deg`.

Solve in the evaluator's relative rotation-vector basis, then reconstruct the
six local spine quaternions hierarchy-first. Do not add independent Euler
pitch/yaw patches after the roll.

## Reviewed inputs

- Approved iteration-38 source:
  `procedural-animation-toolkit(v8.1)/approved_snapshots/v8.1-walk-iteration-38/asset/tarbosaurus_procedural_v8_1_walk_iteration_38.glb`
- Current analytic candidate:
  `candidates/v8.2-balance-transfer/generated/iteration-c-official-relative-fixed/tarbosaurus_v8_2_balance_transfer.glb`
- Official metric implementation:
  `reports/V8-2-BALANCE-TRANSFER/evaluation/tools/evaluate_balance.py`, in
  particular `rotation_vector`, `analyze`, and
  `candidate_a_upper_only_gate`.
- Candidate overlay implementation:
  `candidates/v8.2-balance-transfer/scripts/generate_balance_overlay.py`.

The official in-place measurements are:

| Metric | Approved | Current | Gate |
| --- | ---: | ---: | --- |
| Chest relative pitch P2P | 4.102972 | 3.445999 | within 0.2 of approved |
| Chest relative yaw P2P | 2.612021 | 2.167328 | >= approved |
| Chest relative roll P2P | 4.673977 | 5.407666 | 5.4-6.25 |
| Roll/pelvis-roll correlation | -.828681 | -.891371 | -.95 to -.70 |
| Head world P2P pitch/yaw/roll | n/a | 2.580082 / 1.528826 / .966140 | <= 2.9 / 2.1 / 1.2 |

Pelvis, protected lower-leg channels, head caps, tail gates, and seam already
pass in the current candidate.

## Feasibility experiment

I performed a read-only 120-phase numerical experiment using the official
evaluator's own pose traversal and rotation-vector convention. No GLB or
implementation file was written.

For each phase, let:

```text
v0(phi) = Log(R_current_chest_world(phi) * R_frozen_pelvis_world(phi)^T)
vb(phi) = equivalent approved iteration-38 vector
```

Fit the pitch and yaw differences `vb - v0` to a periodic two-harmonic basis:

```text
[1, sin(2pi phi), cos(2pi phi), sin(4pi phi), cos(4pi phi)]
```

Then use only three bounded solve variables:

```text
v_target.x = v0.x + s_pitch * fit2(vb.x - v0.x)
v_target.y = v0.y + s_yaw   * fit2(vb.y - v0.y)
v_target.z = mean(v0.z) + (v0.z - mean(v0.z)) * A_roll / P2P(v0.z)
```

A deterministic grid/coordinate solve found the following existence witness:

| Variable | Value |
| --- | ---: |
| `s_pitch` | .8799 |
| `s_yaw` | 1.6154 |
| `A_roll` | 5.6000 deg |

The resulting official-basis target envelopes before float32 export are:

| Metric | Target | Gate margin |
| --- | ---: | --- |
| Pitch P2P | 4.102957 deg | .000015 deg from approved; allowed .2 |
| Yaw P2P | 2.612025 deg | +.000003 deg over approved |
| Roll P2P | 5.600000 deg | .20 above lower and .65 below upper bound |
| Roll correlation | -.891371 | unchanged and inside gate |

The maximum current-to-target chest-world correction was `1.153503 deg`
(`.670168 deg` RMS). With the existing spine weights distributed cumulatively
as `[.08, .19, .33, .51, .73, 1.0]`, the largest incremental share is about
`.311446 deg` before hierarchy reconstruction.

A hierarchy reconstruction at the same 120 phases, measured against the
approved source local quaternions, produced these maxima:

- maximum spine local delta: `.249310 deg` (`Bone_002`);
- maximum neck local delta while cancelling the chest change: `.310745 deg`;
- head local delta: `.123476 deg`, effectively the already-approved overlay;
- head world target error by construction: zero before float32 export;
- tail change: zero by construction because tail is a pelvis sibling, not a
  chest descendant.

These are comfortably inside the existing 1.0-degree spine and .75-degree
neck local bounds. This experiment proves feasibility but is not an exported
candidate or a release verdict; the final GLB must be measured again by the
official evaluator.

## Recommended bounded solver

### 1. Optimize a smooth chest-relative target, not 245 independent keys

Use the three-variable construction above, or equivalently optimize the
coefficients of at most two periodic harmonics. Do not expose one variable per
frame. Per-frame optimization would satisfy peak-to-peak metrics too easily
while permitting jitter, extrema swapping, and non-reproducible overfit.

A dependency-free deterministic coordinate search is sufficient:

1. evaluate a fixed coarse grid over `s_pitch`, `s_yaw`, and `A_roll`;
2. retain feasible points;
3. refine around the lowest-cost point with fixed step sizes;
4. break ties lexicographically and record the complete search bounds/steps.

Suggested search box:

```text
s_pitch in [0.70, 1.10]
s_yaw   in [1.40, 1.90]
A_roll  in [5.50, 5.90] degrees
```

Minimize the integrated squared geodesic change from the current candidate,
plus a small second-derivative penalty on the target curve. Treat all gates as
hard constraints, not weighted penalties.

### 2. Use robust internal targets

Do not optimize to the exact gate edge. Require internally:

- chest pitch P2P in `[4.00, 4.20] deg`;
- chest yaw P2P in `[2.66, 2.90] deg` (at least `.048 deg` official margin);
- chest roll P2P in `[5.55, 5.90] deg`;
- roll correlation in `[-.93, -.75]`;
- maximum phase-sample chest-world correction <= `1.25 deg`;
- zero-mean pitch/yaw correction within `.01 deg` so neutral posture does not
  drift.

The numerical witness used yaw almost exactly on its public lower edge only to
prove feasibility. The implementation should choose the robust yaw interval
above.

### 3. Reconstruct the spine hierarchy safely

For each baked key, build the official-basis target directly:

```text
R_relative_target = Exp(radians(v_target))
R_chest_target = R_relative_target * R_pelvis_frozen
D = R_chest_target * inverse(R_chest_current)
```

For the six bones `Bone_007 -> ... -> Bone_002`, assign desired world rotations
using cumulative fractions `c = [.08, .19, .33, .51, .73, 1.0]`:

```text
R_world_target[i] = Power(D, c[i]) * R_world_current[i]
R_local_target[i] = inverse(R_world_target[parent(i)]) * R_world_target[i]
```

Use the already-updated target parent. This reaches the exact chest target and
spreads the correction smoothly. Enforce quaternion sign continuity and exact
first/last loop equality after reconstruction.

### 4. Preserve the current head result with deterministic neck cancellation

Tail channels need no compensation and must remain byte-identical to the
current passing tail overlay.

The head is a chest descendant, so leaving neck locals untouched would change
head-world motion. Cancel the new chest delta gradually through the existing
five-neck chain, using cumulative cancellation fractions
`[.11, .26, .45, .69, 1.0]`. At the final neck bone, restore the pre-solver
world rotation exactly; retain the current candidate's head world target and
reconstruct `Bone_036` locally from that parent.

This is not a second optimization. It is a deterministic inverse hierarchy
step. It keeps the current passing head envelope while distributing the local
countertransform within the neck bound.

## Hard safety constraints

The solver must fail closed unless all of the following pass on both walk
clips after float32 export:

1. Source SHA and changed-accessor allowlist remain exact.
2. Root, pelvis, every lower-body rotation/translation, all foot pivot and toe
   channels, and all non-walk data remain byte-identical.
3. Tail rotation accessors are byte-identical to the current passing analytic
   candidate, or their official metrics and local arrays are separately
   re-approved; the chest solver itself has no authority to touch them.
4. Spine local delta from approved iteration 38 <= `1.0 deg` per bone and
   chest-world correction from the current candidate <= `1.25 deg`.
5. Neck local delta from approved <= `.75 deg`; head local delta remains <=
   `1.0 deg`; head world rotation differs from the pre-solver candidate by <=
   `.01 deg` at every baked key and still passes `2.9/2.1/1.2 deg` envelopes.
6. Official chest internal margins above pass, plus the public Candidate-A
   gate.
7. First/last local quaternion equality is exact; no quaternion sign flips;
   existing angular velocity/acceleration limits pass. Also cap the correction
   layer itself at `60 deg/s` and `600 deg/s^2` per spine/neck bone so a smooth
   base animation cannot conceal a noisy overlay.
8. Root-motion and in-place allowed rotation arrays remain identical.
9. Iteration-38 world-matrix, skinned-contact, stride, rocker, toe dwell,
   passive-lag, and support inheritance gates remain unchanged.

## Adversarial cautions

- Do not optimize only the three peak-to-peak scalars. Include correlation,
  curve smoothness, seam, local bounds, and head preservation as hard checks;
  otherwise the optimizer can move extrema to isolated keys.
- Do not use Euler angles anywhere in the objective or reconstruction. Euler
  values may be logged as diagnostics only.
- Do not clip individual quaternion samples after solving. If a bound is hit,
  reject the candidate or reduce the global solve variables and rerun.
- Measure after float32 GLB export with the frozen official evaluator. An
  in-memory result is only a feasibility witness.
- Keep the analytic/current candidate immutable as the comparison input. Write
  a new iteration directory for the optimized candidate.

## Conclusion

Proceed with a bounded, two-harmonic rotation-vector solve. There is ample
geometric headroom: the feasibility witness satisfies the official chest
envelopes with only a `1.1535 deg` maximum chest-world correction, while the
distributed local spine and compensating neck deltas remain below `.32 deg`
in the 120-phase test. The exact pelvis/lower-body freeze does not need to be
relaxed.
