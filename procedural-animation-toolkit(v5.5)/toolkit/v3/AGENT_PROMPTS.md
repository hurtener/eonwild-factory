# V3 Agent Prompt Pack

## Implementation agent

```text
Implement Eonwild procedural animation V3 without modifying V1 or V2. Preserve every source deformation bone and the semantic YAML contract. Never add an 18-bone limit.

Treat knee and ankle anatomy as hard constraints. Derive each signed hinge direction from the source rest pose, enforce non-zero minimum flexion and bounded maximum flexion on every internal sample, and prefer small target error over an impossible bend. Keep lateral hip correction separate from the sagittal hinge solve. Use previous-sample continuity and bounded/backtracked solver steps.

Retain the 120 Hz solve, 60 Hz GLB bake, neutral jaw, support-aware pelvis, distributed torso/neck/head posture, and nine-segment tail. Make the Tarbosaurus profile a relaxed horizon-facing walk and soften only the distal tail; the root must remain muscular.

For every change, run unit tests, real-rig fixture validation, baked-GLB validation, and fixed-camera side/three-quarter review. Report signed joint ranges and exact frames of any acceleration spike. Do not approve from export success alone.
```

## Motion-review agent

```text
Review V3 at 1×, 0.5×, and frame stepping. Prioritize: anatomical knee/ankle direction, loading compression, extension through stance, rear-to-front swing recovery, pre-contact foot placement, pelvis anticipation, relaxed torso/head horizon, and proximal-versus-distal tail response.

Use timestamps. Classify each issue as contact planning, joint constraint, target reachability, body balance, posture, tail dynamics, jaw neutral pose, source weights, or camera illusion. Do not request generic “more movement”; identify the physical cause and the owning layer.
```

## Reference-analysis agent

```text
Analyze supplied motion references without pretending they are calibrated mocap. Separate measured file properties from visual inference. Estimate steady-walk intervals, cycle time, duty factor, stride-to-hip ratio, head/torso attitude, pelvis movement, and tail lag with confidence ranges. Ignore pose transitions and action fragments when fitting locomotion. Produce profile candidates; do not rewrite the family solver for species tuning.
```

## Validation agent

```text
Confirm source and generated node counts, skin joint order, inverse-bind matrices, animation names, valid channel targets, strictly increasing times, continuous quaternion signs, exact loop endpoints, root-motion distance, loaded contact error, toe-ground proxy error, signed knee/ankle ranges, zero hinge reversals, and minimum flexion margins. Reject any report that omits the anatomical series or hides unreachable targets.
```
