"""Endpoint-exact, derivative-aware V5.5 transition synthesis."""
from __future__ import annotations
import numpy as np
from scipy.spatial.transform import Rotation, RotationSpline, Slerp
from eonproc_v3.curves import minimum_jerk
from eonproc_v4.clip import AnimationClip

def _idx(clip,phase): return int(np.clip(round(phase*(len(clip.times)-1)),0,len(clip.times)-1))
def _neighbor(values,index,direction,loop):
    n=len(values)
    if loop: return values[(index+direction)%(n-1 if n>2 else n)]
    return values[int(np.clip(index+direction,0,n-1))]
def pose_transition(name,source,target,duration,sample_hz,source_phase=0.,target_phase=0.,root_name=None,tags=()):
    count=int(round(duration*sample_hz))+1; times=np.linspace(0.,duration,count); si=_idx(source,source_phase); ti=_idx(target,target_phase); actual_source_phase=si/max(len(source.times)-1,1); actual_target_phase=ti/max(len(target.times)-1,1)
    bones=sorted(set(source.rotations)|set(target.rotations)); rotations={}
    dt=max(1./sample_hz,.01)
    for bone in bones:
        sv=source.rotations.get(bone,target.rotations[bone]); tv=target.rotations.get(bone,source.rotations[bone])
        q0=sv[si]; q1=tv[ti]
        qm=_neighbor(sv,si,-1,bool(source.extras.get("loop",False))); qp=_neighbor(tv,ti,1,bool(target.extras.get("loop",False)))
        key=Rotation.from_quat(np.stack([qm,q0,q1,qp])); spline=RotationSpline([-dt,0.,duration,duration+dt],key); arr=spline(times).as_quat(); arr[0]=q0; arr[-1]=q1; rotations[bone]=arr
    translations={}
    for node in sorted(set(source.translations)|set(target.translations)):
        sv=source.translations.get(node); tv=target.translations.get(node)
        if sv is None: sv=np.repeat(tv[ti][None,:],len(source.times),axis=0)
        if tv is None: tv=np.repeat(sv[si][None,:],len(target.times),axis=0)
        p0=sv[si].copy(); p1=tv[ti].copy()
        sm=_neighbor(sv,si,-1,bool(source.extras.get("loop",False))); tp=_neighbor(tv,ti,1,bool(target.extras.get("loop",False)))
        v0=(p0-sm)/dt; v1=(tp-p1)/dt; u=times/duration
        h00=2*u**3-3*u**2+1; h10=u**3-2*u**2+u; h01=-2*u**3+3*u**2; h11=u**3-u**2
        arr=h00[:,None]*p0+h10[:,None]*duration*v0+h01[:,None]*p1+h11[:,None]*duration*v1; arr[0]=p0; arr[-1]=p1; translations[node]=arr
    return AnimationClip(name,times,rotations,translations,{"generator":"Eonwild V5.5","version":"5.5.0","loop":False,"rootMotion":False,"transition":True,"transitionType":"RotationSpline + Hermite endpoint match","sourceClip":source.name,"targetClip":target.name,"sourcePhase":actual_source_phase,"targetPhase":actual_target_phase,"exactRuntimeHandoff":True,"tags":list(tags)},{"exact_endpoints":True,"duration_seconds":duration}).normalize()
def phase_matched_loop_transition(name,source,target,duration,sample_hz,root_name,tags=()):
    count=int(round(duration*sample_hz))+1; times=np.linspace(0,duration,count); phase=times/duration; blend=np.asarray([minimum_jerk(float(x)) for x in phase])
    def sample(vals,p):
        f=p*(len(vals)-1); i=int(np.floor(f)); j=min(i+1,len(vals)-1); u=f-i
        return Slerp([0,1],Rotation.from_quat(np.stack([vals[i],vals[j]])))([u]).as_quat()[0]
    rotations={b:[] for b in sorted(set(source.rotations)|set(target.rotations))}
    for p,m in zip(phase,blend):
        for b in rotations:
            a=sample(source.rotations.get(b,target.rotations[b]),float(p)); c=sample(target.rotations.get(b,source.rotations[b]),float(p)); rotations[b].append(Slerp([0,1],Rotation.from_quat(np.stack([a,c])))([float(m)]).as_quat()[0])
    def sample_vec(vals,p):
        f=p*(len(vals)-1); i=int(np.floor(f)); j=min(i+1,len(vals)-1); u=f-i
        return vals[i]*(1.0-u)+vals[j]*u
    translations={node:[] for node in sorted(set(source.translations)|set(target.translations))}
    for p,m in zip(phase,blend):
        for node in translations:
            av=source.translations.get(node); bv=target.translations.get(node)
            if av is None: av=np.repeat(bv[0][None,:],len(source.times),axis=0)
            if bv is None: bv=np.repeat(av[0][None,:],len(target.times),axis=0)
            translations[node].append(sample_vec(av,float(p))*(1.0-m)+sample_vec(bv,float(p))*m)
    tr={node:np.asarray(values) for node,values in translations.items()}
    if root_name in tr:
        tr[root_name][:]=source.translations[root_name][0]
    return AnimationClip(name,times,{b:np.asarray(v) for b,v in rotations.items()},tr,{"generator":"Eonwild V5.5","version":"5.5.0","loop":False,"rootMotion":False,"transition":True,"transitionType":"phase-matched C2 loop blend","sourceClip":source.name,"targetClip":target.name,"sourcePhase":0.,"targetPhase":1.,"exactRuntimeHandoff":True,"tags":list(tags)},{"phase_matched":True,"exact_endpoints":True}).normalize()
