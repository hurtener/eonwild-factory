"""Declared living posture intent, separate from source bind transforms.

These small motions are authored behavior, not simulated respiration. Callers
solve planted limbs and audit mechanics after applying them.
"""
import numpy as np


def living_standing(reference, names, tail_chain, time, policy, leg_length):
    q=np.array(reference,copy=True);index={n:i for i,n in enumerate(names)}
    for name,value in policy['coordinates_rad'].items():
        q[index[name]]=value
    q[index['height']]=policy['hip_height_over_leg_length']*leg_length
    lengths=np.array([p['length_m'] for p in tail_chain]);fractions=lengths/lengths.sum()
    arcs=np.cumsum(fractions)-fractions/2
    density=np.interp(arcs,policy['tail_bend_density']['arc'],policy['tail_bend_density']['radians_per_arc'])
    phase=2*np.pi*time/policy['idle_period_s']
    q[index['height']]+=leg_length*policy['breath_height_leg_lengths']*np.sin(phase)
    q[index['chest']]+=policy['chest_breath_radians']*np.sin(phase)
    q[index['neck']]-=policy['chest_breath_radians']*.6*np.sin(phase)
    q[index['head']]-=policy['chest_breath_radians']*.4*np.sin(phase)
    for p,f,arc,bend in zip(tail_chain,fractions,arcs,density):
        q[index[p['body']]]=f*bend
        q[index[p['body']+'_yaw']]=f*policy['tail_sway_total_radians']*np.sin(phase-policy['tail_phase_lag_radians']*arc)
    return q


def jaw_binding(context, profile, roles, policy):
    """A zero closure is valid; it must never disable a bound breathing jaw."""
    if policy is None:return context.jaw,context.jaw_axis,context.jaw_neutral_close_degrees
    if context.jaw is not None:
        node,axis=context.jaw,context.jaw_axis
    else:
        spec=profile['secondary']['jaw'];node=roles[spec['role']];axis=spec['axis']
    axis=np.asarray(axis,dtype=float)
    if axis.shape!=(3,) or not np.isfinite(axis).all() or np.linalg.norm(axis)<1e-8:
        raise ValueError('Invalid semantic jaw axis')
    close=policy.get('neutral_close_degrees',context.jaw_neutral_close_degrees)
    if not 0<=close<=70:raise ValueError('Invalid neutral jaw closure')
    return node,axis/np.linalg.norm(axis),close
