# V5 to V5.5: complete motion changes and V8.1 transfer guide

## Why this document exists

V5.5 was the body-balance correction pass built from V5. Its strongest result is the neutral/relaxed idle: one hind leg visibly supports the animal while the other rests forward, so the pose distributes weight instead of reading as a symmetric, nose-heavy crouch. Its walking also improved. The user reports that a separate V8 now has a stronger walk, but that V8 retains V5's uncorrected forward-leaning chest and idle stance. V6 was rejected.

When V8 is brought into this repository, the intended next step is therefore not to replace it with V5.5. It is to create V8.1, preserve V8 unchanged, selectively combine the strongest ideas, and compare V5.5, V8, and V8.1 under identical review conditions.

This document records what actually changed between the accepted V5 and V5.5 implementations. It also distinguishes:

- implemented code and profile facts;
- measured or visually reviewed outcomes;
- recommendations that remain unverified until V8 is available here.

V8 and V6 are not currently in this repository. Nothing in this document claims to have inspected their code or outputs.

## Executive summary

V5.5 was not a cosmetic layer placed on top of the V5 GLB. It changed the generation path and regenerated the constrained animation pack from the source model.

The central changes were:

1. The whole-body neutral orientation was made less forward-leaning through coordinated body, pelvis, neck, and head pitch changes.
2. Idle actions gained explicit foot placement and stable asymmetric load assignment.
3. Pelvis translation was exported in locomotion, in-place, idle, action, and transition clips.
4. Walking used a shorter stride, shorter stance, earlier forward placement, less hip extension, a longer/stronger toe-off, and slightly stronger continuity weighting.
5. Eating became a pelvis-led whole-body settle with wider fixed support and stronger tail counterbalance.
6. Bite attack gained an explicit rear/down brace before forward delivery, reduced head/neck reach, and delayed mouth preparation.
7. Transitions were rebuilt to preserve every translation channel, including the newly exported pelvis channel.
8. A later accepted V5.5 rig correction lowered both lower-foot pivots to 90% of the measured gap toward the three toe-root origins while preserving the undeformed mesh.

The apparent “higher chest” in V5.5 deserves a precise description: V5.5 did **not** add a direct chest-height translation. It reduced forward body lean and reoriented the pelvis, neck, and head. V8 reportedly retains the V5 values in this area, so V8.1 must deliberately port this V5.5 neutral-chain correction rather than assuming V8 already contains it.

## Release boundaries

| Release | Commit | Role |
| --- | --- | --- |
| V5 | `b04259d` and earlier V5 history | Frozen baseline used for comparison. |
| Initial V5.5 body-balance release | `c055c66` | Full constrained regeneration, posture/idle/walk/action corrections, pelvis translation, transition rebuild, and review page. |
| Accepted V5.5 lower-foot calibration | `e04c6a3` | Promoted the stronger Test 2 pivot position and regenerated the canonical GLB/media. |

The V5 tracked-entry hash remained unchanged throughout V5.5 work.

## Generation-path change

### V5

V5 starts from the already-generated and validated V4 animation pack. `upgrade_v4_pack_to_v5.py` preserves the V4 leg/contact tracks and adds V5 jaw calibration, secondary quaternion polish, clip renaming, and transitions.

### V5.5

V5.5 starts again from `inputs/tarbosaurus_source.glb` and runs the complete constrained pipeline with `tarbosaurus-v5.5.json`. Only after that solve does it apply the V5-style jaw calibration/polish, rebuild transitions, calibrate the lower-foot pivots, and package the V5.5 GLB.

The V5.5 build fails if the constrained source report is absent or its automated quality gates did not pass. This distinction matters for V8.1: body-balance settings that affect foot placement, pelvis position, or leg constraints should be introduced before or during the solve, not as post-bake rotations.

## Every release-profile value changed

The table below compares the profile actually used by V5 (`tarbosaurus-v4.json`) with the profile actually used by V5.5 (`tarbosaurus-v5.5.json`). Fractions described as “hip” are normalized by reference hip height; stride-relative values are normalized by stride.

