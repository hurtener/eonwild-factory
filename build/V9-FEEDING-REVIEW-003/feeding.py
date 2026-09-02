"""Feeding-only resisted oral contact layered into planted whole-body composition."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'build/V9-FEEDING-REVIEW-002'))
from channels import curve
spec=importlib.util.spec_from_file_location('feeding003_foundation',ROOT/'build/V9-FEEDING-REVIEW-001/feeding.py')
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
FREE_POSE=BASE.pose

def signal(time,profile):
    phase=time*6/profile['duration_seconds']
    return {name:curve(phase,keys) for name,keys in profile['channels'].items()}

def smooth(u):
    u=float(np.clip(u,0,1));return u*u*u*(10+u*(-15+6*u))

def anchor_gain(phase,config):
    return smooth((phase-config['enter'])/(config['capture']-config['enter']))*(1-smooth((phase-config['resisted_end'])/(config['release']-config['resisted_end'])))

def correction_modes(rig):
    if hasattr(rig,'feeding_modes'):return rig.feeding_modes
    neutral=rig.world(*rig.pose(0));lateral=np.cross([0.,1.,0.],rig.forward)
    groups=[rig.roles['spine'],rig.roles['chest']+rig.roles['neck'][:3],rig.roles['neck'][3:]+rig.roles['head']]
    pitches={n:BASE.unit(np.linalg.solve(neutral[n,:3,:3],lateral)) for g in groups for n in g}
    yaws={n:BASE.unit(np.linalg.solve(neutral[n,:3,:3],[0.,1.,0.])) for n in rig.roles['neck']+rig.roles['head']}
    rig.feeding_modes=(groups,pitches,yaws);return rig.feeding_modes

def apply_correction(rig,r,x):
    groups,pitches,yaws=correction_modes(rig);rr=r.copy()
    for group,value in zip(groups,x[:3]):
        for n in group:rr[n]=BASE._qmul(rr[n],BASE.A.axis_q(pitches[n],np.radians(value)))
    for role,value in zip(('neck','head'),x[3:]):
        for n in rig.roles[role]:rr[n]=BASE._qmul(rr[n],BASE.A.axis_q(yaws[n],np.radians(value/len(rig.roles[role]))))
    return rr

def solve_oral_anchor(rig,t,r,s,target,profile,state):
    """Five smooth semantic correction modes; never move an attachment.

    Proximal trunk, middle neck, distal neck/head pitch and two yaw modes
    leave orientation freedom around a fixed oral witness. Joint envelopes
    bound the modes before optimization; final serialization checks them again.
    """
    groups,_,_=correction_modes(rig)
    bounds=json.loads((ROOT/'profiles/v9/body-articulation.grounded-bite.v1.json').read_text())['joint_pitch_limits_degrees']
    allowed={n:high for role in ('spine','chest','neck','head') for n,(_,high) in zip(rig.roles[role],bounds[role])}
    preferred={n:angle*state['body'] for role in ('spine','chest','neck','head') for n,angle in zip(rig.roles[role],profile['base_pitch_degrees'][role])}
    low=[max(-preferred[n]+.002 for n in g) for g in groups]+[-12,-12]
    high=[min(allowed[n]-preferred[n]-.01 for n in g) for g in groups]+[12,12]
    def rotations(x):
        return apply_correction(rig,r,x)
    def residual(x):
        rr=rotations(x);w=rig.world(t,rr,s)
        error=(rig.centroid(w,'upper')-target)/profile['anchor']['tolerance_m']
        cervical=[preferred[n]+x[1 if n in groups[1] else 2] for n in rig.roles['chest']+rig.roles['neck']+rig.roles['head']]
        kink=np.maximum(np.abs(np.diff(cervical))-9.5,0)
        return np.r_[error,.003*x,10*kink]
    fit=BASE.A.least_squares(lambda x:residual(np.degrees(x)),np.zeros(5),np.radians(low),np.radians(high),65)
    rr=rotations(np.degrees(fit));error=float(np.linalg.norm(rig.centroid(rig.world(t,rr,s),'upper')-target))
    if error>profile['anchor']['tolerance_m']:raise ValueError(f'unreachable bounded oral anchor {error:.6f} m')
    return rr,error,np.degrees(fit)

def pose(rig,source,profile,time):
    t,r,s,state,legs=FREE_POSE(rig,source,profile,time)
    config=profile['anchor'];phase=time*6/profile['duration_seconds'];gain=anchor_gain(phase,config)
    state['anchor_gain']=gain;state['anchor_error_m']=0.
    if gain>1e-8:
        cache_key=json.dumps(profile,sort_keys=True)
        if getattr(rig,'anchor_cache_key',None)!=cache_key:
            at=config['capture']*profile['duration_seconds']/6
            ta,ra,sa,_,_=FREE_POSE(rig,source,profile,at)
            rig.oral_anchor=rig.centroid(rig.world(ta,ra,sa),'upper');rig.anchor_cache_key=cache_key
            rig.release_correction=None
        if phase<=config['resisted_end']:
            free=rig.centroid(rig.world(t,r,s),'upper')
            target=(1-gain)*free+gain*rig.oral_anchor
            r,state['anchor_error_m'],_=solve_oral_anchor(rig,t,r,s,target,profile,state)
        else:
            # Yield releases contact authority. Carry correction velocity into
            # a bounded pose-space handoff, not an unreachable Cartesian chord.
            if rig.release_correction is None:
                end=config['resisted_end'];h=.001;values=[]
                for at in (end-h,end):
                    ta,ra,sa,st,_=FREE_POSE(rig,source,profile,at*profile['duration_seconds']/6)
                    values.append(solve_oral_anchor(rig,ta,ra,sa,rig.oral_anchor,profile,st)[2])
                rig.release_correction=(values[1],(values[1]-values[0])/h)
            value,velocity=rig.release_correction
            duration=config['release']-config['resisted_end'];u=(phase-config['resisted_end'])/duration
            tangent=u-6*u**3+8*u**4-3*u**5
            r=apply_correction(rig,r,(1-smooth(u))*value+duration*tangent*velocity)
    return t,r,s,state,legs

BASE.signal=signal;BASE.pose=pose;BASE.CLIP='feeding_braced_closed_grip_review'
setup=BASE.setup

def build(profile_path=HERE/'profile.json',output=HERE/'feeding.glb',receipt_path=HERE/'receipt.json'):
    result=BASE.build(profile_path,output,receipt_path)
    p=json.loads(profile_path.read_text());rows=result['samples'];c=p['anchor']
    held=[row for row in rows if c['capture']<=row['time_seconds']*6/p['duration_seconds']<=c['resisted_end']]
    point=np.asarray(held[0]['upper_mouth'])
    result['oral_contact']={'witness':'skinned upper rostral oral surface centroid','maximum_resisted_drift_m':max(float(np.linalg.norm(np.asarray(row['upper_mouth'])-point)) for row in held),'maximum_resisted_jaw_degrees':max(row['state']['actual_jaw_degrees'] for row in held),'config':c}
    result['preserved_feeding002_sha256']=BASE.B.sha((ROOT/'build/V9-FEEDING-REVIEW-002/feeding.glb').read_bytes())
    receipt_path.write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,default=HERE/'profile.json');p.add_argument('--output',type=Path,default=HERE/'feeding.glb');p.add_argument('--receipt',type=Path,default=HERE/'receipt.json');a=p.parse_args()
    print(json.dumps({k:v for k,v in build(a.profile,a.output,a.receipt).items() if k!='samples'},indent=2))
