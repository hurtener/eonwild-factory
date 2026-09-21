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
        def mapped(row,name,kind):
            coordinates=row['coordinates']
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
                    if n=='forward':value+=repeat*admission['step_length_m'];value-=self.speed*t;velocity-=self.speed
                    values.append(value);speeds.append(velocity)
                times.append(t);q.append(values);u.append(speeds)
        # Remove sub-frame corners inherited from an unconverged coarse solve.
        # This changes the initializer only; contact/effort are recomputed by
        # inverse dynamics and the subsequent Moco trajectory remains free.
        smoothing=self.policy.get('baseline_smoothing_stride_fraction',0.)
        if smoothing:
            q=gaussian_filter1d(np.asarray(q),smoothing*self.period/(times[1]-times[0]),axis=0,mode='wrap').tolist()
        offset=q[0][self.index['forward']]
        for values in q:values[self.index['forward']]-=offset
        times.append(self.period);q.append(q[0]);u.append(u[0])
        self.base=CubicSpline(times,q,axis=0,bc_type='periodic')
        self.parameters=basis_parameters(self.names,int(self.policy['harmonics']))
        self.times=np.linspace(0,half,int(self.policy['samples']))
        self.times_dense=np.linspace(0,half,241)
        self.contact_forces=[self.model.getForceSet().get(c['force']) for c in self.metadata['contacts']]
        self.contact_bodies=[self.model.getBodySet().get(c['body']) for c in self.metadata['contacts']]
        self.contact_points=[o.Vec3(*c['center_local_m']) for c in self.metadata['contacts']]
        self.clearance_frames=[(o.PhysicalFrame.safeDownCast(self.model.getComponent(c['path'])),c['minimum_height_m']) for c in self.metadata['clearance_frames']]
        self.nose=o.PhysicalOffsetFrame.safeDownCast(self.model.getComponent('/nose'))
        self.head=self.model.getBodySet().get('head')
        self.reference=self.evaluate_kinematics(np.zeros(len(self.parameters)),self.times)
        nose_positions=[]
        for t,qq,uu in zip(self.times,self.reference[0],self.reference[1]):
            self.set_state(t,qq,uu)
            nose_positions.append(self.nose.getPositionInGround(self.state).to_numpy()-[self.speed*t,0,0])
        self.target=np.mean(nose_positions,axis=0);self.target[2]=0
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
                if re.search(r'_l(?=_|$)',n):
                    sign=(-1 if reflected_coordinate(n) else 1)*(-1)**order
                    basis[:,self.index[opposite(n)],j]=sign*v
            out.append(basis)
        self._cache[key]=out
        return out

    def evaluate_kinematics(self,x,times):
        basis=self._arrays(times) if hasattr(self,'_cache') else None
        if basis is None:self._cache={};basis=self._arrays(times)
        outputs=[]
        for derivative in range(3):
            values=self.base(times,derivative)+np.einsum('tqp,p->tq',basis[derivative],x)
            if derivative==0:values[:,self.index['forward']]+=self.speed*times
            if derivative==1:values[:,self.index['forward']]+=self.speed
            outputs.append(values)
        return outputs

    def set_state(self,t,q,u):
        self.state.setTime(float(t))
        for i,c in enumerate(self.coordinates):
            c.setValue(self.state,float(q[i]),False);c.setSpeedValue(self.state,float(u[i]))
        self.model.realizeVelocity(self.state)

    def mechanics(self,x,times):
        q,u,acc=self.evaluate_kinematics(x,times)
        root=[];effort=[];nose=[];direction=[];slip=[];forces=[];clearance=[]
        for t,qq,uu,aa in zip(times,q,u,acc):
            self.set_state(t,qq,uu)
            udot=self.o.Vector(self.state.getNU(),0)
            for i,n in enumerate(self.names):udot[self.uindex[n]]=float(aa[i])
            torque=self.inverse.solve(self.state,udot).to_numpy()
            root.append(torque[self.root_indices]/self.root_scale)
            effort.append(torque[self.motor_indices]/self.capacities)
            nose.append(self.nose.getPositionInGround(self.state).to_numpy()-[self.speed*t,0,0])
            R=self.head.getTransformInGround(self.state).R()
            direction.append([R.get(0,0),R.get(1,0),R.get(2,0)])
            ff=[];vv=[]
            for f,b,p,c in zip(self.contact_forces,self.contact_bodies,self.contact_points,self.metadata['contacts']):
                record=f.getRecordValues(self.state)
                force=np.array([record.get(i) for i in range(3)])
                velocity=b.findStationVelocityInGround(self.state,p).to_numpy()
                velocity+=np.cross(b.getAngularVelocityInGround(self.state).to_numpy(),[0,-c['radius_m'],0])
                ff.append(force);vv.append(velocity[[0,2]]*np.sqrt(max(0.,force[1]/self.bw)))
            forces.append(ff);slip.append(vv)
            clearance.append([frame.getPositionInGround(self.state).get(1)-floor for frame,floor in self.clearance_frames])
        return dict(q=q,u=u,acc=acc,root=np.asarray(root),effort=np.asarray(effort),
                    nose=np.asarray(nose),direction=np.asarray(direction),slip=np.asarray(slip),forces=np.asarray(forces),clearance=np.asarray(clearance))

    def residual(self,x):
        m=self.mechanics(x,self.times);p=self.policy;self.calls+=1
        target=[np.cos(self.pitch_target),np.sin(self.pitch_target),0.]
        delta=m['q']-self.reference[0]
        deviation=[]
        for i,n in enumerate(self.names):
            weight=p['leg_deviation_weight'] if n.startswith(('hip_','knee_','ankle_','mtp_','digit_')) else p['body_deviation_weight']
            if n.endswith(('_yaw','_roll')) or n in ('lateral','yaw','roll'):weight=.1
            deviation.extend(weight*delta[:,i])
        range_error=[]
        for n,b in self.metadata['coordinates'].items():
            value=m['q'][:,self.index[n]];lo,hi=b['bounds_rad']
            range_error.extend(p.get('range_weight',3.)*(np.minimum(value-lo,0)+np.maximum(value-hi,0)))
        tail_indices=[i for i,n in enumerate(self.names) if n.startswith('tail_')]
        tail_acceleration=m['acc'][:,tail_indices]*(self.period/(2*np.pi))**2
        effort=m['effort'];command=effort+np.gradient(effort,self.times,axis=0)*self.recipe['activation_time_constant_s']
        result=np.concatenate([
            (p['root_balance_weight']*m['root']).ravel(),
            (p['gaze_position_weight']*(m['nose']-self.target)/self.L).ravel(),
            (p['gaze_orientation_weight']*(m['direction']-target)).ravel(),
            np.asarray(deviation),np.asarray(range_error),
            (p['effort_weight']*effort).ravel(),
            (p['capacity_weight']*np.maximum(np.abs(effort)-.95,0)).ravel(),
            (p['capacity_weight']*.5*np.maximum(np.abs(command)-.98,0)).ravel(),
            (p['root_attitude_weight']*m['q'][:,[self.index['yaw'],self.index['roll']]]).ravel(),
            (p['foot_velocity_weight']*m['slip']).ravel(),
            (p.get('clearance_weight',100.)*np.minimum(m['clearance'],0)/self.L).ravel(),
            (p.get('tail_acceleration_weight',0.)*tail_acceleration).ravel(),
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
                             x_scale='jac',ftol=2e-5,xtol=1e-6,gtol=1e-6,verbose=1)
        x=result.x
        evaluations=int(result.nfev)
    report=problem.export(x)
    (output/'solve-receipt.json').write_text(json.dumps(dict(success=False,status='REDUCED_COORDINATE_INITIALIZER',
        iterations=None,function_evaluations=evaluations,residual_calls=problem.calls,objective=problem.best if np.isfinite(problem.best) else None,mesh_intervals=len(problem.times)-1,
        model_sha256=problem.metadata['model_sha256'],claim='Guided initializer, not an accepted Moco solve'),indent=2)+'\n')
    print(json.dumps(report),flush=True)