| Area | Parameter | V5 | V5.5 | Intended effect |
| --- | --- | ---: | ---: | --- |
| Identity | `name` | `tarbosaurus_reference_fitted_v4` | `tarbosaurus_balance_corrected_v5_5` | Explicit independent iteration lane. |
| Walk | `stride_length_m` | 2.05 | 1.90 | Shorter spatial reach. |
| Walk | `stance_fraction` | 0.72 | 0.70 | Ends rear stance sooner. |
| Walk | `contact_lead_stride` | 0.36 | 0.40 | Places the next contact farther forward relative to the shorter stride. |
| Walk | `toe_off_window_fraction` | 0.20 | 0.24 | Gives foot roll and toe push more time. |
| Neutral | `body_lean_deg` | -2.8 | -1.0 | Reduces whole-body forward pitch; principal source of the higher-chest reading. |
| Neutral | `pelvis_neutral_pitch_deg` | -0.35 | -1.10 | Rebalances the pelvis as the torso is brought closer to level. |
| Neutral | `neck_relaxed_pitch_deg` | -1.35 | -0.60 | Reduces relaxed neck compensation. |
| Neutral | `head_horizon_pitch_deg` | -0.45 | +0.35 | Brings the skull closer to a horizon-facing attitude. |
| Leg | `hip_extension_limit_deg` | 34.0 | 31.0 | Bounds trailing-leg extension. |
| Leg | `leg_continuity_weight` | 0.22 | 0.24 | Slightly favors continuity between consecutive leg solves. |
| Foot | `toe_off_foot_deg` | 9.0 | 12.0 | Stronger metatarsal/foot roll during release. |
| Foot | `contact_foot_deg` | 2.2 | 2.4 | Small change to the planted-foot contact attitude. |
| Foot | `toe_push_deg` | 10.5 | 14.0 | Stronger late-stance toe articulation. |
| Swing | `swing_advance_end_fraction` | 0.93 | 0.91 | Finishes forward swing placement earlier before contact. |
| Eating | `eating_body_lower_deg` | 6.5 | 5.0 | Reduces torso-only folding. |
| Eating | `eating_neck_lower_deg` | 24.0 | 20.0 | Reduces neck-only reach. |
| Eating | `eating_head_lower_deg` | 14.0 | 10.0 | Reduces head-only reach. |
| Eating | `eating_pelvis_back_hip_fraction` | 0.035 | 0.075 | Moves the pelvis farther back as the body settles. |
| Eating | `eating_knee_flex_deg` | 5.0 | 9.0 | Records the desired stronger hind-leg flexion. See the implementation caveat below. |
| Bite | `bite_anticipation_fraction` | 0.28 | 0.36 | Makes more time for the brace before contact. |
| Bite | `bite_lunge_hip_fraction` | 0.30 | 0.20 | Reduces forward reach/overextension. |
| Bite | `bite_body_crouch_deg` | 6.0 | 5.5 | Reduces torso-led crouch while the pelvis supplies the load. |
| Bite | `bite_rear_load_hip_fraction` | absent | 0.10 | Adds explicit backward preload. |
| Bite | `bite_neck_thrust_deg` | 16.0 | 11.0 | Reduces head/neck-led delivery. |
| Rig | `foot_pivot_gap_fraction` | absent | 0.90 | Lowers each foot pivot toward its own toe-root plane. |

### Profile caveats

- The JSON profile above is release truth. Some dataclass fallback defaults in `eonproc_v4/profile.py` use intermediate values—for example `bite_body_crouch_deg = 3.5`, `bite_rear_load_hip_fraction = 0.075`, and `leg_continuity_weight = 0.28`. The committed V5.5 build loads the JSON values `5.5`, `0.10`, and `0.24`. A V8.1 port should copy intentional resolved values into its own explicit profile rather than relying on defaults.
- `eating_knee_flex_deg` was raised to 9.0 in the profile, but the current V5.5 `ActionGenerator` does not directly read that parameter. The visible eating leg compression comes from pelvis translation, fixed-foot targets, load assignment, and the constrained leg solve. V8.1 should either remove this dead parameter or wire it deliberately; it should not assume the number alone changes the animation.

## Neutral posture and chest attitude

