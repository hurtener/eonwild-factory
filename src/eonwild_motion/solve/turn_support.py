"""Pelvis accommodation to planted leg planes for directional diagnostics."""
import numpy as np
import math
from scipy.ndimage import gaussian_filter1d
from ..planning.grounded_gait import smooth


def contact_loads(sequence, time, transfer_fraction=.35):
    """Planned vertical load shares: unload before lift, accept after touch.

    The fractions are choreography, not a measured ground-reaction force.
    An airborne foot never carries a share of the body's weight.
    """
    loads={s:1. for s in sequence.anchors}
    for e in sequence.events:
        d=e['duration'];lift=e['start']+.10*d;touch=e['end']-.10*d
        unload=smooth((time-(lift-transfer_fraction*d))/(transfer_fraction*d))
        reload=smooth((time-touch)/(transfer_fraction*d))
        loads[e['side']]*=1-unload*(1-reload)
    total=sum(loads.values())
    if total<=1e-10:raise ValueError('Turn load schedule has no support')
    return {s:v/total for s,v in loads.items()}


class TurnLoadResponse:
    """Mass/force-scaled preparation of a small pelvis roll before leg IK.

    Offline symmetric filtering anticipates the known support schedule. This
    regularizes an authored compliant-body response, not final COM dynamics.
    """
    def __init__(self, sequence, capabilities, policy):
        self.sequence=sequence;self.policy=policy
        self.times=np.linspace(0,sequence.duration,math.ceil(sequence.duration*120)+1)
        self.dt=self.times[1]-self.times[0]
        # a = effective lateral force / mass. Higher mass at the same force
        # lengthens preparation; bigger animals are not assigned a species rule.
        self.response_seconds=policy['response_scale']*math.sqrt(
            sequence.height/capabilities['lateralAccelerationMps2'])
        balances=[]
        for t in self.times:
            loads=self.loads(t)
            balances.append(sum(math.copysign(v,sequence.lanes[s]) for s,v in loads.items()))
        self.balance=gaussian_filter1d(np.asarray(balances),
            self.response_seconds/self.dt,mode='nearest')

    def loads(self,time):
        return contact_loads(self.sequence,time,self.policy['transfer_fraction_of_step'])

    def roll(self,time):
        return math.radians(self.policy['maximum_roll_degrees'])*float(
            np.interp(time,self.times,self.balance))


def loaded_hip_roll(hips,pelvis,loads,forward,up,angle):
    """Rotate about the load-weighted hip height, without lifting support.

    Returns hip positions and one pelvis translation. Leg joints receive no
    independent lateral offsets; the existing shared IK solves them afterwards.
    """
    f=np.asarray(forward);u=np.asarray(up);p=np.asarray(pelvis)
    def rotate(v):
        return v*math.cos(angle)+np.cross(f,v)*math.sin(angle)+f*(f@v)*(1-math.cos(angle))
    turned={s:p+rotate(np.asarray(h)-p) for s,h in hips.items()}
    vertical=sum(loads[s]*float((turned[s]-hips[s])@u) for s in hips)
    delta=-u*vertical
    return {s:h+delta for s,h in turned.items()},delta


def accommodate_support_planes(hips, ankles, normals, gains, up, forward, lateral, height):
    """Move the pelvis, not individual limb joints, toward loaded leg planes.

    Independent horizontal projections avoid an ill-conditioned double-support snap.
    This is a bounded geometric accommodation, not a mass/force simulation.
    """
    basis=np.column_stack((lateral,forward))
    a=np.asarray([normals[s]@basis for s in hips])
    error=np.asarray([normals[s]@(ankles[s]-hips[s]) for s in hips])
    w=np.asarray([gains[s] for s in hips])
    # Blend independent plane projections. Solving the two almost-parallel
    # equations together amplified tiny load changes into pelvis snaps.
    lengths=np.sum(a*a,axis=1)
    projections=a*(error/np.maximum(lengths,1e-8))[:,None]
    delta=np.sum(w[:,None]*projections,axis=0)/max(float(w.sum()),1.)
    length=np.linalg.norm(delta)
    if length>.12*height:delta*=.12*height/length
    return basis@delta
