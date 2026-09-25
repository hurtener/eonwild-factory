#!/usr/bin/env python3
"""Polish a saved periodic trajectory with shared temporal contact IK.

Preserve the existing root/axial trajectory and world foot targets. This is
contact-constrained kinematic refinement with a fresh inverse-dynamics audit,
not Moco convergence or a new gait generator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_contact_coordination import coordinate_contacts
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline

ap=argparse.ArgumentParser()
for key in ('source','baseline','settings','output'):ap.add_argument('--'+key,type=Path,required=True)
ap.add_argument('--recipe',type=Path)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
source=json.loads((a.source/'replay.json').read_text());meta=source['metadata']
settings=json.loads(a.settings.read_text())
if abs(meta['recipe']['coordination']['path_task']['yaw_rate_rad_s'])>1e-12:
    raise ValueError('Periodic contact polish currently requires a straight local path')
if a.recipe:meta['recipe']=json.loads(a.recipe.read_text())
if not settings.get('periodic') or settings.get('optimize_root',True):
    raise ValueError('This tool requires periodic limb-only contact coordination')
p=Coordination(meta['admission'],meta['recipe'],json.loads(a.baseline.read_text()),a.output)
rows=source['frames'];times=np.array([r['time_s'] for r in rows])
q=np.array([[r['coordinates'][name]['value'] for name in p.names] for r in rows])
positions=[];rotations=[];digits=[];weights=[];forces=[]
for time,pose in zip(times,q):
    p.set_state(time,pose,np.zeros(len(p.names)));fp=[];fr=[];fd=[];fw=[];ff=[]
    for side,foot in zip(('l','r'),p.feet):
        fp.append(foot.getPositionInGround(p.state).to_numpy());R=foot.getTransformInGround(p.state).R()
        fr.append([[R.get(i,j) for j in range(3)] for i in range(3)])
        fd.append(pose[p.index['digit_'+side]])
        load=sum(p.model.getForceSet().get(c['force']).getRecordValues(p.state).get(1) for c in p.metadata['contacts'] if c['force'].endswith('_'+side))/p.bw
        ff.append(load)
        fw.append(1.+settings.get('loaded_contact_multiplier',1.)*min(1.,max(0.,load/.1)))
    positions.append(fp);rotations.append(fr);digits.append(fd);weights.append(fw);forces.append(ff)
poses,receipt=coordinate_contacts(p,times,q,np.array(positions),np.array(rotations),np.array(digits),settings,np.array(weights),np.array(forces))
# Remove linear root travel for a periodic interpolant, then restore it exactly.
travel=np.zeros(len(p.names));travel[p.index['forward']]=p.speed
local=poses-times[:,None]*travel;local[-1]=local[0]
bounds={p.index[n]:v['bounds_rad'] for n,v in p.metadata['coordinates'].items()}
trajectory=BoundedJointSpline(times,local,bounds,bc_type='periodic')
p.evaluate_kinematics=lambda x,t:(trajectory(t)+np.asarray(t)[:,None]*travel,trajectory(t,1)+travel,trajectory(t,2))
p.times_dense=times;p.path_task=None
p.recipe['periodic_contact_polish']=settings
p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,
    status='TEMPORAL_CONTACT_POLISH',classification=__doc__.strip(),user_review='PENDING',
    contact_polish=dict(source=str(a.source),source_sha256=hashlib.sha256((a.source/'solution.sto').read_bytes()).hexdigest(),receipt=receipt))
p.model.printToXML(str(a.output/'model.osim'))
p.metadata['model_sha256']=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest()
(a.output/'model-receipt.json').write_text(json.dumps(p.metadata,indent=2)+'\n')
(a.output/'temporal-contact-coordination.json').write_text(json.dumps(receipt,indent=2)+'\n')
report=p.export(np.zeros(len(p.parameters)))
(a.output/'solve-receipt.json').write_text(json.dumps(dict(success=False,status='TEMPORAL_CONTACT_POLISH',
    claim='Kinematic refinement and inverse-dynamics audit; not full Moco convergence'),indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['root_residual_rms_BW_or_BWL','maximum_control','nose_range_m']}),flush=True)
