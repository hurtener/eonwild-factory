#!/usr/bin/env python3
"""Geometric skull-space jaw midline validation under symmetric head turns."""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parents[1]/'scripts'; sys.path.insert(0,str(HERE))
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import AnatomicalBasis,SemanticMap
from eonproc_v5.jaw import JawClosureModel
from eonproc_v7.actions import ActionControlsV7
from eonproc_v8.generator import TarbosaurusV8Generator
from eonproc_v8.pivots import lower_foot_pivots
from eonproc_v8.profile import BipedV8Profile

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--bone-map',required=True);ap.add_argument('--profile',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    asset=GlbAsset(a.source); sem=SemanticMap.load(a.bone_map); basis=AnatomicalBasis.gltf_y_up(asset,sem); profile=BipedV8Profile.from_json(a.profile); lower_foot_pivots(asset,sem,basis,profile.foot_pivot_gap_fraction); gen=TarbosaurusV8Generator(asset,sem,profile); model=JawClosureModel(asset,sem,basis,gen.locomotion.hip_height); prim=asset.primitive(); skull=sem.bone('skull'); si=asset.name_to_node[skull]; lateral_local=asset.rest_world_rotation[si].inv().apply(basis.lateral)
    samples=[]
    for yaw,roll in ((0.,0.),(18.,2.),(-18.,-2.)):
        c=ActionControlsV7(pelvis_translation=np.zeros(3),head_yaw=math.radians(yaw),head_roll=math.radians(roll),jaw_open=math.radians(25),left_load=.66,right_load=.34,left_foot_forward=-.03*gen.locomotion.hip_height,right_foot_forward=.32*gen.locomotion.hip_height)
        pose,_,_=gen.actions._pose(0,1,c,{'l':None,'r':None}); points=asset.skin_points(prim.positions,prim.joints,prim.weights,pose.world_matrices); inv=np.linalg.inv(pose.world_matrices[si]); local=(inv@np.c_[points,np.ones(len(points))].T).T[:,:3]; lower=float(np.median(local[model.jaw_mask]@lateral_local)); upper=float(np.median(local[model.upper_mask]@lateral_local)); samples.append({'headYawDegrees':yaw,'headRollDegrees':roll,'lowerMidlineM':lower,'upperMidlineM':upper,'absoluteOffsetM':abs(lower-upper)})
    maximum=max(x['absoluteOffsetM'] for x in samples); result={'status':'PASS' if maximum<=.002 else 'FAIL','method':'weighted jaw and upper-skull vertices transformed into animated skull space at fixed 25-degree gape','samples':samples,'maximumMidlineOffsetM':maximum,'gateM':.002}
    Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
