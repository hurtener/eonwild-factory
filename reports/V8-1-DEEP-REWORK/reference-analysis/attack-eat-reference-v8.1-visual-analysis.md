# V8.1 power-attack reference analysis

## Scope and conclusion

This is a pixel-based review of the actual local Tarbosaurus attack/eat reference used by V8. It is intended to ground the V8.1 power-attack rework in observable timing and pose relationships rather than inventing a choreography. No engine files were changed.

The reference does contain the requested core read: target attention, a loaded one-foot takeoff, a short interval with both feet visibly clear, a first-foot landing with the other foot late, a low forward charge, and a separate grounded feeding sequence. The most important implementation anchors are:

- last unambiguous takeoff support: frame 30 / 1.250 s;
- toe-off transition: frames 30–31 / 1.250–1.292 s;
- unequivocal two-feet-airborne interval: frames 32–35 / 1.333–1.458 s;
- first visible lead-foot landing: frame 36 / 1.500 s;
- attack jaw opening begins before flight: frame 25 / 1.042 s;
- widest attack gape: approximately frames 28–35 / 1.167–1.458 s;
- first visible feeding contact with the carcass: frames 238–240 / 9.917–10.000 s;
- clamp/brace: approximately frames 240–270 / 10.000–11.250 s;
- release and head recovery: frames 276–288 / 11.500–12.000 s.

The source cuts camera at frame 100 / 4.167 s. Therefore the side-view attack and frontal feeding section should be treated as two reference shots, not as proof of a continuous world-space path.

## Source and method