V5.5 changed the neutral chain as a coordinated set:

- body lean: -2.8° to -1.0°;
- pelvis neutral pitch: -0.35° to -1.10°;
- relaxed neck pitch: -1.35° to -0.60°;
- head horizon pitch: -0.45° to +0.35°.

The result is a slightly more level torso and head, not a translated chest control. The measured median torso-pitch change is modest—about 0.19° closer to level in idle—but the neck/head compensation and asymmetric legs make the complete silhouette read less front-heavy.

For V8.1, begin by porting the complete V5.5 neutral chain—body lean, pelvis neutral pitch, relaxed neck pitch, and head horizon pitch—into the V8 solver. Then retune only if V8's walking implementation requires clip-specific separation between locomotion and idle. The chest correction must not be omitted merely because V8 walking is stronger.

## Idle stance: the V5.5 behavior most worth preserving

V5 idle alternated load approximately symmetrically:

- left load: `0.50 + 0.18 × sin(cycle)`;
- right load: `0.50 - 0.18 × sin(cycle)`;
- both fixed-foot targets remained at their rest positions.

V5.5 relaxed idle establishes stable, different jobs for the two legs:

- left/support load: `0.66 + 0.035 × sin(cycle)`;
- right/resting load: `0.34 - 0.035 × sin(cycle)`;
- left foot offset: 3.0% of hip height backward;
- right foot offset: 32.0% of hip height forward.

The support role no longer swaps every half-cycle. The small sinusoidal variation keeps the pose alive without erasing the weight assignment.

Alert idle also gained a smaller stagger:

- left foot: 2.5% of hip height backward;
- right foot: 12.0% of hip height forward.

Its previous load oscillation remains, so relaxed idle is the cleaner reference for V8.1.

Measured relaxed-idle differences:

| Metric | V5 | V5.5 |
| --- | ---: | ---: |
| Median torso pitch | -12.005° | -11.812° |
| Median head pitch | 15.307° | 14.095° |
| Median fore/aft foot spread | 0.0256 hip heights | 0.4089 hip heights |

The foot spread is the dominant measurable change. For V8.1, port the idle support arrangement as one coherent unit: foot targets, stable load bias, neutral pelvis/body attitude, and exported pelvis translation. Copying only the forward foot offset risks producing an unweighted split stance.

## Walking changes

### Spatial and temporal changes

- Stride length decreased 7.3%, from 2.05 m to 1.90 m.
- Stance decreased from 72% to 70% of the cycle.
- Contact lead increased from 36% to 40% of stride, helping the swing foot arrive in front despite the shorter total stride.
- Hip extension was capped at 31° instead of 34°.
- Swing advance finishes at 91% instead of 93% of swing.

### Foot and toe relationship

- Toe-off window increased from 20% to 24% of the cycle.
- Foot roll at toe-off increased from 9° to 12°.
- Toe push increased from 10.5° to 14°.
- Contact foot angle increased slightly from 2.2° to 2.4°.

The intended sequence is support through a flexed leg, metatarsal/foot roll, toe-last release, hip-led recovery, knee fold, ankle follow, then forward placement. The locomotion implementation also documents the staggered knee/ankle release rather than folding every joint simultaneously, although the release equations themselves were already present in V5.

### Continuity and output

- The release profile raises leg continuity weighting from 0.22 to 0.24.
- Pelvis translation is captured and exported alongside root translation.
- In-place clips retain pelvis translation even though root locomotion is removed.
- Loop endpoints explicitly close the pelvis translation channel.

Measured relaxed-walk differences:

| Metric | V5 | V5.5 |
| --- | ---: | ---: |
| Maximum rear ankle reach | -0.3791 hip heights | -0.3378 hip heights |
| Reduction in rear ankle reach magnitude | — | 10.9% |
| Median fore/aft foot spread | 0.3451 hip heights | 0.3468 hip heights |
| Median torso pitch | -12.050° | -11.854° |
| Median head pitch | 14.904° | 13.691° |

The ankle is the cross-rig landmark for rear-leg overextension. The foot-bone origin changed later during pivot calibration and is therefore not a stable V5/V5.5 gait landmark.

