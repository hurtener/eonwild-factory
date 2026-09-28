"""Shared body-to-foot support coordination for finite floor behaviors.

Kinematic initializer with admitted joint limits and material floor witnesses.
Contact and required effort are audited afterwards; this is not forward dynamics.
"""
import json
from pathlib import Path
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
    # A stance planted under the lying body (standing root moved) is reached
    # by the same rise; with standing forward==rest forward this is a no-op.
    for n in ('forward','lateral'):
        if n in index:i=index[n];q[i]=rest[i]+rise*(standing[i]-rest[i])
    return q


LEG_JOINTS=(('hip','thigh'),('knee','shin'),('ankle','metatarsus'),('mtp','toe'))


def leg_effort(p,side,share):
    """Quasi-static sagittal joint torque / admitted capacity for one leg.

    The leg carries `share` of body weight as a vertical force at the toe
    segment's mass centre (pad-centroid proxy). Leg segment weight is ignored.
    Capacities are the model's estimated actuator ceilings (engineering priors,
    not measured strength); only their ratios shape the preferred posture.
    """
    bodies=p.model.getBodySet();trunk=bodies.get('trunk').getTransformInGround(p.state).R()
    lateral=np.array([trunk.get(i,2) for i in range(3)])
    toe=bodies.get('toe_'+side);contact=toe.findStationLocationInGround(p.state,toe.getMassCenter()).to_numpy()
    force=np.array([0.,share*p.bw,0.]);out=[]
    for joint,body in LEG_JOINTS:
        centre=bodies.get(body+'_'+side).getPositionInGround(p.state).to_numpy()
        cap=p.metadata['actuators']['motor_'+joint+'_'+side]['capacity_Nm']
        out.append(float(np.cross(contact-centre,force)@lateral)/cap)
    return np.asarray(out)


