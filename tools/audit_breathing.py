#!/usr/bin/env python3
"""Usage: audit_breathing.py <skin dir with root_motion.glb, source-animal.profile.json, retarget.json>. Bone-rotation breathing at rest.
Breathing/jaw audit from GLB rotation tracks: angle of chest and jaw bones vs time, at rest windows."""
import json,sys,numpy as np
from pathlib import Path
from scipy.spatial.transform import Rotation
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
skin=Path(sys.argv[1]);glb=Glb(skin/'root_motion.glb');prof=json.loads((skin/'source-animal.profile.json').read_text())
roles={b['role']:glb.name_to_node[b['bone']] for b in prof['bindings']}
tracks,_=read_animation_tracks(glb,'moco-prototype',require_common_timeline=True)
meas=json.loads((skin/'retarget.json').read_text())['measurements'];t=np.array([x['time_s'] for x in meas])
pel=np.array([x['landmarks']['pelvis'] for x in meas]);rest=np.linalg.norm(np.gradient(pel[:,[0,2]],t,axis=0),axis=1)<.05
out={}
for role in ('chest','spine.3','spine.4','jaw_lower','leftShoulder','neck.0'):
    if role not in roles or (roles[role],'rotation') not in tracks:out[role]='no track';continue
    q=np.array([tracks[(roles[role],'rotation')].sample(x) for x in t]);R=Rotation.from_quat(q)
    ang=np.degrees((R[0].inv()*R).magnitude()) if False else np.degrees((Rotation.from_quat(np.mean(q[rest],0)/np.linalg.norm(np.mean(q[rest],0))).inv()*R).magnitude())
    a=ang[rest]
    if len(a)<48:out[role]='no rest';continue
    x=a-a.mean();f=np.fft.rfftfreq(len(x),t[1]-t[0]);s=np.abs(np.fft.rfft(x*np.hanning(len(x))));s[f<.05]=0
    out[role]=dict(rest_range_deg=round(float(np.percentile(a,97.5)-np.percentile(a,2.5)),3),period_s=round(float(1/f[np.argmax(s)]),2) if s.max()>0 else None)
print(skin.parent.name+'/'+skin.name,json.dumps(out))