Because V8 is reported to have the better walk, V8.1 should not wholesale replace its locomotion profile with these V5.5 numbers. Instead, use this list to identify which ideas V8 already contains and test only missing relationships.

## Eating changes

V5 used a nearly constant pelvis-back/down pose while assigning large angles to body, neck, and head lowering. V5.5 changed the action to a loop-safe whole-body settle:

- settle envelope: `0.55 + 0.45 × (0.5 - 0.5 × cos(cycle))`;
- pelvis moves backward using the 7.5% hip-height profile value scaled by the settle envelope;
- pelvis moves downward by up to 11.0% of hip height, also scaled by settle;
- pelvis pitch changes with the settle rather than staying at a constant positive pitch;
- body, neck, and head contributions were reduced;
- tail downward counterbalance increased from 3.5° to 7.5° at full settle;
- left foot is placed 3% of hip height backward;
- right foot is placed 14% of hip height forward;
- the feet stay fixed while the constrained solver flexes the legs under the moving pelvis.

Measured outcomes:

| Metric | V5 | V5.5 |
| --- | ---: | ---: |
| Median torso pitch | -15.817° | -11.280° |
| Median fore/aft foot spread | 0.0257 hip heights | 0.2064 hip heights |
| V5.5 pelvis vertical excursion | — | 0.0495 hip heights |

This makes feeding body-supported rather than merely neck-led. It remains a qualitative animation hypothesis because the reference camera changes during the eating section.

## Bite/attack changes

V5.5 made the first readable event a rear/down body brace rather than mouth/head extension.

- Anticipation lasts to 36% instead of 28% of the clip.
- A new brace envelope drives the pelvis backward by up to 10% of hip height.
- The pelvis drops by up to 8.2% of hip height during the brace, plus a smaller lunge drop.
- Root motion includes the same rear load, followed by a bounded 20% forward drive instead of the former 30% lunge.
- Pelvis pitch, spine pitch, load bias, and tail pitch participate in the brace.
- The stance is staggered: left foot 4% of hip height backward, right foot 16% forward.
- Neck thrust decreased from 16° to 11°; head lunge pitch decreased from 5° to 3°.
- The underlying action layer delays jaw preparation until 48% of the anticipation interval, rather than opening from the first anticipation frame.
- The final calibrated V5.5 jaw replacement is slightly stricter: with anticipation ending at 36% of the clip, it holds the mouth closed until 18% of the clip—exactly halfway through anticipation—so the body preload is established first.

Measured V5.5 attack outcomes:

| Metric | V5.5 |
| --- | ---: |
| Rear preload | -0.1000 hip heights |
| Forward drive | +0.2000 hip heights |
| Maximum pelvis drop | -0.0820 hip heights |
| Ordering | preload before drive |

The source reference includes a multi-step charge. V5.5 remains a bounded one-shot bite and only adopts the rear-load/drive ordering.

## Pelvis translation and transitions

V5.5 exports pelvis translation in:

- root-motion locomotion;
- in-place locomotion;
- relaxed and alert idle;
- eating, bite, roar, and other generated actions;
- authored transitions.

The transition system was updated in two places:

1. Pose transitions now handle translation channels missing from one endpoint by holding the available endpoint value instead of assuming both clips contain the same channel.
2. Phase-matched loop transitions now blend every translation channel, not only a constant root track.

All 16 transitions still land exactly on the next clip. Final validation measured approximately `9.57e-15°` maximum rotational endpoint error and zero positional endpoint error.

Any V8.1 player or exporter must retain these pelvis translations. If a runtime strips the pelvis channel or applies an extra crossfade after an authored transition, the body-balance work will not survive playback.

## Lower-foot pivot calibration added after the initial V5.5 pass

The accepted Test 2 placement moves each lower-foot pivot 90% of the vertical gap from its original position toward the centroid plane of that foot’s three toe-root joints.

It is a profile calibration, not a fixed coordinate:

- left movement: 0.104443 m downward;
- right movement: 0.104443 m downward;
- remaining vertical gap: approximately 0.011605 m;
- toe-root origins remain fixed;
- only the two intended inverse-bind entries change;
- undeformed skinned-mesh maximum error: `2.24e-8 m`.

