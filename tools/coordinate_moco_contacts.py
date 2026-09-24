#!/usr/bin/env python3
"""Initialize a connected transition with simultaneous temporal contact IK."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.spatial.transform import Rotation,Slerp
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline
from eonwild_motion.solve.moco_contact_coordination import coordinate_contacts

p=argparse.ArgumentParser()
for name in ('source','targets','baseline','settings','output'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
d=json.loads((a.source/'replay.json').read_text());m=d['metadata'];s=json.loads(a.settings.read_text())
problem=Coordination(m['admission'],copy.deepcopy(m['recipe']),json.loads(a.baseline.read_text()),a.output)
t=np.array([f['time_s'] for f in d['frames']]);q=np.array([[f['coordinates'][n]['value'] for n in problem.names] for f in d['frames']])
mask=(t>=s['start_s'])&(t<=s['end_s']);target=np.load(a.targets);tt=target['times']
positions=CubicSpline(tt,target['positions'],axis=0)(t[mask]);digits=CubicSpline(tt,target['digits'],axis=0)(t[mask])
rotations=np.stack([Slerp(tt,Rotation.from_matrix(target['rotations'][:,j]))(t[mask]).as_matrix() for j in range(2)],axis=1)
q[mask],receipt=coordinate_contacts(problem,t[mask],q[mask],positions,rotations,digits,s)
bounds={problem.index[n]:v['bounds_rad'] for n,v in problem.metadata['coordinates'].items()}
bounds.update({problem.index[n]:v for n,v in problem.recipe['spatial'].get('root_bounds',{}).items() if n in ('pitch','yaw','roll')})
trajectory=BoundedJointSpline(t,q,bounds,bc_type=((1,np.zeros(q.shape[1])),(1,np.zeros(q.shape[1]))))
problem.path_task=None;problem.speed=0.;problem.evaluate_kinematics=lambda unused,times:[trajectory(times,d) for d in range(3)];problem.times_dense=t
problem.metadata.pop('path_cycle',None);problem.metadata['sequence']=copy.deepcopy(m['sequence']);problem.metadata['sequence']['temporal_contact_coordination']=receipt
problem.model.printToXML(str(a.output/'model.osim'))
problem.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=problem.admission,recipe=problem.recipe,model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='CONNECTED_CONTACT_CANDIDATE',user_review='PENDING')
for name,value in [('model-receipt',problem.metadata),('sequence-receipt',problem.metadata['sequence']),('contact-coordination',receipt),('solve-receipt',{'success':False,'status':'TEMPORAL_CONTACT_INITIALIZER_NOT_FULL_MOCO','optimizer':receipt})]:
    (a.output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
np.savez(a.output/'connected-seed.npz',times=t,poses=q,names=problem.names)
report=problem.export(np.zeros(len(problem.parameters)))
print(json.dumps({'root_rms':report['root_residual_rms_BW_or_BWL'],'max_control':report['maximum_control']}),flush=True)
