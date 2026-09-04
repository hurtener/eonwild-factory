# V8.1 final Blender media — adversarial visual review

**Review date:** 2026-08-27  
**Review scope:** read-only visual review of the final V8.1 Blender composite media.  
**Source GLB:** `procedural-animation-toolkit(v8.1)/validated_result/v8.1/tarbosaurus_procedural_v8_1_animation_pack.glb`  
**Source GLB SHA-256:** `c160df63e9f2d92028a62fc8a911a25aa08c163f647201533b2e9510390bd118`

## Verdict

**CONDITIONAL PASS — P1 remains open.**

The final media is renderable, inspectable, and generally coherent. Full-body framing is usable, the mesh and materials are present, the jaw is visually centered, and no obvious ground penetration or catastrophic deformation appears in the reviewed frames. However, the central V8.1 behavior is not yet visually convincing: the power attack reads as a subtle crouch/pose change with a short gape pulse rather than an unmistakable one-footed explosive jump, airborne bite, landing, weight arrest, and feeding continuation. The numeric release gates are useful corroboration, but they do not close this visual finding.

This is an adversarial media review, not an engine modification. No engine source, GLB, render script, or source media was edited.

## Method and evidence boundary

I inspected the complete 10 fps side and three-quarter power-sequence frame runs through contact sheets, then checked representative frames at original detail. I also inspected the available idle, walk, and jaw-turn media and the existing source-grounded reference analysis. The reviewed final films are actual Blender outputs from the GLB above; the report does not infer behavior from filenames alone.

No usable Gemini/Mimo visual API credential was used for this pass. The conclusions below come from direct local frame inspection. The technical validation JSON and animation manifest were consulted only to map authored event timing; they are not treated as proof of visual quality.

The final power sequence is an authored composite, not a single uninterrupted root-motion take:

| Film frames | Approx. time | Composite segment |
|---:|---:|---|
| 1–10 | 0.00–0.90 s | `PROC_WALK_RELAXED_V8_1_INPLACE` |
| 11–17 | 1.00–1.60 s | `PROC_WALK_TO_POWER_ATTACK_V8_1` |
| 18–45 | 1.70–4.40 s | `PROC_POWER_ATTACK_V8_1` |
| 46–53 | 4.50–5.20 s | `PROC_POWER_ATTACK_TO_EAT_V8_1` |
| 54–100 | 5.30–9.90 s | `PROC_EAT_LOOP_V8_1` |

The manifest places the authored power events at normalized fractions `takeoff=.38`, `apex=.415`, `bite_contact=.44`, `lead_land=.45`, `second_catch=.55`, and `weight_arrest=.76`. On this 10 fps composite those map approximately to film frames 28, 29, 30, 30, 33, and 39 respectively. Several of those events fall between very sparse samples, so the film is a weak medium for proving a short airborne event.

## Findings

### P1-VIS-01 — The power attack does not visibly sell the requested explosive jump

**Status: OPEN / release-blocking for visual acceptance**  
**Media:**

- `showcase/v8.1/blender-final-side/films/power-sequence-side.mp4`, frames 18–35, approximately 1.70–3.40 s.
- `showcase/v8.1/blender-final-threeq/films/power-sequence-threeq.mp4`, frames 27–35, approximately 2.60–3.40 s.
- Contact sheets: `side-foot-events.jpg`, `threeq-foot-events.jpg`, `side-head-2.4-4.4s.jpg`, `threeq-head-2.4-4.4s.jpg`.

**Visible evidence:** Frames 18–27 show a gradual lowering/coil. Around frame 28 (2.70 s) the jaw opens, but both hind feet remain visually close to the floor. Frames 29–31 continue the gape/closure while the feet stay near the floor plane. Frames 32–35 show only a subtle body extension; there is no clearly readable multi-frame silhouette with both soles separated from the ground. The three-quarter view has the same ambiguity: limb overlap and small vertical separation make any short clearance read as a near-ground pose, not a jump.

**Impact:** The requested behavior was an energy burst: see prey, jump one-footed forward while biting, land, stop the weight, then continue eating. A viewer cannot reliably identify takeoff, both-feet flight, or an airborne bite from these final films. This is the central V8.1 acceptance criterion, so numeric airborne diagnostics alone are insufficient.

**Recommendation:** Re-author or retime the visual attack so the launch-foot preload, toe-off, root arc, and apex are legible at the delivery frame rate. The final review should show at least several consecutive frames with a clear sole-to-floor gap and a clearly displaced body arc; render at 20–24 fps or higher for the editorial acceptance media. Preserve the technical gates, but add a visual gate based on a fixed camera and visible floor contact.