def gathered_plant(p,folded,standing,feet,legnames,bounds,balance_share=.35,effort_weight=0.,sitting=None):
    """Place the admitted standing stance where the folded legs can reach it.

    The stance keeps its standing width and foot orientation; only its
    horizontal placement is chosen, jointly with bounded leg joints of the lying
    body. Reach dominates; balance (standing mass-centre offset over the feet)
    is a softer preference. Both residuals are returned, never hidden.
    """
    ix=p.index;zeros=np.zeros(len(p.names))
    p.set_state(0,standing,zeros)
    mid=.5*(feet['l'][0]+feet['r'][0]);offset=p.model.calcMassCenterPosition(p.state).to_numpy()-mid;offset[1]=0.
    ids=[ix[n] for n in legnames];lo=np.array([bounds[n][0] for n in legnames])+1e-6;hi=np.array([bounds[n][1] for n in legnames])-1e-6
    q=folded.copy();x_ref=q[ids].copy()
    def unpack(x):
        for i,v in zip(ids,x[:-2]):p.coordinates[i].setValue(p.state,float(v),False)
        p.model.realizePosition(p.state);return np.array([x[-2],0.,x[-1]])
    def residual(x):
        shift=unpack(x);r=[]
        for s in ('l','r'):
            b=p.model.getBodySet().get('toe_'+s);tf=b.getTransformInGround(p.state);m=tf.R()
            R=np.array([[m.get(i,j) for j in range(3)] for i in range(3)])
            r.extend(30*(tf.p().to_numpy()-(feet[s][0]+shift))/p.L)
            r.extend(3*Rotation.from_matrix(feet[s][1].T@R).as_rotvec())
        com=p.model.calcMassCenterPosition(p.state).to_numpy()
        r.extend(30*balance_share*(com-(mid+shift+offset))[[0,2]]/p.L)
        if sitting:
            # Tarsal resting posture (theropod sitting traces, resting birds):
            # ankle on the ground behind flat metatarsi, toes forward. With the
            # pelvis low this requires a forward femur, i.e. knees up.
            heading=(p.model.getBodySet().get('head').getPositionInGround(p.state).to_numpy()-p.model.getBodySet().get('trunk').getPositionInGround(p.state).to_numpy())[[0,2]]
            heading/=np.linalg.norm(heading)
            for s in ('l','r'):
                bodies=p.model.getBodySet();ankle=bodies.get('metatarsus_'+s).getPositionInGround(p.state).to_numpy()
                r.append(sitting['weight']*(ankle[1]-sitting['ankle_height_leg_lengths']*p.L)/p.L)
                # Metatarsus points forward from the ankle (toes ahead): the
                # straight-ankle, backward-foot branch is not a resting posture.
                ahead=(bodies.get('toe_'+s).getPositionInGround(p.state).to_numpy()-ankle)[[0,2]]@heading
                length=np.linalg.norm(bodies.get('toe_'+s).getPositionInGround(p.state).to_numpy()-ankle)
                r.append(sitting['weight']*min(ahead-.5*length,0.)/p.L)
        if effort_weight:
            # The plant is where the push-up starts: prefer feet the legs can
            # lift the body from cheaply (knees forward, foot under the hip),
            # not a reachable point a metre behind the hip.
            for s in ('l','r'):r.extend(effort_weight*leg_effort(p,s,.5))
        r.extend(.05*(x[:-2]-x_ref))
        return np.asarray(r)
    p.set_state(0,q,zeros)
    com=p.model.calcMassCenterPosition(p.state).to_numpy();start=(com-mid-offset)[[0,2]]
    seeds=[np.clip(x_ref,lo,hi)]
    if sitting and sitting.get('seed_radians'):
        # Also start from the tarsal-resting configuration: from a knee-back
        # seed the solver stays on that branch even when sitting is cheaper.
        alt=x_ref.copy()
        for j,n in enumerate(legnames):
            base=n.rsplit('_',1)[0] if n.endswith(('_l','_r')) else n
            if base in sitting['seed_radians']:alt[j]=sitting['seed_radians'][base]
        seeds.append(np.clip(alt,lo,hi))
    fits=[least_squares(residual,np.r_[x,start],bounds=(np.r_[lo,-np.inf,-np.inf],np.r_[hi,np.inf,np.inf]),max_nfev=400,ftol=1e-10,xtol=1e-10) for x in seeds]
    fit=min(fits,key=lambda f:f.cost);gathered_plant.seed_costs=[float(f.cost) for f in fits]
    shift=unpack(fit.x)
    reach={s:float(np.linalg.norm(p.model.getBodySet().get('toe_'+s).getPositionInGround(p.state).to_numpy()-(feet[s][0]+shift))) for s in ('l','r')}
    com=p.model.calcMassCenterPosition(p.state).to_numpy()
    achieved={}
    for s in ('l','r'):
        tf=p.model.getBodySet().get('toe_'+s).getTransformInGround(p.state);m=tf.R()
        achieved[s]=(tf.p().to_numpy().copy(),np.array([[m.get(i,j) for j in range(3)] for i in range(3)]),feet[s][2])
    q[ids]=fit.x[:-2]
    gathered_plant.achieved=achieved
    effort={s:leg_effort(p,s,.5).round(3).tolist() for s in ('l','r')}
    ankles={s:float(p.model.getBodySet().get('metatarsus_'+s).getPositionInGround(p.state).get(1)) for s in ('l','r')}
    knees={s:float((p.model.getBodySet().get('shin_'+s).getPositionInGround(p.state).to_numpy()-p.model.getBodySet().get('thigh_'+s).getPositionInGround(p.state).to_numpy())[0]) for s in ('l','r')}
    return shift,q,dict(seed_costs=gathered_plant.seed_costs,plant_effort_torque_per_capacity=effort,plant_ankle_height_m=ankles,plant_knee_ahead_of_hip_x_m=knees,stance_shift_m=shift.tolist(),reach_error_m=reach,
        mass_centre_error_m=float(np.linalg.norm((com-(mid+shift+offset))[[0,2]])),
        mass_centre_start_error_m=float(np.linalg.norm(start)),success=bool(fit.success),
        method='Bounded placement of the admitted standing stance under the folded lying body; admitted joint limits unchanged')


def balance_weight(rise,policy):
    """Weight of CoM-over-feet balance as the body stops bearing load.

    Once the trunk leaves the floor only the feet can carry body weight, so the
    mass centre must project inside their support. Ramped over the first part
    of the rise so the constraint does not switch on in a single frame.
    """
    balance=policy.get('balance')
    if not balance:return 3.
    ramp=float(np.clip(rise/balance.get('ramp_rise_fraction',.12),0,1))
    return 3.+(balance['weight']-3.)*ramp*ramp*(3-2*ramp)


