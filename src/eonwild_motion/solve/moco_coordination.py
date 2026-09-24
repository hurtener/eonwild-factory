"""Periodic reduced-coordinate initialization for the optional spatial Moco model.

Uses the exact OpenSim inverse dynamics, contact and passive forces. Fourier
coefficients describe smooth corrections around an earlier physical trajectory;
they are decision variables, not authored joint curves. Root residuals are
measured, never supplied by actuators. This is a guided initializer, not a
replacement for Moco convergence or independent forward replay.
"""
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import least_squares

from .moco_prototype import make_model
from .moco_spatial import reflected_coordinate


def opposite(name):
    return re.sub(r'_(l|r)(?=_|$)', lambda m: '_r' if m[1]=='l' else '_l', name)


def basis_parameters(names,harmonics):
    """Independent half-stride coordinates, including bilateral mean adduction."""
    parameters=[]
    for name in names:
        if re.search(r'_r(?=_|$)',name):continue
        limb=bool(re.search(r'_l(?=_|$)',name))
        orders=range(1,harmonics+1) if limb else range(1,2*harmonics,2) if reflected_coordinate(name) else range(2,2*harmonics+1,2)
        if limb or (not reflected_coordinate(name) and name!='forward'):
            parameters.append((name,0,'constant'))
        for order in orders:
            parameters.append((name,order,'sin'))
            if name!='forward':parameters.append((name,order,'cos'))
    return parameters


