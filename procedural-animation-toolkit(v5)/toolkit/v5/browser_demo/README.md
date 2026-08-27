# Tarbosaurus V4 interactive browser demo

This demo uses a dependency-free WebGL2 renderer included in `v4-viewer.js`. It loads the complete 37-clip GLB, performs 75-joint GPU skinning with all three glTF joint/weight sets, and exposes locomotion, terrain, turns, starts/stops, alert states, eating, bite, roar, and transition sequences.

Browsers normally block `fetch()` from `file://`, so serve this folder locally:

```bash
python3 -m http.server 8765
```

Then open:

```text
http://localhost:8765/
```

No package installation or CDN is required.
