# Connected walking checkpoint — iteration 16

Scope: idle → start → normal walk → faster walk → slow down → stop, on both admitted animals. Pause for user playback feedback at this checkpoint. No subsequent behaviors, Unity delivery, merge or push are included.

Approved normal-walk references remain Allosaurus iteration 14 and Tarbosaurus iteration 15 (quarter vertical body-control coefficients). The recipe under catalog/review-sequences records their controls. Neither prior GLB animation is an input to the new motion: poses are generated from admitted geometry, semantic rig data and the shared solver.

The sequence lasts 18.679456 seconds. Faster walking is an authored 1.35 cadence ratio with the same configured step length and grounded support choreography. Quintic cadence ramps integrate displacement continuously. Starts/stops use the existing integrated-support placement behavior. The approved body controls follow locomotion phase and activity, retaining the reduced Tarbosaurus vertical response. These remain engineering body-response controls, not a converged force simulation.

Material contact acquisitions are derived before body-control application and held during their support interval. Corrections run after body response. Each GLB has 1127 source keys (60 Hz plus stage joins); the saved GLB is reopened and its keys and interpolation midpoints measured. Source-key contact residuals do not substitute for saved playback checks.

The first pass exposed a shared transition defect: reduced-speed stance rolled into an unscaled full-speed swing heel angle. The second pass carries the push-off amplitude through lift-off and releases it smoothly. The normal walk retains a default release scale of one.

Focused verification: 40 passing tests covering stage continuity, integrated root speed, immobile stance placements, support availability, transition coordination, heel-release amplitude and rolling-plan binding. Production contact/dynamics acceptance, Unity parity and user approval of this sequence remain separate.

Final review packages: allo-sequence-b and tarbo-sequence-b. The earlier unsuffixed packages and interrupted render folders are superseded diagnostic attempts, not review baselines.
