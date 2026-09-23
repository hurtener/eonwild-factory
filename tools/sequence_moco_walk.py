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
ap.add_argument('--turn-plan',type=Path)
ap.add_argument('--attention-profile',type=Path)
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
turn_plan=None
if a.turn_plan:
    from eonwild_motion.solve.moco_turn_plan import TurnPlan
    def sequence_velocity(t):
        active=np.clip(np.asarray(t)-start,0,active_end)
        return speed*smooth(active/1.8)*smooth((active_end-active)/1.8)
    turn_plan=TurnPlan(json.loads(a.turn_plan.read_text()),duration,sequence_velocity)
attention=None;attention_rows=[]
if a.attention_profile:
    if turn_plan is None:raise ValueError('Profile attention requires a turn plan')
    from eonwild_motion.solve.moco_attention import ProfileAttention
    attention=ProfileAttention(json.loads(a.attention_profile.read_text()),p.metadata,
                               turn_plan.specification['attention_mode'])
    peak_lead=max(abs(turn_plan.attention(float(t))) for t in np.linspace(0,duration,1601))
    if peak_lead<1e-8:raise ValueError('Attention turn must have nonzero planned lead')
    attention_indices=[ix[n] for n in attention.names]
    attention_coords=[p.coordinates[i] for i in attention_indices]
    attention.description.update(profile_path=str(a.attention_profile),
        profile_sha256=__import__('hashlib').sha256(a.attention_profile.read_bytes()).hexdigest(),
        heading_reference='skull forward projected horizontally relative to trunk forward')
def frame_at_progress(tau):
    if turn_plan:return turn_plan.frame(start+float(inverse(np.clip(tau,0,end_progress))))
    return path_frame(travel(tau)/speed,speed,rate)
def gain_at_progress(tau):
    t=float(inverse(np.clip(tau,0,end_progress)))
    return float(smooth(t/1.8)*smooth((active_end-t)/1.8))
def anchor_progress(start_tau,mid_tau):
    if start_tau < 1e-8:return 0.
    if start_tau >= (cycles-.5)*T-1e-8:return end_progress
    return mid_tau
def anchor(start_tau,mid_tau,side):
    return frame_at_progress(anchor_progress(start_tau,mid_tau))
def support_gain(start_tau,tau,side):
    if start_tau >= (cycles-.5)*T-1e-8:return 0.
    if start_tau < 0:return gain_at_progress(tau)
    return 1.
seq=SimpleNamespace(policy=p.policy,period=T,speed=speed,admission=p.admission,metadata=p.metadata,
                    anchor_frame=anchor,support_gain=support_gain)