The builder counter-translates the toe-root children and updates the affected inverse bind so the rest mesh remains visually identical. The benefit appears during deformation.

For V8.1, this calibration can only be reused directly if V8 uses the same mesh, skeleton hierarchy, toe mappings, and skin. Otherwise rerun the measurement against V8’s own rig; do not copy world coordinates or inverse-bind matrices.

## What V5.5 intentionally kept

- The same Tarbosaurus source mesh, materials, and texture payload.
- The 75-joint skin order.
- The 37-clip catalog, including 16 authored transitions.
- V5 living-neutral jaw calibration.
- V5 action-specific jaw tracks, after correcting the early bite opening.
- Protected contact-bone behavior during secondary quaternion polish.
- Existing sole, terrain, anatomical-direction, velocity, and acceleration quality gates.
- Babylon/browser runtime contracts and exact transition handoff behavior.

## Changes that are evidence/tooling rather than motion

V5.5 also added a separate reproducible package, V5 immutability checks, V5.5-specific tests, release validation, profile/build reports, package inventories/checksums, Blender rendering scripts, and an offline review site with 21 stills and four primary films.

These additions do not change the animal’s motion, but they should be reused for V8/V8.1 because they make comparisons repeatable. The procedural solver remains CPU-based. Blender uses Metal for rendering; an MPS solver port was rejected for this release because the workload is serial, small-matrix, deterministic NumPy/SciPy work.

## Recommended V8.1 merge strategy

### Preserve V8 first

1. Import V8 into its own immutable directory and record its full tracked-entry hash.
2. Duplicate V8 into V8.1 before changing any code, profile, GLB, or media.
3. Give V8.1 independent clip names, manifests, reports, and showcase paths.
4. Do not “upgrade” V8 in place.

### Port in this order

1. **Idle support arrangement:** port the V5.5 stable load split and staggered foot targets as a coherent idle-only feature.
2. **Neutral-chain/chest correction:** port V5.5's coordinated body lean, pelvis pitch, neck pitch, and head-horizon values because V8 still has the V5 chest attitude. Apply them inside the V8.1 solve, not as post-bake rotations.
3. **Pelvis translation contract:** ensure V8.1 exports and plays pelvis translation in idle, locomotion, actions, and transitions.
4. **Lower-foot pivot:** adopt the 90% measured rule only after proving rig/skin compatibility.
5. **Walk relationships:** keep V8 walking as the baseline. Test individual V5.5 ideas only if V8 lacks bounded rear extension, toe-last release, or hip-led recovery.
6. **Attack/eating:** evaluate separately; do not let those action changes delay the idle/walk comparison.

### Minimum first V8.1 candidate

The first comparison candidate should be intentionally narrow:

- begin from an untouched copy of V8;
- keep V8's walking timing, stride, foot-cycle, and leg-solver changes;
- change the neutral chain to V5.5's resolved values: body lean `-1.0°`, pelvis neutral pitch `-1.10°`, relaxed neck pitch `-0.60°`, and head horizon pitch `+0.35°`;
- change relaxed idle to the V5.5 support assignment: left load `0.66 + 0.035 × sin(cycle)`, right load `0.34 - 0.035 × sin(cycle)`, left foot `-0.030` hip heights, and right foot `+0.320` hip heights;
- preserve/export pelvis translation;
- apply the 90% measured lower-foot pivot only if V8's rig and skin prove compatible;
- regenerate relaxed idle and relaxed walk before touching attack, eating, or other clips.

This creates the cleanest test of the user's hypothesis: V8 walking plus the missing V5.5 chest and idle corrections. If the global neutral-chain values damage V8 walking, keep the corrected neutral chain for idle/actions and derive a locomotion-specific neutral variant rather than reverting the idle correction.

### Avoid these merges

- Do not paste the whole V5.5 profile over V8.
- Do not port only the 32% forward idle foot offset without its load bias and pelvis solve.
- Do not apply chest or leg rotations after baking if the constrained solve can own them.
- Do not copy the V5.5 inverse-bind matrices into a changed V8 rig.
- Do not use one metric to select the winner; the final choice requires full-body loop review.

