#!/usr/bin/env python3
"""Usage: audit_liveliness.py <retarget.json>. Tail/arm/head life from skinned-rig landmarks. NOTE: chest/jaw landmarks are pivots; use audit_breathing.py for breathing.
Liveliness audit on the skinned rig (retarget landmarks): breathing, tail wave, head/arm life, rest stillness."""
import json,sys,numpy as np
path=sys.argv[1];r=json.load(open(path));m=r['measurements']
t=np.array([x['time_s'] for x in m]);dt=t[1]-t[0]
P=lambda k:np.array([x['landmarks'][k] for x in m])
pel=P('pelvis');chest=P('chest')
fwd=chest-pel;fwd[:,1]=0;fwd/=np.linalg.norm(fwd,axis=1)[:,None];up=np.array([0,1.,0]);lat=np.cross(fwd,up)
def local(k):
    d=P(k)-pel;return np.stack([(d*fwd).sum(1),d[:,1],(d*lat).sum(1)],1)
speed=np.linalg.norm(np.gradient(pel[:,[0,2]],t,axis=0),axis=1)
rest=speed<.05;walk=speed>1.
def period(x,mask):
    x=x[mask]-x[mask].mean()
    if len(x)<48:return None
    f=np.fft.rfftfreq(len(x),dt);a=np.abs(np.fft.rfft(x*np.hanning(len(x))));a[f<.05]=0
    return float(1/f[np.argmax(a)]) if a.max()>0 else None
def amp(x,mask):
    x=x[mask];return float(np.percentile(x,97.5)-np.percentile(x,2.5)) if mask.sum()>10 else None
tail=sorted([k for k in m[0]['landmarks'] if k.startswith('tail.')],key=lambda k:int(k.split('.')[1]))
out=dict(clip=path.split('research/')[-1],duration_s=float(t[-1]),rest_s=float(rest.sum()*dt),walk_s=float(walk.sum()*dt))
chestv=local('chest')[:,1];jaw=np.linalg.norm(P('jaw_lower')-P('skull_fixed_nose'),axis=1)
for name,mask in (('rest',rest),('walk',walk)):
    if mask.sum()<24:continue
    o=out[name]={}
    o['chest_vertical_mm']=1000*amp(chestv,mask);o['chest_period_s']=period(chestv,mask)
    o['jaw_gape_change_mm']=1000*amp(jaw,mask);o['jaw_period_s']=period(jaw,mask)
    hd=local('head');o['head_rel_body_mm']={a:round(1000*amp(hd[:,i],mask),1) for i,a in enumerate(('fwd','up','lat'))}
    for s in ('left','right'):
        w=P(s+'Wrist')-P(s+'Shoulder');o[s+'_wrist_rel_shoulder_mm']=round(1000*float(np.linalg.norm([amp(w[:,i],mask) for i in range(3)])),1)
    o['tail_lateral_mm_by_node']=[round(1000*amp(local(k)[:,2],mask)) for k in tail]
    o['tail_vertical_mm_by_node']=[round(1000*amp(local(k)[:,1],mask)) for k in tail]
    if name=='walk':
        ref=np.gradient(pel[:,2] if False else local(tail[0])[:,2]*0+ (pel*lat).sum(1),t)
        lags=[]
        for k in tail[1::3]:
            x=np.gradient(local(k)[:,2],t);best=max(range(0,36),key=lambda L:np.corrcoef(ref[mask][:len(ref[mask])-L] if L else ref[mask],x[mask][L:])[0,1] if L<mask.sum()-10 else -1)
            lags.append(round(best*dt,2))
        o['tail_node_lag_behind_pelvis_s']=lags
    if name=='rest':
        motion=np.stack([np.linalg.norm(np.gradient(local(k),axis=0),axis=1) for k in ['chest','head','jaw_lower',tail[len(tail)//2],tail[-1],'leftWrist']],1)
        o['frozen_rest_frames_pct']=round(100*float((motion[mask].max(1)<.0005).mean()),1)
print(json.dumps(out,indent=1))
