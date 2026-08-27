# Migrating a v1 creature to v2

1. Keep the original fully rigged GLB unchanged.
2. Reuse the semantic YAML; add any missing toe branches, jaw root, full spine/neck, and tail chain roles.
3. Run the v2 generator with the default family profile.
4. Calibrate `neutral_jaw_close_deg` independently from locomotion.
5. Resolve cadence and stride before tuning body amplitude.
6. Tune swing lift, duty factor, and contact lead while watching side view.
7. Tune support shift and pelvis roll while watching front view.
8. Tune torso/head compensation and tail dynamics only after contacts are credible.
9. Compare v1 and v2 in the same cameras at 1×, 0.5×, and frame stepping.
10. Promote only after numeric gates and perceptual reviewers agree.

The semantic map remains the stable contract. Do not rewrite the family kernel for ordinary species differences; create a new profile.
