# Video-to-Pipeline Notes

The two supplied videos are useful for the core procedural-animation mindset:

- a small set of controllable signals can generate repeatable motion;
- procedural controls should expose meaningful parameters rather than require editing every key;
- noise/phase/driver systems are valuable for ambient variation;
- procedural results can be sampled and baked for ordinary playback.

V2 deliberately extends beyond the tutorials’ simple demonstrations. Creature locomotion requires contact persistence, articulated leg solving, support-aware body balance, and inertial secondary motion. Geometry Nodes remain useful for authoring controls and visual experiments, but ordinary GLB runtime playback requires the final skeletal motion to be sampled into animation channels.

References supplied by the project owner:

- https://www.youtube.com/watch?v=qvqRyRxAmM8 — “So I made Procedural animation in blender!” by Cleverpoly.
- https://www.youtube.com/watch?v=uV3LtA_KiAY — “Animate the Smart Way in Blender (Procedural Animation Tutorial)” by CG Boost.

Additional implementation references used as conceptual cross-checks:

- ground matching, foot contacts, heel/toe handling, and torso leaning;
- procedural walkers that persist contact targets and bake live solutions;
- standard walk-cycle contact, passing, down, and up poses.

These are principles, not copied source code. The package implementation is original and tailored to rich GLB creature rigs.
