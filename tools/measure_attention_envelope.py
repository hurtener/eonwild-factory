"""Measure emitted head heading relative to the torso at keys and midpoints."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.attention import resolve_attention


def measure(package):
    g=Glb(package/'root_motion.glb');d=json.loads((package/'directional.json').read_text())
    raw=(package/'source-animal.profile.json').read_bytes();p=json.loads(raw)
    if hashlib.sha256(g.raw).hexdigest()!=d['emitted_sha256'] or hashlib.sha256(raw).hexdigest()!=d['profile_sha256']:
        raise ValueError('Motion/profile identity mismatch')
    a=resolve_attention(p);bindings={b['role']:b['bone'] for b in p['bindings']}
    nodes={role:g.name_to_node[bindings[role]] for role in ('head','chest')}
    tracks,_=read_animation_tracks(g,'directional-review',require_common_timeline=True)
    def worlds(time):
        tr=list(g.rest_translation);ro=list(g.rest_rotation)
        for (node,path),track in tracks.items():
            if path=='translation':tr[node]=track.sample(float(time))
            elif path=='rotation':ro[node]=track.sample(float(time))
        return np.asarray(_world_matrices(g,tr,ro,g.rest_scale))
    neutral=worlds(0.)
    local={role:np.linalg.solve(neutral[node][:3,:3],np.array([0.,0.,1.])) for role,node in nodes.items()}
    keys=np.asarray([s['time_s'] for s in d['samples']]);times=np.sort(np.r_[keys,(keys[1:]+keys[:-1])/2])
    rows=[]
    for t in times:
        w=worlds(t);f={r:w[n][:3,:3]@local[r] for r,n in nodes.items()}
        headings={r:math.atan2(v[0],v[2]) for r,v in f.items()}
        delta=headings['head']-headings['chest'];yaw=math.degrees(math.atan2(math.sin(delta),math.cos(delta)))
        rows.append({'time_s':float(t),'head_relative_torso_yaw_degrees':yaw})
    maximum=max(abs(r['head_relative_torso_yaw_degrees']) for r in rows)
    return {'method':'Projected head/torso forward axes calibrated from the neutral frame-zero pose; admitted +Y up/+Z forward; keys and midpoints. Not eye field of view, anatomical joint ROM or continuous-time certification.',
            'motion_sha256':d['emitted_sha256'],'profile_sha256':d['profile_sha256'],
            'maximum_absolute_yaw_degrees':maximum,'routine_cap_degrees':a['envelope']['maximumDegrees'],
            'within_routine_cap':maximum<=a['envelope']['maximumDegrees']+1e-4,'samples':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--package',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    data=measure(args.package);args.output.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k!='samples'},indent=2))
    if not data['within_routine_cap']:raise SystemExit('Emitted attention exceeds routine envelope')
