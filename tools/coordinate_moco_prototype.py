#!/usr/bin/env python3
"""Generate a smooth, force-aware 3D initialization for Moco continuation."""
import argparse
from eonwild_motion.solve.moco_coordination import run
p=argparse.ArgumentParser()
for name in ('admission','recipe','baseline','output'):p.add_argument('--'+name,required=True)
p.add_argument('--initial');p.add_argument('--evaluate-only',action='store_true')
a=p.parse_args()
run(a.admission,a.recipe,a.baseline,a.output,a.initial,a.evaluate_only)
