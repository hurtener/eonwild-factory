# Migrating V2 Creatures to V3

1. Keep the V2 source and generated assets unchanged for regression comparison.
2. Reuse the same fully rigged GLB and semantic YAML map.
3. Run V3 once with a copied family profile.
4. Inspect the reported rest knee/ankle signs and flexion values for both sides.
5. Set conservative non-zero minimum flexion and species-appropriate maxima.
6. Validate that `anatomical_flip_count.knee` and `.ankle` are both zero.
7. Tune cadence, stride, stance fraction, and contact lead before posture.
8. Tune pelvis/chest/neck/head posture from fixed side-view references.
9. Tune tail root and tip separately; preserve a muscular root while allowing distal lag.
10. Re-run fixture, baked-GLB, half-speed, side, and three-quarter review before promotion.

## Parameter mapping

V2 contact, body, jaw, and tail concepts remain, but V3 adds:

```text
hip_extension_limit_deg
hip_flexion_limit_deg
hip_abduction_limit_deg
knee_min_flex_deg
knee_max_flex_deg
ankle_min_flex_deg
ankle_max_flex_deg
leg_preference_weight
leg_continuity_weight
anatomical_margin_deg
neck_relaxed_pitch_deg
head_horizon_pitch_deg
tail_phase_lag_seconds_per_bone
tail_dynamic_limit_root_deg
tail_dynamic_limit_tip_deg
```

## Promotion rule

Do not promote a V3 profile merely because it reaches foot targets. Anatomy has priority:

```text
zero hinge reversals
→ safe flexion margin
→ credible contacts
→ credible posture
→ credible tail/body mass
```