**Important qualification:** The technical report records a passing 0.196 s airborne window, 0.0988 m vertical apex, 0.0480 m minimum sole clearance, and correct landing order. Those values explain why the validator passes; they do not contradict the visual finding that the motion is too small/brief to read in this presentation.

### P1-VIS-02 — Walk-to-power support transfer is not visually legible

**Status: OPEN**  
**Media:** side and three-quarter films, frames 11–27, approximately 1.00–2.60 s; see `side-all-10s.jpg`, `threeq-all-10s.jpg`, and the foot-event sheets.

**Visible evidence:** The transition lowers the animal and changes the head/jaw pose, but the torso remains almost screen-stationary and the supporting hind foot is not held as an unmistakable loaded anchor before launch. The lead/trailing leg relationships are obscured by overlap and the low-contrast floor. The result reads as a generic slow crouch followed by a pose change rather than hips/legs taking and redirecting the body mass.

**Impact:** The exact issue the V8.1 rework was intended to solve—prey response driven from the hips and legs instead of a head-led extension—is not clear to a viewer. The transition therefore does not establish the cause-and-effect needed for the later jump to feel explosive.

**Recommendation:** Make the support transfer explicit in the authored phase: hold one hind foot as the planted support, flex hip/knee/ankle in a connected chain, shift pelvis/chest over that support, then release the launch foot into toe-off. Give the pelvis a visible preparatory displacement before the head/jaw commits. Review with a higher frame rate and a floor/contact shadow that does not hide sole clearance.

### P1-VIS-03 — Landing-to-feeding continuity cannot be visually verified from this composite

**Status: OPEN as an evidence/shot-design issue; engine defect not proven**  
**Media:** frames 46–100, approximately 4.50–9.90 s; `side-all-10s.jpg` and `threeq-all-10s.jpg`.

**Visible evidence:** The head descends after the power segment and the eat loop holds a head-down posture with subtle jaw motion. No carcass, prey, or other target is visible. Consequently, bite contact, lead-foot landing, second-foot catch, weight arrest, and continuation into eating cannot be distinguished from a targetless head-down animation.

**Impact:** The film does not demonstrate the requested narrative beat “lands and stops the weight for then continue to eat.” It demonstrates a feeding-ready pose, but not an interaction with something that explains the bite and the subsequent halt.

**Recommendation:** Either add a minimal target/carcass prop to the review render, or publish separate motion-only and interaction shots with the distinction stated in the page. Keep the target visually simple and clearly project-owned; this is a review aid, not a request to ingest protected reference art. If the engine intentionally has no prey asset yet, label this as an evidence limitation rather than calling the bite visually verified.

### P2-VIS-04 — Jaw gape is readable, but the bite is not connected to the flight

**Status: FOLLOW-UP**  
**Media:** side frames 28–31 (2.70–3.00 s) and three-quarter frames 28–31.

The jaw opens dramatically around frame 28, remains open at frame 29, then closes by approximately frame 31. This is a visible pulse, and the jaw looks centered in the inspected turn-left still. But because the body never presents a clear airborne/target relationship, the opening reads as a pose cue rather than a bite during flight. In the source reference analysis, the gape remains wide through the flight and early catch; the final edit closes it almost immediately around the suspected contact.

Recommendation: keep the gape open from the pre-takeoff commitment through lead-foot catch, then close at a clearly staged bite/contact moment. If the targetless motion-only shot is retained, label the event as an attack gape rather than a visually verified bite.

### P2-VIS-05 — Material and lighting quality is inconsistent across the final review set

**Status: FOLLOW-UP**  
**Media:** final power films versus `showcase/v8.1/site/v8_1_idle_side_20fps.mp4` and `v8_1_walk_side_20fps.mp4`; sheets `idle-side-overview.jpg` and `walk-side-overview.jpg`.

The idle/walk media has a darker brown, higher-contrast scale treatment on a light-grey stage. The final side/three-quarter power films are pale/cream on a dark black/green stage. The final texture is present and readable, but the two looks do not feel like one consistent editorial quality bar. This is not a mesh or missing-texture failure.

Recommendation: standardize color management, key/fill/rim balance, background, and exposure across the comparison clips. The page should make camera changes intentional rather than making the material look like it changed between versions.

### P2-VIS-06 — Delivery sampling is too sparse for a short airborne event

**Status: FOLLOW-UP / supports P1-VIS-01**

The power film is 10 fps at 720×406. A technically valid airborne window of approximately 0.196 s provides only about two sampled frames, and the event timing falls between the authored samples. This is enough to inspect that a render exists, but not enough to judge nuanced toe-off, mid-air bite, and landing sequencing. Use 20–24 fps or higher for the quality page and retain the 10 fps clip only as a lightweight preview if needed.

