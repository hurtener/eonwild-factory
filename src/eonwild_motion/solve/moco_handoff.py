"""State-carrying trajectory handoffs for offline mixed-gait experiments.

Warm trajectories supply motion intent, not physical acceptance. A handoff
preserves joint/root state and carries each loaded foot's world offset until
release. The caller resolves anatomy and audits the final connected trajectory.
"""
import numpy as np
from scipy.interpolate import BPoly


def smooth5(x):
    x=np.clip(x,0.,1.)
    return x*x*x*(10+x*(-15+6*x))


class StateCarry:
    """C2 inertial correction; travel velocity decays without a position reset."""
    def __init__(self, outgoing, incoming, duration, travel_indices):
        if duration<=0: raise ValueError('Positive handoff duration required')
        self.duration=float(duration); self.travel_indices=list(travel_indices)
        delta=np.asarray(outgoing)-np.asarray(incoming)
        end=np.zeros_like(delta)
        # The extra travel accumulates while velocity is reconciled. Do not
        # pull the root backward to recover an arbitrary source origin.
        for i in self.travel_indices:
            end[0,i]=delta[0,i]+.5*duration*delta[1,i]+duration**2*delta[2,i]/12
        self.curve=BPoly.from_derivatives([0.,duration],[delta,end])
        self.end=end[0]

    def __call__(self,t,derivative=0):
        t=np.asarray(t);value=self.curve(np.clip(t,0,self.duration),nu=derivative)
        if derivative:
            return np.where((t>=self.duration)[...,None],0.,value)
        return np.where((t>=self.duration)[...,None],self.end,value)


class FootCarry:
    """World correction is retained through initial support, released in swing."""
    def __init__(self,times,loaded,travel_correction,initial_offset):
        self.times=np.asarray(times);self.loaded=np.asarray(loaded,dtype=bool)
        if len(times)!=len(loaded) or len(times)<2:raise ValueError('Invalid support timeline')
        self.travel=travel_correction;self.initial=np.asarray(initial_offset)
        # Incoming foot may already be airborne; then reconciliation starts
        # immediately. Otherwise wait for its first observed release.
        free=np.flatnonzero(~self.loaded)
        self.release=float(self.times[free[0]]) if len(free) else np.inf
        land=np.flatnonzero(self.loaded & (self.times>self.release))
        self.landing=float(self.times[land[0]]) if len(land) else float(self.times[-1])
        if self.landing<=self.release:self.landing=self.release+1e-6
        # Freeze travel correction over every subsequent loaded interval.
        self.anchors=[];i=0
        while i<len(times):
            if not self.loaded[i]:i+=1;continue
            j=i+1
            while j<len(times) and self.loaded[j]:j+=1
            end=float(times[min(j,len(times)-1)])
            # Placement anticipates travel over the upcoming support interval;
            # sampling only touchdown strands the foot behind an accelerating
            # body (or too far ahead of a braking one).
            self.anchors.append((float(times[i]),end,np.asarray(self.travel(.5*(times[i]+end)))))
            i=j

    def adoption_gain(self,t):
        if not np.isfinite(self.release):return 1.
        return float(1-smooth5((t-self.release)/(self.landing-self.release)))

    def __call__(self,t):
        previous_end=0.;previous=self.initial
        for start,end,offset in self.anchors:
            if start==0.:offset=self.initial
            if t<start:
                alpha=smooth5((t-previous_end)/max(start-previous_end,1e-9))
                return (1-alpha)*previous+alpha*offset
            if t<end:return offset.copy()
            previous_end=end;previous=offset
        # A terminal free interval carries the last support correction away
        # smoothly, rather than jumping to the root's accumulated correction.
        alpha=smooth5((t-previous_end)/max(self.times[-1]-previous_end,1e-9))
        return (1-alpha)*previous+alpha*np.asarray(self.travel(self.times[-1]))


def fit_orientation_carry(outgoing, incoming, reference, duration, indices,
                          minimum_duration, envelope_margin=0.05):
    """C2 angular reconciliation without inheriting a large turning excursion.

    Select the longest reconciliation time fitting the outgoing/incoming angular
    envelope. This is a numerical handoff policy, not an anatomical ROM limit.
    The caller retains the normal carry for translation and other coordinates.
    No stance foot is moved by this function.
    """
    if not 0 < minimum_duration <= duration:
        raise ValueError('Invalid orientation reconciliation interval')
    probes=np.linspace(0.,duration,161)
    reference_values=np.asarray(reference(probes))
    curves={};receipt={}
    for i in indices:
        low=min(float(outgoing[0,i]),float(np.min(reference_values[:,i])))
        high=max(float(outgoing[0,i]),float(np.max(reference_values[:,i])))
        margin=max((high-low)*envelope_margin,1e-6)
        lower,upper=low-margin,high+margin
        best=None
        for span in np.geomspace(duration,minimum_duration,41):
            curve=StateCarry(outgoing[:,i:i+1],incoming[:,i:i+1],float(span),[])
            values=reference_values[:,i]+curve(probes)[:,0]
            excess=float(max(0.,np.max(values-upper),np.max(lower-values)))
            candidate=(excess,float(span),curve)
            if best is None or excess<best[0]:best=candidate
            if excess<=1e-10:
                best=candidate;break
        excess,span,curve=best;curves[i]=curve
        receipt[i]=dict(duration_s=span,envelope_rad=[lower,upper],
                        unresolved_envelope_excess_rad=excess)
    return curves,receipt


class OrientationCarry:
    """Replace only designated angular corrections; preserve full C2 state."""
    def __init__(self,carry,curves):
        self.carry=carry;self.curves=curves
    def __call__(self,t,derivative=0):
        value=self.carry(t,derivative).copy()
        for i,curve in self.curves.items():value[...,i]=curve(t,derivative)[...,0]
        return value
