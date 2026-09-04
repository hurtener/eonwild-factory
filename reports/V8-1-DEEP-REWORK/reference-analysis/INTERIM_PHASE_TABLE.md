# Interim visual phase table — source attack/eat reference

Source: `procedural-animation-toolkit(v8)/inputs/v8/tarbosaurus-attack-eat-reference.mp4` (736×400, 24 fps, 289 video frames, 12.041667 s). This is a frame review of the actual pixels; the source uses a side-to-front camera change, so timings below are source-frame timings and not calibrated world-space motion capture.

| Source frames | Time | Visible event | Implementation implication |
|---:|---:|---|---|
| 0–10 | 0.000–0.417 | Side-on alert/lowering: head and neck descend; both hind feet remain ground-connected while knees/ankles begin to flex. | Keep the initial target lock quiet; lower the skull after the body starts the coil rather than leading with a large head swing. |
| 11–23 | 0.458–0.958 | Deep coil and rapid pivot: pelvis/body compress; the cranial axis turns toward camera before the hips finish reorienting. | Use pelvis-first compression with a head/eye lead, then commit the root heading; do not rotate a straight walk in place. |
| 24–30 | 1.000–1.250 | Release preparation: jaw opens rapidly; one hind foot is visibly planted while the opposite limb trails/folds; body rises out of the coil. | Make the takeoff one-foot driven. Jaw opening begins before airborne motion, not at the landing. |
| 31–35 | 1.292–1.458 | **Both feet visibly clear the ground**; legs fold under the pelvis while the head stays open and forward. | This is the required real jump window. Preserve an explicit airborne interval of about 0.17–0.21 s at 24 fps rather than two adjacent grounded keys. |
| 36–38 | 1.500–1.583 | First visible landing/catch: lead/near foot reaches the floor; the trailing foot remains airborne behind; body continues forward. | Land with one foot first and keep the second foot late; do not make a symmetric two-foot plant. |
| 39–57 | 1.625–2.375 | Low forward charge with alternating catches. Near leg cycles through stance while the other folds/reaches; trunk stays relatively low; jaw remains deliberately open. | Blend flight into a low charge through velocity continuity; leg motion should be one linked chain (hip → knee → ankle/toes), not independent pulls. |
| 58–82 | 2.417–3.417 | Continued committed stride. Contacts alternate and the planted foot travels from rear/under-body toward a forward catch; head begins to lower while gape persists. | Add a visible braking/weight-absorption arc before feeding descent; avoid holding a constant airborne “run” pose. |
| 83–96 | 3.458–4.000 | Stride commitment eases; body begins to settle before the camera cut. Jaw is still open in the side view. | Do not close the bite at the first landing; keep the attack read open through the deceleration, then hand off to a grounded recovery. |

The most defensible jump landmarks from the side/three-quarter pixels are: planted takeoff support through roughly frame 30 (1.250 s), toe-off between frames 30–31 (1.250–1.292 s), unequivocal airborne frames 32–35 (1.333–1.458 s), and first visible lead-foot contact at frame 36 (1.500 s). Frame 31 is transitional/ambiguous because the toes are near the ground line and the camera is still settling.

This interim table is being refined with the 4.05–12.04 s feeding section and frame-level jaw/landing checks.
