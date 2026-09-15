#!/usr/bin/env python3
"""Reopen the emitted pelvis on every native 24 fps review frame."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices


def measure(package, fps=24):
    receipt=json.loads((package/'directional.json').read_text())
    profile_bytes=(package/'source-animal.profile.json').read_bytes()
    glb=Glb(package/'root_motion.glb')
    if (hashlib.sha256(glb.raw).hexdigest()!=receipt['emitted_sha256'] or
            hashlib.sha256(profile_bytes).hexdigest()!=receipt['profile_sha256']):
        raise ValueError('Candidate identity mismatch')
    bindings={b['role']:b['bone'] for b in json.loads(profile_bytes)['bindings']}
    pelvis=glb.name_to_node[bindings['pelvis']]
    tracks,_=read_animation_tracks(glb,'directional-review',require_common_timeline=True)
    times=np.arange(0,receipt['duration_s']+1e-7,1/fps)
    points=[]
    for t in times:
        tr,ro=list(glb.rest_translation),list(glb.rest_rotation)
        for (node,path),track in tracks.items():
            if path=='translation':tr[node]=track.sample(float(t))
            elif path=='rotation':ro[node]=track.sample(float(t))
        worlds=np.asarray(_world_matrices(glb,tr,ro,glb.rest_scale))
        points.append(worlds[pelvis][:3,3])
    points=np.asarray(points)
    velocity=np.diff(points,axis=0)*fps
    acceleration=np.diff(velocity,axis=0)*fps
    hit=receipt['reactive_impact']['hitTimeS']
    active=(times[2:]>hit+.08)&(times[2:]<hit+2.4)
    samples=[dict(frame=i,timeS=float(t),pelvisM=p.tolist(),
                  lateralDisplacementM=float(p[0]-points[0,0])) for i,(t,p) in enumerate(zip(times,points))]
    return dict(method='Reopened emitted pelvis at every native 24 fps frame; +X lateral. Pelvis is not whole-body COM. Frame differences are diagnostic, not a force measurement.',motionSha256=receipt['emitted_sha256'],profileSha256=receipt['profile_sha256'],fps=fps,hitTimeS=hit,
        maximumPostHitLateralAccelerationMps2=float(np.max(np.abs(acceleration[active,0]))),samples=samples)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();data=measure(a.package)
    a.output.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k!='samples'},indent=2))
