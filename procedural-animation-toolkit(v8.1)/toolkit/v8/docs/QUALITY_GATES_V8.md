# V8 Quality Gates

## Structural

- 75 skin joints preserved.
- All semantic tags resolve.
- No duplicate animation names.
- Every channel targets an existing node.
- Timelines are finite and strictly increasing.
- Root and pelvis translation channels are preserved where required.
- Authored transition endpoints match source and target exactly.

## Contact and anatomy

- Final pelvis transform is established before leg IK.
- No post-solve balance translation.
- Signed knee and ankle branches remain anatomical.
- Selected sole vertices stay within penetration and hover tolerances.
- At least one foot remains support-capable during grounded attacks.

## Turn expression

- Authored skull lead ≥ 12°.
- Authored neck lead ≥ 7°.
- Tail counter target ≥ 4°.
- Attention lead begins before half the root heading change.
- Baked world-space skull/neck/chest/tail relationships are measured after export.

## Power attack

- pelvis preload back ≥ 8.5% hip height;
- pelvis preload down ≥ 5.5% hip height;
- persistent root delivery ≥ 22% hip height;
- two sequential catch-step schedules present;
- additive jaw gape ≤ 1.5° at contact;
- additive jaw gape ≤ 1.5° at recovery;
- head/tear expression ≥ 4°;
- zero anatomical reversals;
- no selected-sole penetration beyond gate.

## Feeding

- at least three distinct bite events;
- alternating tear direction and unequal strength;
- head-yaw span ≥ 6°;
- pelvis lowering ≥ 5.5% hip height;
- late gape and contact closure;
- clamped pull before chew;
- exact full-loop closure;
- zero anatomical reversals;
- stable planted feet.

## Perceptual review

Automation does not certify final realism. Review at fixed side, three-quarter, front, rear, and overhead cameras for:

- intent readability;
- force propagation;
- skull/neck silhouette;
- jaw contact timing;
- support changes;
- tail damping;
- foot deformation;
- transition artifacts;
- behavior under the game camera.
