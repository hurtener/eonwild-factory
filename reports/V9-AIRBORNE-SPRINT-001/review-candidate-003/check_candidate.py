"""Focused exact-candidate gate; no shared source mutations."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state,_pose
parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
p=args.directory
r=json.loads((p/'solve-receipt.json').read_text())
a=json.loads((p/'articulation-diagnostics.json').read_text())
profile=json.loads((p/'engineering-profile.json').read_text())['parameters']
source=Glb(ROOT/'build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb')
source_tracks,_=_clip_state(source,'PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION')
bt,_,bs=_pose(source,source_tracks,0)
g=Glb(p/'airborne-run-root_motion.glb');tracks,times=_clip_state(g,'V9_AIRBORNE_RUN_ROOT_MOTION')
names=set()
for leg in r['semantic_binding']['legs'].values():
    names.update(leg['contactChain'])
    for chain in leg['toeChains']:names.update(chain)
max_translation=max_scale=0.
for i in range(len(times)):
    t,_,s=_pose(g,tracks,i)
    for name in names:
        n=g.name_to_node[name];base=source.name_to_node[name]
        max_translation=max(max_translation,float(np.linalg.norm(np.asarray(t[n])-bt[base])))
        max_scale=max(max_scale,float(np.linalg.norm(np.asarray(s[n])-bs[base])))
max_rate=max(v['maximum_angular_velocity_degrees_per_s'] for side in a['per_side'].values() for v in side['rotation_rates'].values())
max_seam=max(v['cyclic_rotation_seam_degrees'] for side in a['per_side'].values() for v in side['rotation_rates'].values())
checks={'unreachable_extension':r['max_unreachable_extension_m']<1e-6,'target_residual':r['max_foot_target_residual_m']<1e-6,'angle_envelope':r['maximum_articulation_envelope_violation_degrees']<.01,'joint_rate':max_rate<=profile['max_joint_angular_velocity_degrees_per_s']+.01,'rotation_seam':max_seam<.1,'anatomical_branches':all(side['bend_sign_flip_count']==0 for side in a['per_side'].values()),'limb_translations':max_translation<1e-6,'limb_scales':max_scale<1e-7}
out={'status':'PASS_FOCUSED_KINEMATICS' if all(checks.values()) else 'FAIL_FOCUSED_KINEMATICS','checks':checks,'maximum_joint_rate_degrees_per_s':max_rate,'maximum_seam_degrees':max_seam,'max_leg_toe_local_translation_difference_from_source_m':max_translation,'max_leg_toe_local_scale_difference_from_source':max_scale,'late_left_approach':[{'time_s':f['time_s'],'hip_degrees':f['hip_sagittal_degrees'],'knee_interior_degrees':f['knee_interior_degrees'],'ankle_interior_degrees':f['ankle_interior_degrees'],'pitch_degrees':r['emitted_proxy_samples'][i]['feet']['left']['solved_foot_pitch_degrees']} for i,f in enumerate(a['per_side']['left']['frames']) if .80<f['time_s']<.93]}
(p/'focused-gate.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
