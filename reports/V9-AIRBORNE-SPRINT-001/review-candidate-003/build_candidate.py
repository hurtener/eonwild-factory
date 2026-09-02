"""Bounded profile-only Sprint builder using the corrected generic solver."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'reports/V9-AIRBORNE-RUN-001'))
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.solve.airborne_gait import solve_airborne_gait
from measure_stroke import measure
from inspect_articulation import inspect

parser=argparse.ArgumentParser()
parser.add_argument('--name',required=True)
parser.add_argument('--travel',type=float,required=True)
parser.add_argument('--reach',type=float,required=True)
parser.add_argument('--clearance',type=float,default=.24)
parser.add_argument('--crouch',type=float,default=.14)
parser.add_argument('--lift',type=float,default=.15)
args=parser.parse_args()
out=ROOT/'build/V9-AIRBORNE-SPRINT-001/review-candidate-003'/args.name
out.mkdir(parents=True,exist_ok=False)
profile=json.loads((ROOT/'build/V9-AIRBORNE-RUN-001/iteration-006-anatomical-knee/feasible-recovery/engineering-profile.json').read_text())
profile['status']='SPRINT_REVIEW_CANDIDATE_NOT_ACCEPTED'
profile['parameters'].update(step_period_s=11.5/24,flight_fraction=2/11.5,step_length_body_heights=args.travel,touchdown_reach_body_heights=args.reach,swing_clearance_body_heights=args.clearance,pelvis_crouch_body_heights=args.crouch,swing_lift_fraction=args.lift,swing_lower_fraction=.22,continuous_body_launch_fraction=0,rounded_swing_peak_fraction=0,cycles=1)
(out/'engineering-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
source=ROOT/'build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb'
binding=ROOT/'catalog/rigs/hero-theropod-v8_3.semantic-rig.json'
roles=json.loads(binding.read_text())['roles']
files=[source,binding,ROOT/'src/eonwild_motion/planning/airborne_gait.py',ROOT/'src/eonwild_motion/solve/airborne_gait.py']
(out/'input-hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2)+'\n')
root,ip,plan,receipt=solve_airborne_gait(Glb(source),source_clip='PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION',semantic_roles=roles,gait=load_airborne_gait(profile))
(out/'airborne-run-root_motion.glb').write_bytes(root)
(out/'airborne-run-in_place.glb').write_bytes(ip)
for name,value in [('world-plan',plan),('solve-receipt',receipt),('stroke-comparison',measure(out/'airborne-run-root_motion.glb',roles)),('articulation-diagnostics',inspect(out/'airborne-run-root_motion.glb',roles))]:
    (out/f'{name}.json').write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
summary={k:v for k,v in receipt.items() if k not in {'emitted_proxy_samples','semantic_binding'}}
summary['stroke']=json.loads((out/'stroke-comparison.json').read_text())
summary['articulation']={s:{k:v for k,v in side.items() if k!='frames'} for s,side in json.loads((out/'articulation-diagnostics.json').read_text())['per_side'].items()}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