## Planned V5.5 vs V8 vs V8.1 comparison

Use the same source model scale, side orientation, floor, lighting, 960×540 resolution, 24 fps, locked global-bounds camera, and complete native clip durations. Do not auto-frame each version independently per frame.

| Review area | V5.5 reference | V8 baseline | V8.1 target |
| --- | --- | --- | --- |
| Relaxed idle support | Stable support leg; opposite foot forward | User reports this remains at the weaker V5-style result | Port the V5.5 support arrangement while preserving V8's stronger walking work |
| Chest attitude | Less forward lean; no direct height translation | User reports this remains like V5 and is uncorrected | Port the complete V5.5 neutral-chain correction into V8.1 |
| Head/neck neutral | Coordinated horizon correction | To inspect | Calm head without compensating for chest by overbending neck |
| Relaxed walk | Bounded rear ankle reach; toe-last release | User reports this is stronger | No regression from V8; only adopt missing V5.5 relationships |
| Foot deformation | Accepted 90% measured pivot | To inspect | Compatible measured pivot with no pinching or ground penetration |
| Bite | Rear/down brace before jaw/head | To inspect | Preserve best body-driven ordering |
| Eating | Pelvis-led settle and staggered support | To inspect | Preserve best whole-body support |
| Transitions | 16 exact endpoints including pelvis | To inspect | Exact rotation and translation handoffs |

### Required visual films

- relaxed idle, at least 10 seconds;
- relaxed walk, at least two complete cycles;
- alert idle;
- bite attack;
- eating loop;
- matched V5.5/V8/V8.1 three-column versions for idle and walk;
- enlarged synchronized foot/ankle comparison for walk.

### Required measurements

- torso and head median pitch in idle and walk;
- fore/aft foot spread in relaxed idle;
- support-load stability over the idle loop;
- maximum rear ankle reach during walk;
- stance/contact/toe-off timing;
- foot/toe ground penetration and loaded gaps;
- pelvis vertical/forward excursion for attack and eating;
- transition endpoint rotation and translation error;
- rest-skinned-mesh error if any pivot or inverse bind changes.

## V8.1 acceptance criteria

V8.1 should only replace V8 if all of these are true:

- relaxed idle clearly reads as one supporting leg plus one forward resting leg;
- the support role does not visibly swap during the breathing loop;
- the V5.5 chest/neutral-chain correction is present and the animal no longer carries the V5/V8 forward-heavy chest attitude;
- the head remains calm and horizon-aware;
- V8 walking quality does not regress in rear extension, limb cohesion, foot support, or toe-off;
- the lower-foot deformation remains clean through support and swing;
- pelvis motion survives GLB export and browser playback;
- transitions remain exact;
- full-body side review finds no new ground penetration, knee reversal, ankle collapse, skin pinching, or loop seam.

If V8.1 wins idle but loses walk, keep separate idle and locomotion profile/action ownership rather than forcing one global neutral setting to solve both.

## Canonical evidence map

- V5.5 profile: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`
- Neutral/action implementation: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/actions.py`
- Locomotion/export implementation: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v4/locomotion.py`
- Translation-aware transitions: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/transitions.py`
- V5.5 build and jaw timing: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/build_v5_5.py`
- Lower-foot calibration: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v5_5/pivots.py`
- Release validator: `procedural-animation-toolkit(v5.5)/toolkit/v5.5/tests/validate_v5_5_release.py`
- Numerical comparison: `reports/V5-5-BALANCE-001/metrics.json`
- Reference analysis: `reports/V5-5-BALANCE-001/reference-analysis.md`
- Review disposition: `reports/V5-5-BALANCE-001/reviews.md`
- Accepted pivot evidence: `reports/V5-5-FOOT-PIVOT-TEST-2/`

## Evidence boundary

The posture and gait values are animated-skeleton and silhouette proxies. They do not establish a biological center of mass, real force distribution, or scientifically measured Tarbosaurus kinetics. The V8/V8.1 recommendations remain a plan until V8 is imported, structurally inspected, rendered through the same camera, and compared directly.
