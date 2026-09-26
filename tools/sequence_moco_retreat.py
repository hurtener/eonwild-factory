#!/usr/bin/env python3
"""Backward contact task from an adopted grounded state; exact-model audit."""
import argparse,hashlib,json,copy
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares,brentq
from scipy.spatial.transform import Rotation
from scipy.special import logsumexp
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline
from eonwild_motion.solve.moco_retreat_task import RetreatPlan
from eonwild_motion.solve.moco_tasks import smooth

ap=argparse.ArgumentParser()
for n in ('source','baseline','plan','output'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
source=json.loads(a.source.read_text());meta=source['metadata'];first=source['frames'][0]
spec=json.loads(a.plan.read_text());recipe=copy.deepcopy(meta['recipe'])
recipe['calibrated_task']['surface_edge_pads']=spec.get('surface_edge_pads',False)
# Finite state adoption does not need to regenerate a periodic contact seed.
if spec.get('family'):
 recipe['coordination'].get('path_task',{}).pop('temporal_contact_seed',None)
p=Coordination(meta['admission'],recipe,json.loads(a.baseline.read_text()),a.output)
ix=p.index;initial=np.array([first['coordinates'][n]['value'] for n in p.names]);zeros=np.zeros(len(initial))
if max(abs(first['coordinates'][n]['speed']) for n in p.names)>1e-6:raise ValueError('First retreat checkpoint requires grounded rest adoption')
p.set_state(0,initial,zeros);com=p.model.calcMassCenterPosition(p.state).to_numpy().copy()
feet={side:dict(origin=first['bodies']['toe_'+side]['origin'],rotation=first['bodies']['toe_'+side]['rotation'],digit=first['coordinates']['digit_'+side]['value']) for side in ('l','r')}
plan_type=RetreatPlan
if spec.get('family'):
 from eonwild_motion.solve.moco_placement_task import PlacementPlan
 plan_type=PlacementPlan
plan=plan_type(spec,feet,p.metadata['foot_geometry'],p.admission['step_length_m'],p.L)
attention=None;attention_rows=[]
if spec.get('attention_profile'):
 from eonwild_motion.solve.moco_attention import ProfileAttention
 attention=ProfileAttention(json.loads(Path(spec['attention_profile']).read_text()),p.metadata,'scan')
 attention_indices=[ix[n] for n in attention.names]
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
def pad_height(position,rotation,digit,side):
 values=[];distal=Rotation.from_rotvec([0.,0.,digit]).as_matrix()
 for site in geometry.get('sites_by_side',{}).get(side,geometry['sites']):
  point=np.asarray(site['center_local_m'])
  if site.get('distal'):point=np.asarray(geometry['toe_midpoint_m'])+distal@point
  values.append((position+rotation@point)[1]-site['radius_m'])
 # Smooth lowest-pad witness avoids a derivative corner at a left/right pad swap.
 return -float(logsumexp(-500*np.asarray(values)))/500
for time in times:
 world=initial.copy();target_com=balance(time)
 world[ix['forward']]+=target_com[0]-com[0];world[ix['lateral']]+=target_com[1]-com[2]
 if spec.get('family'):
  world[ix['yaw']]+=plan.heading(time)
  if attention:
   p.set_state(time,world,zeros)
   def heading(values):
    for i,v in zip(attention_indices,values):p.coordinates[i].setValue(p.state,float(v),False)
    p.model.realizePosition(p.state);angles=[]
    for body in ('head','trunk'):
     R=p.model.getBodySet().get(body).getTransformInGround(p.state).R()
     angles.append(np.arctan2(-R.get(2,0),R.get(0,0)))
    return float(np.degrees(np.arctan2(np.sin(angles[0]-angles[1]),np.cos(angles[0]-angles[1]))))
   values,receipt=attention.solve(plan.attention_degrees(time),heading)
   world[attention_indices]=values;attention_rows.append(dict(time_s=float(time),**receipt))
 # Small relaxed tail reaction to the horizontal mass-transfer velocity.
 # Distributed across admitted lengths; explicit secondary task, not muscles.
 for part in ([] if spec.get('finite_coordination') else p.metadata.get('tail_chain',[])):
  tail_time=max(0.,time-spec['tail_delay_s']*(part['arc_end_m']/p.metadata['tail_chain'][-1]['arc_end_m']))
  vy=balance(tail_time,1)[1]
  total=spec['tail_response_gain']*np.arctan2(-vy,spec['velocity_scale_mps'])
  world[ix[part['body']+'_yaw']]+=total*part['length_m']/p.metadata['tail_chain'][-1]['arc_end_m']
 # Planted support has priority over a reduced COM reference. Jointly solve
 # pelvis lateral position and both legs so COM targets cannot tip a sole.
 if spec.get('planted_whole_body'):
  names=[name for side in ('l','r') for name in ['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side,'digit_'+side]]
  indices=[ix[name] for name in names]
  bounds=np.array([p.metadata['coordinates'][name]['bounds_rad'] for name in names]).T
  margin=.01*(bounds[1]-bounds[0]);bounds[0]+=margin;bounds[1]-=margin
  lower=np.r_[initial[ix['lateral']]-p.L*.25,bounds[0]]
  upper=np.r_[initial[ix['lateral']]+p.L*.25,bounds[1]]
  targets={side:plan.foot(time,side) for side in ('l','r')}
  target_pads={side:pad_height(*targets[side],side) for side in ('l','r')}
  p.set_state(time,world,zeros)
  def whole_residual(x):
   p.coordinates[ix['lateral']].setValue(p.state,float(x[0]),False)
   for i,v in zip(indices,x[1:]):p.coordinates[i].setValue(p.state,float(v),False)
   p.model.realizePosition(p.state);res=[]
   for side in ('l','r'):
    target,orientation,digit=targets[side];toe=p.model.getBodySet().get('toe_'+side)
    pos=toe.getPositionInGround(p.state).to_numpy();mat=toe.getTransformInGround(p.state).R()
    R=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
    actual_digit=x[1+names.index('digit_'+side)]
    # Strong material placement and sole orientation; no ankle roll degree
    # of freedom is added and no contact anchor is translated.
    res.extend(20*np.array([pos[0]-target[0],pad_height(pos,R,actual_digit,side)-target_pads[side],pos[2]-target[2]])/p.L)
    res.extend(4*Rotation.from_matrix(orientation.T@R).as_rotvec())
    res.append(.4*(actual_digit-digit))
   actual=p.model.calcMassCenterPosition(p.state).to_numpy()
   res.extend([.05*(actual[2]-target_com[1])/p.L,.2*(actual[0]-target_com[0])/p.L])
   res.extend(.001*(x[1:]-initial[indices]))
   return np.array(res)
  seed=np.r_[previous[ix['lateral']],previous[indices]]
  opt=least_squares(whole_residual,np.clip(seed,lower+1e-6,upper-1e-6),bounds=(lower,upper),max_nfev=70,ftol=1e-9,xtol=1e-9,gtol=1e-9)
  world[ix['lateral']]=opt.x[0];world[indices]=opt.x[1:]
  residual=whole_residual(opt.x)
  for j,side in enumerate(('l','r')):
   errors.append(float(np.linalg.norm(residual[j*7:j*7+3])*p.L/20))
   ik_receipts.append(dict(time_s=float(time),side=side,nfev=int(opt.nfev),success=bool(opt.success)))
  p.set_state(time,world,zeros)
  com_errors.append(float(np.linalg.norm(p.model.calcMassCenterPosition(p.state).to_numpy()[[0,2]]-target_com)))
 else:
  # Reconcile articulated COM displacement from limb/tail motion, then solve
  # feet again. A loaded foot is never translated as a body correction.
  for iteration in range(3):
   p.set_state(time,world,zeros)
   for side in ('l','r'):
    target,orientation,digit=plan.foot(time,side)
    target_pad=pad_height(target,orientation,digit,side)
    names=['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side,'digit_'+side]
    indices=[ix[n] for n in names];coords=[p.coordinates[i] for i in indices];toe=p.model.getBodySet().get('toe_'+side)
    def residual(x):
     for c,val in zip(coords,x):c.setValue(p.state,float(val),False)
     p.model.realizePosition(p.state);pos=toe.getPositionInGround(p.state).to_numpy();mat=toe.getTransformInGround(p.state).R()
     R=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
     # The sole, not the toe-frame origin, owns vertical contact. The reduced
     # leg has sagittal ankle/MTP hinges: leave sole roll a soft preference so
     # lateral hip loading can use the actual distributed pad geometry.
     position_error=np.array([pos[0]-target[0],pad_height(pos,R,x[-1],side)-target_pad,pos[2]-target[2]])/p.L
     return np.r_[position_error,np.array([.02,.4,.4])*Rotation.from_matrix(orientation.T@R).as_rotvec(),.4*(x[-1]-digit),.001*(x-initial[indices])]
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
np.savez(a.output/'placement-diagnostic.npz',times=times,poses=poses,names=p.names,errors=errors,com_errors=com_errors)
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
 try:offsets.append(brentq(vertical,-.025,.025,xtol=1e-9))
 except ValueError as error:
  raise ValueError(f'Contact settling outside unchanged 25 mm bracket at t={t}: forces minus demand {vertical(-.025)}, {vertical(.025)} N; max foot task error {max(errors)} m') from error
offsets=gaussian_filter1d(offsets,.04/(times[1]-times[0]),mode='nearest')
# Preserve exact initial state and resting contact until preparation begins.
blend=smooth((times-spec['prepare_s'])/spec['adoption_seconds'])
poses[:,ix['height']]+=blend*offsets
trajectory=BoundedJointSpline(times,poses,joint_bounds,bc_type=((1,zeros),(1,zeros)))
p.evaluate_kinematics=lambda x,t:(trajectory(t),trajectory(t,1),trajectory(t,2))
finite_result=None
if spec.get('finite_coordination'):
 from eonwild_motion.solve.moco_finite_coordination import FiniteCoordination
 settings=spec['finite_coordination']
 solve_times=np.linspace(settings['start_s'],settings['end_s'],settings['samples'])
 finite=FiniteCoordination(p,trajectory,solve_times,plan.foot,settings)
 finite_result,finite_receipt=finite.solve()
 p.evaluate_kinematics=lambda x,t:finite.evaluate(finite_result,t)

p.times_dense=times;p.path_task=None;p.speed=0.
p.metadata.pop('path_cycle',None)
sequence=dict(duration_s=duration,travel_direction=spec.get('family','backward'),start_s=spec['prepare_s'],stop_s=plan.end+spec['adoption_seconds'],
 distance_m=float(-plan.final_translation[0]),signed_forward_displacement_m=float(plan.final_translation[0]),steps=len(plan.events),periodic=False,
 method='Finite support task; LIPM horizontal balance prior; exact articulated IK and inverse dynamics, not converged Moco',
 input_state=str(a.source),input_state_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),plan=spec,
 contact_events=[dict(side=e['side'],lift_s=e['lift'],land_s=e['land'],translation_m=e['translation'].tolist()) for e in plan.events],
 max_foot_task_error_m=max(errors),max_horizontal_com_error_m=max(com_errors),contact_depth_range_m=[float(min(offsets)),float(max(offsets))],
 initial_coordinate_error=float(np.max(np.abs(poses[0]-initial))))
if finite_result is not None:
 sequence['method']='Shared finite whole-body coordination with exact OpenSim inverse dynamics, passive forces, contact and distal-release task; not full Moco convergence'
 for key in ('max_foot_task_error_m','max_horizontal_com_error_m','contact_depth_range_m'):
  sequence['seed_'+key]=sequence.pop(key)
 sequence['finite_coordination']=finite_receipt
if attention_rows:
 (a.output/'attention-receipt.json').write_text(json.dumps(attention_rows,indent=2)+'\n')
p.metadata['sequence']=sequence;p.model.printToXML(str(a.output/'model.osim'))
p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,
 model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='AUTHORED_TRANSITION_MODEL',
 classification='Backward support task and reduced balance prior; exact-model audit',user_review='PENDING')
if finite_result is not None:
 p.metadata.update(classification=sequence['method'],status='FINITE_COORDINATION_CANDIDATE')
solve_receipt=dict(success=False,status='AUTHORED_CONTACT_TRANSITION',claim='No full Moco convergence; physical forces and residuals reported')
if finite_result is not None:
 solve_receipt=dict(success=False,status='FINITE_COORDINATION_NOT_FULL_MOCO',optimizer=finite_receipt,claim='Reduced-coordinate finite optimization; no full Moco convergence or forward validation')
for name,data in [('model-receipt',p.metadata),('sequence-receipt',sequence),('ik-receipt',ik_receipts),('solve-receipt',solve_receipt)]:
 (a.output/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
report=p.export(np.zeros(len(p.parameters)));
if finite_result is not None:report['finite_coordination']=finite_receipt
report['method']=sequence['method'];(a.output/'coordination-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
(a.output/'balance-prior.json').write_text(json.dumps(dict(times_s=times.tolist(),support_xz_m=support.tolist(),com_xz_m=balance(times).tolist(),classification='Constant-height zero-angular-momentum LIPM prior; articulated/contact residual remains'),indent=2)+'\n')
print(json.dumps(dict(sequence=sequence,root_rms=report['root_residual_rms_BW_or_BWL'],max_control=report['maximum_control'])),flush=True)
