#!/usr/bin/env python3
"""Reopen a directional export and inspect actual skinned contact patches."""
import argparse,json
from pathlib import Path
import numpy as np
from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.solve.skin_rig import SkinRig
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.airborne_gait import _qrotvec,_qrotate
class Captured(Exception):pass
ap=argparse.ArgumentParser();ap.add_argument('--motion-set',type=Path,required=True);ap.add_argument('--package',type=Path,required=True);ap.add_argument('--comparison-package',type=Path,required=True);a=ap.parse_args()
cap={};original=CanonicalConstantSkinTargetLaw.__dict__['build']
def intercept(cls,query,provider,**kwargs):cap.update(query=query,provider=provider,kwargs=kwargs);raise Captured()
CanonicalConstantSkinTargetLaw.build=classmethod(intercept)
try:
 try:compile_motion_set(a.motion_set.resolve(),'walk',root=Path.cwd(),output=a.package/'verification.never-published')
 except Captured:pass
finally:CanonicalConstantSkinTargetLaw.build=original
c=cap['query'].context;glb=Glb(a.package/'root_motion.glb');tracks,times=read_animation_tracks(glb,'directional-review',require_common_timeline=True)
skin=SkinRig(glb,c.roles,c.forward,c.up,cap['kwargs']['contact_profile']);ids={s:np.asarray(cap['provider'].anchor_for(s).material_vertex_indices) for s in c.legs}

for package in [a.comparison_package,a.package]:
 glb=Glb(package/'root_motion.glb');tracks,times=read_animation_tracks(glb,'directional-review',require_common_timeline=True)
 receipt=json.loads((package/'directional.json').read_text());runs={s:[] for s in c.legs};current={s:[] for s in c.legs}
 for sample in receipt['samples']:
  t=sample['time_s'];tr=list(c.base_t);ro=list(c.base_r)
  for (node,path),track in tracks.items():
   if path=='translation':tr[node]=tuple(track.sample(float(t)))
   elif path=='rotation':ro[node]=tuple(track.sample(float(t)))
  worlds=np.asarray(_world_matrices(glb,tr,ro,c.base_s))
  for side,chain in c.legs.items():
   f=sample['feet'][side]
   if f['contact']:
    normal=np.asarray(_qrotate(_qrotvec(c.up*f['heading']),c.lateral))
    current[side].append([float((worlds[node][:3,3]-worlds[chain[-1]][:3,3])@normal) for node in chain])
   elif current[side]:runs[side].append(current[side]);current[side]=[]
 for side in c.legs:
  if current[side]:runs[side].append(current[side])
 result={side:np.max([np.ptp(np.asarray(run),axis=0) for run in parts if len(run)>2],axis=0).tolist() for side,parts in runs.items()}
 (package/'loaded-lateral-travel.json').write_text(json.dumps({'metric':'Maximum within-planted-interval peak-to-peak joint displacement across the planted foot lateral axis; hip,knee,ankle,foot; metres; not a force or joint stress measure','values':result},indent=2))
 print(package.name,result)
