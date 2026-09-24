#!/usr/bin/env python3
"""Contact-aware mixed-generator sequence, with exact-model final audit.

Approved trajectories are warm references for this research checkpoint only.
They are not treated as newly predicted gaits or reusable production admission.
Each incoming segment adopts actual outgoing state and loaded foot witnesses.
"""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicHermiteSpline,CubicSpline
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation,Slerp
from eonwild_motion.solve.moco_coordination import Coordination,opposite
from eonwild_motion.solve.moco_spatial import reflected_coordinate
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline,bounded
from eonwild_motion.solve.moco_handoff import StateCarry,FootCarry,fit_orientation_carry,OrientationCarry


class Reference:
    def __init__(self,path,names,repeats=1):
        self.path=Path(path);d=json.loads(self.path.read_text());self.meta=d['metadata'];rows=d['frames']
        self.names=names;half=rows[-1]['time_s'];times=[];qs=[];us=[];feet={s:[] for s in ('l','r')};rots={s:[] for s in feet};loads={s:[] for s in feet}
        periodic=not self.meta.get('sequence');reflect=periodic and not self.meta.get('path_cycle')
        step=self.meta['admission']['step_length_m']*(1 if reflect else 2)
        for repeat in range(repeats):
            mirror=reflect and repeat%2;S=np.diag([1,1,-1]) if mirror else np.eye(3)
            for row in (rows if repeat==repeats-1 else rows[:-1]):
                times.append(row['time_s']+repeat*half);q=[];u=[]
                for name in names:
                    other=opposite(name) if mirror else name;sign=-1 if mirror and reflected_coordinate(name) else 1
                    q.append(sign*row['coordinates'][other]['value']+(repeat*step if name=='forward' else 0))
                    u.append(sign*row['coordinates'][other]['speed'])
                qs.append(q);us.append(u)
                for side in feet:
                    other=('r' if side=='l' else 'l') if mirror else side
                    body=row['bodies']['toe_'+other]
                    feet[side].append(S@np.array(body['origin'])+[repeat*step,0,0]);rots[side].append(S@np.array(body['rotation'])@S)
                    loads[side].append(sum(c['force_N'][1] for c in row['contacts'] if c['name'].endswith('_'+other))/(self.meta['mass_kg']*9.80665))
        self.times=np.asarray(times);self.end=times[-1];self.raw=CubicHermiteSpline(times,qs,us,axis=0)
        self.bounds={names.index(n):v['bounds_rad'] for n,v in self.meta['coordinates'].items()}
        self.bounds.update({names.index(n):v for n,v in self.meta['recipe']['spatial'].get('root_bounds',{}).items() if n in ('pitch','yaw','roll')})
        self.feet={s:CubicSpline(times,feet[s],axis=0) for s in feet}
        self.rotations={s:Slerp(times,Rotation.from_matrix(rots[s])) for s in feet}
        self.loads={s:CubicSpline(times,loads[s]) for s in feet}

    def q(self,t,d=0):
        raw=self.raw(t);out=self.raw(t,d)
        for i,(lo,hi) in self.bounds.items():
            value,first,second=bounded(raw[...,i],lo,hi)
            out[...,i]=value if d==0 else first*self.raw(t,1)[...,i] if d==1 else first*self.raw(t,2)[...,i]+second*self.raw(t,1)[...,i]**2
        return out

    def foot(self,t,side):
        return self.feet[side](t),self.rotations[side](float(np.clip(t,0,self.end))).as_matrix(),float(self.q(t)[self.names.index('digit_'+side)])


