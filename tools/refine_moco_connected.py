#!/usr/bin/env python3
"""Refine a connected handoff window using the shared finite coordinator."""
import argparse,hashlib,json,copy
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.spatial.transform import Rotation,Slerp
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_finite_coordination import FiniteCoordination
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline

p=argparse.ArgumentParser()
for n in ('source','baseline','settings','output'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
m=json.loads((a.source/'model-receipt.json').read_text());settings=json.loads(a.settings.read_text())
problem=Coordination(m['admission'],copy.deepcopy(m['recipe']),json.loads(a.baseline.read_text()),a.output)
d=np.load(a.source/'connected-seed.npz');times=d['times'];q=d['poses']
bounds={problem.index[n]:tuple(v['bounds_rad']) for n,v in problem.metadata['coordinates'].items()}
bounds.update({problem.index[n]:tuple(v) for n,v in problem.recipe['spatial'].get('root_bounds',{}).items() if n in ('pitch','yaw','roll')})
trajectory=BoundedJointSpline(times,q,bounds,bc_type=((1,np.zeros(len(problem.names))),(1,np.zeros(len(problem.names)))))
targets=np.load(a.source/'foot-targets.npz');positions=CubicSpline(times,targets['positions'],axis=0);digits=CubicSpline(times,targets['digits'],axis=0)
rotations=[Slerp(times,Rotation.from_matrix(targets['rotations'][:,j])) for j in range(2)]
def foot(t,side):
 j=('l','r').index(side);return positions(t)[j],rotations[j](float(t)).as_matrix(),float(digits(t)[j])
finite=FiniteCoordination(problem,trajectory,np.linspace(settings['start_s'],settings['end_s'],settings['samples']),foot,settings)
x,receipt=finite.solve();problem.evaluate_kinematics=lambda unused,t:finite.evaluate(x,t);problem.times_dense=times
problem.metadata.pop('path_cycle',None)
seq=copy.deepcopy(m['sequence']);seq['finite_coordination']=[receipt];seq['seed_source']=str(a.source);seq['seed_source_sha256']=hashlib.sha256((a.source/'solution.sto').read_bytes()).hexdigest()
problem.metadata['sequence']=seq;problem.model.printToXML(str(a.output/'model.osim'))
problem.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=problem.admission,recipe=problem.recipe,model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='CONNECTED_FINITE_CANDIDATE',classification=seq['method'],user_review='PENDING')
for name,value in [('model-receipt',problem.metadata),('sequence-receipt',seq),('solve-receipt',dict(success=False,status='CONNECTED_FINITE_NOT_FULL_MOCO',optimizer=receipt))]:
 (a.output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
report=problem.export(np.zeros(len(problem.parameters)));print(json.dumps(dict(root_rms=report['root_residual_rms_BW_or_BWL'],max_control=report['maximum_control'])),flush=True)
