#!/usr/bin/env python3
"""Finite behavior tasks through shared bounded OpenSim contact coordination.

Source trajectories are explicitly warm references. No full Moco convergence
or autonomous game behavior is claimed. Every output is physically replayed.
"""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares,brentq
from scipy.spatial.transform import Rotation
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import CubicSpline
from eonwild_motion.solve.moco_coordination import Coordination
from eonwild_motion.solve.moco_behavior_intent import BehaviorIntent,SupportRetime
from eonwild_motion.solve.moco_living_intent import LivingIntent,keyed
from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline
from eonwild_motion.solve.moco_attention import ProfileAttention
from eonwild_motion.solve.moco_tasks import smooth
from sequence_moco_connected import Reference


def main():
    ap=argparse.ArgumentParser()
    for name in ('source','baseline','plan','output'):ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    src=json.loads(a.source.read_text());meta=src['metadata'];spec=json.loads(a.plan.read_text())
    recipe=copy.deepcopy(meta['recipe']);recipe['coordination'].get('path_task',{}).pop('temporal_contact_seed',None)
    if spec.get('body_support_contacts'):recipe['body_support_contacts']=spec['body_support_contacts']
    admission=copy.deepcopy(meta['admission'])
    if spec.get('body_surface_file'):
        surface=json.loads(Path(spec['body_surface_file']).read_text())
        if surface['source_geometry_sha256']!=admission['source_geometry_sha256']:raise ValueError('Body surface anatomy mismatch')
        admission['body_surface_sites']=surface['sites']
    p=Coordination(admission,recipe,json.loads(a.baseline.read_text()),a.output)
    ix=p.index;nq=len(p.names);zeros=np.zeros(nq);duration=spec['duration_s']
    bounds={n:tuple(v['bounds_rad']) for n,v in p.metadata['coordinates'].items()}
    intent=BehaviorIntent(spec,p.names,p.L,bounds)
    life=LivingIntent(spec['living_intent'],intent,p.names,p.metadata['tail_chain'],p.L,bounds)
    attention=ProfileAttention(json.loads(Path(spec['attention_profile']).read_text()),p.metadata,'scan')
    ai=[ix[n] for n in attention.names]
    initial_row=src['frames'][-1] if spec.get('adopt_final_state') else src['frames'][0]
    rest=np.array([initial_row['coordinates'][n]['value'] for n in p.names])
    standing=None;standing_row=None
    if spec.get('standing_reference'):
        standing_source=json.loads(Path(spec['standing_reference']).read_text())
        if standing_source['metadata']['admission']['source_geometry_sha256']!=meta['admission']['source_geometry_sha256']:raise ValueError('Standing target anatomy differs from adopted state')
        standing_row=standing_source['frames'][0]
        standing=np.array([standing_row['coordinates'][n]['value'] for n in p.names])
        standing[[ix['forward'],ix['lateral']]]=rest[[ix['forward'],ix['lateral']]]
    ref=Reference(a.source,p.names,spec.get('reference_repeats',1)) if spec.get('reference_motion',False) else None
    times=np.linspace(0,duration,round(duration*spec.get('sample_hz',48))+1)
    clock_rate=spec.get('reference_clock_rate',1.)
    if ref and duration*clock_rate+spec.get('source_start_s',0)>ref.end+1e-7:raise ValueError('Reference exhausted')
    feet_row=standing_row or initial_row
    shift=np.array([rest[ix['forward']]-feet_row['coordinates']['forward']['value'],0.,rest[ix['lateral']]-feet_row['coordinates']['lateral']['value']]) if standing_row else np.zeros(3)
    feet0={s:(np.array(feet_row['bodies']['toe_'+s]['origin'])+shift,np.array(feet_row['bodies']['toe_'+s]['rotation']),feet_row['coordinates']['digit_'+s]['value']) for s in ('l','r')}
    legnames=[n for s in ('l','r') for n in ['hip_'+s,'hip_'+s+'_yaw','hip_'+s+'_roll','knee_'+s,'ankle_'+s,'mtp_'+s,'digit_'+s]]
    ids=[ix[n] for n in legnames];limits=np.array([bounds[n] for n in legnames]).T
    oral=spec.get('oral_target')
    if oral:
        extra=['neck','neck_upper','head','height','pitch','forward']
        ids.extend(ix[n] for n in extra)
        limits=np.column_stack((limits,np.array([bounds[n] for n in extra[:3]]+[
            (rest[ix['height']]-.6*p.L,rest[ix['height']]+.1*p.L),
            (rest[ix['pitch']]-.6,rest[ix['pitch']]+.12),
            (rest[ix['forward']]-.45*p.L,rest[ix['forward']]+.20*p.L)]).T))
        p.set_state(0,rest,zeros);nose_rest=p.nose.getPositionInGround(p.state).to_numpy().copy()
        com_rest=p.model.calcMassCenterPosition(p.state).to_numpy().copy()
        tail_names=[part['body'] for part in p.metadata['tail_chain']]
        ids.extend(ix[n] for n in tail_names)
        limits=np.column_stack((limits,np.array([bounds[n] for n in tail_names]).T))
        tail_regions=[p.model.getBodySet().get(tail_names[i]) for i in sorted(set([1,len(tail_names)//2,len(tail_names)-1]))]
        tail_heights=np.array([body.getPositionInGround(p.state).get(1) for body in tail_regions])
    margin=.001*(limits[1]-limits[0]);limits[0]+=margin;limits[1]-=margin
    poses=[];tasks=[];errors=[];attentions=[];support_failures=[];previous=rest.copy()
    def source_time(t):
        stop=spec.get('reference_stop')
        if stop:
            begin,end=stop['begin_s'],stop['end_s'];D=end-begin
            if D<=0:raise ValueError('Reference braking duration must be positive')
            u=np.clip((t-begin)/D,0,1)
            t=min(t,end)-D*(u**6-3*u**5+2.5*u**4)
        return t*clock_rate+spec.get('source_start_s',0)
    ground_support=None
    if spec.get('anchored_body_support'):
        from eonwild_motion.solve.moco_ground_support import GroundSupport,recovery_reference
        ground_support=GroundSupport(p,spec,bounds,rest,standing)
    if spec.get('support_transfer'):
        if standing is None:raise ValueError('Support transfer requires admitted standing anatomy')
        crouch=recovery_reference(rest,standing,spec['support_transfer']['plant_pose_time_s'],spec['support_transfer'],ix,bounds)
        crouch[ix['roll']]=standing[ix['roll']];crouch[ix['pitch']]=standing[ix['pitch']]
        p.set_state(0,crouch,zeros)
        for side in ('l','r'):
            toe=p.model.getBodySet().get('toe_'+side);position=toe.getPositionInGround(p.state).to_numpy().copy()
            # Horizontal stance is chosen once from folded anatomy and remains
            # a world anchor through the leg-driven rise.
            p.set_state(0,standing,zeros);height=p.model.getBodySet().get('toe_'+side).getPositionInGround(p.state).get(1)
            position[1]=height;feet0[side]=(position,feet0[side][1],feet0[side][2]);p.set_state(0,crouch,zeros)
    foot_paths={}
    retimers={s:SupportRetime(ref.times,ref.loads[s](ref.times)>.08,fraction) for s,fraction in spec.get('support_retime',{}).items()} if ref else {}
    if ref and spec.get('follow_root_placements'):
        # Each support keeps one world displacement; the next footprint is
        # anticipated and reached only during swing. No loaded anchor slide.
        for s in ('l','r'):
            loaded=ref.loads[s](np.array([source_time(t) for t in times]))>.08
            starts=np.flatnonzero(loaded & ~np.r_[False,loaded[:-1]])
            ends=np.flatnonzero(loaded & ~np.r_[loaded[1:],False])
            keys=[]
            for start,end in zip(starts,ends):
                middle=(times[start]+times[end])/2
                delta=np.array([p.L*keyed(middle,spec.get('root_offsets_leg_lengths',{}).get(n,[[0,0],[duration,0]])) for n in ('forward','lateral')])
                placement=spec.get('foot_placement_offsets_leg_lengths',{}).get(s,{})
                delta+=p.L*np.array([keyed(middle,placement.get(n,[[0,0],[duration,0]])) for n in ('forward','lateral')])
                keys.extend([(times[start],delta),(times[end],delta)])
            foot_paths[s]=keys
    def path_offset(t,s):
        keys=foot_paths.get(s,[])
        if not keys:return np.zeros(3)
        if t<=keys[0][0]:v=keys[0][1]
        elif t>=keys[-1][0]:v=keys[-1][1]
        else:
            for (a,x),(b,y) in zip(keys[:-1],keys[1:]):
                if a<=t<=b:
                    v=x+(y-x)*float(smooth((t-a)/(b-a))) if b>a else y;break
        return np.array([v[0],0.,v[1]])
    for k,t in enumerate(times):
        st=source_time(t)
        reference=ref.raw(st).copy() if ref else rest.copy()
        if standing is not None:
            reference=recovery_reference(rest,standing,t,spec['support_transfer'],ix,bounds) if spec.get('support_transfer') else rest+keyed(t,spec['stand_adoption_keys'])*(standing-rest)
        goals={s:ref.foot(retimers[s](st) if s in retimers else st,s) if ref else feet0[s] for s in ('l','r')}
        for s,retimer in retimers.items():
            limb=[ix[n] for n in legnames if n.endswith('_'+s) or n.startswith('hip_'+s+'_')]
            reference[limb]=ref.raw(retimer(st))[limb]
        stride_scale=spec.get('stride_scale',1.)
        reference[ix['forward']]*=stride_scale
        for s in goals:
            pos,R,digit=goals[s];pos=pos.copy();pos[0]*=stride_scale
            pos+=path_offset(t,s)
            for j,n in enumerate(('forward','height','lateral')):
                keys=spec.get('foot_goal_offsets_leg_lengths',{}).get(n)
                if keys:pos[j]+=p.L*keyed(t,keys)
            obstacle=spec.get('step_over')
            if obstacle and ref:
                load=max(0.,float(ref.loads[s](st)))
                swing=float(smooth((.08-load)/.08))
                center=obstacle['forward_leg_lengths']*p.L
                span=obstacle['approach_leg_lengths']*p.L
                pos[1]+=swing*p.L*obstacle['extra_clearance_leg_lengths']*np.exp(-((pos[0]-center)/span)**4)
            goals[s]=(pos,R,digit)
        q=intent.apply(reference,t);q=life.apply(q,t)
        if spec.get('attention_enabled',True):
            p.set_state(t,q,zeros)
            def heading(values):
                for i,v in zip(ai,values):p.coordinates[i].setValue(p.state,float(v),False)
                p.model.realizePosition(p.state);angles=[]
                for name in ('head','trunk'):
                    R=p.model.getBodySet().get(name).getTransformInGround(p.state).R()
                    angles.append(np.arctan2(-R.get(2,0),R.get(0,0)))
                return float(np.rad2deg(np.arctan2(np.sin(angles[0]-angles[1]),np.cos(angles[0]-angles[1]))))
            reference_attention=0.
            if ref and spec.get('retain_reference_attention',True):
                p.set_state(t,reference,zeros);reference_attention=heading(reference[ai]);p.set_state(t,q,zeros)
            values,receipt=attention.solve(reference_attention+life.attention(t),heading);q[ai]=values
            attentions.append(dict(time_s=float(t),**receipt))
        p.set_state(t,q,zeros)
        target_pose=q[ids].copy()
        support_gain=keyed(t,spec.get('foot_support_gain',[[0,1],[duration,1]]))
        def residual(x):
            for i,v in zip(ids,x):p.coordinates[i].setValue(p.state,float(v),False)
            p.model.realizePosition(p.state);r=[]
            for s in ('l','r'):
                b=p.model.getBodySet().get('toe_'+s);pos=b.getPositionInGround(p.state).to_numpy();mat=b.getTransformInGround(p.state).R()
                R=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
                target,orientation,digit=goals[s]
                r.extend(support_gain*30*(pos-target)/p.L);r.extend(support_gain*4*Rotation.from_matrix(orientation.T@R).as_rotvec())
                r.append(support_gain*.5*(x[legnames.index('digit_'+s)]-digit))
            r.extend((.035+2*(1-support_gain))*(x-target_pose))
            if oral:
                gain=keyed(t,oral['engagement_keys'])
                target=nose_rest.copy();target[1]=oral['height_leg_lengths']*p.L
                target[0]+=oral.get('forward_offset_leg_lengths',0)*p.L
                target=nose_rest+gain*(target-nose_rest)
                actual=p.nose.getPositionInGround(p.state).to_numpy()
                r.extend(np.array([2.,15.,4.])*(actual-target)/p.L)
                com=p.model.calcMassCenterPosition(p.state).to_numpy()
                r.extend(2*(com[[0,2]]-com_rest[[0,2]])/p.L)
                heights=np.array([body.getPositionInGround(p.state).get(1) for body in tail_regions])
                r.extend(2*(heights-tail_heights)/p.L)
                prediction=2*previous[ids]-poses[-2][ids] if len(poses)>1 else previous[ids]
                r.extend(.65*(x-prediction))
            return np.array(r)
        seed=target_pose if k==0 else previous[ids]+reference[ids]-(ref.raw(source_time(times[k-1]))[ids] if ref else rest[ids])
        if ground_support is None:
            fit=least_squares(residual,np.clip(seed,limits[0]+1e-8,limits[1]-1e-8),bounds=limits,max_nfev=45,ftol=1e-8,xtol=1e-8,gtol=1e-8)
            q[ids]=fit.x;rr=residual(fit.x);errors.append(max(np.linalg.norm(rr[:3]),np.linalg.norm(rr[7:10]))*p.L/30)
        if ground_support is not None:
            q=ground_support.solve(q,t,goals,previous,poses[-2] if len(poses)>1 else None)
            errors.append(max(ground_support.receipts[-1]['loaded_foot_error_m'].values()))
        if ground_support is None and spec.get('body_support_gain') and not (k==0 and spec.get('adopt_final_state')):
            gain=keyed(t,spec['body_support_gain'])
            if gain>0:
                # Additive projection becomes exact at full broad-body
                # support. Contact comes from real model forces, not a visual
                # floor overlay. It remains a kinematic contact initializer.
                p.set_state(t,q,zeros)
                from scipy.special import logsumexp
                supports=spec['body_support_contacts'].get('primary_support_bodies',['trunk','chest','thigh_l','thigh_r'])
                heights=[b.findStationLocationInGround(p.state,point).get(1)-c['radius_m'] for b,point,c in zip(p.contact_bodies,p.contact_points,p.metadata['contacts']) if c['body'] in supports]
                floor=float(logsumexp(-150*np.array(heights)))/150
                q[ix['height']]+=gain*floor
                if gain>.02:
                    # The trunk must settle onto broad support. Tail/limbs
                    # accommodate the floor instead of lifting the whole
                    # fallen animal on a distal tail point.
                    free_names=legnames+['neck','neck_yaw','neck_upper','neck_upper_yaw','head','head_yaw']+[name for part in p.metadata['tail_chain'] for name in (part['body'],part['body']+'_yaw')]+([] if spec.get('anchored_body_support') else ['height'])
                    free_ids=[ix[n] for n in free_names];target=q[free_ids].copy()
                    lim=np.array([bounds[n] if n!='height' else (q[ix['height']]-.05*p.L,q[ix['height']]+.35*p.L) for n in free_names]).T
                    p.set_state(t,q,zeros)
                    def clearance(values):
                        for i,v in zip(free_ids,values):p.coordinates[i].setValue(p.state,float(v),False)
                        p.model.realizePosition(p.state)
                        h=np.array([b.findStationLocationInGround(p.state,point).get(1)-c['radius_m'] for b,point,c in zip(p.contact_bodies,p.contact_points,p.metadata['contacts']) if c['body'] not in supports])
                        return np.r_[35*gain*np.minimum(h-.004,0)/p.L,.10*(values-target),.08*(values-previous[free_ids])]
                    ground_fit=least_squares(clearance,np.clip(target,lim[0]+1e-6,lim[1]-1e-6),bounds=(lim[0]+1e-7,lim[1]-1e-7),max_nfev=25,ftol=1e-7,xtol=1e-7,gtol=1e-7)
                    q[free_ids]=ground_fit.x
                def load(dy):
                    qq=q.copy();qq[ix['height']]+=dy;p.set_state(t,qq,zeros)
                    return sum(f.getRecordValues(p.state).get(1) for f in p.contact_forces)-p.bw
                try:q[ix['height']]+=gain*brentq(load,-.035,.035)
                except ValueError:support_failures.append(dict(time_s=float(t),low_N=float(load(-.035)),high_N=float(load(.035))))
        poses.append(q.copy());tasks.append(goals);previous=q
    poses=np.array(poses)
    if spec.get('body_support_gain') and ground_support is None:
        gain=np.array([keyed(t,spec['body_support_gain']) for t in times])
        # Physical-time smoothing of the coupled clearance initializer; all
        # forces/contact are evaluated AFTER this operation in final replay.
        smoothed=gaussian_filter1d(poses,.065/(times[1]-times[0]),axis=0,mode='nearest')
        poses+=gain[:,None]*(smoothed-poses)
        # Global C2 root clearance, AFTER all coupled pose modifications.
        # Local projection followed by smoothing can bury a rolling foot.
        # Fit the support envelope over time instead of clipping individual
        # frames; actual contact forces are still audited, not assumed solved.
        from scipy.optimize import minimize,LinearConstraint
        required=[]
        for t,q in zip(times,poses):
            p.set_state(t,q,zeros)
            h=[body.findStationLocationInGround(p.state,point).get(1)-c['radius_m'] for body,point,c in zip(p.contact_bodies,p.contact_points,p.metadata['contacts'])]
            required.append(q[ix['height']]-min(h)-.0015*p.L)
        required=np.array(required);nodes=np.linspace(0,duration,round(duration/.18)+1)
        basis=CubicSpline(nodes,np.eye(len(nodes)),bc_type=((1,np.zeros(len(nodes))),(1,np.zeros(len(nodes)))))
        B=basis(times);D=basis(times,2);V=basis(times,1)
        def objective(c):
            error=B@c-required;acc=D@c;velocity=V@c
            return float(10*error@error+.002*acc@acc+.01*velocity@velocity)
        def jac(c):return 20*B.T@(B@c-required)+.004*D.T@(D@c)+.02*V.T@(V@c)
        fit=minimize(objective,np.interp(nodes,times,required)+.2*p.L,jac=jac,
            constraints=[LinearConstraint(B,required,np.inf)],method='SLSQP',options=dict(maxiter=180,ftol=1e-9))
        if not fit.success or np.min(B@fit.x-required)<-1e-6:raise ValueError('Global body-support clearance did not solve: '+fit.message)
        poses[:,ix['height']]=B@fit.x
        (a.output/'root-clearance-receipt.json').write_text(json.dumps(dict(method='Global C2 geometric support envelope, not force convergence',success=bool(fit.success),iterations=int(fit.nit),maximum_extra_clearance_m=float(max(B@fit.x-required)),minimum_margin_m=float(min(B@fit.x-required))),indent=2)+'\n')
    if ground_support is not None:(a.output/'ground-support-receipt.json').write_text(json.dumps(ground_support.receipts,indent=2)+'\n')
    trajectory=BoundedJointSpline(times,poses,{ix[n]:v for n,v in bounds.items()},bc_type='not-a-knot' if ref else ((1,zeros),(1,zeros)))
    p.path_task=None;p.speed=0.;p.times_dense=times;p.metadata.pop('path_cycle',None)
    finite_receipt=None
    if spec.get('finite_coordination'):
        from eonwild_motion.solve.moco_finite_coordination import FiniteCoordination
        from scipy.spatial.transform import Slerp
        pos={s:CubicSpline(times,[v[s][0] for v in tasks]) for s in ('l','r')}
        rot={s:Slerp(times,Rotation.from_matrix([v[s][1] for v in tasks])) for s in ('l','r')}
        digit={s:CubicSpline(times,[v[s][2] for v in tasks]) for s in ('l','r')}
        task=lambda t,s:(pos[s](t),rot[s](float(t)).as_matrix(),float(digit[s](t)))
        settings=spec['finite_coordination'];finite=FiniteCoordination(p,trajectory,np.linspace(settings['start_s'],settings['end_s'],settings['samples']),task,settings)
        x,finite_receipt=finite.solve();p.evaluate_kinematics=lambda unused,t:finite.evaluate(x,t)
    else:p.evaluate_kinematics=lambda unused,t:(trajectory(t),trajectory(t,1),trajectory(t,2))
    if spec.get('water'):
        if finite_receipt:raise ValueError('Water forces must be computed from the final trajectory, not a discarded seed')
        from eonwild_motion.solve.moco_environment import install_water_replay
        water=dict(spec['water']);water['height_m']=water.pop('height_leg_lengths')*p.L
        loads=install_water_replay(p,times,trajectory,water)
        (a.output/'environment-loads.json').write_text(json.dumps(dict(times_s=times.tolist(),policy=water,forces_N=loads))+'\n')
    seq=dict(duration_s=duration,distance_m=float(poses[-1,ix['forward']]-poses[0,ix['forward']]),periodic=False,
        family=spec['family'],plan=spec,living_intent=dict(policy=spec['living_intent']),seed_max_foot_task_error_m=float(max(errors)),
        source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),source_path=str(a.source),finite_coordination=finite_receipt,
        body_support_settling_failures=support_failures,
        method='Authored behavior intent with bounded shared contact coordination and exact OpenSim inverse-dynamics audit; not full Moco convergence')
    p.metadata['sequence']=seq;p.model.printToXML(str(a.output/'model.osim'))
    p.metadata.update(admission=p.admission,recipe=p.recipe,model_sha256=hashlib.sha256((a.output/'model.osim').read_bytes()).hexdigest(),status='BEHAVIOR_DIAGNOSTIC',user_review='PENDING')
    for name,data in [('model-receipt',p.metadata),('sequence-receipt',seq),('solve-receipt',dict(success=False,status='BEHAVIOR_DIAGNOSTIC_NOT_FULL_MOCO',optimizer=finite_receipt)),('attention-receipt',attentions)]:
        (a.output/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    np.savez(a.output/'behavior-seed.npz',times=times,poses=poses,names=p.names,foot_errors=errors)
    report=p.export(np.zeros(len(p.parameters)));print(json.dumps(dict(max_foot_error_m=max(errors),root_rms=report['root_residual_rms_BW_or_BWL'],max_control=report['maximum_control'])),flush=True)


if __name__=='__main__':main()
