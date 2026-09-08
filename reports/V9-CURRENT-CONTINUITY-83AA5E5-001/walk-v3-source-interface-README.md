# Walk v3 source-interface probe

## Decision

Measurements are consistent with a shared continuous source trajectory at both
tested interfaces; no finite jump is resolved. After applying the factory's
documented constant root travel alignment, the start terminal, steady phase,
and stop initial source poses agree at the interface to floating-point noise.
Independently sampled same-phase neighborhoods also agree. The difference
between backward and forward first-order velocity estimates decreases with the
requested step size; the material witness falls from 15.2675 mm/s at 1 ms to
0.458080 mm/s at 30 microseconds. This is evidence of truncation over a curved
shared source trajectory, not a formal continuity theorem.

The smallest next motion stage supported by this result is a source-derived
tangent experiment: estimate local TRS tangents at every retained key with an
explicit converged one-sided/centered scheme and a numerical error bound, then
serialize those tangents through the existing CUBICSPLINE consumer and require
the exact serialized TRS plus FK/LBS join and loop checks. The estimate remains
numerical evidence; the serialized CUBICSPLINE derivative is the runtime
quantity. This result does not authorize copying an emitted boundary tangent,
fitting completed poses, relaxing the 1 mm/s gate, or declaring global C1.

The source-time skin-correction law is still a prerequisite for a refined
candidate. This probe deliberately evaluates the actual recipe inputs before
the current per-grid-row `target_offset_m` refinements. It therefore does not
show that a discrete correction table has a source-time derivative.

## Bound inputs and method

The driver ran on clean published source
`83aa5e5391848493c902af0c6bd4ecab6228afe6` and independently loaded:

- `heavy-biped.walk.v3`, recipe SHA-256
  `0e9c04f6e38d5d523cd354577ed82650846cf4edae3d1cddfacf76906530c783`;
- `heavy-biped.walk-start.v3`, recipe SHA-256
  `0d0be8f4012ada48fd38f5914def40937a8dc0d76713f8184b10b1022e9f50e9`;
- `heavy-biped.walk-stop.v3`, recipe SHA-256
  `72e96a8370486a86dda99734cd607e09163a67efdc6bdae478b350ef9c9e7204`.

All three bind source `044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6`,
rig `c3de770bf7dcc68219a28fb9851e9b75f3d3eebe2c2c0c7deb0078850100fd7e`,
contact profile `fef6279c1e7653ae6c7c485c3f934fd647410a726acb59393312b72af754a89f`,
performance v2 `ade6d37243d4b9597c9d2c15a86a667b5528654aca3998315abe7f2f06a968be`,
and gait v3 `d74b6a84a82fb013be3b5622356fa48e5a976c86c11beb327e15971887c108f0`.
The machine result records every path and digest, transition inputs, normalized
axes, recipe/sample identities, all rows used, solver witnesses, all 75
semantic-root descendants, and the ordered 1,564-left/1,417-right material
vertex correspondences.

The gait-owned interface is 0.3075 s, exactly 0.125 of the 2.46 s same-foot
cycle. At this phase the left foot is loaded and the right foot has just entered
swing; this is a loaded-support interface, not double support. The joins are:

- start time 7.9875 s to steady time 0.3075 s;
- steady time 0.3075 s to stop time 0 s.

For each join the before-side world joint and material points were translated by
`-forward * (before.root_forward_m - after.root_forward_m)`, exactly matching
the handoff verifier's root-travel alignment. No phase search occurred. At each
`h = 1e-3, 3e-4, 1e-4, 3e-5` seconds the driver compared the correct same-phase
source neighborhoods and separately compared the backward before-side with the
forward after-side velocity estimate. Local angular rates use shortest
sign-aligned quaternion logarithms.

## Measurements

| Join | exact joints | exact ordered material | exact local rotation |
|---|---:|---:|---:|
| start terminal -> steady phase | 2.667e-15 m | 3.622e-15 m | 3.768e-15 rad |
| steady phase -> stop initial | 1.493e-15 m | 2.356e-15 m | 6.243e-17 rad |

Same-phase offset poses remain equal within `6.061e-15 m` for joints and
`5.341e-15 m` for material on the start side. On the stop side, the maximum
same-phase joint difference decreases from `2.862e-11 m` at 1 ms to
`3.534e-15 m` at 30 microseconds; its approximately cubic decrease is consistent
with the transition envelope approaching the shared gait law smoothly.

The two joins produce the same rounded one-sided mismatch sequence:

| h (s) | max world-joint velocity difference (m/s) | max material velocity difference (m/s) | max local angular difference (rad/s) |
|---:|---:|---:|---:|
| 1e-3 | 0.02088264 | 0.01526753 | 0.04305590 |
| 3e-4 | 0.00634146 | 0.00458075 | 0.01302921 |
| 1e-4 | 0.00218650 | 0.00152693 | 0.00444931 |
| 3e-5 | 0.000525382 | 0.000458080 | 0.00114380 |

The joint and angular witness is `Bone_014`, the semantic right knee. The
material witness is ordered right-foot item 342, source vertex 41510. Both lie
on the just-unloaded right swing chain. The before/after estimates themselves,
row states, foot pitch/height/swing values, and branch witnesses are retained in
`result.json`. The approximately linear shrinkage with `h`, exact same-phase
pose agreement, zero articulation-envelope violation, and zero unreachable
extension distinguish local curvature/first-order truncation from a source-law
boundary jump in this bounded case.

Root independently applied a second-order one-sided formula to the same bound
builder, 75 joints, 2,981 ordered material rows, and four `h` values. At 1 ms,
both joins differed by at most `0.0135064 mm/s` for world joints and
`0.0138220 mm/s` for material. Across all requested `h`, the largest observed
world-joint estimate difference was `0.36507 mm/s` and the largest material
difference was `0.0138220 mm/s`, each below 1 mm/s. The smallest-step joint
sequence is non-monotonic, consistent with the finite pitch search's numerical
resolution, so these remain diagnostic estimates rather than derivative
authority or a technical pass. Agreement between the independent first- and
second-order probes supports testing source-derived serialized tangents; it
does not replace exact CUBICSPLINE/FK/LBS validation.

## Evidence

- `analyze.py` SHA-256
  `ca7545b46571ad46aa08a6adbfd034324d6c6a69f4fe2aa14649dab958f64738`
- `result.json` SHA-256
  `8fc1be56080aad3484c15f262005d42791a1b3fd768d01eb09c983a38d70486b`
- independent `root-source-quadratic-inputs-83aa5e5.py` SHA-256
  `ca7545b46571ad46aa08a6adbfd034324d6c6a69f4fe2aa14649dab958f64738`
- independent `root-source-quadratic-probe.py` SHA-256
  `efd720d26cf0879ecf67d3ae56d37a87d3b9d8128d12aa7047f34b3edbad393c`
- independent `root-source-quadratic-probe.json` SHA-256
  `9e78293ea8f9c17b770e96a44d8af55681c8fba183a1336216e8a03d2a4862a9`

Run from the repository root with the task SSD environment:

```sh
source /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/task-env.sh
PYTHONPATH=src uv run --frozen python /Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/audits/walk-v3-source-interface-001/analyze.py
```

This is a read-only source planner/FK/LBS diagnostic. It is not emitted
continuity evidence, derivative authority, refined-skin evidence, visual or
biological approval, or Unity validation.
