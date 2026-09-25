"""Reduced unloaded forefoot compliance, applied before mechanics replay.

Gravity and inertia come from the admitted physical segments. Relaxation
frequency, damping and preparation times are authored behavioral estimates;
this is not a forward simulation of the complete animal or measured muscle tone.
"""
import numpy as np
from scipy.integrate import solve_ivp
from .moco_tasks import smooth


def released_forefoot(times, load_bw, torque, inertia, policy):
    t=np.asarray(times);load=np.asarray(load_bw);result=np.zeros_like(t)
    free=load<policy['unloaded_threshold_BW']
    starts=np.flatnonzero(free & ~np.r_[False,free[:-1]])
    ends=np.flatnonzero(free & ~np.r_[free[1:],False])
    omega=2*np.pi*policy['frequency_hz'];zeta=policy['damping_ratio'];windows=[]
    for begin,end in zip(starts,ends):
        if begin==0 or end==len(t)-1:continue
        a,b=t[begin],t[end]
        if b-a<=policy['release_seconds']+policy['prepare_seconds']:continue
        def gate(time):
            return float(smooth((time-a)/policy['release_seconds'])*smooth((b-time)/policy['prepare_seconds']))
        def rhs(time,state):
            force=np.interp(time,t,torque)/np.interp(time,t,inertia)
            return [state[1],gate(time)*force-2*zeta*omega*state[1]-omega**2*state[0]]
        sample=t[begin:end+1]
        solution=solve_ivp(rhs,(a,b),[0.,0.],t_eval=sample,max_step=.002,rtol=1e-7,atol=1e-9)
        if not solution.success:raise RuntimeError(solution.message)
        # Active preparation returns to the reviewed pose with C2 boundaries.
        # This happens in the source trajectory before contact/dynamics audit.
        result[begin:end+1]=solution.y[0]*np.array([gate(time) for time in sample])
        windows.append(dict(release_s=float(a),prepare_s=float(b-policy['prepare_seconds']),contact_ready_s=float(b)))
    return result,windows
