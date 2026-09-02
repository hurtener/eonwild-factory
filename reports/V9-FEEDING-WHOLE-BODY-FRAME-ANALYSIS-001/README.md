# V9 Feeding + Tear/Pull Whole-Body Frame Analysis

Status: complete. This report is an analysis-only artifact; it does not change the animation engine or any existing V9 authority.

## Source and frame convention

- Source: `/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence/FEEDING + TEAR:PULL — fixed side.mp4`
- Source SHA-256: `e56f2dc9ecc22716892b36d7559bf5cb348dee3459ca725dc7ae4205d98c7e43`
- Native video stream: H.264, 736x400, 24/1 fps, 145 frames, 6.041667 s.
- Native frame convention in this report: zero-based decoded frame index `F000..F144`; timestamp `t = frame_index / 24` seconds. The final frame is therefore `F144 @ 6.000 s`; this is the frame timestamp convention, not a claim about presentation-duration semantics.
- Extracted evidence: lossless PNG decode of the native video frames at `build/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/native-frames/frame_000.png` through `frame_144.png`.
- Coverage: the full contiguous native interval `F000..F144` (all 145 frames) was inspected. This covers the requested 100–150-frame interval and includes entry, acquisition, repeated pulls, release/reposition, and end relaxation.

## Inspection method

Every native frame was viewed in a labeled six-frame contact sheet (`build/.../contact-sheets/sheet_*.png`) and ambiguous transitions were revisited as enlarged, nearest-neighbor crops (`build/.../enlarged-transitions/head-foot-F*_2x.png`) and full-frame views. The sheets are temporal neighbors, not a substitute for frame inspection. The ledger records visible 2D facts separately from inferred 3D/force/anatomy; hidden contacts, depth, exact COM, and loads are marked unknown. Measurements are approximate image-plane readings, normalized by the 736 px frame width and 400 px frame height, with a practical uncertainty of roughly +/-0.02 frame width or +/-0.02 frame height unless a transition is occluded. Per-frame pelvis deltas smaller than that threshold are treated as qualitative trend/hold annotations, not measured micromotion.

The visible lateral side faces left (head at image-left, tail at image-right). Limb names are camera-relative and neutral: `hind_imgL` / `hind_imgR` identify the two large hind-foot silhouettes by image position only. The small tucked forelimbs are never called hind feet and are marked separately as `fore_visible_contact`. A side camera cannot certify hidden limb contact or whether a silhouette overlap is actual 3D contact.

Ledger shorthand: `P` = visibly planted, `T` = partial/toe contact, `U` = unloaded but still near the floor, `S` = swing/step, `O` = occluded/unknown, and `N` = no visible contact (the small forelimbs are not treated as support unless their claws visibly touch). `pelvis_xy_norm` is a rough visible hip/pelvis proxy in `(x/736,y/400)` image coordinates; `pelvis_delta_norm` is a coarse frame-to-frame annotation, not a claim of sub-threshold measurement. `pelvis_shift_yaw` records apparent fore/aft (image x), vertical (image y), and silhouette/yaw changes; lateral depth shift is `unknown` in this side camera. `hind_coordination` describes hip/knee/hock/foot coupling without asserting hidden 3D joint centers.

## Ledger status

The machine-readable per-frame ledger is `reports/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/frame-ledger.csv`. It contains 145 complete rows (`F000..F144`) plus the header; no `PENDING` rows remain.

## Evidence inventory and validation

The lossless native-frame evidence is in `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/build/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/native-frames/frame_000.png` through `frame_144.png`. The complete temporal contact-sheet set is `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/build/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/contact-sheets/sheet_*.png`, plus `overview_all_000_144.png`. Enlarged nearest-neighbor transition crops are in `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/build/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/enlarged-transitions/`; the `head-foot-F020_2x.png` through `head-foot-F110_2x.png` run covers the ambiguous approach, first coupling, first pull, release, and regrip, with full-frame boundary enlargements alongside it. The generation scripts are `build/V9-FEEDING-WHOLE-BODY-FRAME-ANALYSIS-001/make_contact_sheets.py` and `make_enlarged.py`.

All 145 labeled native frames were visually examined in their temporal neighbors. Individual/enlarged views were used at the contact boundary and during the first tissue connector, first prop lift, release, second grip, and second release. The final readback of the ledger with Ruby CSV reported `header=18 rows=145 bad=[] ids_unique=145 contiguous=true`; the file has 146 lines including the header.

