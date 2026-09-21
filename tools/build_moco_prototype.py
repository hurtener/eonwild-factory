#!/usr/bin/env python3
"""Build/solve optional OpenSim Moco mechanics from semantic admission JSON."""
import argparse
from pathlib import Path
from eonwild_motion.solve.moco_prototype import run

p = argparse.ArgumentParser()
p.add_argument("--admission", type=Path, required=True)
p.add_argument("--recipe", type=Path, default=Path("catalog/behaviors/moco-stride-prototype.v1.json"))
p.add_argument("--output", type=Path, required=True)
p.add_argument("--mesh", type=int, default=25)
p.add_argument("--warm-start", type=Path)
p.add_argument("--build-only", action="store_true")
a = p.parse_args()
result = run(a.admission, a.recipe, a.output, a.mesh, a.warm_start, a.build_only)
if result is not None and not result['success']:
    raise SystemExit(2)
