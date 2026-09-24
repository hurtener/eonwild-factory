"""Finite backward support task and reduced horizontal balance prior.

Placement/release choices are explicit engineering hypotheses. The LIPM prior
uses modeled COM height but does not replace articulated inverse dynamics,
contact validation, or a converged Moco solve. No reference clip is reversed.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.linalg import solve_banded
from scipy.spatial.transform import Rotation
from .moco_tasks import smooth


def horizontal_balance(times, support, height, initial, final):
    """Solve c - h/g c'' = support with fixed endpoint COM positions."""
    times=np.asarray(times);dt=times[1]-times[0]
    if height<=0 or not np.allclose(np.diff(times),dt):raise ValueError('Positive height and uniform times required')
    n=len(times);k=height/(9.80665*dt*dt)
    ab=np.zeros((3,n));ab[0,1:]=-k;ab[1]=1+2*k;ab[2,:-1]=-k
    ab[1,0]=ab[1,-1]=1.;ab[0,1]=0.;ab[2,-2]=0.
    rhs=np.array(support,copy=True);rhs[0]=initial;rhs[-1]=final
    return solve_banded((1,1),ab,rhs)


class RetreatPlan:
    def __init__(self, specification, initial_feet, geometry, normal_step, leg_length):
        self.specification=specification;self.initial=initial_feet
        if specification['steps']!=4:raise ValueError('First finite retreat task admits four placements including closing')
        self.step=normal_step*specification['step_scale_of_normal']
        self.clearance=leg_length*specification['clearance_leg_lengths']
        if self.step<=0 or self.clearance<=0:raise ValueError('Positive step and clearance required')
        first=specification['first_swing_s'];interval=specification['step_interval_s'];swing=specification['swing_seconds']
        if not 0<swing<interval:raise ValueError('Retreat requires overlapping support')
        if first-specification['release_seconds']<specification['prepare_s']:
            raise ValueError('Initial unloading must follow preparation')
        self.events=[]
        # Three progressively rearward landings, then a real closing placement.
        for i,(side,multiple) in enumerate([('r',1),('l',2),('r',3),('l',3)]):
            self.events.append(dict(side=side,lift=first+i*interval,land=first+i*interval+swing,
                                   translation=np.array([-multiple*self.step,0.,0.])))
        self.end=self.events[-1]['land']+specification['settle_seconds']
        if self.end>=specification['duration_s']:raise ValueError('Sequence must include final rest')
        self.final_translation=np.array([-3*self.step,0.,0.])
        rear=min((s for s in geometry['sites'] if not s.get('distal')),key=lambda s:s['center_local_m'][0])
        self.pivot=np.array(rear['center_local_m']);self.pivot[1]-=rear['radius_m']
        self.front_release=specification.get('release_contact','rear')=='distal'
        if self.front_release:
            # The distal material witness retains its world anchor while the
            # proximal foot peels away. This is contact intent, not a muscle law.
            distal=max((s for s in geometry['sites'] if s.get('distal')),key=lambda s:s['center_local_m'][0])
            self.distal_center=np.array(distal['center_local_m'])
            self.midpoint=np.array(geometry['toe_midpoint_m'])
            self.radius=distal['radius_m']
        self.keys=[(0.,.5),(specification['prepare_s'],.5)]
        for e in self.events:
            left_weight=1. if e['side']=='r' else 0.
            self.keys.extend([(e['lift'],left_weight),(e['land'],left_weight)])
        self.keys.extend([(self.end,.5),(specification['duration_s'],.5)])

    def weights(self,t):
        for (a,wa),(b,wb) in zip(self.keys[:-1],self.keys[1:]):
            if t<=b:
                w=wa+(wb-wa)*float(smooth((t-a)/(b-a)))
                return np.array([w,1-w])
        return np.array([.5,.5])

    def foot(self,t,side):
        initial=self.initial[side];translation=np.zeros(3);pitch=0.;lift=0.;curl=0.
        s=self.specification
        for e in self.events:
            if e['side']!=side:continue
            if t>=e['land']:translation=e['translation'];continue
            prepare=e['lift']-s['release_seconds']
            if t<prepare:break
            if t<e['lift']:
                pitch=s['release_pitch_rad']*float(smooth((t-prepare)/s['release_seconds']))
            else:
                u=(t-e['lift'])/(e['land']-e['lift']);blend=float(smooth(u))
                bump=64*u**3*(1-u)**3
                translation=(1-blend)*translation+blend*e['translation']
                lift=self.clearance*bump
                pitch=s['release_pitch_rad']*(1-blend)+s['recovery_pitch_rad']*bump
                curl=s['recovery_digit_rad']*bump
            break
        if self.front_release:
            pitch=-pitch
            # Counter-flex the digit during peel so the distal segment stays
            # at its initial orientation until release, then relax in recovery.
            curl-=pitch
        R0=np.asarray(initial['rotation']);R=R0@Rotation.from_rotvec([0,0,pitch]).as_matrix()
        if self.front_release:
            D0=Rotation.from_rotvec([0,0,initial['digit']]).as_matrix()
            D=Rotation.from_rotvec([0,0,initial['digit']+curl]).as_matrix()
            initial_witness=R0@(self.midpoint+D0@self.distal_center)
            current_witness=R@(self.midpoint+D@self.distal_center)
            position=np.asarray(initial['origin'])+translation+initial_witness-current_witness+[0,lift,0]
        else:
            position=np.asarray(initial['origin'])+translation+R0@self.pivot-R@self.pivot+[0,lift,0]
        return position,R,initial['digit']+curl

    def support_center(self,t,sole_centers):
        # During swing its weight is zero. Otherwise use the unchanged loaded
        # footprint. Release rolls from the sole center toward the rear pad.
        centers=[]
        for side in ('l','r'):
            initial=self.initial[side];position,R,_=self.foot(t,side)
            point=np.array(sole_centers[side])
            for e in self.events:
                if e['side']==side and e['lift']-self.specification['release_seconds']<=t<e['lift']:
                    u=(t-e['lift']+self.specification['release_seconds'])/self.specification['release_seconds']
                    pivot=self.pivot
                    if self.front_release:
                        digit=self.foot(t,side)[2]
                        pivot=self.midpoint+Rotation.from_rotvec([0,0,digit]).apply(self.distal_center)
                        # Support is the lower surface, not the sphere center.
                        pivot=pivot+R.T@np.array([0,-self.radius,0])
                    point=(1-float(smooth(u)))*point+float(smooth(u))*pivot
                    break
            centers.append(position+R@point)
        return self.weights(t)@np.array(centers)

    def balance(self,times,com,sole_centers):
        support=np.array([self.support_center(t,sole_centers) for t in times])[:,[0,2]]
        # Preserve the observed standing COM relative to its support region.
        offset=np.asarray(com)[[0,2]]-support[0];support+=offset
        targets=horizontal_balance(times,support,com[1],np.asarray(com)[[0,2]],
                                   np.asarray(com)[[0,2]]+self.final_translation[[0,2]])
        # Exact idle adoption/settling with C2 envelopes; the small departure
        # from the reduced equation is measured, not called physical convergence.
        start=self.specification['prepare_s']
        gate=smooth((times-start)/self.specification['adoption_seconds'])
        targets=np.asarray(com)[[0,2]]+gate[:,None]*(targets-np.asarray(com)[[0,2]])
        gate=smooth((times-self.end)/self.specification['adoption_seconds'])
        final=np.asarray(com)[[0,2]]+self.final_translation[[0,2]]
        targets=(1-gate[:,None])*targets+gate[:,None]*final
        return CubicSpline(times,targets,bc_type=((1,[0.,0.]),(1,[0.,0.]))),support