Source file:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/procedural-animation-toolkit(v8)/inputs/v8/tarbosaurus-attack-eat-reference.mp4`

Verified media facts:

| Property | Value |
|---|---:|
| Codec | H.264 video, AAC audio |
| Image size | 736 × 400 |
| Video rate | 24 fps |
| Video frames | 289 (0–288) |
| Duration | 12.041667 s |
| File size | 5,408,810 bytes |

Frames were extracted with FFmpeg directly from the source, including source-resolution selected frames and dense contact sheets. The selected frames were inspected at original resolution with the local visual inspection tool. The video itself is a rendered/reference shot, not calibrated motion capture: pixel observations support timing and relative relationships, but not anatomical measurements or exact world-space velocities.

No external Gemini/Mimo endpoint was invoked: no usable visual-model API credential was discoverable in the environment. The conclusions below are therefore direct inspection of the supplied source pixels, with uncertainty called out where the camera prevents certainty.

## Shot structure and camera limitation

The first shot is a side/three-quarter attack from 0.000 s through frame 99 (4.125 s). The animal starts facing screen-left, pivots toward a more frontal/rightward heading during the load, then travels through the frame. At frame 100 (4.167 s) the image cuts to a frontal feeding/display shot. The feeding shot begins around 8.000 s after an unshown edit/hold.

Do not use screen-left/right as the V8.1 locomotion direction. Use the animal's path-relative forward vector. Do not claim that the attack's landing is directly continuous with the carcass contact; the cut removes that evidence.

## Attack shot: frame-level event table

The labels “near/lead” and “opposite/trailing” are used instead of anatomical left/right where the view overlaps the limbs.

| Frames | Time (s) | Direct visual evidence | Procedural reading |
|---:|---:|---|---|
| 0–4 | 0.000–0.167 | Side-on alert/display pose; mouth is already open; both hind feet are on the floor. | Treat this as an initial attention/display beat, not the attack bite onset. |
| 5–10 | 0.208–0.417 | Jaw narrows toward closed while head/neck lower; both feet remain connected to the floor. | Close the initial display gape before loading the attack. Let body lowering precede a large head swing. |
| 11–18 | 0.458–0.750 | Pelvis/trunk compress and the animal begins turning; knees and ankles flex while the support base remains grounded. | Build the load from pelvis/hips and leg compression. |
| 19–23 | 0.792–0.958 | Three-quarter turn deepens; the cranial axis turns toward camera before the hips finish reorienting. | Use a head/eye lead over a pelvis-first reorientation, but keep the root/path coherent. |
| 24–25 | 1.000–1.042 | Low coil persists; one hind limb is dominant support and the opposite limb trails/folds. The attack jaw begins reopening by frame 25. | Start the attack gape during release preparation, before takeoff. |
| 26–30 | 1.083–1.250 | Gape becomes visibly wide; body rises out of the load; one foot remains the clear floor support while the opposite limb trails. | Make the launch one-foot driven. Preserve a grounded compression-to-extension arc. |
| 31 | 1.292 | Transitional frame: toes/feet are close to the floor line and support is not fully unambiguous. | Keep a short toe-off transition; do not classify this frame as a clean airborne key. |
| 32–35 | 1.333–1.458 | Both feet are visibly clear of the ground; limbs fold under the pelvis; jaw is wide open and the head is forward. | Required true-flight window. Preserve roughly 4–5 source frames of unmistakable air. |
| 34–35 | 1.417–1.458 | Lead/near foot starts to extend downward while the other remains folded/trailing; body appears to be descending. | Begin landing preparation from the lead foot, not with a symmetric two-foot pose. |
| 36–38 | 1.500–1.583 | Lead/near foot reaches the floor first; opposite foot remains airborne behind. | First catch is one-footed. Keep the second foot late. |
| 39–45 | 1.625–1.875 | Low forward continuation; lead support absorbs motion while the opposite limb folds/reaches. | Blend flight into a low charge through velocity continuity and compression. |
| 46–57 | 1.917–2.375 | Alternating catches are visible; the planted foot moves from rear/under-body toward a forward catch; jaw is narrow/closed around 2.0–2.25 s, then begins reopening. | Drive the leg as one linked chain (hip → knee → ankle → toes), not as separately timed bones. |
| 58–69 | 2.417–2.875 | Continued low charge; one foot supports while the other cycles behind/under the body; jaw is wide again. | Keep bite intent through the charge without freezing the legs into a run cycle. |
| 70–82 | 2.917–3.417 | Another linked stride/catch; near foot descends around 3.1–3.3 s while the opposite limb extends back; head begins lowering. | Add a visible weight-absorption arc and toe/foot roll during the charge. |
| 83–96 | 3.458–4.000 | Stride eases; one foot remains the clear support and the other is lifted/folded; gape gradually narrows but is still present. | Brake before the feeding handoff; do not close the attack at first landing. |
| 97–99 | 4.042–4.125 | Side shot settles with one supported foot and the other trailing/lifted. | Use a grounded settle pose before any shot transition. |
| 100 | 4.167 | Hard camera/shot change to frontal feeding/display. | Do not interpolate attack world-space path through this edit. |

### Launch, flight, and landing anchors

The most defensible event order from the pixels is:

1. Load/support through frame 30 (1.250 s).
2. Toe-off transition over frames 30–31 (1.250–1.292 s).
3. Both-feet-airborne core at frames 32–35 (1.333–1.458 s). Frame 31 is ambiguous; it should not be used as the only flight proof.
4. Lead/near foot first contact at frame 36 (1.500 s).
5. Opposite/trailing limb remains late through at least frames 37–39 (1.542–1.625 s), followed by alternating catches during frames 40–60 (1.667–2.500 s).

The camera and limb overlap make the exact identity of the opposite foot's first later catch uncertain. The robust requirement is temporal staggering: lead foot contact first, short single-foot absorption, then opposite-foot catch. A symmetric two-foot landing would contradict the visible sequence.

### Jaw timing in the attack shot

There are two separate gape events:

- Initial display: already open at frame 0; visibly narrowing by frames 5–10 and approximately closed by frames 10–12 (0.417–0.500 s).
- Attack gape: onset at frame 25 (1.042 s), clearly open at frames 26–30, near maximum through frames 28–35 (1.167–1.458 s), remains open through the low charge, and gradually narrows in the braking section around frames 87–99 (3.625–4.125 s).

The attack gape is therefore an anticipatory/release action, not a landing reaction. In V8.1 the jaw should open before toe-off, reach its widest state in flight/early catch, and remain readable through the low charge.

## Feeding shot: frame-level event table

This is a separate frontal shot. It is useful for the requested “land, stop the weight, then eat” handoff, but not proof of continuous attack-to-carcass travel.

| Frames | Time (s) | Direct visual evidence | Procedural reading |
|---:|---:|---|---|
| 192–204 | 8.000–8.500 | Frontal target/display; head is relatively high, eyes attentive, mouth slightly open with teeth visible. | Establish target lock and a controlled head lead. |
| 205–214 | 8.542–8.917 | Head/neck begin controlled descent and yaw toward the target; jaw narrows/near-closes. | Lower from the neck and chest after weight is caught; avoid a sudden head-only drop. |
| 216–222 | 9.000–9.250 | Muzzle is low and approaching; mouth transitions from narrow to opening. | Use a short approach-to-gape transition. |
| 224–230 | 9.333–9.583 | Gape is clearly open by frame 228 (9.500 s); head continues descending. | Open before contact, with the neck and trunk already committed downward. |
| 232–238 | 9.667–9.917 | Muzzle reaches the carcass area; carcass becomes visibly adjacent/under the jaws by frame 238. | Bite contact begins in this window; exact first tooth contact is partly occluded by the muzzle. |
| 239–240 | 9.958–10.000 | Carcass is visibly under/in the open jaws. | First defensible clamp/contact anchor. |
| 246–270 | 10.250–11.250 | Head remains down; jaws stay engaged around the carcass; feet are planted and brace the body. | After contact, stop forward weight and brace through both hind legs before tearing. |
| 276–282 | 11.500–11.750 | Neck/head lift begins; jaws release/tear; detached blood/debris is visible at frame 282. | Release should include a visible head recovery, not an instant loop reset. |
| 283–288 | 11.792–12.000 | Mouth approaches closed; head/neck settle/reposition; carcass is mostly out of frame. | End in a grounded recovery/feeding-ready pose. |

The feeding frames show a progressive descent, contact, clamp, brace, and release. They do not show a jump bite; the jump bite evidence comes from frames 25–36 of the attack shot. V8.1 should compose the two reads, not merge the separate camera shots into a literal continuous reconstruction.

## Body and limb relationships visible in the source

### Pelvis/chest/head

The body lowers and compresses during the 0.45–1.00 s load, rises into release, then returns to a low trunk during the 1.50–3.50 s charge. The head/cranial axis leads the turn and is already forward/open during flight. During the later charge it begins to lower while the body remains committed. The visually supported correction is therefore a pelvis/leg-driven load and release with a controlled head lead, not a head/chest pull that drags the rest of the animal.

### Hind legs and feet

The support leg visibly compresses and extends as a chain. The opposite leg folds/trails during flight, then participates in later catches. In the charge, the planted foot is not a rigid vertical post: it travels from a rear/under-body position toward the next forward catch, with visible ankle/toe attitude changes. Exact digit joint angles cannot be calibrated from this shot, but the source supports a toe/foot roll and sequential hip → knee → ankle → toe timing.

### Tail

The tail counter-rotates and follows the body through the pivot/launch, then makes a broad stabilizing arc during the low charge. Camera perspective and the partial crop prevent a reliable numeric tail trajectory. Use it as a delayed counterbalance, not as a fixed rigid extension of the pelvis.

### Gaze/attention

The animal begins alert, turns its cranial axis during the load, and keeps the head directed into the attack path. This is evidence for target-relative gaze/aim, but not enough to infer exact eye tracking. A V8.1 implementation should separate gaze/cranial targeting from root translation and keep both bounded.

## Recommended normalized V8.1 choreography

The following windows preserve the source ordering while allowing a different authored clip duration. They are normalized to the attack segment only; the feeding segment should begin after a grounded settle or explicit shot transition.

| Normalized phase | Source-relative anchor | Required relationship |
|---:|---:|---|
| 0.00–0.04 | frames 0–4 | Alert/target lock; initial display gape may be present. |
| 0.04–0.12 | frames 5–12 | Close display jaw while head/body lower into load. |
| 0.12–0.23 | frames 13–23 | Deep hip/pelvis coil and pivot; head leads the heading change. |
| 0.23–0.30 | frames 24–30 | Release preparation; attack jaw opens; one clear support leg. |
| 0.30–0.36 | frames 30–31 | One-foot toe-off transition; no instant two-foot launch key. |
| 0.36–0.40 | frames 32–35 | Both feet clearly airborne; limbs fold; jaw near maximum. |
| 0.40–0.48 | frames 36–45 | Lead-foot landing and absorption; opposite foot late. |
| 0.48–0.60 | frames 46–60 | Staggered opposite catch and first alternating stride. |
| 0.60–0.82 | frames 61–82 | Low committed charge; linked leg chain and toe/foot roll. |
| 0.82–1.00 | frames 83–100 | Brake/settle; maintain attack read until recovery/cut. |

For a shorter gameplay attack, retain a true-air core of approximately 0.15–0.20 of the attack's authored time, with two to three frames/keys of lead-foot-only absorption before the trailing foot catches. The exact source flight is about 0.17 s unequivocally (frames 32–35), with a 0.25 s transition-to-first-contact envelope from frame 30 to 36.

## Implementation guardrails derived from evidence

1. Keep target-relative forward separate from screen-space direction.
2. Load the hips/pelvis and support leg before the head reaches its attack pose.
3. Open the attack jaw before toe-off; do not trigger it only on landing.
4. Require an explicit both-feet-clear condition for the power attack. One frame with toes near the ground is not enough.
5. Land lead foot first, absorb, then catch with the opposite foot. Avoid a symmetric landing blend.
6. Generate each stride from a continuous hip-to-toe chain so the knee, ankle, and digits share timing; the source does not read as independent bone pulls.
7. Preserve foot roll/ankle flex during stance and toe-off; avoid a straight, flat support foot.
8. Keep the torso low during the post-landing charge and add braking before the feeding descent.
9. For the feed handoff, lower head/neck after the body has caught weight, brace both feet, then clamp and release with a delayed head recovery.
10. Treat the source cut at 4.167 s as a shot boundary in review tooling and in any procedural validation.

## Evidence artifact index

Primary report:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-eat-reference-v8.1-visual-analysis.md`

