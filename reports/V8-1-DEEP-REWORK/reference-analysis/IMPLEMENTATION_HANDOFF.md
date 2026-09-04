# V8.1 implementation handoff — source-grounded anchors

Source: `procedural-animation-toolkit(v8)/inputs/v8/tarbosaurus-attack-eat-reference.mp4`, 24 fps.

Use these source-frame anchors for the first V8.1 tuning pass:

| Event | Source frames | Time |
|---|---:|---:|
| Attack jaw onset | 25 | 1.042 s |
| Last clear takeoff support | 30 | 1.250 s |
| Toe-off transition | 30–31 | 1.250–1.292 s |
| Both feet unequivocally airborne | 32–35 | 1.333–1.458 s |
| Approximate flight apex | 33–34 | 1.375–1.417 s |
| Lead/near foot first landing | 36 | 1.500 s |
| Lead-only absorption before opposite catch | 36–39 | 1.500–1.625 s |
| Alternating catches / low charge | 40–82 | 1.667–3.417 s |
| Brake/settle | 83–99 | 3.458–4.125 s |
| Camera cut | 100 | 4.167 s |
| Feeding gape clearly open | 228 | 9.500 s |
| First visible carcass adjacency/contact window | 238–240 | 9.917–10.000 s |
| Clamp/brace | 240–270 | 10.000–11.250 s |
| Release/head recovery | 276–288 | 11.500–12.000 s |

Implementation decisions grounded in the pixels:

1. Keep the initial frame-0 display gape separate from the attack gape. The initial gape narrows by frames 5–12; the attack gape starts at frame 25 and is wide through flight.
2. Make takeoff one-foot driven. Keep one clear support through frame 30, use a short toe-off transition, and require a real two-feet-clear interval at frames 32–35. Frame 31 is ambiguous.
3. Land the lead foot first at frame 36 and hold a short single-foot absorption before the trailing/opposite catch. Do not blend into a symmetric two-foot landing.
4. Generate the leg as hip → knee → ankle → toe. The planted foot travels from rear/under-body toward the next forward catch; it does not stay a rigid vertical post.
5. Keep the torso low after landing, brake before feeding, and lower the head/neck after weight is caught. Brace both feet before clamp/tear.
6. Treat frame 100 as a shot boundary. Do not infer a continuous attack-to-carcass path through the camera cut.

Full evidence and limitations:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/attack-eat-reference-v8.1-visual-analysis.md`

Original-resolution selected frames:

`/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-DEEP-REWORK/reference-analysis/selected-frames/`