steering=turn_plan.specification.get('step_steering') if turn_plan else None
if steering:
    from eonwild_motion.solve.moco_turn_plan import attenuate_heading_correction
    def support_context(start_tau,mid_tau):
        progress=anchor_progress(start_tau,mid_tau)
        native=start+float(inverse(np.clip(progress,0,end_progress)))
        # Convert half a gait cycle to native time, including the first step.
        before=float(inverse(np.clip(progress-T*.25,0,end_progress)))
        after=float(inverse(np.clip(progress+T*.25,0,end_progress)))
        return native,max(after-before,T*.25)
    def support_outward(start_tau,mid_tau,side,outward):
        native,step_seconds=support_context(start_tau,mid_tau)
        return turn_plan.support_outward(native,step_seconds,outward)
    seq.support_outward=support_outward
    def foot_steering_gain(tau,side):
        offset=0. if side=='l' else .5
        continuous=tau/T+offset;phase=continuous-np.floor(continuous)
        begin=(np.floor(continuous)-offset)*T;duty=p.path_task['duty_factor']
        def at(begin):
            native,step_seconds=support_context(begin,begin+duty*T*.5)
            return turn_plan.steering_gain(native,step_seconds,p.path_task['toe_out_radians'])
        blend=float(smooth(max(0.,(phase-duty)/(1-duty))))
        return (1-blend)*at(begin)+blend*at(begin+T)
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
times=np.linspace(0,duration,769);poses=[];errors=[];ik_receipts=[]
for t in times:
    local_t=float(np.clip(t-start,0,active_end));tau=float(clock(local_t));phase=tau%T
    gain=gain_at_progress(tau);local=neutral+gain*(cycle(phase)-neutral)
    local[ix['forward']]*=gain
    # At rest head returns to the body's heading, retaining the reviewed pitch.
    for n in ('chest_yaw','neck_yaw','neck_upper_yaw','head_yaw'):local[ix[n]]*=gain
    if turn_plan:
        if steering:
            turn_gain=turn_plan.steering_gain(float(t),T*.5,p.path_task['toe_out_radians'])
            fraction=1-(1-steering['torso_yaw_reference_fraction'])*turn_gain
            local[ix['yaw']]=neutral[ix['yaw']]+fraction*(local[ix['yaw']]-neutral[ix['yaw']])
        tail_count=len(p.metadata.get('tail_chain',[]))
        for name,offset in turn_plan.body_offsets(float(t),tail_count).items():local[ix[name]]+=offset
        if attention:
            p.set_state(t,local,np.zeros(len(local)))
            def projected_heading(values):
                for c,value in zip(attention_coords,values):c.setValue(p.state,float(value),False)
                p.model.realizePosition(p.state)
                headings=[]
                for body in ('head','trunk'):
                    rot=p.model.getBodySet().get(body).getTransformInGround(p.state).R()
                    headings.append(np.arctan2(-rot.get(2,0),rot.get(0,0)))
                delta=headings[0]-headings[1]
                return float(np.degrees(np.arctan2(np.sin(delta),np.cos(delta))))
            requested=attention.target_degrees*turn_plan.attention(float(t))/peak_lead
            values,receipt=attention.solve(requested,projected_heading)
            local[attention_indices]=values
            attention_rows.append(dict(time_s=float(t),coordinates_rad=values.tolist(),**receipt))
        for name,setting in p.metadata['coordinates'].items():
            lo,hi=setting['bounds_rad']
            if not lo<=local[ix[name]]<=hi:raise ValueError('Turn intent exceeds admitted joint range: '+name)
    org,rr=frame_at_progress(tau);world=local.copy();world[xyz]=org+rr@local[xyz]
    world[angles]=Rotation.from_matrix(rr@Rotation.from_euler('ZYX',local[angles]).as_matrix()).as_euler('ZYX')
    p.set_state(t,world,np.zeros(len(world)))
    for side in ('l','r'):
        target,orientation,digit=foot_task(seq,tau,side)
        dp,dr,dd=correction[side];target=target+gain*rr@dp(phase)
        corrected=orientation@Rotation.from_rotvec(gain*dr(phase)).as_matrix()
        orientation=(attenuate_heading_correction(orientation,corrected,foot_steering_gain(tau,side))
                     if steering else corrected)
        digit+=gain*float(dd(phase))
        names=['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side,'digit_'+side]
        indices=[ix[n] for n in names];coords=[p.coordinates[i] for i in indices]
        reference=local[indices];toe=p.model.getBodySet().get('toe_'+side)
        def residual(x):
            for c,val in zip(coords,x):c.setValue(p.state,float(val),False)
            p.model.realizePosition(p.state)
            pos=toe.getPositionInGround(p.state).to_numpy();mat=toe.getTransformInGround(p.state).R()
            rot=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
            return np.r_[(pos-target)/p.L,.4*Rotation.from_matrix(orientation.T@rot).as_rotvec(),.4*(x[-1]-digit),.001*(x-reference)]
        bounds=np.array([p.metadata['coordinates'][n]['bounds_rad'] for n in names]).T
        margin=.01*(bounds[1]-bounds[0]);bounds[0]+=margin;bounds[1]-=margin
        # Warm from this cycle pose to avoid history-dependent branch switches.
        opt=least_squares(residual,np.clip(reference,bounds[0]+1e-6,bounds[1]-1e-6),bounds=bounds,max_nfev=100,ftol=1e-9,xtol=1e-9,gtol=1e-9)
        ik_receipts.append(dict(time_s=float(t),side=side,nfev=int(opt.nfev),success=bool(opt.success),optimality=float(opt.optimality)))
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
if turn_plan:p.metadata['sequence']['turn_plan']=turn_plan.specification
if attention:
    p.metadata['sequence']['attention_profile']=attention.description
    (a.output/'attention-receipt.json').write_text(json.dumps(dict(
        profile=attention.description,frames=attention_rows),indent=2)+'\n')
p.path_task=None
p.model.printToXML(str(a.output/'model.osim'))
import hashlib
p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,
    model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='AUTHORED_TRANSITION_MODEL',
    classification='Finite contact-planned walking sequence; inverse-dynamics diagnostic',user_review='PENDING')
(a.output/'model-receipt.json').write_text(json.dumps(p.metadata,indent=2)+'\n')
(a.output/'ik-receipt.json').write_text(json.dumps(ik_receipts,indent=2)+'\n')
report=p.export(np.zeros(len(p.parameters)))
(a.output/'sequence-receipt.json').write_text(json.dumps(p.metadata['sequence'],indent=2)+'\n')
(a.output/'solve-receipt.json').write_text(json.dumps(dict(success=False,status='AUTHORED_CONTACT_TRANSITION',
    source_status=source['report']['optimizer']['status'],claim='Bounded IK and inverse-dynamics audit only; not a converged dynamics solution'),indent=2)+'\n')
print(json.dumps({'sequence':p.metadata['sequence'],'root_rms':report['root_residual_rms_BW_or_BWL'],'maximum_control':report['maximum_control']}),flush=True)
