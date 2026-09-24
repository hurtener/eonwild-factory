"""Finite whole-body coordination using the shared OpenSim mechanics.

A task supplies a boundary state, travel reference, foot poses and attention.
It does not supply torso or tail animation. All admitted coordinates participate
in the same bounded trajectory optimization, including the twelve tail links.
This reduced-coordinate optimizer is NOT a converged Moco/forward simulation.
"""
import json
import hashlib
from pathlib import Path
import time
import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import least_squares
from scipy.sparse import csr_matrix
from scipy.spatial.transform import Rotation
from .moco_joint_spline import bounded
from .moco_coordination_costs import shared_effort_residual, shared_cf_residual, shared_tail_carriage_residual


def coefficient_limits(names, common, overrides):
    """Tighten numerical search radii without changing physical joint limits."""
    if not np.isfinite(common) or common <= 0:
        raise ValueError('Common coefficient limit must be finite and positive')
    limits=np.full(len(names),float(common))
    for prefix,limit in overrides.items():
        if not np.isfinite(limit) or not 0<float(limit)<=common:
            raise ValueError('Coordinate trust region must tighten the common coefficient limit')
        matches=[i for i,name in enumerate(names) if name.startswith(prefix)]
        if not matches:
            raise ValueError(f'Coordinate trust region matches no coordinates: {prefix}')
        for i in matches:limits[i]=min(limits[i],float(limit))
    return limits


class FiniteBasis:
    """Compact quintic corrections with exact C2 zero endpoint conditions."""
    def __init__(self, start, end, intervals):
        if not end > start or intervals < 4:
            raise ValueError('Finite basis requires positive duration and at least four intervals')
        edges=np.linspace(start,end,intervals+1)
        knots=np.r_[[start]*5,edges,[end]*5]
        n=len(knots)-6
        # Clamped first/last three coefficients are zero: position, speed,
        # acceleration all match the supplied boundary trajectory.
        self.spline=BSpline(knots,np.eye(n)[:,3:-3],5,extrapolate=False)
        self.size=n-6;self.start=start;self.end=end

    def arrays(self,times):
        t=np.atleast_1d(times);mask=(t>=self.start)&(t<=self.end)
        out=[]
        for d in range(3):
            a=np.zeros((len(t),self.size));a[mask]=self.spline(t[mask],nu=d);out.append(a)
        return out




