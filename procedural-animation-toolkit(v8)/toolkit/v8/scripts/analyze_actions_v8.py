#!/usr/bin/env python3
"""Measure actual baked V8 power-attack and feeding tracks."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap,AnatomicalBasis
from eonproc_v4.animation_reader import AnimationPackReader

def rot_of(m):
 u,_,vt=np.linalg.svd(m[:3,:3]);r=u@vt
 if np.linalg.det(r)<0:u[:,-1]*=-1;r=u@vt
 return Rotation.from_matrix(r)
def heading(v):return math.atan2(float(v[0]),float(v[2]))
def wrap(x):return (x+math.pi)%(2*math.pi)-math.pi

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--glb',required=True);ap.add_argument('--bone-map',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 asset=GlbAsset(a.glb);sem=SemanticMap.load(a.bone_map);basis=AnatomicalBasis.gltf_y_up(asset,sem);pack=AnimationPackReader(asset)
 names={k:sem.bone(k) for k in ('root','pelvis','head','jaw','foot_l','foot_r','tail_09')};idx={k:asset.name_to_node[v] for k,v in names.items()}
 rest_world_rot={k:rot_of(asset.rest_world[i]) for k,i in idx.items()};ground=float(asset.primitive().positions[:,1].min())
 out={'scope':'actual baked GLB kinematics; camera-independent geometric diagnostics, not force reconstruction','clips':{}}
 for clip_name in ('PROC_BITE_ATTACK_V8','PROC_BITE_ATTACK_MIRRORED_V8','PROC_EAT_LOOP_V8'):
  anim=pack.animation(clip_name);samples=[]
  for t in anim.times:
   worlds=pack.world_matrices_at(anim,float(t));rots,trans=pack.sample_tracks(anim,float(t));root_rot=rot_of(worlds[idx['root']]);root_dir=(root_rot*rest_world_rot['root'].inv()).apply(basis.forward);rh=heading(root_dir)
   head_rot=rot_of(worlds[idx['head']]);head_dir=(head_rot*rest_world_rot['head'].inv()).apply(basis.forward)
   q=rots.get(names['jaw'],asset.rest_rotation[idx['jaw']].as_quat());jaw_delta=asset.rest_rotation[idx['jaw']].inv()*Rotation.from_quat(q)
   row={'time':float(t),'phase':float(t/anim.duration),'root_position':worlds[idx['root']][:3,3].tolist(),'pelvis_position':worlds[idx['pelvis']][:3,3].tolist(),'head_position':worlds[idx['head']][:3,3].tolist(),'left_foot_position':worlds[idx['foot_l']][:3,3].tolist(),'right_foot_position':worlds[idx['foot_r']][:3,3].tolist(),'head_relative_yaw_deg':math.degrees(wrap(heading(head_dir)-rh)),'jaw_local_delta_magnitude_deg':math.degrees(jaw_delta.magnitude())}
   samples.append(row)
  root=np.asarray([s['root_position'] for s in samples]);pelvis=np.asarray([s['pelvis_position'] for s in samples]);head=np.asarray([s['head_position'] for s in samples]);lf=np.asarray([s['left_foot_position'] for s in samples]);rf=np.asarray([s['right_foot_position'] for s in samples]);hy=np.asarray([s['head_relative_yaw_deg'] for s in samples]);jaw=np.asarray([s['jaw_local_delta_magnitude_deg'] for s in samples])
  summary={'sample_count':len(samples),'duration_seconds':anim.duration,'root_forward_displacement_m':float(np.dot(root[-1]-root[0],basis.forward)),'pelvis_vertical_span_m':float(np.ptp(pelvis@basis.up)),'pelvis_forward_span_m':float(np.ptp(pelvis@basis.forward)),'head_vertical_span_m':float(np.ptp(head@basis.up)),'head_relative_yaw_span_deg':float(np.ptp(hy)),'maximum_abs_head_relative_yaw_deg':float(np.max(np.abs(hy))),'jaw_delta_min_deg':float(np.min(jaw)),'jaw_delta_max_deg':float(np.max(jaw)),'left_foot_height_min_m':float(np.min(lf[:,1]-ground)),'right_foot_height_min_m':float(np.min(rf[:,1]-ground)),'samples':samples}
  out['clips'][clip_name]=summary
 Path(a.output).write_text(json.dumps(out,indent=2));print(json.dumps({k:{x:y for x,y in v.items() if x!='samples'} for k,v in out['clips'].items()},indent=2))
if __name__=='__main__':main()
