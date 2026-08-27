# Procedural Animation Skill v1 — Compatibility Baseline

V1 is preserved because it proved that a dense Meshy/UniRig GLB can be animated directly from semantic tags without reducing the skeleton.

Its locomotion is intentionally simple:

- one normalized gait phase;
- phase-shaped FK rotations;
- preset pelvis and torso counter-rotation;
- a delayed sine wave across the tail;
- 30 Hz sampling;
- no world-space foot locking;
- no neutral-jaw layer;
- no center-of-support calculation.

Run it with:

```bash
python3 scripts/run_pipeline.py \
  --input creature.glb \
  --bone-map creature.bone-map.yml \
  --output-dir output-v1
```

Keep v1 for regression tests, low-cost previews, and rigs whose semantic mapping is incomplete. Use v2 for production-facing locomotion.
