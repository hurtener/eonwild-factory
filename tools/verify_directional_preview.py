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
class Captured(Exception):pass
ap=argparse.ArgumentParser();ap.add_argument('--motion-set',type=Path,required=True);ap.add_argument('--package',type=Path,required=True);a=ap.parse_args()
cap={};original=CanonicalConstantSkinTargetLaw.__dict__['build']
def intercept(cls,query,provider,**kwargs):cap.update(query=query,provider=provider,kwargs=kwargs);raise Captured()
CanonicalConstantSkinTargetLaw.build=classmethod(intercept)
try:
 try:compile_motion_set(a.motion_set.resolve(),'walk',root=Path.cwd(),output=a.package/'verification.never-published')
 except Captured:pass
finally:CanonicalConstantSkinTargetLaw.build=original
c=cap['query'].context;glb=Glb(a.package/'root_motion.glb');tracks,times=read_animation_tracks(glb,'directional-review',require_common_timeline=True)
skin=SkinRig(glb,c.roles,c.forward,c.up,cap['kwargs']['contact_profile']);ids={s:np.asarray(cap['provider'].anchor_for(s).material_vertex_indices) for s in c.legs}
checks=[]
for t in np.linspace(times[0],times[-1],73):
 tr=list(c.base_t);ro=list(c.base_r)
 for (node,path),track in tracks.items():
  if path=='translation':tr[node]=tuple(track.sample(float(t)))
  elif path=='rotation':ro[node]=tuple(track.sample(float(t)))
 worlds=np.asarray(_world_matrices(glb,tr,ro,c.base_s))
 checks.append({'time_s':float(t),'floor_gap_m':{s:float((skin.skin(worlds,v)@c.up).min()-skin.ground) for s,v in ids.items()}})
report={'status':'DIAGNOSTIC_MEASUREMENT_ONLY','sampling':'73 reopened skin samples including interpolation, not production acceptance','minimum_floor_gap_m':min(min(c['floor_gap_m'].values()) for c in checks),'samples':checks}
(a.package/'reopened-skin.json').write_text(json.dumps(report,indent=2));print(report['minimum_floor_gap_m'])