Interim implementation table:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/INTERIM_PHASE_TABLE.md`

Dense overview/contact sheets:

- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-overview-12fps.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-dense-0-1s.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-dense-1-2s.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-dense-2-3s.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-dense-3-4s.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/feeding-overview-12fps.jpg`

Leg/foot crops:

- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-legs-0.00-1.50s.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-legs-1.50-2.50s.jpg`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-legs-2.50-4.17s.jpg`

Original-resolution selected frames are in:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/selected-frames/`

The selected-frame directory includes the exact event anchors such as `frame-25-1.042.jpg`, `frame-30-1.250.jpg`, `frame-32-1.333.jpg`, `frame-36-1.500.jpg`, `frame-238-9.917.jpg`, `frame-240-10.000.jpg`, `frame-270-11.250.jpg`, and `frame-282-11.750.jpg`.

## Evidence limits

- This is visual timing/relationship evidence from a 2D rendered reference, not a biomechanical measurement or mocap solve.
- Far/near limb identity becomes ambiguous during the three-quarter pivot and charge; the report intentionally avoids asserting anatomical left/right where pixels overlap.
- The source does not expose a continuous attack-to-feeding path because of the camera cut and intervening edit.
- The exact first tooth-to-carcass contact is partly occluded; frame 238–240 is the defensible visible contact window.
- The source supports a procedural target for V8.1, but not a claim that every inferred joint trajectory is biologically unique or scientifically validated.