class GroundSupport:
    def __init__(self,p,spec,bounds,initial,standing=None):
        self.p=p;self.spec=spec;self.ix=p.index;self.zeros=np.zeros(len(p.names));self.bounds=bounds
        # Feet travel to their plant through the air from wherever they are,
        # instead of being dragged by a fading-in tracking weight.
        self.swing=(spec.get('support_transfer') or {}).get('swing');self.swing_start={};self.swing_joint={};self.plant_legs=None
        # Resting axial chain lies on the floor instead of hovering stiffly.
        self.drape=spec.get('rest_drape')
        # Measured skin penetration (previous pass, actual skinned mesh) fed
        # back as extra clearance for the matching rigid witness group.
        feedback=spec.get('skin_clearance_feedback')
        self.feedback=json.loads(Path(feedback).read_text())['extra_clearance_m'] if feedback else {}
        self.current_time=0.
        # Do not move yaw/roll to evade the requested roll; resolve limbs and
        # support locations with the same admitted anatomical ranges.
        self.names=list(bounds)+['height','forward','lateral'];self.ids=[p.index[n] for n in self.names]
        limits=[bounds[n] for n in bounds]+[(.02*p.L,1.3*p.L),
            (initial[p.index['forward']]-3*p.L,initial[p.index['forward']]+30*p.L),
            (initial[p.index['lateral']]-2*p.L,initial[p.index['lateral']]+2*p.L)]
        balance=(spec.get('support_transfer') or {}).get('balance')
        self.pitch_free=bool(balance and balance.get('trunk_pitch_range_rad'))
        if self.pitch_free:
            # Whole-body lean is solved from balance, not keyed. The range is
            # a solver envelope about the standing pitch, not a joint limit.
            span=balance['trunk_pitch_range_rad'];centre=standing[p.index['pitch']]
            self.names.append('pitch');self.ids.append(p.index['pitch']);limits.append((centre-span,centre+span))
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
            # Balanced standing CoM offset from the toe-origin midpoint. The
            # previous target (the bare midpoint) is not where a standing
            # animal's mass centre is, so balance fought the final stance.
            feet=[p.model.getBodySet().get('toe_'+s).getPositionInGround(p.state).to_numpy() for s in ('l','r')]
            self.standing_com_offset=p.model.calcMassCenterPosition(p.state).to_numpy()-.5*(feet[0]+feet[1])
            self.standing_com_offset[1]=0.
        self.staged=(spec.get('support_transfer') or {}).get('staged');self.rise_by_joints=False
        self.effort=(spec.get('support_transfer') or {}).get('effort')
        self.step_delta=np.zeros(3);self.stage_start=None;self.goal_log=[];self.step_targets={}
        if self.staged:
            # Rear-first rise: pelvis and chest clearances are separate
            # equalities, so the chest can keep bearing load (a feet+chest
            # tripod) while the feet step in under the mass.
            p.set_state(0,standing,self.zeros)
            self.standing_group_clearance={n:self.group_height(n) for n in ('trunk','chest')}
            self.rise_by_joints=self.staged.get('rise_by')=='joint_centres'
            if self.rise_by_joints:
                # Pelvis (hip joints) and shoulder (chest-neck joint) heights:
                # the lean follows from their difference and each animal's
                # proportions, instead of from mesh-witness minima.
                self.standing_centre={n:self.centre_height(n) for n in ('pelvis','shoulder')}
                b=p.model.getBodySet();hips=.5*sum(b.get('thigh_'+s).getPositionInGround(p.state).to_numpy() for s in ('l','r'))
                self.trunk_span=float(np.linalg.norm((b.get('neck').getPositionInGround(p.state).to_numpy()-hips)))

    def extra(self,name):
        f=self.feedback.get(name)
        return float(np.interp(self.current_time,f['times_s'],f['values_m'])) if f else 0.

    def heights(self):
        all_h=[];primary=[]
        for name,b,points,radii in self.groups:
            tf=b.getTransformInGround(self.p.state);r=tf.R();up=np.array([r.get(1,j) for j in range(3)])
            h=points@up+tf.p().get(1)-radii-self.extra(name);all_h.extend(h)
            if name in self.primary:primary.extend(h)
        return np.asarray(all_h),np.asarray(primary)

    def centre_height(self,name):
        b=self.p.model.getBodySet()
        if name=='pelvis':return .5*sum(b.get('thigh_'+s).getPositionInGround(self.p.state).get(1) for s in ('l','r'))
        return b.get('neck').getPositionInGround(self.p.state).get(1)

    def group_height(self,name):
        for n,b,points,radii in self.groups:
            if n==name:
                tf=b.getTransformInGround(self.p.state);r=tf.R();up=np.array([r.get(1,j) for j in range(3)])
                h=points@up+tf.p().get(1)-radii-self.extra(n)
                # Smooth minimum: a hard min switches witness point and made
                # the lean snap. Temperature is a small fraction of leg length.
                k=(self.staged or self.drape or {}).get('softmin_leg_lengths',.02)*self.p.L if (self.staged or self.drape) else 0.
                if k<=0:return float(np.min(h))
                return float(-k*np.log(np.sum(np.exp(-(h-np.min(h))/k)))+np.min(h))
        raise KeyError(name)

    def step_goals(self,time,goals):
        # Each foot swings to its balanced placement on a low arc while the
        # other foot and the chest carry the body. Orientation is unchanged.
        out={}
        for s in ('l','r'):
            u=keyed(time,self.staged['step_keys'][s]);pos,R,digit=goals[s]
            lift=4*u*(1-u)*self.staged.get('step_height_leg_lengths',.05)*self.p.L
            if s in self.step_targets:
                # From the reachable plant to the exact balanced standing foot.
                final,Rf,_=self.step_targets[s]
                rot=Rotation.from_matrix(np.stack([R,Rf]));R=(rot[0]*Rotation.from_rotvec(u*(rot[0].inv()*rot[1]).as_rotvec())).as_matrix()
                out[s]=(pos+u*(final-pos)+np.array([0.,lift,0.]),R,digit);continue
            out[s]=(pos+u*self.step_delta+np.array([0.,lift,0.]),R,digit)
        return out

    def swing_goals(self,time,goals,gains,previous):
        out=dict(goals)
        for s in ('l','r'):
            keys=self.spec.get('foot_support_by_side',{}).get(s,self.spec['foot_support_gain'])
            start=max(t for t,v in keys if v<=0 and t<=min(t for t,v in keys if v>=1))
            end=min(t for t,v in keys if v>=1)
            if time<start:continue
            if s not in self.swing_start:
                self.p.set_state(time,previous,self.zeros)
                tf=self.p.model.getBodySet().get('toe_'+s).getTransformInGround(self.p.state);m=tf.R()
                self.swing_start[s]=(tf.p().to_numpy().copy(),np.array([[m.get(i,j) for j in range(3)] for i in range(3)]))
            p0,R0=self.swing_start[s];pos,R,digit=goals[s]
            u=float(np.clip((time-start)/max(end-start,1e-6),0,1));w=u*u*(3-2*u)
            if self.swing.get('space')=='joint':
                # Leg joints travel from where they are to the solved plant
                # pose (knee leads, one branch); the foot is only bound to the
                # floor target as it arrives. No Cartesian drag path.
                if s+'_q' not in self.swing_start:
                    self.swing_start[s+'_q']=previous[[self.ix[n] for n in self.leg_names(s)]].copy()
                self.swing_joint[s]=(w,self.swing_start[s+'_q'])
                gains[s]=float(np.clip((u-.7)/.3,0,1))**2
                continue
            lift=np.sin(np.pi*u)*self.swing['lift_leg_lengths']*self.p.L
            rot=Rotation.from_matrix(np.stack([R0,R]));blend=(rot[0]*Rotation.from_rotvec(w*(rot[0].inv()*rot[1]).as_rotvec())).as_matrix()
            out[s]=(p0+w*(pos-p0)+np.array([0.,lift,0.]),blend,digit);gains[s]=1.
        return out

    def leg_names(self,s):
        return [n for n in ('hip_'+s,'hip_'+s+'_yaw','hip_'+s+'_roll','knee_'+s,'ankle_'+s,'mtp_'+s,'digit_'+s) if n in self.ix]

    def solve(self,q,time,goals,previous,previous2=None):
        p=self.p;target=q.copy();body_gain=keyed(time,self.spec['body_support_gain']);self.current_time=time
        gains={s:keyed(time,self.spec.get('foot_support_by_side',{}).get(s,self.spec['foot_support_gain'])) for s in ('l','r')}
        self.swing_joint={}
        if self.swing:goals=self.swing_goals(time,goals,gains,previous)
        for s,(w,q0) in self.swing_joint.items():
            if self.plant_legs is None:raise ValueError('Joint-space swing requires a solved plant pose')
            ids=[self.ix[n] for n in self.leg_names(s)];target[ids]=q0+w*(self.plant_legs[ids]-q0)
        prediction=previous if previous2 is None else 2*previous-previous2
        dt=max(time-self.previous_time,1/120) if self.previous_time is not None else 1/24
        p.set_state(time,q,self.zeros)
        natural_clearance=float(min(self.heights()[1]))
        transfer=self.spec.get('support_transfer')
        rise=keyed(time,transfer['rise_keys']) if transfer else 0.
        desired_clearance=(rise*self.standing_body_clearance if transfer else
                           (1-body_gain)*natural_clearance)
        balanced=bool(transfer and transfer.get('balance'))
        weight=balance_weight(rise,transfer) if transfer else 3.
        release=rise
        stage=None
        if self.staged:
            goals=self.step_goals(time,goals)
            hip=keyed(time,self.staged['hip_rise_keys']);chest=keyed(time,self.staged['chest_rise_keys'])
            if hip>0 or chest>0:
                if self.stage_start is None and self.rise_by_joints:
                    p.set_state(time,previous,self.zeros)
                    self.stage_start={n:self.centre_height(n) for n in ('pelvis','shoulder')}
                    p.set_state(time,q,self.zeros)
                if self.rise_by_joints:
                    stage={n:(1-f)*self.stage_start[n]+f*self.standing_centre[n] for n,f in (('pelvis',hip),('shoulder',chest))}
                    limit=self.staged.get('max_lean_degrees')
                    if limit is not None:
                        # One shared rule instead of per-species keys: the
                        # shoulders start rising early whenever the pelvis
                        # would otherwise pitch the trunk past the limit.
                        floor=stage['pelvis']-self.trunk_span*np.sin(np.deg2rad(limit))
                        stage['shoulder']=max(stage['shoulder'],min(floor,self.standing_centre['shoulder']))
                        # Balance and effort follow the chest's actual progress.
                        span=self.standing_centre['shoulder']-self.stage_start['shoulder']
                        if span>1e-6:chest=float(np.clip((stage['shoulder']-self.stage_start['shoulder'])/span,chest,1.))
                elif self.stage_start is None:
                    # Continue from the actual solved lying clearances.
                    p.set_state(time,previous,self.zeros)
                    self.stage_start={n:self.group_height(n) for n in ('trunk','chest')}
                    # The chest is a support in the tripod phase: keep it on
                    # the floor (not hovering) until its own rise begins.
                    self.stage_start['chest']=min(self.stage_start['chest'],0.)
                    p.set_state(time,q,self.zeros)
                if not self.rise_by_joints:
                    stage={n:(1-f)*self.stage_start[n]+f*self.standing_group_clearance[n] for n,f in (('trunk',hip),('chest',chest))}
            # Balance is required only once the chest stops bearing weight.
            weight=balance_weight(chest,transfer);release=hip
        load=(hip*(1-chest) if self.staged else rise) if transfer else 0.
        # Before the rise the lean stays with the authored roll/fold; it is
        # released only while balance carries the body.
        # Held firmly (not merely weakly regularized) before release: a loose
        # lean let the plant phase pop the body nose-down and swing the tail.
        locked=(self.staged or {}).get('pitch_lock_scale',1.5)
        pitch_scale=locked-(locked-.15)*float(np.clip(release/.12,0,1)) if self.pitch_free else .25
        budget=(transfer.get('balance',{}).get('max_evaluations',55) if balanced and (rise>0 or stage) else 55)
        def residual(values):
            for i,v in zip(self.ids,values):p.coordinates[i].setValue(p.state,float(v),False)
            p.model.realizePosition(p.state);r=[]
            h,body_h=self.heights()
            # Body support is an equality, not merely a non-penetration test.
            # Fade the desired clearance, not the objective weight. Fading
            # weight held the torso down then released it in a single jump.
            # This is a motor task, not a claim of a supporting external force.
            if stage and self.rise_by_joints:
                r.extend(65*(self.centre_height(n)-stage[n])/p.L for n in ('pelvis','shoulder'))
            elif stage:
                r.extend(65*(self.group_height(n)-stage[n]+.001*p.L)/p.L for n in ('trunk','chest'))
            elif transfer or body_gain>0:
                r.append(65*(np.min(body_h)-desired_clearance+.001*p.L)/p.L)
            else:r.append(0.)
            r.extend(65*np.minimum(h+.001*p.L,0)/p.L)
            if self.drape and body_gain>0:
                # Equality to the floor for the resting neck/head/tail: the
                # chain settles within its admitted joint ranges. Eased in so
                # an adopted pose is not yanked to the floor in one frame.
                ease_in=self.drape.get('ease_in_s',1.)
                ease=float(np.clip(time/ease_in,0,1)) if ease_in>0 else 1.;ease=ease*ease*(3-2*ease)
                # Released before the rise: the tail lifts with the hips, and a
                # chain held on the floor was later driven under it by lean.
                ease*=keyed(time,self.drape.get('hold_keys',[[0,1],[1,1]]))
                r.extend(self.drape['weight']*ease*body_gain*(self.group_height(n)+.001*p.L)/p.L for n in self.drape['bodies'])
            for s in ('l','r'):
                b=p.model.getBodySet().get('toe_'+s);tf=b.getTransformInGround(p.state);mat=tf.R();R=np.array([[mat.get(i,j) for j in range(3)] for i in range(3)])
                pos,orientation,digit=goals[s];gain=gains[s]
                r.extend(40*gain*(tf.p().to_numpy()-pos)/p.L)
                r.extend(3*gain*Rotation.from_matrix(orientation.T@R).as_rotvec())
            if self.effort and load>0:
                # Share body weight across hip/knee/ankle/MTP by capacity:
                # the knee takes load instead of the ankle collapsing.
                for s in ('l','r'):
                    if gains[s]>=1 and s not in self.swing_joint:r.extend(self.effort['weight']*leg_effort(p,s,.5*load))
            both=min(gains.values())
            if transfer:
                center=.5*(goals['l'][0]+goals['r'][0]);com=p.model.calcMassCenterPosition(p.state).to_numpy()
                if balanced:center=center+self.standing_com_offset
                r.extend(weight*both*(com[[0,2]]-center[[0,2]])/p.L)
            axial=np.array([n.startswith(('chest','neck','head','tail_')) or (n=='pitch' and self.pitch_free) for n in self.names])
            tau=self.spec.get('support_transfer',{}).get('axial_smoothing_seconds',0.)
            # Unloaded legs get the same physical-time inertia: with only a weak
            # regularizer, new shin witnesses shoved free legs across branches.
            limb_tau=self.spec.get('support_transfer',{}).get('limb_smoothing_seconds',0.)
            if limb_tau:
                limb=np.array([n.startswith(('hip_','knee_','ankle_','mtp_','digit_')) for n in self.names])
                r.extend(limb*(.25+(limb_tau/dt)**2)*(values-prediction[self.ids]))
            scale=np.array([.08 if n in ('height','forward','lateral') else (pitch_scale if n=='pitch' else (1. if tau and a else .25)) for n,a in zip(self.names,axial)])
            if self.swing and self.swing.get('space')=='joint':
                track=self.swing.get('joint_tracking',3.)
                for s in ('l','r'):
                    free=track*(1.-gains[s]) if s not in self.swing_joint else track
                    mask=np.array([n in self.leg_names(s) for n in self.names])
                    scale=np.where(mask,np.maximum(scale,free),scale)
            r.extend(scale*(values-target[self.ids]))
            r.extend((.25+axial*(tau/dt)**2)*(values-prediction[self.ids]))
            r.extend(axial*(tau/dt)*(values-previous[self.ids]))
            return np.asarray(r)
        seed=target[self.ids]
        fit=least_squares(residual,np.clip(seed,self.limits[0]+1e-7,self.limits[1]-1e-7),bounds=self.limits,tr_solver="lsmr",max_nfev=budget,ftol=1e-7,xtol=1e-7,gtol=1e-7)
        q[self.ids]=fit.x;residual(fit.x);h,bh=self.heights()
        errors={s:float(gains[s]*np.linalg.norm(p.model.getBodySet().get('toe_'+s).getPositionInGround(p.state).to_numpy()-goals[s][0])) for s in ('l','r')}
        com=p.model.calcMassCenterPosition(p.state).to_numpy();mid=.5*(goals['l'][0]+goals['r'][0])
        target=mid+(self.standing_com_offset if balanced else 0.)
        self.receipts.append(dict(stage_clearance_m=({n:self.group_height(n) for n in ('trunk','chest')} if self.staged else None),balance_weight=float(weight),com_target_error_m=float(np.linalg.norm((com-target)[[0,2]])),desired_body_clearance_m=float(desired_clearance),loaded_foot_error_m=errors,time_s=float(time),minimum_surface_height_m=float(min(h)),primary_body_gap_m=float(min(bh)),body_support_gain=float(body_gain),foot_support_gain=gains,success=bool(fit.success),evaluations=int(fit.nfev)))
        self.previous_time=time;self.goal_log.append(goals)
        return q