def main():
    ap=argparse.ArgumentParser()
    for n in ('plan','baseline','output'):ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();spec=json.loads(a.plan.read_text());a.output.mkdir(parents=True,exist_ok=False)
    baseline=json.loads(a.baseline.read_text());modelsource=json.loads(Path(spec['model_source']).read_text());m=modelsource['metadata']
    p=Coordination(m['admission'],copy.deepcopy(m['recipe']),baseline,a.output);ix=p.index;nq=len(p.names);zeros=np.zeros(nq)
    references={k:Reference(v['path'],p.names,v.get('repeats',1)) for k,v in spec['references'].items()}
    for ref in references.values():
        if ref.meta['admission']['source_geometry_sha256']!=p.admission['source_geometry_sha256']:raise ValueError('Mixed geometry is not a state handoff')
    bounds={ix[n]:tuple(v['bounds_rad']) for n,v in p.metadata['coordinates'].items()}
    bounds.update({ix[n]:tuple(v) for n,v in p.recipe['spatial'].get('root_bounds',{}).items() if n in ('pitch','yaw','roll')})
    dt=1/spec['sample_hz'];times=[];poses=[];targets=[];receipts=[];errors=[];segments=[];native=0.;previous_spline=None
    xyz=[ix[n] for n in ('forward','height','lateral')];travel=[ix[n] for n in ('forward','lateral')]
    def actual_feet(t,q,u):
        p.set_state(t,q,u);out={}
        for side in ('l','r'):
            body=p.model.getBodySet().get('toe_'+side);R=body.getTransformInGround(p.state).R()
            out[side]=(body.getPositionInGround(p.state).to_numpy().copy(),np.array([[R.get(i,j) for j in range(3)] for i in range(3)]),q[ix['digit_'+side]])
        return out
    for segment in spec['segments']:
        ref=references[segment['reference']];duration=segment['duration_s'];blend=segment.get('handoff_s',1.);source_start=segment.get('source_start_s',0.)
        outgoing=None;orientation_receipt={}
        if poses:
            outgoing=np.array([previous_spline(native,d) for d in range(3)])
            outgoing_feet=actual_feet(native,outgoing[0],outgoing[1]);last=targets[-1]
            if 'start_search_s' in segment:
                candidates=np.linspace(*segment['start_search_s'],101);cost=[]
                leg=[i for i,n in enumerate(p.names) if n.startswith(('hip_','knee_','ankle_','mtp_'))]
                # Match the currently supporting foot before minimizing pose
                # mismatch. Flight is not an acceptable handoff for this trial.
                p.set_state(native,outgoing[0],outgoing[1]);load={s:sum(f.getRecordValues(p.state).get(1) for f,c in zip(p.contact_forces,p.metadata['contacts']) if c['force'].endswith('_'+s))/p.bw for s in ('l','r')}
                for t in candidates:
                    incoming_load={s:max(0.,float(ref.loads[s](t))) for s in load}
                    mismatch=sum(((load[s]>.08)!=(incoming_load[s]>.08))*100 for s in load)
                    # Do not ask an already airborne foot to absorb a large
                    # placement change immediately before touchdown.
                    for s in load:
                        if incoming_load[s]<.08:
                            remaining=np.linspace(t,t+.28,29)
                            if np.any(ref.loads[s](remaining)>.08):mismatch+=100
                    cost.append(mismatch+np.mean((ref.q(t)[leg]-outgoing[0,leg])**2)+.02*np.mean((ref.q(t,1)[leg]-outgoing[1,leg])**2))
                source_start=float(candidates[np.argmin(cost)])
            if 'through_source_s' in segment:duration=segment['through_source_s']-source_start
            # Native source phase selection can change the segment length;
            # sample on a uniform global grid for the final state spline.
            duration=round(duration/dt)*dt
            incoming=np.array([ref.raw(source_start,d) for d in range(3)])
            outgoing_latent=np.array([previous_spline.spline(native,d) for d in range(3)])
            shift=np.zeros(nq);shift[travel]=outgoing[0,travel]-incoming[0,travel];incoming[0]+=shift
            carry=StateCarry(outgoing_latent,incoming,blend,travel)
            if spec.get('orientation_handoff_envelope'):
                orientations=[ix[n] for n in ('pitch','yaw','roll')]
                curves,orientation_receipt=fit_orientation_carry(
                    outgoing_latent,incoming,lambda t:ref.raw(source_start+t)+shift,
                    blend,orientations,min(2*dt,blend),
                    spec['orientation_handoff_envelope']['margin_fraction'])
                orientation_receipt={p.names[i]:v for i,v in orientation_receipt.items()}
                carry=OrientationCarry(carry,curves)
        else:
            shift=np.zeros(nq);carry=None
        if source_start+duration>ref.end+1e-8:raise ValueError('Reference span exhausted')
        local=np.linspace(0,duration,round(duration/dt)+1)
        foot_carry={};rotation_carry={};digit_carry={}
        for side in ('l','r'):
            if carry:
                origin,R,digit=ref.foot(source_start,side)
                offset=outgoing_feet[side][0]-origin-shift[xyz]
                # World ground height is not carried with pelvis height. Only
                # horizontal travel shifts future footprints; adding a pelvis
                # correction here would bury or float a new planted foot.
                foot_carry[side]=FootCarry(local,ref.loads[side](source_start+local)>.08,lambda t:carry(t)[xyz]*np.array([1.,0.,1.]),offset)
                rotation_carry[side]=Rotation.from_matrix(R.T@outgoing_feet[side][1]).as_rotvec()
                digit_carry[side]=outgoing_feet[side][2]-digit
        segment_targets=[];segment_poses=[]
        for j,t in enumerate(local):
            st=source_start+t;world=ref.raw(st)+shift
            if carry:world+=carry(t)
            for i,(lo,hi) in bounds.items():world[i]=bounded(world[i],lo,hi)[0]
            goals={}
            for side in ('l','r'):
                pos,R,digit=ref.foot(st,side);pos=pos+shift[xyz]
                if carry:
                    gain=foot_carry[side].adoption_gain(t);pos+=foot_carry[side](t)
                    R=R@Rotation.from_rotvec(gain*rotation_carry[side]).as_matrix();digit+=gain*digit_carry[side]
                goals[side]=(pos,R,digit)
            # Preserve the actual incoming pose at the boundary. Subsequent
            # samples solve both legs against material world tasks. All body
            # regions retain the C2 inherited pose/velocity correction.
            if j==0 and outgoing is not None:world=outgoing[0].copy()
            elif carry:
                names=[name for s in ('l','r') for name in ['hip_'+s,'hip_'+s+'_yaw','hip_'+s+'_roll','knee_'+s,'ankle_'+s,'mtp_'+s,'digit_'+s]]
                limb_indices=[ix[n] for n in names]
                indices=xyz+limb_indices;reference=world[indices].copy()
                limits=np.array([(world[i]-.3,world[i]+.3) for i in xyz]+[bounds[i] for i in limb_indices]).T
                margin=.005*(limits[1,3:]-limits[0,3:]);limits[0,3:]+=margin;limits[1,3:]-=margin
                prediction=reference.copy()
                if len(segment_poses)>1:
                    prediction=(2*segment_poses[-1]-segment_poses[-2])[indices]
                p.set_state(native+t,world,zeros)
                def residual(values):
                    for i,v in zip(indices,values):p.coordinates[i].setValue(p.state,float(v),False)
                    p.model.realizePosition(p.state);res=[]
                    for s in ('l','r'):
                        body=p.model.getBodySet().get('toe_'+s);pos=body.getPositionInGround(p.state).to_numpy();mat=body.getTransformInGround(p.state).R();R=np.array([[mat.get(k,l) for l in range(3)] for k in range(3)])
                        goal,orient,digit=goals[s]
                        res.extend(35*(pos-goal)/p.L);res.extend(4*Rotation.from_matrix(orient.T@R).as_rotvec());res.append(.8*(values[3+names.index('digit_'+s)]-digit))
                    res.extend(np.r_[4*(values[:3]-reference[:3])/p.L,.08*(values[3:]-reference[3:])])
                    res.extend(.15*(values-prediction));return np.array(res)
                opt=least_squares(residual,np.clip(prediction,limits[0]+1e-7,limits[1]-1e-7),bounds=(limits[0]+1e-8,limits[1]-1e-8),max_nfev=65,ftol=1e-8,xtol=1e-8,gtol=1e-8)
                world[indices]=opt.x;rr=residual(opt.x);errors.extend([float(np.linalg.norm(rr[k:k+3])*p.L/35) for k in (0,7)])
            segment_poses.append(world);segment_targets.append(goals)
        new_times=native+local
        first=0 if not poses else 1
        times.extend(new_times[first:]);poses.extend(segment_poses[first:]);targets.extend(segment_targets[first:])
        previous_spline=BoundedJointSpline(times,np.array(poses),bounds)
        receipts.append(dict(orientation_handoff=orientation_receipt,name=segment['name'],start_s=native,end_s=native+duration,source_start_s=source_start,source_end_s=source_start+duration,handoff_s=blend if carry else 0,initial_pose_error=0. if outgoing is None else float(np.max(abs(segment_poses[0]-outgoing[0]))),feet={s:dict(release_s=foot_carry[s].release,landing_s=foot_carry[s].landing) for s in foot_carry}))
        print(json.dumps(receipts[-1]),flush=True);segments.append((native,native+duration));native+=duration
    times=np.asarray(times);poses=np.asarray(poses);trajectory=BoundedJointSpline(times,poses,bounds,bc_type=((1,zeros),(1,zeros)))
    np.savez(a.output/'connected-seed.npz',times=times,poses=poses,names=p.names)
    np.savez(a.output/'foot-targets.npz',times=times,positions=np.array([[v[s][0] for s in ('l','r')] for v in targets]),rotations=np.array([[v[s][1] for s in ('l','r')] for v in targets]),digits=np.array([[v[s][2] for s in ('l','r')] for v in targets]))
    foot_positions={s:CubicSpline(times,np.array([v[s][0] for v in targets]),axis=0) for s in ('l','r')}
    foot_rotations={s:Slerp(times,Rotation.from_matrix([v[s][1] for v in targets])) for s in ('l','r')}
    digits={s:CubicSpline(times,[v[s][2] for v in targets]) for s in ('l','r')}
    def task(t,s):return foot_positions[s](t),foot_rotations[s](float(t)).as_matrix(),float(digits[s](t))
    finite_receipts=[]
    p.path_task=None;p.speed=0.
    if spec.get('finite_coordination'):
        from eonwild_motion.solve.moco_finite_coordination import FiniteCoordination
        settings=spec['finite_coordination'];ft=np.linspace(settings['start_s'],settings['end_s'],settings['samples'])
        finite=FiniteCoordination(p,trajectory,ft,task,settings);x,receipt=finite.solve();finite_receipts.append(receipt)
        p.evaluate_kinematics=lambda unused,t:finite.evaluate(x,t)
    else:p.evaluate_kinematics=lambda unused,t:(trajectory(t),trajectory(t,1),trajectory(t,2))
    p.times_dense=times;p.metadata.pop('path_cycle',None)
    seq=dict(duration_s=native,periodic=False,distance_m=float(poses[-1,ix['forward']]-poses[0,ix['forward']]),method='Shared state/contact handoff with anatomical IK and optional finite whole-body optimization; not full Moco convergence',segments=receipts,seed_max_foot_task_error_m=max(errors,default=0.),source_plan=spec,reference_hashes={k:hashlib.sha256(v.path.read_bytes()).hexdigest() for k,v in references.items()},finite_coordination=finite_receipts)
    p.metadata['sequence']=seq;p.model.printToXML(str(a.output/'model.osim'))
    p.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=p.admission,recipe=p.recipe,model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='CONNECTED_FINITE_CANDIDATE',classification=seq['method'],user_review='PENDING')
    for name,value in [('model-receipt',p.metadata),('sequence-receipt',seq),('solve-receipt',dict(success=False,status='CONNECTED_DIAGNOSTIC_NOT_FULL_MOCO',finite_coordination=finite_receipts))]:
        (a.output/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    report=p.export(np.zeros(len(p.parameters)));print(json.dumps(dict(root_rms=report['root_residual_rms_BW_or_BWL'],max_control=report['maximum_control'],duration_s=native)),flush=True)


if __name__=='__main__':main()
