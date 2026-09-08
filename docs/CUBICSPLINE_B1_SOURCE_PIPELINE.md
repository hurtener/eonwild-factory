# B1 source pose-and-tangent pipeline boundary

B1 supplies interval math only. It does not enable CUBICSPLINE output or
change an emitter, recipe, threshold, or final technical status.

Its source math follows the [Khronos glTF 2.0 CUBICSPLINE
definition](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#appendix-c-spline-interpolation):
each key supplies in-tangent, value, and out-tangent, and an interpolated
rotation is normalized before it is applied. B1 converts that Hermite segment
to Bezier controls, bounds vector position and the quadratic derivative by
their control hulls, and subdivides quaternion controls until it can prove a
positive raw-norm lower bound. The reported quaternion rate is only the
conservative inequality `2 * max(|qdot|) / min(|q|)` for that normalized
polynomial; it does not call the path constant-speed SLERP. Rounding envelopes
are propagated with directed binary64 intervals through derived controls and
subdivision. The global quadratic derivative-control hull avoids rescaling
rounded controls by each leaf duration. The primitive fails closed on
nonfinite arithmetic, a divisor that crosses zero, or a depth/node budget.

`factory/compiler.py` builds the contact plan and dispatches either
`solve_airborne_gait` or `solve_with_skin_targets`. The steady grounded planner
already has `sample_grounded_gait(gait, time_s, body_height_m)`; transition
planning has `_Choreography.sample(time_s)` through `build_transition_plan`.
Today `solve_airborne_gait` consumes the resulting `plan["samples"]` in its
frame loop and returns serialized channel rows. `solve_with_skin_targets`
iterates a fresh constrained solve and material evaluation over those rows.

The next source interface must therefore be explicit:

```
evaluate_pose_at_phase(program, phase_or_time, source_bindings) ->
  local TRS, contact state, unwrapped root travel, solve convergence witness
differentiate_pose_at_phase(same arguments, declared side/step) ->
  local TRS tangent and convergence/branch witness
```

For grounded steady motion it calls `sample_grounded_gait` at an arbitrary
phase, then the same constrained pose solver used for emitted plan rows. For
start/stop it calls the transition choreography at the declared time; the
handoff endpoint delegates to the exact steady phase evaluator. This shares a
source value and tangent instead of copying a completed transition/steady GLB
pose. The periodic wrapper compares phase zero against phase plus one cycle,
while root travel remains unwrapped. Root motion uses planner travel/tangent;
in-place replaces only that channel with a constant value and zero tangent.

Tangent generation must be selected and recorded per solver version. Preferred
options are analytic derivatives of planner carriers plus differentiated IK
(analytic or AD). If the constrained IK cannot provide that, a source-only,
convergence-checked symmetric finite difference is acceptable only when both
offset solves select the same contact/IK branch, satisfy the same residual and
articulation conditions, and remain inside a declared phase/contact interval.
Near a lift, touchdown, support change, branch boundary, periodic wrap, or
skin-refinement correction discontinuity it must use the appropriate one-sided
source derivative or reject. It may never differentiate, fit, or copy a
finished GLB.

Skin refinement is a viability limit: its iterative offsets are defined on the
plan grid today. Before cubic emission it needs either a continuous
source-defined correction field with its own derivative/convergence witness or
a fail-closed refusal for refined behavior. The same applies to any IK branch
whose source residual or contact identity changes under the derivative probes.
Only after source tangents and continuous FK/LBS contact, clearance,
articulation, and rate authority are bound to the exact float32 export can the
existing full technical CUBICSPLINE guard be removed.