## Whole-clip phase and event timing

The times below use the exact convention `t = frame / 24`. Ranges are inclusive and use native zero-based frame indices.

| Phase | Frames and time | Directly visible sequence | Confidence / interpretation |
|---|---:|---|---|
| Ready and prey entry | F000–F003, 0.000–0.125 s | Head is already low and forward/down; the torso is long and high; both large hind-foot silhouettes read planted; forelimbs are tucked. The carcass enters from image-left. | High for visible pose; no bite. |
| Approach step A | F004–F012, 0.167–0.500 s | `hind_imgR` lifts and swings in F004–F008, toes approach the floor in F009–F010, and the two hind silhouettes read planted again by F011–F012. | High for the visible swing; landing edge is medium because the feet overlap. This is a real setup step, not an anchor hold. |
| Approach step B | F013–F016, 0.542–0.667 s | `hind_imgL` lifts/reaches in F013–F014, is partial/toe-near-floor in F015, and is planted by F016. F014 has a clear background gap between muzzle and carcass. | High for the step and the explicit F014 no-contact observation. |
| Approach hover | F017–F029, 0.708–1.208 s | Both hind silhouettes stay planted while the head/neck lowers and the forward/down body curve deepens. The animal and prey continue to change image position. F020 also has a clear background gap; F028–F029 are only near-contact candidates. | High for no visible grip; medium at the occluded muzzle boundary. This is body motion over anchors, not a post-contact hold. |
| Contact boundary, unresolved | F030–F046, 1.250–1.917 s | The snout overlaps the dorsal prey region and the head makes small pitch/position changes. No tissue strand or unambiguous prop response is visible. Both hind feet appear supported. | Medium/low for contact. Do not backdate the bite from silhouette overlap. |
| First visible connector and grip | F047–F053, 1.958–2.208 s | A tiny red connector first appears in F047; F048 is the first robust mouth-to-prop strand. The jaw opens progressively while feet hold and the prey is still mostly floor-bound. | F047 is a medium-confidence onset cue; F048–F053 are robust coupling evidence. |
| First tear/pull | F054–F071, 2.250–2.958 s | The jaw widens and tissue is drawn toward the mouth. The hip/topline rises while the skull/front body travels image-left and down; the anterior body descends/pivots rather than lifting uniformly. Hips stay high over planted, flexed hind legs; the tail arcs and changes curvature. | High for the 2D counter-motion and anchor hold; 3D force, COM, yaw, and roll remain unknown. |
| First prop lift/tilt pulse | F072–F077, 3.000–3.208 s | The prey edge/rib-cage silhouette lifts and tilts/rolls under the open jaw while the hind-foot silhouettes remain anchored. | High for visible relative prop motion; exact support point and force are unknown. |
| Release and reposition | F078–F083, 3.250–3.458 s | The mouth opens away from the prey and a gap is visible. The head projects image-left/forward; the displaced prey remains on the floor. The feet do not visibly step. | High for release/separation; hidden-side contact cannot be certified. |
| Regrip approach | F084–F087, 3.500–3.625 s | The open jaw and low/forward neck return toward a new prey edge while the high-hip support and planted-foot silhouettes persist. | High for approach; contact remains unresolved until the next two frames. |
| Second grip and pull | F088–F101, 3.667–4.208 s | F088 is a near-contact candidate and F089 is the first established second grip. The jaw is mostly near-closed/clamped rather than repeating the first wide gape. The prop follows with smaller floor-level shifts; feet remain visually planted. | F089–F101 coupling is high by continuity, with some connector occlusion. The second pull is shorter and less gape-dominant than the first. |
| Second release/raise | F102–F107, 4.250–4.458 s | F102 is still a contact transition. The head rises and the jaw opens; F105 is the first clear air-gap/separation frame, continuing through F107. The prey stays floor-supported. | F102–F104 medium transition confidence; F105–F107 high for release. |
| Raised reorientation | F108–F113, 4.500–4.708 s | The head and front body rise to a more level stance; the animal shifts image-left/up relative to the stationary prey. The jaw closes/near-closes before a new gape; both feet appear floor-supported, with far-side overlap. | Medium for individual hidden contacts; high for the large body/head reorientation. No new grip. |
| Postbite gape | F114–F124, 4.750–5.167 s | The jaw opens broadly again while the trunk remains raised and level/high-hipped. The prey is separate and stationary; the tail stays low and responsive. | High for the visible gape and lack of coupling. This is not a frozen postbite clamp. |
| Recovery lowering | F125–F134, 5.208–5.583 s | The jaw closes, the head/neck lower and extend forward, and the forward/down feeding-ready curve returns while the hips remain high. The prey remains separated. | High for no visible grip; contact edges remain side-view limited. |
| End hover | F135–F144, 5.625–6.000 s | The closed mouth hovers above the carcass; both hind silhouettes remain near the floor, no step resolves, and the prop stays uncoupled. | Medium for far-side contact; high for the visible final no-grip hover. |

