#!/usr/bin/env python3
"""Measure actual baked V8 root/head/neck/chest/tail yaw relationships."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap, AnatomicalBasis
from eonproc_v4.animation_reader import AnimationPackReader


def rot_of(m):
    u,_,vt=np.linalg.svd(m[:3,:3]);r=u@vt
    if np.linalg.det(r)<0:u[:,-1]*=-1;r=u@vt
    return Rotation.from_matrix(r)

def heading(vec):
    return math.atan2(float(vec[0]),float(vec[2]))
def wrap(x): return (x+math.pi)%(2*math.pi)-math.pi

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--glb',required=True);ap.add_argument('--bone-map',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    asset=GlbAsset(a.glb);sem=SemanticMap.load(a.bone_map);basis=AnatomicalBasis.gltf_y_up(asset,sem);pack=AnimationPackReader(asset)
    root=sem.bone('root');head=sem.bone('head');neck=sem.bone('neck_05');chest=sem.bone('chest');tail_root=sem.bone('tail_01');tail_tip=sem.bone('tail_09')
    names=[root,head,neck,chest,tail_root,tail_tip];idx={n:asset.name_to_node[n] for n in names};rest_rot={n:rot_of(asset.rest_world[idx[n]]) for n in names}
    results={}
    for clip_name in ('PROC_TURN_LEFT_35_V8_ROOTMOTION','PROC_TURN_RIGHT_35_V8_ROOTMOTION'):
        anim=pack.animation(clip_name);samples=[]
        for t in anim.times:
            worlds=pack.world_matrices_at(anim,float(t));world_rots={n:rot_of(worlds[idx[n]]) for n in names}
            dirs={n:(world_rots[n]*rest_rot[n].inv()).apply(basis.forward) for n in names}
            rh=heading(dirs[root])
            values={'time':float(t),'root_heading_deg':math.degrees(rh)}
            for n,label in ((head,'head'),(neck,'neck'),(chest,'chest'),(tail_root,'tail_root')):
                values[f'{label}_relative_yaw_deg']=math.degrees(wrap(heading(dirs[n])-rh))
            # Tail geometric direction from root toward tip points backwards; reverse to compare with body forward.
            tail_vec=worlds[idx[tail_root]][:3,3]-worlds[idx[tail_tip]][:3,3]
            values['tail_geometry_relative_yaw_deg']=math.degrees(wrap(heading(tail_vec)-rh))
            samples.append(values)
        def peak(key):
            return max(samples,key=lambda x:abs(x[key]))
        results[clip_name]={
            'sample_count':len(samples),'duration_seconds':anim.duration,
            'final_root_heading_deg':samples[-1]['root_heading_deg'],
            'peak_head_relative':peak('head_relative_yaw_deg'),
            'peak_neck_relative':peak('neck_relative_yaw_deg'),
            'peak_chest_relative':peak('chest_relative_yaw_deg'),
            'peak_tail_root_relative':peak('tail_root_relative_yaw_deg'),
            'peak_tail_geometry_relative':peak('tail_geometry_relative_yaw_deg'),
            'samples':samples,
        }
    out={'scope':'actual baked world-space orientation diagnostics; not paleobiological force measurement','clips':results}
    Path(a.output).write_text(json.dumps(out,indent=2));print(json.dumps({k:{x:v[x] for x in v if x!='samples'} for k,v in results.items()},indent=2))
if __name__=='__main__':main()
