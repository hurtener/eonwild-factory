#!/usr/bin/env python3
"""Backward contact task from an adopted grounded state; exact-model audit."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares,brentq
from scipy.spatial.transform import Rotation
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline
from eonwild_motion.solve.moco_retreat_task import RetreatPlan
from eonwild_motion.solve.moco_tasks import smooth

ap=argparse.ArgumentParser()
for n in ('source','baseline','plan','output'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
source=json.loads(a.source.read_text());meta=source['metadata'];first=source['frames'][0]
p=Coordination(meta['admission'],meta['recipe'],json.loads(a.baseline.read_text()),a.output)
ix=p.index;initial=np.array([first['coordinates'][n]['value'] for n in p.names]);zeros=np.zeros(len(initial))
if max(abs(first['coordinates'][n]['speed']) for n in p.names)>1e-6:raise ValueError('First retreat checkpoint requires grounded rest adoption')
p.set_state(0,initial,zeros);com=p.model.calcMassCenterPosition(p.state).to_numpy().copy()
feet={side:dict(origin=first['bodies']['toe_'+side]['origin'],rotation=first['bodies']['toe_'+side]['rotation'],digit=first['coordinates']['digit_'+side]['value']) for side in ('l','r')}
spec=json.loads(a.plan.read_text());plan=RetreatPlan(spec,feet,p.metadata['foot_geometry'],p.admission['step_length_m'],p.L)
geometry=p.metadata['foot_geometry'];centers=[];weights=[]
for site in geometry['sites']:
 center=np.array(site['center_local_m']);center[1]-=site['radius_m']
 if site.get('distal'):center+=geometry['toe_midpoint_m']
 centers.append(center);weights.append(site['radius_m']**2*site.get('stiffness_share',1.))
sole={side:np.average(centers,axis=0,weights=weights) for side in ('l','r')}
duration=spec['duration_s'];times=np.linspace(0,duration,int(duration*48)+1)
balance,support=plan.balance(times,com,sole);poses=[];errors=[];ik_receipts=[];com_errors=[]
joint_bounds={ix[n]:tuple(v['bounds_rad']) for n,v in p.metadata['coordinates'].items()}
previous=initial.copy()
for time in times:
 world=initial.copy();target_com=balance(time)
 world[ix['forward']]+=target_com[0]-com[0];world[ix['lateral']]+=target_com[1]-com[2]
 # Small relaxed tail reaction to the horizontal mass-transfer velocity.
 # Distributed across admitted lengths; explicit secondary task, not muscles.
 for part in p.metadata.get('tail_chain',[]):
  tail_time=max(0.,time-spec['tail_delay_s']*(part['arc_end_m']/p.metadata['tail_chain'][-1]['arc_end_m']))
  vy=balance(tail_time,1)[1]
  total=spec['tail_response_gain']*np.arctan2(-vy,spec['velocity_scale_mps'])
  world[ix[part['body']+'_yaw']]+=total*part['length_m']/p.metadata['tail_chain'][-1]['arc_end_m']
 # Reconcile articulated COM displacement from limb/tail motion, then solve
 # feet again. A loaded foot is never translated as a body correction.
 for iteration in range(3):
  p.set_state(time,world,zeros)
  for side in ('l','r'):
   target,orientation,digit=plan.foot(time,side)
   names=['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side,'digit_'+side]
   indices=[ix[n] for n in names];coords=[p.coordinates[i] for i in indices];toe=p.model.getBodySet().get('toe_'+side)
   def residual(x):
    for c,val in zip(coords,x):c.setValue(p.state,float(val),False)
    p.model.realizePosition(p.state);pos=toe.getPositionInGround(p.state).to_numpy();mat=toe.getTransformInGround(p.state).R()
    R=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
    return np.r_[(pos-target)/p.L,.4*Rotation.from_matrix(orientation.T@R).as_rotvec(),.4*(x[-1]-digit),.001*(x-initial[indices])]
   bounds=np.array([p.metadata['coordinates'][n]['bounds_rad'] for n in names]).T
   margin=.01*(bounds[1]-bounds[0]);bounds[0]+=margin;bounds[1]-=margin
   opt=least_squares(residual,np.clip(previous[indices] if iteration==0 else world[indices],bounds[0]+1e-6,bounds[1]-1e-6),bounds=bounds,max_nfev=70,ftol=1e-9,xtol=1e-9,gtol=1e-9)
   world[indices]=opt.x
   if iteration==2:
    errors.append(float(np.linalg.norm(residual(opt.x)[:3])*p.L));ik_receipts.append(dict(time_s=float(time),side=side,nfev=int(opt.nfev),success=bool(opt.success)))
  p.set_state(time,world,zeros);actual=p.model.calcMassCenterPosition(p.state).to_numpy()[[0,2]];delta=target_com-actual
  if iteration<2:world[[ix['forward'],ix['lateral']]]+=delta
  else:com_errors.append(float(np.linalg.norm(delta)))
 poses.append(world.copy());previous=world
poses=np.array(poses)
# Re-evaluate vertical pad compression under this finite articulated trajectory.
heights=[]
for t,q in zip(times,poses):
 p.set_state(t,q,zeros);heights.append(p.model.calcMassCenterPosition(p.state).get(1))
demand=p.bw+p.metadata['mass_kg']*gaussian_filter1d(CubicSpline(times,heights,bc_type=((1,0.),(1,0.)))(times,2),1.)
if min(demand)<=0:raise ValueError('Retreat demands unsupported vertical acceleration')
offsets=[]
for t,q,load in zip(times,poses,demand):
 def vertical(dy):
  pose=q.copy();pose[ix['height']]+=dy;p.set_state(t,pose,zeros)
  return sum(f.getRecordValues(p.state).get(1) for f in p.contact_forces)-load
 offsets.append(brentq(vertical,-.025,.025,xtol=1e-9))
offsets=gaussian_filter1d(offsets,.04/(times[1]-times[0]),mode='nearest')
# Preserve exact initial state and resting contact until preparation begins.
blend=smooth((times-spec['prepare_s'])/spec['adoption_seconds'])
poses[:,ix['height']]+=blend*offsets
trajectory=BoundedJointSpline(times,poses,joint_bounds,bc_type=((1,zeros),(1,zeros)))
p.evaluate_kinematics=lambda x,t:(trajectory(t),trajectory(t,1),trajectory(t,2))
p.times_dense=times;p.path_task=None;p.speed=0.
p.metadata.pop('path_cycle',None)
sequence=dict(duration_s=duration,travel_direction='backward',start_s=spec['prepare_s'],stop_s=plan.end+spec['adoption_seconds'],
 distance_m=float(-plan.final_translation[0]),signed_forward_displacement_m=float(plan.final_translation[0]),steps=4,periodic=False,
 method='Backward-specific support task; LIPM horizontal balance prior; exact articulated IK and inverse dynamics, not converged Moco',
 input_state=str(a.source),input_state_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),plan=spec,
 contact_events=[dict(side=e['side'],lift_s=e['lift'],land_s=e['land'],translation_m=e['translation'].tolist()) for e in plan.events],
 max_foot_task_error_m=max(errors),max_horizontal_com_error_m=max(com_errors),contact_depth_range_m=[float(min(offsets)),float(max(offsets))],
 initial_coordinate_error=float(np.max(np.abs(poses[0]-initial))))
p.metadata['sequence']=sequence;p.model.printToXML(str(a.output/'model.osim'))
p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,
 model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='AUTHORED_TRANSITION_MODEL',
 classification='Backward support task and reduced balance prior; exact-model audit',user_review='PENDING')
for name,data in [('model-receipt',p.metadata),('sequence-receipt',sequence),('ik-receipt',ik_receipts),('solve-receipt',dict(success=False,status='AUTHORED_CONTACT_TRANSITION',claim='No full Moco convergence; physical forces and residuals reported'))]:
 (a.output/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
report=p.export(np.zeros(len(p.parameters)));report['method']=sequence['method'];(a.output/'coordination-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
(a.output/'balance-prior.json').write_text(json.dumps(dict(times_s=times.tolist(),support_xz_m=support.tolist(),com_xz_m=balance(times).tolist(),classification='Constant-height zero-angular-momentum LIPM prior; articulated/contact residual remains'),indent=2)+'\n')
print(json.dumps(dict(sequence=sequence,root_rms=report['root_residual_rms_BW_or_BWL'],max_control=report['maximum_control'])),flush=True)
