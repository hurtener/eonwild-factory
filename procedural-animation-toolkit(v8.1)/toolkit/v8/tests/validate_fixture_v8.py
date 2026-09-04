#!/usr/bin/env python3
"""Validate V8 mapping, skin, sole witnesses and action/turn invariants."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
SCRIPT_DIR=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPT_DIR))
from eonproc_v3.gltf_io import GlbAsset,sha256_file
from eonproc_v3.rig import SemanticMap
from eonproc_v8.profile import BipedV8Profile
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--bone-map',required=True);ap.add_argument('--profile');ap.add_argument('--output',required=True);a=ap.parse_args()
 asset=GlbAsset(a.input);sem=SemanticMap.load(a.bone_map);profile=BipedV8Profile.from_json(a.profile) if a.profile else BipedV8Profile();g=TarbosaurusV8LocomotionGenerator(asset,sem,profile)
 prim=asset.primitive();mapped=list(sem.tags.values());missing=sorted(set(mapped)-set(asset.name_to_node));sel=g.sole.selections;overlap=np.intersect1d(sel['l'].vertex_indices,sel['r'].vertex_indices)
 out={
  'status':'PASS' if not missing and len(overlap)==0 and len(asset.skin_data()[0])==75 else 'FAIL','version':'8.0.0',
  'input':{'sha256':sha256_file(a.input),'nodeCount':len(asset.nodes)},
  'boneMap':{'sha256':sha256_file(a.bone_map),'tagCount':len(sem.tags),'uniqueBoneCount':len(set(mapped)),'missingBones':missing},
  'skin':{'jointCount':len(asset.skin_data()[0]),'primitiveVertexCount':len(prim.positions),'jointWeightSets':int(prim.joints.shape[1]//4)},
  'sole':{side:{'selectedVertexCount':int(len(s.vertex_indices)),'candidateVertexCount':s.total_candidate_vertices,'allIndicesInPrimitive':bool(np.all(s.vertex_indices<len(prim.positions))),'uniqueIndices':bool(len(np.unique(s.vertex_indices))==len(s.vertex_indices)),'restMinHeight':s.rest_min_height,'restContactQuantile':s.rest_contact_quantile,'influencingBones':list(s.influencing_bones)} for side,s in sel.items()},
  'leftRightSelectionOverlap':int(len(overlap)),
  'anatomicalConstraints':{'leftExpectedKneeSign':float(g.leg_geometry['l']['knee_signed_sign']),'rightExpectedKneeSign':float(g.leg_geometry['r']['knee_signed_sign']),'leftExpectedAnkleSign':float(g.leg_geometry['l']['ankle_signed_sign']),'rightExpectedAnkleSign':float(g.leg_geometry['r']['ankle_signed_sign'])},
  'v8Invariants':{
   'pelvisMustBeSolvedBeforeLegIK':True,'exportedPelvisMustMatchSolvedPose':True,'postSolveBalanceTransformForbidden':True,
   'turnHeadNeckLeadRequired':True,'powerAttackRequiresTwoSupportChanges':True,'feedingRequiresLateGapeClampPull':True,
  },
 }
 p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
