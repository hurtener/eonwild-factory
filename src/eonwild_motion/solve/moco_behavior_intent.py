"""Data-driven finite behavior intent over the admitted articulated model.

These are authored motor goals, not predictions of extinct animal behavior.
The common contact coordinator resolves their limb response. Species data is
restricted to anatomy, dimensions, capacities and semantic bindings.
"""
import numpy as np
from .moco_living_intent import keyed
from .moco_joint_spline import bounded, to_latent
from .moco_tasks import smooth


class SupportRetime:
    """C2 source-phase mapping: earlier unloading, more time for recovery.

    Mapping affects the motor task before IK/forces, never the review clock.
    Stance material points remain world anchors from the source task.
    """
    def __init__(self,times,loaded,unload_fraction):
        if not 0<=unload_fraction<=.3:raise ValueError('Invalid support retiming fraction')
        starts=np.flatnonzero(loaded & ~np.r_[False,loaded[:-1]])
        ends=np.flatnonzero(loaded & ~np.r_[loaded[1:],False])
        keys=[(float(times[0]),float(times[0]))]
        for a,b in zip(starts,ends):
            if times[b]-times[a]<.12 or b==len(times)-1:continue
            if times[a]>keys[-1][0]:keys.append((float(times[a]),float(times[a])))
            advance=(times[b]-times[a])*unload_fraction
            # Keep the later recovery map strictly monotone too.
            nexts=starts[starts>b]
            if len(nexts):advance=min(advance,.45*(times[nexts[0]]-times[b]))
            keys.append((float(times[b]-advance),float(times[b])))
        keys.append((float(times[-1]),float(times[-1])))
        self.keys=keys

    def __call__(self,t):
        for (a,x),(b,y) in zip(self.keys[:-1],self.keys[1:]):
            if t<=b:
                u=np.clip((t-a)/(b-a),0,1)
                return float(x+(b-a)*u+((y-x)-(b-a))*smooth(u))
        return self.keys[-1][1]


class BehaviorIntent:
    def __init__(self, specification, names, leg_length, bounds):
        self.specification=specification
        self.index={n:i for i,n in enumerate(names)}
        self.L=leg_length;self.bounds=bounds
        for name in specification.get('joint_offsets_degrees',{}):
            if name not in self.index:raise ValueError('Unknown semantic coordinate: '+name)
        for channels in ('joint_offsets_degrees','root_offsets_leg_lengths','root_offsets_degrees'):
            for name,keys in specification.get(channels,{}).items():
                a=np.asarray(keys,dtype=float)
                if a.ndim!=2 or a.shape[1]!=2 or not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0):
                    raise ValueError('Behavior keys must be finite and strictly ordered: '+name)

    def heading(self,t):
        return np.deg2rad(keyed(t,self.specification.get('root_offsets_degrees',{}).get('yaw',[[0,0],[self.specification['duration_s'],0]])))

    def attention_degrees(self,t):
        return keyed(t,self.specification.get('attention_keys',[[0,0],[self.specification['duration_s'],0]]))

    def apply(self,reference,t):
        q=np.array(reference,copy=True)
        for name,keys in self.specification.get('joint_offsets_degrees',{}).items():
            i=self.index[name];delta=np.deg2rad(keyed(t,keys))
            if name in self.bounds:
                lo,hi=self.bounds[name]
                q[i]=bounded(to_latent(q[i],lo,hi)+delta,lo,hi)[0]
            else:raise ValueError('Joint intent must name an admitted bounded articulation: '+name)
        for name,signal in self.specification.get('joint_oscillations',{}).items():
            i=self.index[name];lo,hi=self.bounds[name]
            amplitude=np.deg2rad(signal['amplitude_degrees'])
            if signal['period_s']<=0:raise ValueError('Oscillation period must be positive')
            envelope=keyed(t,signal['envelope'])
            delta=amplitude*envelope*np.sin(2*np.pi*t/signal['period_s']+signal.get('phase_rad',0))
            q[i]=bounded(to_latent(q[i],lo,hi)+delta,lo,hi)[0]
        for name,keys in self.specification.get('root_offsets_leg_lengths',{}).items():
            if name not in ('forward','height','lateral'):raise ValueError('Invalid root translation')
            q[self.index[name]]+=self.L*keyed(t,keys)
        for name,keys in self.specification.get('root_offsets_degrees',{}).items():
            if name not in ('pitch','yaw','roll'):raise ValueError('Invalid root orientation')
            q[self.index[name]]+=np.deg2rad(keyed(t,keys))
        return q
