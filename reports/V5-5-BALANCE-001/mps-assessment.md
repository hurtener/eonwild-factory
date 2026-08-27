# MPS / GPU acceleration assessment

## Decision

Keep the deterministic V5.5 procedural solver on CPU. Use Blender's existing Metal-backed Eevee path for final rendering.

## Evidence

- The solver is serial NumPy/SciPy `float64` work dominated by many small 3x3 transforms and constrained leg solves.
- The current environment has no PyTorch/MPS implementation to activate without a solver port.
- A port would change numerical behavior and reproducibility, while transfer and dispatch overhead would likely dominate these small operations.
- Blender 5.2 already renders Eevee through Metal on the Apple M4 GPU.
- VideoToolbox could accelerate downstream H.264 preview encoding, but encoding is not the bottleneck and changing encoders would change media hashes/bitrate.

## Follow-up boundary

Treat a batched GPU solver as separate R&D. It should begin with profiling, a deterministic tolerance contract, and a representative batch benchmark—not as a release-path switch inside V5.5.
