#!/usr/bin/env python3
"""Refine only unloaded MTP compliance in an existing finite diagnostic."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_distal_release import released_forefoot
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline

ap=argparse.ArgumentParser()
for key in ('source','baseline','policy','output'):ap.add_argument('--'+key,type=Path,required=True)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
source=json.loads((a.source/'replay.json').read_text());meta=source['metadata'];rows=source['frames']
policy=json.loads(a.policy.read_text());recipe=copy.deepcopy(meta['recipe'])
# The saved finite trajectory supplies state; no new periodic IK seed is used.
construction=copy.deepcopy(recipe);construction['coordination']['path_task'].pop('temporal_contact_seed',None)
p=Coordination(meta['admission'],construction,json.loads(a.baseline.read_text()),a.output)
times=np.array([r['time_s'] for r in rows]);q=np.array([[r['coordinates'][n]['value'] for n in p.names] for r in rows]);original=q.copy()
receipts={}
for side in ('l','r'):
    load=[];torque=[];inertia=[]
    for row in rows:
        pivot=np.array(row['bodies']['toe_'+side]['origin'])
        axis=np.array(row['bodies']['metatarsus_'+side]['rotation'])[:,2]
        moment=0.;equivalent=0.
        for part in ('toe_','digit_'):
            name=part+side;segment=meta['segments'][name];body=row['bodies'][name]
            mass=segment['mass_kg'];offset=np.array(body['com'])-pivot;R=np.array(body['rotation'])
            moment+=np.dot(axis,np.cross(offset,np.array([0.,-9.80665*mass,0.])))
            equivalent+=axis@(R@np.array(segment['inertia_kg_m2'])@R.T)@axis+mass*(offset@offset-(offset@axis)**2)
        load.append(sum(c['force_N'][1] for c in row['contacts'] if c['name'].endswith('_'+side))/(meta['mass_kg']*9.80665))
        torque.append(moment);inertia.append(equivalent)
    delta,windows=released_forefoot(times,load,torque,inertia,policy)
    index=p.index['mtp_'+side];q[:,index]+=delta
    lo,hi=meta['coordinates']['mtp_'+side]['bounds_rad']
    if np.any(q[:,index]<lo) or np.any(q[:,index]>hi):raise ValueError('Requested distal compliance exceeds anatomical bounds; reduce the declared compliance')
    receipts[side]=dict(windows=windows,maximum_added_sag_degrees=float(-np.min(delta)*180/np.pi),
        inertia_range_kg_m2=[float(min(inertia)),float(max(inertia))],
        gravity_torque_range_Nm=[float(min(torque)),float(max(torque))],
        changed_loaded_samples=int(np.count_nonzero((np.asarray(load)>=policy['unloaded_threshold_BW']) & (delta!=0))))
bounds={p.index[n]:v['bounds_rad'] for n,v in meta['coordinates'].items()}
trajectory=BoundedJointSpline(times,q,bounds,bc_type=((1,np.zeros(len(p.names))),(1,np.zeros(len(p.names)))))
p.evaluate_kinematics=lambda x,t:(trajectory(t),trajectory(t,1),trajectory(t,2))
p.times_dense=times;p.path_task=None;p.recipe=recipe
p.recipe['distal_release']=policy
p.metadata['sequence']=copy.deepcopy(meta['sequence'])
p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,
    status='DISTAL_COMPLIANCE_DIAGNOSTIC',classification=__doc__.strip(),user_review='PENDING',
    distal_release=dict(source=str(a.source),source_sha256=hashlib.sha256((a.source/'solution.sto').read_bytes()).hexdigest(),policy=policy,feet=receipts))
p.model.printToXML(str(a.output/'model.osim'));p.metadata['model_sha256']=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest()
(a.output/'model-receipt.json').write_text(json.dumps(p.metadata,indent=2)+'\n')
(a.output/'distal-release-receipt.json').write_text(json.dumps(p.metadata['distal_release'],indent=2)+'\n')
report=p.export(np.zeros(len(p.parameters)))
(a.output/'solve-receipt.json').write_text(json.dumps(dict(success=False,status='REDUCED_DISTAL_COMPLIANCE',claim='Gravity-driven distal response with authored impedance and preparation; fresh inverse dynamics audit, not full Moco convergence'),indent=2)+'\n')
print(json.dumps(dict(feet=receipts,root_residual=report['root_residual_rms_BW_or_BWL'],maximum_control=report['maximum_control'])),flush=True)