## Positive observations / passed visual checks

- Both final power films keep the complete animal in frame: head, feet, torso, and tail remain visible, with no obvious tail clipping or black/disappeared frames.
- The GLB renders with the expected body texture and scale detail; no missing-material fallback or catastrophic mesh collapse was seen in the inspected frames.
- No obvious sole penetration or floating limb artifact was seen in the sampled final frames. The baked ground validation also reports a passing lead-before-trailing landing order and no sampled penetration.
- The turn-left jaw still shows a centered jaw/hinge relationship without obvious lateral drift. This agrees with the jaw-centering validation gate (`max midline offset 0.001526 m` under the `0.002 m` gate).
- Idle and walk stills show plausible asymmetric support and articulated toes/feet. The static stills cannot prove the complete center-of-gravity trajectory, but they do not expose a new gross foot-rig failure.
- The final full-body framing is usable for a review page. The subject is somewhat small within the 720×406 frame, but this is a presentation improvement rather than a release-blocking framing defect.

## Event-level visual assessment

| Requested event | Expected visual cue | Final media assessment |
|---|---|---|
| Gaze / prey notice | Head and attention commit before whole-body launch | Head/jaw changes are visible, but no target and no strong whole-body attention cue. **Not fully verified.** |
| One-foot preload | One hind foot clearly supports the loaded body | Some lowering is visible; supporting foot is not unambiguous. **P1 open.** |
| Toe-off | Launch foot leaves after a connected hip/knee/ankle drive | **Not visually legible** at 10 fps. |
| Both-feet flight | Several frames with both soles visibly above floor | **Not convincingly visible. P1 open.** |
| Apex | Body arc and vertical separation are obvious | Technical apex exists, but visual arc is too subtle. **Not visually convincing.** |
| Jaw opening / bite | Gape opens before launch, remains linked to airborne bite | Gape pulse is visible; target/flight connection is not. **P2 / evidence gap.** |
| Lead-foot landing | Lead foot catches before trailing foot | Technical order passes; visual distinction is weak in the composite. |
| Second-foot catch | Trailing foot catches after lead foot | Technical timing passes; not clearly separable in the 10 fps view. |
| Weight arrest | Body visibly absorbs landing before feeding descent | Descent is visible, but the arrest is not distinct from the transition. **P1 evidence gap.** |
| Feeding continuation | Target-directed head-down continuation after arrest | Head-down eat loop is present; no target means interaction is not verifiable. **P1 evidence gap.** |

## Technical context used for correlation

The available release validation reports PASS for the authored event schema, mirrored landing order, jaw centering, and baked-ground checks. The final films also report Blender 5.2.0, 720×405 render output encoded as 720×406, 10 fps, and 10 seconds. This review accepts those as reproducibility/context evidence only. The visual verdict remains conditional because the core behavior is not perceptually legible in the final presentation.

The reviewed side/three-quarter films cover the left-lead presentation. A mirrored/right-lead final film was not present in the inspected media set, so symmetry of the visual result is outside this review’s evidence scope.

## Artifact index

Review plan:

- `reports/V8-1-DEEP-REWORK/visual-review/plan.md`

Power-sequence contact sheets:

- `reports/V8-1-DEEP-REWORK/visual-review/side-all-10s.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/side-001-025.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/side-026-050.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/side-051-075.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/side-076-100.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/side-foot-events.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/side-head-2.4-4.4s.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-all-10s.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-001-025.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-026-050.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-051-075.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-076-100.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-foot-events.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/threeq-head-2.4-4.4s.jpg`

Idle/walk/jaw review artifacts:

- `reports/V8-1-DEEP-REWORK/visual-review/idle-side-overview.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/idle-frame-001.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/idle-frame-060.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/walk-side-overview.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/walk-frame-001.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/walk-frame-030.jpg`
- `reports/V8-1-DEEP-REWORK/visual-review/walk-frame-060.jpg`

Source media reviewed:

- `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1/blender-final-side/films/power-sequence-side.mp4`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1/blender-final-threeq/films/power-sequence-threeq.mp4`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1/site/v8_1_idle_side_20fps.mp4`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1/site/v8_1_walk_side_20fps.mp4`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1/blender-final-jaw/stills/turn-left-35-rootmotion.png`

**Handoff:** Technical validation may remain green, but implementation/review should not close V8.1 visual acceptance until P1-VIS-01 and P1-VIS-02 are either corrected or explicitly accepted as a documented exception. P1-VIS-03 can be closed by adding a target interaction shot or by separating the motion-only evidence claim from the feeding-interaction claim.
