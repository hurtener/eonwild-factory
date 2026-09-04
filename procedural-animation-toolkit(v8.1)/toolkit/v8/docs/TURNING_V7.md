# Large-Theropod Turning in V7

V7 does not claim a direct fossil-observed turning sequence. It implements a coherent gameplay biomechanics model for a massive biped: attention and the cranio-cervical chain lead path reorientation, the support geometry changes, the pelvis commits, and the tail resists and then follows.

## Timing hierarchy

```text
0–18%     curvature and head/neck lead rise
18–30%    chest participates; inside/outside steps diverge
30–76%    pelvis/root carry most heading change
76–100%   head recenters; tail releases with lag; body settles
```

## Default 35° turn targets

- head relative lead: 11.5°
- neck distributed lead: 7.6°
- chest distributed lead: 3.2°
- pelvis extra commitment: 1.25°
- body lean: 1.8°
- tail root counter target: 3.2°
- tail tip counter target: 7.8°

These are profile values, not universal tyrannosaurid constants.

## Foot geometry

- inside stride scale: 0.80
- outside stride scale: 1.10
- overall turn stride scale: 0.84
- outside swing receives slightly more clearance
- foot yaw follows the local path frame

## Runtime use

The authored 35° turns are validation and discrete-action assets. Continuous player steering should use the same controller concepts with turn amount driven by curvature and speed, not concatenate many fixed 35° clips.
