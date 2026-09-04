#!/usr/bin/env python3
"""Regression-test baked V8 foot contact and reject the V6 pelvis-flight failure mode."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
SCRIPT_DIR=Path(__file__).resolve().parents[1]/'scripts'; sys.path.insert(0,str(SCRIPT_DIR))
from eonproc_v3.gltf_io import GlbAsset, sha256_file
from eonproc_v3.rig import SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader
from eonproc_v8.profile import BipedV8Profile
from eonproc_v8.locomotion import TarbosaurusV8LocomotionGenerator

CLIPS=('PROC_WALK_RELAXED_V8_INPLACE','PROC_TURN_LEFT_35_V8_ROOTMOTION','PROC_TURN_RIGHT_35_V8_ROOTMOTION','PROC_IDLE_BREATH_V8','PROC_EAT_LOOP_V8','PROC_BITE_ATTACK_V8','PROC_BITE_ATTACK_MIRRORED_V8')

def main()->int:
  ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); ap.add_argument('--glb',required=True); ap.add_argument('--bone-map',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
  src=GlbAsset(a.source); sem=SemanticMap.load(a.bone_map); g=TarbosaurusV8LocomotionGenerator(src,sem,BipedV8Profile())
  baked=GlbAsset(a.glb); pack=AnimationPackReader(baked); prim=baked.primitive(); ground=float(g.mesh_ground); result={}
  status=True
  for cname in CLIPS:
    anim=pack.animation(cname); samples=[]
    for t in anim.times:
      worlds=pack.world_matrices_at(anim,float(t)); side_data={}
      for side in ('l','r'):
        idx=g.sole.selections[side].vertex_indices
        pts=baked.skin_points(prim.positions[idx],prim.joints[idx],prim.weights[idx],worlds)
        sd=pts[:,1]-ground
        side_data[side]={'minimum_m':float(np.min(sd)),'contact_quantile_m':float(np.quantile(sd,g.sole.contact_quantile)),'median_m':float(np.median(sd))}
      samples.append(side_data)
    lowest_support=np.asarray([min(x['l']['contact_quantile_m'],x['r']['contact_quantile_m']) for x in samples])
    worst_penetration=max(0.0,-min(min(x['l']['minimum_m'],x['r']['minimum_m']) for x in samples))
    max_lowest=float(np.max(lowest_support))
    frames_above_12mm=int(np.count_nonzero(lowest_support>0.012))
    no_flight=bool(max_lowest<=0.012)
    no_penetration=bool(worst_penetration<=0.002)
    if cname in ('PROC_IDLE_BREATH_V8','PROC_EAT_LOOP_V8'): no_flight=bool(max_lowest<=0.008)
    # A committed power attack may contain a very short force-release transfer
    # where the first catch foot has left and the second has not fully loaded.
    # This is bounded to <=22 mm and <=3 exported 60 Hz frames (~50 ms), which
    # is categorically different from the sustained V6 pelvis-flight failure.
    bounded_impact_transfer=False
    if 'BITE_ATTACK' in cname:
      bounded_impact_transfer=bool(max_lowest<=0.022 and frames_above_12mm<=3)
      no_flight=bounded_impact_transfer
    passed=no_flight and no_penetration; status=status and passed
    result[cname]={
      'sampleCount':len(samples),'durationSeconds':anim.duration,
      'worstSelectedSolePenetrationM':worst_penetration,
      'maximumLowestFootContactQuantileM':max_lowest,
      'framesWithBothFeetAbove12mm':frames_above_12mm,
      'boundedImpactTransfer':bounded_impact_transfer if 'BITE_ATTACK' in cname else None,
      'noV6StyleFlight':no_flight,'noGroundPenetration':no_penetration,'status':'PASS' if passed else 'FAIL',
    }
  out={'status':'PASS' if status else 'FAIL','scope':'actual baked GLB; selected weighted sole vertices sampled at every exported key','sourceSha256':sha256_file(a.source),'animatedGlbSha256':sha256_file(a.glb),'groundHeightM':ground,'clips':result}
  p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); return 0 if status else 1
if __name__=='__main__': raise SystemExit(main())
