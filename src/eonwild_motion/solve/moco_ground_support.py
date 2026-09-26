"""Shared body-to-foot support coordination for finite floor behaviors.

Kinematic initializer with admitted joint limits and material floor witnesses.
Contact and required effort are audited afterwards; this is not forward dynamics.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .moco_living_intent import keyed


def recovery_reference(rest,standing,time,policy,index,bounds):
    """Fold, roll while low, establish feet, then extend. Not a pose crossfade."""
    q=rest.copy();fold=keyed(time,policy['fold_keys']);roll=keyed(time,policy['roll_keys']);rise=keyed(time,policy['rise_keys'])
    for n in ('pitch','yaw','roll'):
        i=index[n];q[i]=rest[i]+roll*(standing[i]-rest[i])
    for n in bounds:
        i=index[n]
        target=policy.get('crouch_radians',{}).get(n,standing[i])
        lo,hi=bounds[n];target=np.clip(target,lo+1e-4,hi-1e-4)
        folded=rest[i]+fold*(target-rest[i]);q[i]=folded+rise*(standing[i]-folded)
    q[index['height']]=rest[index['height']]+rise*(standing[index['height']]-rest[index['height']])
    return q


class GroundSupport:
    def __init__(self,p,spec,bounds,initial,standing=None):
        self.p=p;self.spec=spec;self.ix=p.index;self.zeros=np.zeros(len(p.names));self.bounds=bounds
        # Do not move yaw/roll to evade the requested roll; resolve limbs and
        # support locations with the same admitted anatomical ranges.
        self.names=list(bounds)+['height','forward','lateral'];self.ids=[p.index[n] for n in self.names]
        limits=[bounds[n] for n in bounds]+[(.02*p.L,1.3*p.L),
            (initial[p.index['forward']]-3*p.L,initial[p.index['forward']]+30*p.L),
            (initial[p.index['lateral']]-2*p.L,initial[p.index['lateral']]+2*p.L)]
        self.limits=np.array(limits).T;self.limits[0]+=1e-7;self.limits[1]-=1e-7
        self.groups=[]
        for name in dict.fromkeys(c['body'] for c in p.metadata['contacts']):
            cs=[c for c in p.metadata['contacts'] if c['body']==name]
            self.groups.append((name,p.model.getBodySet().get(name),np.array([c['center_local_m'] for c in cs]),np.array([c['radius_m'] for c in cs])))
        self.primary=set(spec['body_support_contacts'].get('primary_support_bodies',['trunk','chest','thigh_l','thigh_r']))
        self.receipts=[]
        self.previous_time=None
        self.standing_body_clearance=None
        if spec.get('support_transfer'):
            if standing is None:raise ValueError('Recovery requires a standing target')
            p.set_state(0,standing,self.zeros)
            self.standing_body_clearance=float(min(self.heights()[1]))

    def heights(self):
        all_h=[];primary=[]
        for name,b,points,radii in self.groups:
            tf=b.getTransformInGround(self.p.state);r=tf.R();up=np.array([r.get(1,j) for j in range(3)])
            h=points@up+tf.p().get(1)-radii;all_h.extend(h)
            if name in self.primary:primary.extend(h)
        return np.asarray(all_h),np.asarray(primary)

    def solve(self,q,time,goals,previous,previous2=None):
        p=self.p;target=q.copy();body_gain=keyed(time,self.spec['body_support_gain'])
        gains={s:keyed(time,self.spec.get('foot_support_by_side',{}).get(s,self.spec['foot_support_gain'])) for s in ('l','r')}
        prediction=previous if previous2 is None else 2*previous-previous2
        dt=max(time-self.previous_time,1/120) if self.previous_time is not None else 1/24
        p.set_state(time,q,self.zeros)
        natural_clearance=float(min(self.heights()[1]))
        transfer=self.spec.get('support_transfer')
        rise=keyed(time,transfer['rise_keys']) if transfer else 0.
        desired_clearance=(rise*self.standing_body_clearance if transfer else
                           (1-body_gain)*natural_clearance)
        def residual(values):
            for i,v in zip(self.ids,values):p.coordinates[i].setValue(p.state,float(v),False)
            p.model.realizePosition(p.state);r=[]
            h,body_h=self.heights()
            # Body support is an equality, not merely a non-penetration test.
            # Fade the desired clearance, not the objective weight. Fading
            # weight held the torso down then released it in a single jump.
            # This is a motor task, not a claim of a supporting external force.
            if transfer or body_gain>0:
                r.append(65*(np.min(body_h)-desired_clearance+.001*p.L)/p.L)
            else:r.append(0.)
            r.extend(65*np.minimum(h+.001*p.L,0)/p.L)
            for s in ('l','r'):
                b=p.model.getBodySet().get('toe_'+s);tf=b.getTransformInGround(p.state);mat=tf.R();R=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
                pos,orientation,digit=goals[s];gain=gains[s]
                r.extend(40*gain*(tf.p().to_numpy()-pos)/p.L)
                r.extend(3*gain*Rotation.from_matrix(orientation.T@R).as_rotvec())
            both=min(gains.values())
            if self.spec.get('support_transfer'):
                center=.5*(goals['l'][0]+goals['r'][0]);com=p.model.calcMassCenterPosition(p.state).to_numpy()
                r.extend(3*both*(com[[0,2]]-center[[0,2]])/p.L)
            axial=np.array([n.startswith(('chest','neck','head','tail_')) for n in self.names])
            tau=self.spec.get('support_transfer',{}).get('axial_smoothing_seconds',0.)
            scale=np.array([.08 if n in ('height','forward','lateral') else (1. if tau and a else .25) for n,a in zip(self.names,axial)])
            r.extend(scale*(values-target[self.ids]))
            r.extend((.25+axial*(tau/dt)**2)*(values-prediction[self.ids]))
            r.extend(axial*(tau/dt)*(values-previous[self.ids]))
            return np.asarray(r)
        seed=target[self.ids]
        fit=least_squares(residual,np.clip(seed,self.limits[0]+1e-7,self.limits[1]-1e-7),bounds=self.limits,tr_solver="lsmr",max_nfev=55,ftol=1e-7,xtol=1e-7,gtol=1e-7)
        q[self.ids]=fit.x;residual(fit.x);h,bh=self.heights()
        errors={s:float(gains[s]*np.linalg.norm(p.model.getBodySet().get('toe_'+s).getPositionInGround(p.state).to_numpy()-goals[s][0])) for s in ('l','r')}
        self.receipts.append(dict(desired_body_clearance_m=float(desired_clearance),loaded_foot_error_m=errors,time_s=float(time),minimum_surface_height_m=float(min(h)),primary_body_gap_m=float(min(bh)),body_support_gain=float(body_gain),foot_support_gain=gains,success=bool(fit.success),evaluations=int(fit.nfev)))
        self.previous_time=time
        return q
