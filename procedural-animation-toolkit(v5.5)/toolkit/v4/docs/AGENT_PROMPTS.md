# Agent Prompt Pack

## Implement a new large-theropod profile

You are extending Eonwild Procedural Animation V4. Preserve the complete source deformation skeleton and the GLB skin joint order. Do not create a reduced humanoid rig. Inspect the source hierarchy and create a semantic YAML map. Calibrate signed knee/ankle bend directions from rest geometry. Select sole witnesses from actual skin weights. Fit only cadence and distributed posture from reference video; do not claim calibrated motion capture. Generate relaxed walk, alert walk, start, stop, left/right turn, terrain walk, idle, eat, bite and roar plus transitions. Run every V4 quality gate and provide side/three-quarter/front browser validation. Fail closed on reverse hinges, missing tags, clip collisions or skin changes.

## Review locomotion

Review the generated animation as a biomechanics and browser-runtime reviewer. Check support transfer before swing, loaded sole stability, knee/ankle bend sign, toe-off continuity, swing clearance, horizon-oriented relaxed posture, head residual mass, muscular proximal tail and compliant distal tail. Inspect speed/stride/phase agreement. Reject fixes that merely increase keyframe count without correcting mechanics.

## Review actions

Check that bite, roar and eating are whole-body actions. Verify anticipation, commitment, contact/peak, recoil/release and recovery. Confirm the mouth is mostly closed in neutral locomotion and that action clips return to a valid living-neutral or locomotion state. Check direct browser transitions and priority handling.

## Runtime integration

Integrate the V4 GLB into Babylon. Use in-place locomotion, distance-driven phase and the supplied state graph. Advance the actor from simulation. Use runtime terrain queries only as residual corrections. Preserve explicit action priority and return-to-previous-state behavior. Add deterministic telemetry for state, clip, phase, contact events, speed, terrain correction and transition age.
