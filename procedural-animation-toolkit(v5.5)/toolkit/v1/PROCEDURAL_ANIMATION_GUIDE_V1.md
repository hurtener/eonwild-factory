# Eonwild Procedural Animation Guide — V1

## Mental model

V1 treats normalized gait time as the controller:

```text
phase
  → hip/knee/ankle/foot curves
  → pelvis roll/yaw/pitch
  → spine and neck counter-rotation
  → tail phase wave
  → sampled skeletal Action
```

This is easy to understand and fast to evaluate. It remains useful for learning, diagnostics, and establishing that a rig map is correctly wired.

## Known ceiling

A phase-only FK controller does not know where the ground is, which foot carries weight, whether the center of mass is supported, or how tail inertia should react to body acceleration. Increasing sample count makes the same mechanics smoother but does not solve those missing constraints. Those are the reasons v2 exists.