class Coordination:
    def __init__(self, admission, recipe, baseline, output):
        import opensim as o
        self.o=o; self.admission=admission;self.recipe=recipe;self.output=Path(output)
        self.policy=recipe['coordination'];self.model,self.metadata=make_model(admission,recipe)
        self.state=self.model.initSystem();self.coordinates=list(self.model.updCoordinateSet())
        self.names=[c.getName() for c in self.coordinates];self.index={n:i for i,n in enumerate(self.names)}
        self.uindex={}
        for c in self.coordinates:
            self.state.updU().setToZero();c.setSpeedValue(self.state,1.)
            self.uindex[c.getName()]=int(np.argmax(np.abs(self.state.getU().to_numpy())))
        self.state.updU().setToZero()
        self.inverse=o.InverseDynamicsSolver(self.model)
        self.motors=list(self.metadata['actuators'])
        self.capacities=np.array([self.metadata['actuators'][m]['capacity_Nm'] for m in self.motors])
        self.motor_indices=[self.uindex[m.removeprefix('motor_')] for m in self.motors]
        self.root_names=['pitch','yaw','roll','forward','height','lateral']
        self.root_indices=[self.uindex[n] for n in self.root_names]
        self.L=sum(self.metadata['segment_lengths_m']);self.bw=self.metadata['mass_kg']*9.80665
        self.root_scale=self.bw*np.array([self.L]*3+[1.]*3)
        rows=baseline['frames'];half=rows[-1]['time_s'];self.period=2*half
        self.speed=admission['preferred_speed_mps']
        times=[];q=[];u=[]
        # Transfer bending density when the physical tail subdivision changes.
        old_tail=[b for b in baseline['metadata'].get('axial_bindings',[]) if b['body'].startswith('tail_')]
        new_tail=self.metadata.get('tail_chain',[])
        tail_map={}
        if new_tail and old_tail:
            old_lengths=[np.linalg.norm(baseline['metadata']['segments'][b['body']]['extent_local_m']) for b in old_tail]
            old_edges=np.r_[0,np.cumsum(old_lengths)]
            for part in new_tail:
                weights=[]
                for i,old in enumerate(old_tail):
                    overlap=max(0.,min(part['arc_end_m'],old_edges[i+1])-max(part['arc_start_m'],old_edges[i]))
                    if overlap:weights.append((old['body'],overlap/old_lengths[i]))
                for suffix in ('','_yaw'):
                    tail_map[part['body']+suffix]=[(n+suffix,w) for n,w in weights]
        def mapped(row,name,kind):
            coordinates=row['coordinates']
            if name in tail_map:return sum(coordinates[n][kind]*w for n,w in tail_map[name])
            if name in coordinates:return coordinates[name][kind]
            mapping={'tail_0':('tail_proximal',.6),'tail_1':('tail_proximal',.4),
                     'tail_2':('tail_distal',.6),'tail_3':('tail_distal',.4),
                     'neck_upper':('neck',.45)}
            if name in mapping:
                source,scale=mapping[name];return coordinates[source][kind]*scale
            return 0.
        for repeat in range(2):
            for row in rows[:-1]:
                t=row['time_s']+repeat*half;values=[];speeds=[]
                for n in self.names:
                    source=opposite(n) if repeat else n
                    sign=-1 if repeat and reflected_coordinate(n) else 1
                    value=sign*mapped(row,source,'value');velocity=sign*mapped(row,source,'speed')
                    if n=='neck' and 'neck_upper' not in row['coordinates']:value*=.55;velocity*=.55
                    if n=='forward':
                        prior=baseline['metadata']['admission'] if self.policy.get('path_task') else admission
                        value+=repeat*prior['step_length_m'];value-=prior['preferred_speed_mps']*t;velocity-=prior['preferred_speed_mps']
                    values.append(value);speeds.append(velocity)
                times.append(t);q.append(values);u.append(speeds)
        if self.policy.get('initialization_body'):
            from .moco_bracing import supported_initialization
            q=supported_initialization(self,baseline,np.array(q),np.array(times)).tolist()
        # Remove sub-frame corners inherited from an unconverged coarse solve.
        # This changes the initializer only; contact/effort are recomputed by
        # inverse dynamics and the subsequent Moco trajectory remains free.
        smoothing=self.policy.get('baseline_smoothing_stride_fraction',0.)
        if smoothing:
            q=gaussian_filter1d(np.asarray(q),smoothing*self.period/(times[1]-times[0]),axis=0,mode='wrap').tolist()
        offset=q[0][self.index['forward']]
        for values in q:values[self.index['forward']]-=offset
        times.append(self.period);q.append(q[0]);u.append(u[0])
        self.path_task=self.policy.get('path_task')
        if self.path_task:
            from .moco_path_task import initialize
            if self.path_task.get('align_reference_support',False):
                source_duty=baseline['metadata']['recipe']['calibrated_task']['duty_factor']
                if abs(source_duty-self.path_task['source_duty_factor'])>1e-9:
                    raise ValueError('Support phase mapping disagrees with the saved source gait')
            if self.path_task.get('scale_reference_by_relative_speed',False):
                old_length=sum(baseline['metadata']['segment_lengths_m'])
                old_speed=baseline['metadata']['admission']['preferred_speed_mps']
                scale=min(1.,(self.speed/np.sqrt(self.L))/(old_speed/np.sqrt(old_length)))
                self.metadata['reference_transfer']=dict(relative_dimensionless_speed=scale,
                    source_speed_mps=old_speed,source_leg_length_m=old_length,
                    source_toe_off_radians=baseline['metadata']['recipe']['calibrated_task']['toe_off_pitch_radians'],
                    classification='Speed-scaled warm-reference excursion and release intent; engineering prior, not a predicted gait law')
            times,q=initialize(self,times,q,self.period)
            half=self.period
        self.base=CubicSpline(times,q,axis=0,bc_type='periodic')
        self.bounded={}
        if self.path_task and self.path_task.get('enforce_joint_limits',False):
            # Optimize latent joint coordinates, not unconstrained angles.
            # Sigmoid mapping enforces admitted ROM at every continuous time;
            # no final-pose clamp or contact-affecting playback fix is needed.
            latent=np.array(q,copy=True)
            bounded_settings=dict(self.metadata['coordinates'])
            if self.path_task.get('enforce_root_envelopes',False):
                for name in ('height','pitch','roll'):
                    setting=self.policy['body_envelope'][name]
                    center=float(latent[:,self.index[name]].mean()) if setting.get('center') is None else setting['center']
                    bounded_settings[name]={'bounds_rad':[center-setting['half_range'],center+setting['half_range']]}
            for name,setting in bounded_settings.items():
                i=self.index[name];lo,hi=setting['bounds_rad'];span=hi-lo
                fraction=(latent[:,i]-lo)/span
                if not np.isfinite(fraction).all():raise ValueError('Nonfinite joint seed: '+name)
                if np.min(fraction)<0 or np.max(fraction)>1:
                    self.metadata.setdefault('interior_seed_adjustments_rad',{})[name]=float(max(lo-latent[:,i].min(),latent[:,i].max()-hi,0))
                from .moco_joint_spline import to_latent
                latent[:,i]=to_latent(latent[:,i],lo,hi,interior_fraction=.01)
                self.bounded[i]=(lo,span)
            self.latent_base=CubicSpline(times,latent,axis=0,bc_type='periodic')

        self.parameters=basis_parameters(self.names,int(self.policy['harmonics']))
        if self.path_task:
            self.parameters=[]
            for name in self.names:
                if name.startswith('tail_') and self.path_task.get('retain_tail_warm_start',False):continue
                if name!='forward':self.parameters.append((name,0,'constant'))
                orders=int(self.path_task.get('leg_harmonics',self.policy['harmonics'])) if name.startswith(('hip_','knee_','ankle_','mtp_','digit_')) else int(self.policy['harmonics'])
                for order in range(1,orders+1):
                    self.parameters.append((name,order,'sin'))
                    if name!='forward':self.parameters.append((name,order,'cos'))
        self.times=np.linspace(0,half,int(self.policy['samples']))
        self.times_dense=np.linspace(0,half,241)
        self.contact_forces=[self.model.getForceSet().get(c['force']) for c in self.metadata['contacts']]
        self.contact_bodies=[self.model.getBodySet().get(c['body']) for c in self.metadata['contacts']]
        self.contact_points=[o.Vec3(*c['center_local_m']) for c in self.metadata['contacts']]
        self.clearance_frames=[(o.PhysicalFrame.safeDownCast(self.model.getComponent(c['path'])),c['minimum_height_m']) for c in self.metadata['clearance_frames']]
        self.nose=o.PhysicalOffsetFrame.safeDownCast(self.model.getComponent('/nose'))
        self.head=self.model.getBodySet().get('head')
        self.feet=[self.model.getBodySet().get('toe_'+side) for side in ('l','r')]
        self.reference=self.evaluate_kinematics(np.zeros(len(self.parameters)),self.times)
        nose_positions=[]
        for t,qq,uu in zip(self.times,self.reference[0],self.reference[1]):
            self.set_state(t,qq,uu)
            position=self.nose.getPositionInGround(self.state).to_numpy()
            if self.path_task:
                from .moco_path_task import path_frame
                origin,R=path_frame(t,self.speed,self.path_task['yaw_rate_rad_s'])
                position=R.T@(position-origin)
            else:position=position-[self.speed*t,0,0]
            nose_positions.append(position)
        self.target=np.mean(nose_positions,axis=0)
        if not self.path_task:self.target[2]=0
        self.vertical_regions=[]
        for setting in self.policy.get('vertical_regions',[]):
            region=self.model.getBodySet().get(setting['body']);heights=[]
            for t,qq,uu in zip(self.times,self.reference[0],self.reference[1]):
                self.set_state(t,qq,uu);heights.append(region.getPositionInGround(self.state).get(1))
            self.vertical_regions.append((region,float(np.mean(heights)),setting))
        self.pitch_target=recipe['attention']['nose_pitch_radians']
        self.last_log=0;self.calls=0;self.best=np.inf;self.best_x=None
        self._cache={}
        self._arrays(self.times)

    def _arrays(self,times):
        key=tuple(times)
        if key in self._cache:return self._cache[key]
        out=[]
        for derivative in range(3):
            basis=np.zeros((len(times),len(self.names),len(self.parameters)))
            for j,(n,order,kind) in enumerate(self.parameters):
                w=2*np.pi*order/self.period
                if kind=='constant':v=np.ones(len(times)) if derivative==0 else np.zeros(len(times))
                else:
                    angle=w*times+derivative*np.pi/2
                    v=w**derivative*(np.sin(angle) if kind=='sin' else np.cos(angle))
                basis[:,self.index[n],j]=v
                if not self.path_task and re.search(r'_l(?=_|$)',n):
                    sign=(-1 if reflected_coordinate(n) else 1)*(-1)**order
                    basis[:,self.index[opposite(n)],j]=sign*v
            out.append(basis)
        self._cache[key]=out
        return out

    def evaluate_kinematics(self,x,times):
        if self.path_task:
            from .moco_path_task import to_world
            if abs(self.path_task['yaw_rate_rad_s'])<1e-12:
                q,u,acc=self.local_derivatives(x,times)
                q[:,self.index['forward']]+=self.speed*times
                u[:,self.index['forward']]+=self.speed
                return q,u,acc
            def sample(t):
                values=self.local_kinematics(x,t)
                return to_world(values,t,self.index,self.speed,self.path_task['yaw_rate_rad_s'])
            h=1e-4
            q=sample(times);before=sample(times-h);after=sample(times+h)
            return q,(after-before)/(2*h),(after-2*q+before)/(h*h)
        basis=self._arrays(times) if hasattr(self,'_cache') else None
        if basis is None:self._cache={};basis=self._arrays(times)
        outputs=[]
        for derivative in range(3):
            values=self.base(times,derivative)+np.einsum('tqp,p->tq',basis[derivative],x)
            if derivative==0:values[:,self.index['forward']]+=self.speed*times
            if derivative==1:values[:,self.index['forward']]+=self.speed
            outputs.append(values)
        return outputs

    def local_derivatives(self,x,times):
        if not hasattr(self,'_cache'):self._cache={}
        basis=self._arrays(times)
        outputs=[self.base(times,d)+np.einsum('tqp,p->tq',basis[d],x) for d in range(3)]
        if self.bounded:
            from .moco_joint_spline import bounded
            latent=[self.latent_base(times,d)+np.einsum('tqp,p->tq',basis[d],x) for d in range(3)]
            for i,(lo,span) in self.bounded.items():
                value,first,second=bounded(latent[0][:,i],lo,lo+span)
                outputs[0][:,i]=value
                outputs[1][:,i]=first*latent[1][:,i]
                outputs[2][:,i]=first*latent[2][:,i]+second*latent[1][:,i]**2
        return outputs

    def local_kinematics(self,x,times):
        return self.local_derivatives(x,times)[0]

    def set_state(self,t,q,u):
        self.state.setTime(float(t))
        for i,c in enumerate(self.coordinates):
            c.setValue(self.state,float(q[i]),False);c.setSpeedValue(self.state,float(u[i]))
        self.model.realizeVelocity(self.state)

    def mechanics(self,x,times):
        q,u,acc=self.evaluate_kinematics(x,times)
        root=[];effort=[];nose=[];direction=[];slip=[];forces=[];clearance=[];com_velocity=[];region_heights=[];feet=[]
        for t,qq,uu,aa in zip(times,q,u,acc):
            self.set_state(t,qq,uu)
            udot=self.o.Vector(self.state.getNU(),0)
            for i,n in enumerate(self.names):udot[self.uindex[n]]=float(aa[i])
            torque=self.inverse.solve(self.state,udot).to_numpy()
            root.append(torque[self.root_indices]/self.root_scale)
            effort.append(torque[self.motor_indices]/self.capacities)
            com_velocity.append(self.model.calcMassCenterVelocity(self.state).to_numpy())
            feet.append([b.getPositionInGround(self.state).to_numpy().copy() for b in self.feet])
            region_heights.append([b.getPositionInGround(self.state).get(1) for b,_,_ in self.vertical_regions])
            nose.append(self.nose.getPositionInGround(self.state).to_numpy()-[self.speed*t,0,0])
            R=self.head.getTransformInGround(self.state).R()
            direction.append([R.get(0,0),R.get(1,0),R.get(2,0)])
            if self.path_task:
                from .moco_path_task import path_frame
                origin,path_rotation=path_frame(t,self.speed,self.path_task['yaw_rate_rad_s'])
                nose[-1]=path_rotation.T@(self.nose.getPositionInGround(self.state).to_numpy()-origin)
                direction[-1]=path_rotation.T@np.array(direction[-1])
            ff=[];vv=[]
            for f,b,p,c in zip(self.contact_forces,self.contact_bodies,self.contact_points,self.metadata['contacts']):
                record=f.getRecordValues(self.state)
                force=np.array([record.get(i) for i in range(3)])
                velocity=b.findStationVelocityInGround(self.state,p).to_numpy()
                velocity+=np.cross(b.getAngularVelocityInGround(self.state).to_numpy(),[0,-c['radius_m'],0])
                ff.append(force);vv.append(velocity[[0,2]]*np.sqrt(max(0.,force[1]/self.bw)))
            forces.append(ff);slip.append(vv)
            clearance.append([frame.getPositionInGround(self.state).get(1)-floor for frame,floor in self.clearance_frames])
        tail_vz=[];tail_xz=[]
        # These optional display-space tasks are inactive for the support pass.
        axial_times=zip(times,q,u,acc) if (self.policy.get('tail_vertical_damp_weight',0.) or self.policy.get('tail_figure8_weight',0.)) else []
        for t,qq,uu,aa in axial_times:
            self.set_state(t,qq,uu)
            vz=[];xz=[]
            for frame,floor in self.clearance_frames:
                pos=frame.getPositionInGround(self.state).to_numpy()
                vel=frame.findStationVelocityInGround(self.state,self.o.Vec3(0)).to_numpy()
                vz.append(vel[1])
                xz.append([pos[1],pos[2]])
            tail_vz.append(vz);tail_xz.append(xz)
        return dict(q=q,u=u,acc=acc,root=np.asarray(root),effort=np.asarray(effort),
                    nose=np.asarray(nose),direction=np.asarray(direction),slip=np.asarray(slip),forces=np.asarray(forces),clearance=np.asarray(clearance),com_velocity=np.asarray(com_velocity),region_heights=np.asarray(region_heights),
                    feet=np.asarray(feet),tail_vz=np.asarray(tail_vz),tail_xz=np.asarray(tail_xz))

    def residual(self,x):
        m=self.mechanics(x,self.times);p=self.policy;self.calls+=1
        target=[np.cos(self.pitch_target),np.sin(self.pitch_target),0.]
        if self.path_task:
            from .moco_path_task import path_frame,foot_task
            from scipy.spatial.transform import Rotation
            lead=self.path_task['yaw_rate_rad_s']*self.path_task['attention_lead_s']
            target=Rotation.from_rotvec([0,lead,0]).apply(target)
            m['q']=self.local_kinematics(x,self.times)
        delta=m['q']-self.reference[0]
        if self.path_task:delta=m['q']-self.base(self.times)
        deviation=[]
        for i,n in enumerate(self.names):
            weight=p['leg_deviation_weight'] if n.startswith(('hip_','knee_','ankle_','mtp_','digit_')) else p['body_deviation_weight']
            if n.endswith(('_yaw','_roll')) or n in ('lateral','yaw','roll'):weight=.1
            for prefix,override in p.get('reference_coordinate_weights',{}).items():
                if n.startswith(prefix):weight=float(override)
            deviation.extend(weight*delta[:,i])
        range_error=[]
        for n,b in self.metadata['coordinates'].items():
            value=m['q'][:,self.index[n]];lo,hi=b['bounds_rad']
            # An optional interior target prepares a feasible warm start. The
            # physical joint limits and emitted poses are never projected.
            margin=p.get('initialization_bound_margin',0.)
            lo+=margin;hi-=margin
            range_error.extend(p.get('range_weight',3.)*(np.minimum(value-lo,0)+np.maximum(value-hi,0)))
        for n,(lo,hi) in self.recipe.get('spatial',{}).get('root_bounds',{}).items():
            value=m['q'][:,self.index[n]]
            margin=p.get('initialization_bound_margin',0.)
            lo+=margin;hi-=margin
            range_error.extend(p.get('range_weight',3.)*(np.minimum(value-lo,0)+np.maximum(value-hi,0)))
        body_envelope=[]
        for n,setting in p.get('body_envelope',{}).items():
            value=m['q'][:,self.index[n]]
            center=float(value.mean()) if setting.get('center') is None else setting['center']
            body_envelope.extend(setting['weight']*np.maximum(np.abs(value-center)-setting['half_range'],0))
        region_error=[]
        for i,(_,center,setting) in enumerate(self.vertical_regions):
            excursion=np.abs(m['region_heights'][:,i]-center)/self.L
            region_error.extend(setting['weight']*np.maximum(excursion-setting['half_range_leg_lengths'],0))
        tail_smooth=[]
        chain=self.metadata.get('tail_chain',[])
        if chain:
            for suffix in ('','_yaw'):
                curvature=np.column_stack([m['q'][:,self.index[b['body']+suffix]]/b['length_m'] for b in chain])
                tail_smooth.extend((p.get('tail_curvature_weight',0.)*np.diff(curvature,axis=1)).ravel())
        from .moco_coordination_costs import shared_tail_carriage_residual
        # Preserve the previous periodic residual ordering exactly.
        tail_carriage=shared_tail_carriage_residual(self,m).T.ravel()
        # Angular-momentum counterbalance: the tail must counter-rotate against
        # the trunk so the pair conserves angular momentum.  This is the
        # physical role of a theropod tail as ballast.  First-order inertia-
        # weighted balance about pitch (lateral axis) and yaw (vertical axis);
        # the caudofemoralis coupling that enforces this in vivo is deferred.
        counterbalance=[]
        if chain and p.get('counterbalance_weight',0.):
            trunk_meta=self.metadata['segments']['trunk']['inertia_kg_m2']
            trunk_pitch_I=trunk_meta[2][2];trunk_yaw_I=trunk_meta[1][1]
            tail_pitch_I=0.;tail_yaw_I=0.
            tail_pitch_rate=np.zeros(len(self.times))
            tail_yaw_rate=np.zeros(len(self.times))
            for b in chain:
                I=self.metadata['segments'][b['body']]['inertia_kg_m2']
                tail_pitch_I+=I[2][2];tail_yaw_I+=I[1][1]
                tail_pitch_rate+=m['u'][:,self.index[b['body']]]
                tail_yaw_rate+=m['u'][:,self.index[b['body']+'_yaw']]
            scale=self.bw*self.L**2
            counterbalance=np.column_stack([
                (trunk_pitch_I*m['u'][:,self.index['pitch']]+tail_pitch_I*tail_pitch_rate)/scale,
                (trunk_yaw_I*m['u'][:,self.index['yaw']]+tail_yaw_I*tail_yaw_rate)/scale])
        # Figure-8 (lemniscate) tail tip objective: the tip should trace a
        # horizontal infinity path — lateral sway at 1x stride + forward recovery
        # at 2x stride — instead of springy vertical bouncing.
        tail_fig8=[]
        if chain and p.get('tail_figure8_weight',0.) and m.get('tail_xz') is not None:
            tip_idx=len(chain)-1
            xz=m['tail_xz'][:,tip_idx,:]  # (T,2) x/z relative to root
            # Reference lemniscate in YZ plane (vertical-lateral):
            # y = A*sin(2wt) at 2x stride, z = B*sin(wt) at 1x stride.
            # This is the horizontal-8 counterbalance path: lateral sway (1x)
            # + vertical recovery (2x) creates the infinity loop.
            period=self.period
            wt=2*np.pi*self.times/period
            A=p.get('figure8_vertical_amplitude_m',0.05)*self.L
            B=p.get('figure8_lateral_amplitude_m',0.12)*self.L
            y_ref=A*np.sin(2*wt)
            z_ref=B*np.sin(wt)
            # Penalize deviation from the lemniscate path
            tail_fig8=np.column_stack([
                (xz[:,0]-y_ref)/self.L,
                (xz[:,1]-z_ref)/self.L])
        # Caudofemoralis coupling: tail lateral torque is mechanically linked to
        # hip retraction torque through the CF muscle.  Left CF contracts →
        # tail flexes left + left femur retracts.  Right CF contracts → tail
        # flexes right + right femur retracts.  Net relationship:
        #   τ_tail_0_yaw = (r_tail/r_hip) * (τ_hip_r − τ_hip_l)
        # Engineering soft torque-coupling objective, not a reconstructed
        # muscle, enforced mechanical constraint, or identified moment arm.
        from .moco_coordination_costs import shared_cf_residual
        cf_residual=shared_cf_residual(self,m['effort'])
        # Soft velocity regularization between adjacent links and at base
        # reversals. This favors continuity; it does not establish a physical
        # propagation speed, activation sequence, or prohibit phase lead.
        tail_wave=[]
        wave_weight=p.get('tail_wave_weight',0.)
        if chain and wave_weight:
            for suffix in ('','_yaw'):
                vels=np.column_stack([m['u'][:,self.index[b['body']+suffix]] for b in chain])
                # Velocity continuity: penalize velocity jumps between adjacent links
                tail_wave.extend((wave_weight*np.diff(vels,axis=1)/self.speed).ravel())
                # Phase lead penalty: when base is near zero velocity (reversing),
                # tip should not be moving much (prevents tip-first reversal)
                base_vel=vels[:,0]
                tip_vel=vels[:,-1]
                reversal_mask=np.exp(-(base_vel/self.speed)**2/0.05)
                tail_wave.extend((wave_weight*reversal_mask*tip_vel/self.speed).ravel())
        support_task=[]
        if p.get('support_refinement'):
            from .moco_support import recovery_residual,lane_residual
            task=p['support_refinement']
            loads=np.column_stack([m['forces'][:,[i for i,c in enumerate(self.metadata['contacts']) if c['force'].endswith('_'+side)],1].sum(axis=1)/self.bw for side in ('l','r')])
            for j,side in enumerate(('l','r')):
                idx=self.index['ankle_'+side]
                support_task.extend(recovery_residual(m['q'][:,idx],m['u'][:,idx],m['acc'][:,idx],loads[:,j],self.period,task['ankle_recovery']))
                # A smooth load-gated comfort cost discourages rapid back-and-
                # forth ankle bending under support. This leaves every angle
                # free and recomputes contact/effort; it is not an angle clamp.
                loaded=task.get('ankle_loaded',{})
                if loaded:
                    gate=np.sqrt(np.maximum(loads[:,j],0)/(np.maximum(loads[:,j],0)+.08))
                    omega=np.sqrt(9.80665/self.L)
                    support_task.extend(loaded['rate_weight']*gate*m['u'][:,idx]/omega)
                    support_task.extend(loaded['acceleration_weight']*gate*m['acc'][:,idx]/omega**2)

            hip_width=abs(self.admission['points']['rightLeg.0'][2]-self.admission['points']['leftLeg.0'][2])
            lateral=m['feet'][:,:,2]
            if self.path_task:
                origin,rotation=path_frame(self.times,self.speed,self.path_task['yaw_rate_rad_s'])
                lateral=np.einsum('tji,tsj->tsi',rotation,m['feet']-origin[:,None,:])[:,:,2]
            support_task.extend(lane_residual(lateral,loads,
                task['half_track_hip_width_ratio']*hip_width,
                task['track_allowance_leg_lengths']*self.L,self.L,task['track_weight']))
        if self.path_task:
            targets=np.array([[foot_task(self,t,side)[0] for side in ('l','r')] for t in self.times])
            support_task.extend((self.path_task['foot_task_weight']*(m['feet']-targets)/self.L).ravel())
        motor_speed=np.column_stack([m['u'][:,self.index[n.removeprefix('motor_')]] for n in self.motors])
        positive_power=np.maximum(m['effort']*self.capacities*motor_speed,0)/(self.bw*self.speed)
        tail_indices=[i for i,n in enumerate(self.names) if n.startswith('tail_')]
        tail_acceleration=m['acc'][:,tail_indices]*(self.period/(2*np.pi))**2
        effort=m['effort'];command=effort+np.gradient(effort,self.times,axis=0)*self.recipe['activation_time_constant_s']
        from .moco_coordination_costs import shared_effort_residual
        effort_costs=shared_effort_residual(effort,command,p)
        result=np.concatenate([
            (p['root_balance_weight']*m['root']).ravel(),
            (p['gaze_position_weight']*(m['nose']-self.target)/self.L).ravel(),
            (p['gaze_orientation_weight']*(m['direction']-target)).ravel(),
            np.asarray(deviation),np.asarray(range_error),
            np.asarray(body_envelope),np.asarray(region_error),np.asarray(tail_smooth),np.asarray(tail_carriage),
            (p.get('positive_work_weight',0.)*positive_power).ravel(),
            p.get('vertical_work_weight',0.)*m['com_velocity'][:,1]/self.speed,
            *(v.ravel() for v in effort_costs),
            (p['root_attitude_weight']*m['q'][:,[self.index['yaw'],self.index['roll']]]).ravel(),
            (p['foot_velocity_weight']*m['slip']).ravel(),
            (p.get('clearance_weight',100.)*np.minimum(m['clearance'],0)/self.L).ravel(),
            (p.get('tail_acceleration_weight',0.)*tail_acceleration).ravel(),
            (p.get('counterbalance_weight',0.)*counterbalance).ravel() if len(counterbalance) else np.array([]),
            (p.get('tail_vertical_damp_weight',0.)*m['tail_vz']/self.speed).ravel() if m.get('tail_vz') is not None else np.array([]),
            (p.get('tail_figure8_weight',0.)*tail_fig8).ravel() if len(tail_fig8) else np.array([]),
            cf_residual.ravel() if len(cf_residual) else np.array([]),
            np.asarray(tail_wave) if len(tail_wave) else np.array([]),
            np.asarray(support_task),
            .003*x
        ])
        score=float(result@result)
        if score<self.best:
            self.best=score;self.best_x=x.copy()
        now=time.monotonic()
        if now-self.last_log>30:
            self.last_log=now
            print(json.dumps(dict(calls=self.calls,cost=score,root_rms=float(np.sqrt(np.mean(m['root']**2))),
                                 nose_range_m=np.ptp(m['nose'],axis=0).tolist(),max_activation=float(np.max(np.abs(effort))))),flush=True)
            np.save(self.output/'latest-coefficients.npy',self.best_x)
        return result

    def export(self,x):
        times=self.times_dense;m=self.mechanics(x,times);names=[]
        states=[]
        for i,n in enumerate(self.names):
            c=self.coordinates[i];path=c.getAbsolutePathString()
            names.extend([path+'/value',path+'/speed']);states.extend([m['q'][:,i],m['u'][:,i]])
        for i,n in enumerate(self.motors):
            names.append('/forceset/'+n+'/activation');states.append(m['effort'][:,i])
        controls=m['effort']+self.recipe['activation_time_constant_s']*np.gradient(m['effort'],times,axis=0)
        control_names=['/forceset/'+n for n in self.motors]
        matrix=np.column_stack([times,*states,*controls.T])
        header='inDegrees=no\nnum_controls='+str(len(control_names))+'\nnum_derivatives=0\nnum_input_controls=0\nnum_multipliers=0\nnum_parameters=0\nnum_slacks=0\nnum_states='+str(len(names))+'\nendheader\n'
        with (self.output/'solution.sto').open('w') as f:
            f.write(header);f.write('\t'.join(['time',*names,*control_names])+'\n');np.savetxt(f,matrix,delimiter='\t',fmt='%.15g')
        report=dict(schema='eonwild.motion.spatial-initialization.v1',
            method='Smooth periodic coefficient optimization using exact OpenSim inverse dynamics and ground contact; no root force actuators',
            root_residual_rms_BW_or_BWL=float(np.sqrt(np.mean(m['root']**2))),
            root_residual_max_by_axis=np.max(np.abs(m['root']),axis=0).tolist(),
            nose_range_m=np.ptp(m['nose'],axis=0).tolist(),nose_target_m=self.target.tolist(),
            maximum_activation=float(np.max(np.abs(m['effort']))),maximum_control=float(np.max(np.abs(controls))),
            vertical_region_ranges_m={setting['body']:float(np.ptp(m['region_heights'][:,i])) for i,(_,_,setting) in enumerate(self.vertical_regions)},
            maximum_activation_by_motor={n:float(np.max(np.abs(m['effort'][:,i]))) for i,n in enumerate(self.motors)},
            coordinate_ranges={n:[float(m['q'][:,i].min()),float(m['q'][:,i].max())] for i,n in enumerate(self.names)},
            clearance_margin_m={c['path']:float(m['clearance'][:,i].min()) for i,c in enumerate(self.metadata['clearance_frames'])},
            tail_yaw_ranges_rad={n:float(np.ptp(m['q'][:,self.index[n]])) for n in self.names if n.startswith('tail') and n.endswith('yaw')},
            status='INITIALIZER_NOT_MOCO_CONVERGENCE',calls=self.calls)
        (self.output/'coordination-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
        np.save(self.output/'coefficients.npy',x)
        (self.output/'coefficient-layout.json').write_text(json.dumps(self.parameters,indent=2)+'\n')
        return report


def run(admission_path,recipe_path,baseline_path,output,initial=None,evaluate_only=False):
    import opensim as o
    o.Logger.removeFileSink()
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if (output/'solution.sto').exists():raise FileExistsError('Preserve earlier coordination result; use a new directory')
    admission=json.loads(Path(admission_path).read_text());recipe=json.loads(Path(recipe_path).read_text())
    baseline=json.loads(Path(baseline_path).read_text())
    problem=Coordination(admission,recipe,baseline,output)
    problem.model.printToXML(str(output/'model.osim'))
    problem.metadata.update(schema='eonwild.motion.moco-model-receipt.v1',admission=admission,recipe=recipe,
        model_sha256=hashlib.sha256((output/'model.osim').read_bytes()).hexdigest(),status='INITIALIZATION_MODEL',
        classification=recipe['classification'],reference_directory=str(output),user_review='PENDING',opensim=o.GetVersion())
    (output/'model-receipt.json').write_text(json.dumps(problem.metadata,indent=2)+'\n')
    (output/'coefficient-layout.json').write_text(json.dumps(problem.parameters,indent=2)+'\n')
    x=np.zeros(len(problem.parameters))
    if initial:
        prior=np.load(initial)
        layout_path=Path(initial).with_name('coefficient-layout.json')
        if layout_path.exists():
            layout=json.loads(layout_path.read_text())
            if len(layout)!=len(prior):raise ValueError('Coefficient layout does not match saved values')
            by_parameter={tuple(k):v for k,v in zip(layout,prior)}
            x=np.array([by_parameter.get(k,0.) for k in problem.parameters])
        elif prior.shape==x.shape:x=prior
        else:raise ValueError('Changed coordination basis requires saved coefficient-layout.json')
        if not np.isfinite(x).all():raise ValueError('Nonfinite coordination coefficients')
    print('Parameters',len(x),'samples',len(problem.times),flush=True)
    evaluations=None
    if not evaluate_only:
        result=least_squares(problem.residual,x,max_nfev=problem.policy['max_evaluations'],
                             x_scale='jac',diff_step=problem.policy.get('numerical_diff_step'),ftol=2e-5,xtol=1e-6,gtol=1e-6,verbose=1)
        x=result.x
        evaluations=int(result.nfev)
    report=problem.export(x)
    (output/'solve-receipt.json').write_text(json.dumps(dict(success=False,status='REDUCED_COORDINATE_INITIALIZER',
        iterations=None,function_evaluations=evaluations,residual_calls=problem.calls,objective=problem.best if np.isfinite(problem.best) else None,mesh_intervals=len(problem.times)-1,
        model_sha256=problem.metadata['model_sha256'],claim='Guided initializer, not an accepted Moco solve'),indent=2)+'\n')
    print(json.dumps(report),flush=True)