The most defensible first-contact statement is therefore: F047 is the first visible connector candidate (approximately `±1` frame because the strand is tiny), F048 is the first robust connector, and F030–F046 are unresolved rather than contact-positive. The most defensible second-grip statement is F088 candidate/F089 established. The first unambiguous release gap is F078; the second is F105, with F102–F104 transitional.

## Foot support, steps, and body motion over anchors

Only two foot events are unambiguous in this side view: `hind_imgR` swings in F004–F008 and resolves by F011–F012; `hind_imgL` swings in F013–F014 and resolves by F016. `hind_imgL` and `hind_imgR` are image-position labels only; they are not biological left/right or near/far labels. The small forelimbs stay tucked or hang clear of the floor in the analyzed clip and are never used as hind-foot evidence.

Useful planted-foot intervals are:

- F016–F046: both large silhouettes appear planted while the body/head continues to lower and advance; contact confidence is high early and medium near the muzzle overlap.
- F047–F077: both silhouettes remain planted through first grip, hip/front-body counter-motion, tail change, and the visible prop lift/tilt.
- F078–F101: the release, forward reorientation, regrip, and second pull occur without a resolved hind-foot step.
- F102–F144: the feet remain visually supported through the rise, gape, and recovery; confidence is medium because one far-side ankle/foot is repeatedly merged by projection.

The reference therefore contains substantial motion without stepping: F017–F029 head/neck and trunk adjustment; F047–F077 hip/topline versus skull/front-body counter-motion plus prop movement; F078–F101 release/reposition/regrip; and F102–F124 head/body rise and image translation. These are not reasons to pin every body joint. Conversely, the two early swings are real steps and should not be erased by a universal foot lock. The side view cannot distinguish a hidden lift, a small depth shift, or a camera-relative translation when a silhouette is merged.

## Observed whole-body coordination

### Pelvis, hips, knees, hocks, and feet

The visible feeding support is high-hipped, with the knees/hocks flexing and changing compression while the foot silhouettes stay on the floor. The first pull is especially clear: the hip/topline rises while the snout/front body descends, so the animal is not simply crouching lower and not simply lifting the whole trunk. The second pull retains this high pelvis/forward-down composition with smaller jaw motion. No exact 3D joint centers, loads, or COM can be recovered from this camera.

The implementation implication is to preserve a contact mask for each visible planted foot but solve a movable pelvis and high hip target over that support. Let the pelvis translate and rotate in the feeding-specific composition, then distribute knee/hock flexion through the leg chain. Do not lock pelvis and feet simultaneously and leave the ankle as the only compensator; that produces the inward ankle drift seen in the current R5 context. The visible evidence supports foot anchors plus body sway/settling, not rigid foot-to-pelvis geometry.

### Trunk pitch and curvature

The curve is distributed: a high pelvis/topline flows into a forward/down thorax and long neck during approach and pulling. During F048–F059, the hip/topline rises while the anterior body remains down/forward. During F060–F077 the same support composition persists while the jaw and prey move. During F108–F124 the anterior body/head releases upward into a more level raised stance, then F125–F144 returns to a forward/down hover. A single localized dorsal bump is not the observed explanation for the silhouette change; the visible change is a coordinated hip, thorax, neck, and tail composition.

### Neck and head

The first pull direction is important. Enlarged/native checks put the snout at approximately `(257,278)` in F048, `(232,287)` in F054, and `(185,302)` in F059 pixels. Relative to F048 this is about `(-72 px, +24 px)`, or `(-0.098 frame-width, +0.060 frame-height)` over 11 frame intervals (`0.458 s`). Hand readings carry roughly `±4–8 px` uncertainty and are image-plane only. Thus the skull travels left/down while the jaw gape grows; jaw opening must not be mistaken for skull elevation. The head does rise clearly only in the F102–F124 release/reorientation/gape sequence. True lateral yaw and roll are not certifiable from this fixed side view, although small image-plane asymmetries and head reversals are visible.