class FiniteCoordination:
    def __init__(self,problem,seed,times,foot_task,settings):
        self.p=problem;self.seed=seed;self.settings=settings;self.foot_task=foot_task
        self.times=np.asarray(times);self.nq=len(problem.names)
        self.basis=FiniteBasis(settings['start_s'],settings['end_s'],settings['intervals'])
        self.scales=np.array([problem.L*.03 if n in ('forward','height','lateral') else .06 for n in problem.names])
        self.joint_bounds={problem.index[n]:tuple(v['bounds_rad']) for n,v in problem.metadata['coordinates'].items()}
        self.joint_bounds.update({problem.index[n]:tuple(v) for n,v in problem.recipe['spatial'].get('root_bounds',{}).items()})
        self.reference=seed(self.times)
        self.targets=np.array([[foot_task(t,s)[0] for s in ('l','r')] for t in self.times])
        self.rotations=np.array([[foot_task(t,s)[1] for s in ('l','r')] for t in self.times])
        self.digits=np.array([[foot_task(t,s)[2] for s in ('l','r')] for t in self.times])
        self.old=None;self.cache=None;self.calls=0;self.best=np.inf;self.best_x=None;self.last_log=0
        self.chain=problem.metadata.get('tail_chain',[])
        self.char_speed=np.sqrt(9.80665*problem.L)
        self.char_time=np.sqrt(problem.L/9.80665)
        # Shared mechanics reports positions in world coordinates for this task.
        problem.path_task=None;problem.speed=0.
        problem.evaluate_kinematics=self.evaluate
        self.reference_nose=[];self.reference_direction=[]
        for t,q in zip(self.times,self.reference):
            problem.set_state(t,q,np.zeros(self.nq))
            self.reference_nose.append(problem.nose.getPositionInGround(problem.state).to_numpy().copy())
            R=problem.head.getTransformInGround(problem.state).R()
            self.reference_direction.append([R.get(i,0) for i in range(3)])
        self.reference_nose=np.array(self.reference_nose);self.reference_direction=np.array(self.reference_direction)
        # Tail starts from a carried rest, not the old balance-reference sway.
        self.reference_regions=np.zeros((len(self.times),len(problem.vertical_regions)))
        for j, (body,_,_) in enumerate(problem.vertical_regions):
            for i,(t,q) in enumerate(zip(self.times,self.reference)):
                problem.set_state(t,q,np.zeros(self.nq));self.reference_regions[i,j]=body.getPositionInGround(problem.state).get(1)

    def evaluate(self,x,times):
        times=np.atleast_1d(times);B=self.basis.arrays(times)
        coefficients=np.asarray(x).reshape(self.basis.size,self.nq)*self.scales
        outputs=[self.seed(times,d)+B[d]@coefficients for d in range(3)]
        # BoundedJointSpline exposes its latent spline; modify latent variables
        # so continuous ROM is preserved without clipping final moving angles.
        for i,(lo,hi) in self.joint_bounds.items():
            if i in self.seed.bounds:
                raw=[self.seed.spline(times,d)[:,i]+(B[d]@coefficients)[:,i] for d in range(3)]
            else:
                # Root bounds are handled as smooth residuals: preserve exact
                # adopted boundary values without silently projecting them.
                continue
            value,first,second=bounded(raw[0],lo,hi)
            outputs[0][:,i]=value;outputs[1][:,i]=first*raw[1]
            outputs[2][:,i]=first*raw[2]+second*raw[1]**2
        return outputs

    def mechanics(self,x):
        state=np.stack(self.evaluate(x,self.times))
        changed=np.arange(len(self.times)) if self.old is None else np.flatnonzero(np.any(state!=self.old,axis=(0,2)))
        if len(changed):
            values=self.p.mechanics(x,self.times[changed])
            orientations=[]
            for t,q,u in zip(self.times[changed],state[0,changed],state[1,changed]):
                self.p.set_state(t,q,u);row=[]
                for foot in self.p.feet:
                    R=foot.getTransformInGround(self.p.state).R();row.append([[R.get(i,j) for j in range(3)] for i in range(3)])
                orientations.append(row)
            values['foot_rotations']=np.array(orientations)
            if self.cache is None:self.cache={k:np.zeros((len(self.times),)+v.shape[1:]) for k,v in values.items() if len(v)==len(changed)}
            for k in self.cache:self.cache[k][changed]=values[k]
        self.old=state.copy()
        return self.cache

    def residual(self,x):
        p=self.p;policy=p.policy;m=self.mechanics(x);self.calls+=1
        q,u,acc=m['q'],m['u'],m['acc'];effort=m['effort']
        command=effort+np.gradient(effort,self.times,axis=0)*p.recipe['activation_time_constant_s']
        def rows(v):return np.asarray(v).reshape(len(self.times),-1)
        parts=[policy['root_balance_weight']*m['root'],*shared_effort_residual(effort,command,policy),
               rows(policy['foot_velocity_weight']*m['slip']),
               policy.get('clearance_weight',100.)*np.minimum(m['clearance'],0)/p.L,
               policy['gaze_position_weight']*(m['nose']-self.reference_nose)/p.L,
               policy['gaze_orientation_weight']*(m['direction']-self.reference_direction),
               shared_cf_residual(p,effort)]
        # Contact task remains dominant, but body/legs can distribute effort.
        parts.append(rows(self.settings['foot_position_weight']*(m['feet']-self.targets)/p.L))
        relative=np.einsum('tsji,tsjk->tsik',self.rotations,m['foot_rotations'])
        angle=Rotation.from_matrix(relative.reshape(-1,3,3)).as_rotvec().reshape(len(self.times),2,3)
        parts.append(rows(self.settings['foot_orientation_weight']*angle))
        parts.append(self.settings['digit_weight']*(q[:,[p.index['digit_l'],p.index['digit_r']]]-self.digits))
        weights=[]
        for n in p.names:
            weight=policy['leg_deviation_weight'] if n.startswith(('hip_','knee_','ankle_','mtp_','digit_')) else policy['body_deviation_weight']
            for prefix,override in policy.get('reference_coordinate_weights',{}).items():
                if n.startswith(prefix):weight=override
            weights.append(weight)
        parts.append((q-self.reference)*weights)
        for i,(lo,hi) in self.joint_bounds.items():
            parts.append(policy.get('range_weight',200.)*(np.minimum(q[:,i]-lo,0)+np.maximum(q[:,i]-hi,0))[:,None])
        for n,s in policy.get('body_envelope',{}).items():
            i=p.index[n];center=self.reference[:,i] if s.get('center') is None else s['center']
            parts.append((s['weight']*np.maximum(abs(q[:,i]-center)-s['half_range'],0))[:,None])
        for j,(_,_,s) in enumerate(p.vertical_regions):
            parts.append((s['weight']*np.maximum(abs(m['region_heights'][:,j]-self.reference_regions[:,j])/p.L-s['half_range_leg_lengths'],0))[:,None])
        # Retain the same loaded-tail carriage objective as periodic motion.
        # Effort minimization must not evade gravity by hoisting the tail.
        parts.append(shared_tail_carriage_residual(p,m))
        for suffix in ('','_yaw'):
            indices=[p.index[b['body']+suffix] for b in self.chain]
            if indices:
                lengths=np.array([b['length_m'] for b in self.chain])
                parts.extend([policy.get('tail_curvature_weight',0.)*np.diff(q[:,indices]/lengths,axis=1),
                    policy.get('tail_wave_weight',0.)*np.diff(u[:,indices],axis=1)/self.char_speed,
                    policy.get('tail_acceleration_weight',0.)*acc[:,indices]*self.char_time**2])
        # All coordinates are regularized in physical time, with no gait clock.
        parts.append(self.settings['acceleration_weight']*acc*self.char_time**2)
        motorspeed=u[:,[p.index[n.removeprefix('motor_')] for n in p.motors]]
        parts.append(policy.get('positive_work_weight',0.)*np.maximum(effort*p.capacities*motorspeed,0)/(p.bw*self.char_speed))
        from .moco_support import ankle_support_residual
        support=policy.get('support_refinement',{})
        for side in ('l','r'):
            load=m['forces'][:,[j for j,c in enumerate(p.metadata['contacts']) if c['force'].endswith('_'+side)],1].sum(axis=1)/p.bw
            i=p.index['ankle_'+side]
            parts.append(ankle_support_residual(q[:,i],u[:,i],acc[:,i],load,
                                               p.period,p.L,support))
        result=np.concatenate([rows(v) for v in parts],axis=1)
        self.row_size=result.shape[1]
        score=float(np.sum(result**2))
        if score<self.best:self.best=score;self.best_x=np.array(x,copy=True)
        if time.monotonic()-self.last_log>30:
            self.last_log=time.monotonic()
            print(json.dumps(dict(finite_calls=self.calls,cost=score,root_rms=float(np.sqrt(np.mean(m['root']**2))),max_activation=float(abs(effort).max()))),flush=True)
        return result.ravel()

    def solve(self):
        zero=np.zeros(self.basis.size*self.nq)
        limits=np.tile(coefficient_limits(self.p.names,
            self.settings['coefficient_limit'],
            self.settings.get('coordinate_coefficient_limits',{})),self.basis.size)
        warm=self.settings.get('initial_coefficients')
        if warm:
            zero=np.load(warm)
            if zero.shape!=(self.basis.size*self.nq,) or not np.isfinite(zero).all():
                raise ValueError('Incompatible finite warm-start coefficients')
            # Numerical warm-start projection only; physical angles, anatomical
            # stops and all acceptance thresholds are unchanged.
            zero=np.clip(zero,-limits+1e-10,limits-1e-10)
        initial=self.residual(zero).copy()
        B=self.basis.arrays(self.times)
        active=sum(abs(v) for v in B)>1e-14
        # Activation command costs use adjacent time samples as well.
        active[1:]|=active[:-1].copy();active[:-1]|=active[1:].copy()
        pattern=np.repeat(np.repeat(active,self.nq,axis=1),self.row_size,axis=0)
        result=least_squares(self.residual,zero,jac_sparsity=csr_matrix(pattern),
            bounds=(-limits,limits),
            max_nfev=self.settings['max_evaluations'],diff_step=1e-4,
            ftol=1e-5,xtol=1e-5,gtol=1e-5,verbose=1,tr_solver='lsmr')
        final=self.residual(result.x)
        receipt=dict(classification='Shared finite whole-body reduced-coordinate optimization; not full Moco convergence',
            status=int(result.status),optimizer_success=bool(result.success),message=result.message,
            evaluations=int(result.nfev),residual_calls=self.calls,initial_cost=float(initial@initial),final_cost=float(final@final),
            free_coordinates=self.p.names,temporal_basis='C2 endpoint-preserving quintic B-spline corrections',
            coefficients=len(result.x),settings=self.settings,task_foot_position_weight=self.settings['foot_position_weight'],
            model_limits_unchanged=True,physical_validation='PENDING dense final replay',
            initial_coefficients_sha256=hashlib.sha256(Path(warm).read_bytes()).hexdigest() if warm else None)
        (self.p.output/'finite-coordination.json').write_text(json.dumps(receipt,indent=2)+'\n')
        np.save(self.p.output/'finite-coefficients.npy',result.x)
        return result.x,receipt
