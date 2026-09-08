# Phase-local solved-pose seam

`solve_airborne_plan_sample(AirborneSolveContext, row, body_response_sample=...)`
solves one already-built airborne or compatible override-plan row into local TRS
and skeletal foot/contact/articulation witnesses. The compiler still builds the
plan and body response first; `solve_airborne_gait` calls the row solver in the
existing plan order and retains the same float32 encoding and reopened checks.

This is not an arbitrary-time evaluation or source-tangent interface. A later
stage must still bind arbitrary time to `sample_airborne_gait` or the transition
choreography, pass the same source body/performance carrier at that time, and
record contact/IK branch convergence. Continuous skin refinement remains a
plan-grid iterative correction; it has no phase-local interpolation or
derivative witness here. No emitted GLB is read to construct this seam.

The context snapshots source topology, semantic roles and plan data into nested
read-only containers; its base TRS/world transforms and geometry arrays are
also detached and read-only. Each row starts from fresh local TRS lists and
returns its own witnesses. Its constructed context is
therefore suitable for testing phase/order independence, but it does not by
itself authorize CUBICSPLINE emission, tangents, float32 interval authority,
FK/LBS contact extrema, or any approval state.
