#!/usr/bin/env python3
"""Contact-planned start/stop around a saved spatial walking initializer.

The cycle is a warm pose/secondary-motion reference, not a forward simulation.
Rebuild each foot against world stance anchors, re-evaluate all internal effort
and unsupported root demand, and label the result as an authored diagnostic.
"""
import argparse, json, shutil
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.integrate import cumulative_trapezoid
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares, brentq
from scipy.spatial.transform import Rotation
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_path_task import path_frame, foot_task
from eonwild_motion.solve.moco_tasks import smooth
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline

ap=argparse.ArgumentParser()
for n in ('source','baseline','output'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
source=json.loads((a.source/'replay.json').read_text());meta=source['metadata']
p=Coordination(meta['admission'],meta['recipe'],json.loads(a.baseline.read_text()),a.output)
T=p.period;speed=p.speed;rate=p.path_task['yaw_rate_rad_s'];ix=p.index
rows=source['frames'];ts=np.array([r['time_s'] for r in rows]);q=np.array([[r['coordinates'][n]['value'] for n in p.names] for r in rows])
xyz=[ix[n] for n in ('forward','height','lateral')];angles=[ix[n] for n in ('pitch','yaw','roll')]
origin,R=path_frame(ts,speed,rate)
q[:,xyz]=np.einsum('tji,tj->ti',R,q[:,xyz]-origin)
q[:,angles]=Rotation.from_matrix(np.transpose(R,(0,2,1))@Rotation.from_euler('ZYX',q[:,angles]).as_matrix()).as_euler('ZYX')
q[-1]=q[0]
joint_bounds={ix[n]:tuple(v['bounds_rad']) for n,v in p.metadata['coordinates'].items()}
cycle=BoundedJointSpline(ts,q,joint_bounds,bc_type='periodic');neutral=q[:-1].mean(axis=0)
# Six full strides plus final double support. Slower first step, subsequent
# swing cadence is full pace; deceleration shortens final placement, not swing.
start=2.;duration=16.;cycles=6;end_progress=(cycles+.12)*T
clock_grid=np.linspace(0,14,14001)
clock_rate=.6+.4*smooth(clock_grid/1.)
progress=cumulative_trapezoid(clock_rate,clock_grid,initial=0)
clock=CubicSpline(clock_grid,progress)
inverse=PchipInterpolator(progress,clock_grid)
active_end=float(inverse(end_progress));stop=start+active_end
v=speed*smooth(clock_grid/1.8)*smooth((active_end-clock_grid)/1.8)
distance=CubicSpline(clock_grid,cumulative_trapezoid(v,clock_grid,initial=0))
def travel(tau):return float(distance(float(np.clip(inverse(np.clip(tau,0,end_progress)),0,active_end))))
def frame_at_progress(tau):return path_frame(travel(tau)/speed,speed,rate)
def gain_at_progress(tau):
    t=float(inverse(np.clip(tau,0,end_progress)))
    return float(smooth(t/1.8)*smooth((active_end-t)/1.8))
def anchor(start_tau,mid_tau,side):
    if start_tau < 1e-8:return frame_at_progress(0.)
    if start_tau >= (cycles-.5)*T-1e-8:return frame_at_progress(end_progress)
    return frame_at_progress(mid_tau)
def support_gain(start_tau,tau,side):
    if start_tau >= (cycles-.5)*T-1e-8:return 0.
    if start_tau < 0:return float(smooth(tau/(.10*T)))
    return 1.
seq=SimpleNamespace(policy=p.policy,period=T,speed=speed,admission=p.admission,metadata=p.metadata,
                    anchor_frame=anchor,support_gain=support_gain)
# Actual cycle-vs-task discrepancies retained at steady speed. The finite
# transition fades these small optimization corrections; feet are never fixed
# in the renderer, and final contact is measured after all pose modifications.
correction={}
for side in ('l','r'):
    positions=[];rotvec=[];digits=[]
    for tau,row in zip(ts,rows):
        target,rot,digit=foot_task(p,float(tau),side)
        org,rr=path_frame(tau,speed,rate)
        positions.append(rr.T@(np.array(row['bodies']['toe_'+side]['origin'])-target))
        actual=np.array(row['bodies']['toe_'+side]['rotation'])
        rotvec.append(Rotation.from_matrix(rot.T@actual).as_rotvec())
        digits.append(row['coordinates']['digit_'+side]['value']-digit)
    positions[-1]=positions[0];rotvec[-1]=rotvec[0];digits[-1]=digits[0]
    correction[side]=(CubicSpline(ts,positions,axis=0,bc_type='periodic'),CubicSpline(ts,rotvec,axis=0,bc_type='periodic'),CubicSpline(ts,digits,bc_type='periodic'))
times=np.linspace(0,duration,769);poses=[];errors=[]
for t in times:
    local_t=float(np.clip(t-start,0,active_end));tau=float(clock(local_t));phase=tau%T
    gain=gain_at_progress(tau);local=neutral+gain*(cycle(phase)-neutral)
    local[ix['forward']]*=gain
    # At rest head returns to the body's heading, retaining the reviewed pitch.
    for n in ('chest_yaw','neck_yaw','neck_upper_yaw','head_yaw'):local[ix[n]]*=gain
    org,rr=frame_at_progress(tau);world=local.copy();world[xyz]=org+rr@local[xyz]
    world[angles]=Rotation.from_matrix(rr@Rotation.from_euler('ZYX',local[angles]).as_matrix()).as_euler('ZYX')
    p.set_state(t,world,np.zeros(len(world)))
    for side in ('l','r'):
        target,orientation,digit=foot_task(seq,tau,side)
        dp,dr,dd=correction[side];target=target+gain*rr@dp(phase)
        orientation=orientation@Rotation.from_rotvec(gain*dr(phase)).as_matrix()
        digit+=gain*float(dd(phase))
        names=['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side,'digit_'+side]
        indices=[ix[n] for n in names];coords=[p.coordinates[i] for i in indices]
        reference=cycle(phase)[indices];toe=p.model.getBodySet().get('toe_'+side)
        def residual(x):
            for c,val in zip(coords,x):c.setValue(p.state,float(val),False)
            p.model.realizePosition(p.state)
            pos=toe.getPositionInGround(p.state).to_numpy();mat=toe.getTransformInGround(p.state).R()
            rot=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
            return np.r_[(pos-target)/p.L,.4*Rotation.from_matrix(orientation.T@rot).as_rotvec(),.4*(x[-1]-digit),.001*(x-reference)]
        bounds=np.array([p.metadata['coordinates'][n]['bounds_rad'] for n in names]).T
        margin=.01*(bounds[1]-bounds[0]);bounds[0]+=margin;bounds[1]-=margin
        # Warm from this cycle pose to avoid history-dependent branch switches.
        opt=least_squares(residual,np.clip(reference,bounds[0]+1e-6,bounds[1]-1e-6),bounds=bounds,max_nfev=35,ftol=1e-9,xtol=1e-9,gtol=1e-9)
        world[indices]=opt.x
        errors.append(float(np.linalg.norm(residual(opt.x)[:3])*p.L))
    poses.append(world)
poses=np.array(poses)
# Settle contact compression with the unchanged contact law. Match the vertical
# demand of the planned COM trajectory, then smooth the tiny depth correction.
# This adds no force actuator; replay measures the residual after correction.
com_height=[]
for pose,time in zip(poses,times):
    p.set_state(time,pose,np.zeros(len(p.names)))
    com_height.append(p.model.calcMassCenterPosition(p.state).get(1))
com_spline=CubicSpline(times,com_height,bc_type=((1,0.),(1,0.)))
demand=p.bw+p.metadata['mass_kg']*gaussian_filter1d(com_spline(times,2),1.,mode='nearest')
if np.min(demand)<=0:raise ValueError('Walking plan requires unsupported negative vertical contact load')
offsets=[]
for pose,time,load in zip(poses,times,demand):
    def balance(offset):
        values=pose.copy();values[ix['height']]+=offset
        p.set_state(time,values,np.zeros(len(values)))
        return sum(f.getRecordValues(p.state).get(1) for f in p.contact_forces)-load
    offsets.append(brentq(balance,-.025,.025,xtol=1e-9))
offsets=gaussian_filter1d(offsets,.04/(times[1]-times[0]),mode='nearest')
poses[:,ix['height']]+=offsets
rest_offsets=[float(offsets[0]),float(offsets[-1])]
trajectory=BoundedJointSpline(times,poses,joint_bounds,bc_type=((1,np.zeros(len(p.names))),(1,np.zeros(len(p.names)))))
p.evaluate_kinematics=lambda x,t:(trajectory(t),trajectory(t,1),trajectory(t,2))
p.times_dense=times
p.metadata.pop('path_cycle',None)
p.metadata['sequence']=dict(duration_s=duration,start_s=start,stop_s=stop,steady_speed_mps=speed,
    distance_m=travel(end_progress),steps=2*cycles,first_step_cadence_ratio=.6,acceleration_seconds=1.8,deceleration_seconds=1.8,
    method='Authored cadence and support plan; IK in exact anatomy; inverse dynamics audit, not forward simulation or optimal control',
    max_foot_task_error_m=max(errors),rest_contact_offsets_m=rest_offsets,contact_depth_correction_range_m=[float(offsets.min()),float(offsets.max())],source=str(a.source),periodic=False)
# The mechanics/nose report must not subtract a constant-velocity path from a
# finite sequence. Physical joint efforts/root residuals never use this field.
p.path_task=None
p.model.printToXML(str(a.output/'model.osim'))
import hashlib
p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,
    model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='AUTHORED_TRANSITION_MODEL',
    classification='C52 B revised 16-second walking sequence; inverse-dynamics diagnostic',user_review='PENDING')
(a.output/'model-receipt.json').write_text(json.dumps(p.metadata,indent=2)+'\n')
report=p.export(np.zeros(len(p.parameters)))
(a.output/'sequence-receipt.json').write_text(json.dumps(p.metadata['sequence'],indent=2)+'\n')
(a.output/'solve-receipt.json').write_text(json.dumps(dict(success=False,status='AUTHORED_CONTACT_TRANSITION',
    source_status=source['report']['optimizer']['status'],claim='Bounded IK and inverse-dynamics audit only; not a converged dynamics solution'),indent=2)+'\n')
print(json.dumps({'sequence':p.metadata['sequence'],'root_rms':report['root_residual_rms_BW_or_BWL'],'maximum_control':report['maximum_control']}),flush=True)