### Jaw, grip, and regrip

The jaw is not a single held pose: it is closed during approach; forms a tiny connector candidate at F047; establishes the first strand at F048; opens wider through the first pull; releases into a visible gap at F078; approaches again with an open jaw; closes into the second grip at F088–F089; holds a mostly near-closed second pull through F101; releases and opens at F102–F107; holds a broad no-prop gape at F114–F124; then closes during recovery. This sequence supplies visible regrip, pause, and uneven timing for liveliness.

### Tail

The tail is not a fixed trailing spline. It begins long and slightly down-curved, arcs higher during the first grip/pull, changes curvature during the F072–F077 prop response, flattens/straightens through release and reorientation, and remains low but responsive during the broad gape and final hover. The tail response can be coupled to feeding pull/release events with a lag and modest variation; no walking-phase alternation is implied.

### Prop coupling

The reliable coupling windows are F047–F077 for the first strand/pull/tilt, F088–F101 for the second grip/pull, and none after F105. The first visible prop response is delayed relative to the first connector: the strand is visible by F047–F048, while a clear edge/rib lift/tilt appears at F072–F077. The prey can therefore have a compliant visual connector and a delayed, uneven prop response. The video does not establish the hidden attachment point, 3D pull vector, mass, friction, force, or load.

## Feeding-specific parameterization guidance

This reference is better represented as a feeding composition with event states than as a walking gait. A reusable composition can expose the following behavior-specific states: `approach`, `foot-set`, `jaw-seek`, `grip`, `tear-pull`, `prop-lift/tilt`, `release`, `reposition`, `regrip`, `recover/gape`, and `hover`. State durations should be allowed to vary; the first coupled pull/prop response occupies roughly F047–F077 (`~1.29 s` including onset and lift), while the second established grip is roughly F089–F101 (`~0.54 s`) before the release rise.

For each pull/regrip event, parameterize the coordination in this order:

1. Mark visible hind-foot anchors and confidence; retain planted contacts through the pull, but permit a pelvis/hip translation and hock-compression response.
2. Target a high pelvis and a forward/down trunk curve; distribute the curve across pelvis, thorax, and neck rather than using one neck hinge or freezing the dorsal line.
3. Aim the head/jaw at a behavior-specific bite point. Drive jaw gape and tissue/prop coupling separately from skull translation so a wide jaw does not imply an upward head motion.
4. Add a compliant connector/prop response with a delayed lift/tilt and a release gap. Regrip from a new point rather than looping the identical bite pose.
5. Add a tail counter-curve/settle response and small lateral/image-plane composition changes. Treat true yaw/roll and hidden contacts as unknown targets, not measured facts.

Useful variation is visible in the clip itself: the first pull is gape-heavy with a clear prop-lift pulse, the second is a shorter near-closed clamp, and the post-release phase opens widely before recovery. Preserve short settling pauses and nonuniform pull timing. Avoid a universal stride oscillator, fixed phase alternation, or a frozen pelvis/trunk rule; generic geometric primitives may be reused, but feeding needs its own solver composition and event timing.

## Existing-spec calibration note

The existing feeding posture language in `v9_extension/docs/animations/03_FEEDING_DRINKING_AND_GROUND_POSTURE.md` should be read with an explicit qualification: “stable pelvis/trunk” can mean stable support/contact state, not immobile body geometry. F047–F077 show the hip/front-body counter-motion and prop response over apparently planted feet; F078–F101 show release, head reposition, and regrip over the same support; F102–F124 show a large head/body rise and gape without a step. The analysis does not modify that specification or the engine, but it flags where “stable” would understate the visible feeding motion.

## Evidence boundaries and corrections retained

Observed facts are the labeled 2D silhouette, visible gaps, visible tissue connector, relative prop edge movement, and temporal continuity. Inferred labels such as “pull,” “anchor,” or “tension” describe the apparent composition and are not claims about 3D forces, anatomy, exact COM, or hidden contact. The explicit F014/F020 background gaps override any earlier near-contact intuition. The tiny F047 strand is retained as a candidate, with F048 as the robust first connector. The corrected F048/F054/F059 direction is retained: skull/front body moves left/down while hip/topline rises; it is not a uniform head lift. No small forelimb is labeled as a hind foot.
