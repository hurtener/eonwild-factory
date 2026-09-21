#!/usr/bin/env python3
"""Independent open-loop time stepping of a saved Moco model and controls.

No tracking controller, prescribed pose or root assistance is added. Numerical
drift is reported, not relabeled as a validated dinosaur or hidden by retargeting.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import opensim as o

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
a = p.parse_args()
root = a.directory
source = o.MocoTrajectory(str(root / 'solution.sto'))
model = o.Model(str(root / 'model.osim'))
integrated = o.simulateTrajectoryWithTimeStepping(source, model, 1e-6)
integrated.write(str(root / 'forward-integrated.sto'))
requested_end=float(np.asarray(source.getTimeMat())[-1])
integrated.resampleWithNumTimes(241)
ti = np.asarray(integrated.getTimeMat())
# OpenSim's convenience function exports at 1 kHz, ending at the last full
# millisecond. Compare at those actual times; never stretch either trajectory.
if ti[0] != 0 or requested_end-ti[-1] > .001001:
    raise ValueError('Integrator did not cover the requested interval')
sample_times=o.Vector(len(ti),0)
for i,t in enumerate(ti):sample_times[i]=float(t)
source.resample(sample_times)
reference = np.asarray(source.getStatesTrajectoryMat())
actual = np.asarray(integrated.getStatesTrajectoryMat())
names = list(source.getStateNames())
actual_names = list(integrated.getStateNames())
errors = {}
for i, name in enumerate(names):
    if not name.endswith('/value'):
        continue
    error = actual[:, actual_names.index(name)] - reference[:, i]
    errors[name] = dict(maximum_absolute=float(np.max(np.abs(error))),
                       final=float(error[-1]),
                       unit='m' if name.split('/')[-2] in ('forward', 'height', 'lateral') else 'rad')
result = dict(schema='eonwild.motion.moco-forward-replay.v1',
    scope='OpenSim simulateTrajectoryWithTimeStepping; saved controls and initial state; no pose tracking or root assistance',
    status='MEASURED_NOT_CERTIFIED', integrator_accuracy=1e-6, duration_s=float(ti[-1]),
    requested_duration_s=requested_end,
    model_sha256=hashlib.sha256((root / 'model.osim').read_bytes()).hexdigest(),
    solution_sha256=hashlib.sha256((root / 'solution.sto').read_bytes()).hexdigest(),
    coordinate_errors=errors,
    limitations='One half-stride, open loop, estimated anatomy/contact/strength; no biological or gameplay validation')
(root / 'forward-receipt.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
