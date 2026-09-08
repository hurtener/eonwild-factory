from __future__ import annotations
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
WT=Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-source-motion-query-diagnostic')
sys.path.insert(0,str(WT/'tests'))
from test_v9_airborne_gait import fixture
from eonwild_motion.errors import ContractError
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import GroundedGait,build_grounded_plan
from eonwild_motion.solve.source_motion_query import SourceMotionQuery

def make(source,roles,gait,plan,**kw):
 return SourceMotionQuery(source,semantic_roles=roles,solver_gait=AirborneGait(step_period_s=gait.step_period_s,cycles=1,sample_hz=24),locomotion_gait=gait,plan=plan,forward_axis=(0,0,1),**kw)
source,roles=fixture('review2_',1.,upper_body=True)
gait=GroundedGait(cycles=1,sample_hz=24,step_length_body_heights=.2)
plan=build_grounded_plan(gait,2.)
query=make(source,roles,gait,plan)
t=plan['samples'][1]['time_s']; exact=query.evaluate(t); adjacent=query.evaluate(math.nextafter(t,math.inf))
plan2=build_grounded_plan(gait,query.context.body_height)
bad_gait=GroundedGait(cycles=1,sample_hz=24,step_length_body_heights=.4)
bad_query=make(source,roles,bad_gait,plan2)
t2=plan2['samples'][10]['time_s']; bad_exact=bad_query.evaluate(t2); bad_adjacent=bad_query.evaluate(math.nextafter(t2,math.inf))
# Right-foot liftoff for the canonical grounded law, absent from sampled-row boundary inference.
event=gait.step_period_s+(gait.duty_factor-1)*2*gait.step_period_s
aligned=make(source,roles,gait,plan2)
side_rows={side:aligned.evaluate(event,side=side) for side in ('left_limit','value','right_limit')}
side_derivatives={side:aligned.derivative(event,side=side) for side in ('left_limit','value','right_limit')}
# Current production contact profile is hash-bound to 2cdd, but the query admits it on 044.
old_path=WT/'assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb'
old=Glb.from_bytes(old_path.read_bytes()); rig=json.loads((WT/'catalog/rigs/heavy-biped.v9.json').read_text())['roles']; contact=json.loads((WT/'catalog/contacts/heavy-biped.v10.json').read_text())
h=geometry_height(old,rig,(0,1,0)); actual_gait=GroundedGait(cycles=1,sample_hz=24,step_length_body_heights=.1,touchdown_reach_body_heights=.05,swing_clearance_body_heights=.08); actual_plan=build_grounded_plan(actual_gait,h)
material=SourceMotionQuery(old,semantic_roles=rig,solver_gait=AirborneGait(step_period_s=actual_gait.step_period_s,cycles=1,sample_hz=24),locomotion_gait=actual_gait,plan=actual_plan,up_axis=(0,1,0),forward_axis=(.03893162055641767,0,.9992418770852486),contact_profile=contact).evaluate(actual_plan['samples'][5]['time_s'])
malformed={}
for name,payload in [('missing_time',{'samples':[{},{}]}),('nonnumeric_time',{'samples':[{'time_s':'x'},{'time_s':1}]} )]:
 try: make(source,roles,gait,payload)
 except Exception as exc: malformed[name]={'type':type(exc).__name__,'message':str(exc)}
legacy=SourceMotionQuery(source,semantic_roles=roles,solver_gait=AirborneGait(step_period_s=gait.step_period_s,cycles=1,sample_hz=24),locomotion_gait=gait,plan=plan2,forward_axis=(0,0,1),legacy_overlay='false')
out={
 'review_head':'c02a17769d86841d9c9dddb66b4e0ed8e9365deb',
 'body_height_mismatch':{'context':query.context.body_height,'plan':plan['body_height_m'],'time_s':t,'exact_root_forward_m':exact.row['root_forward_m'],'nextafter_root_forward_m':adjacent.row['root_forward_m'],'max_local_translation_jump_m':float(np.max(np.abs(np.asarray(exact.pose.translations)-np.asarray(adjacent.pose.translations))))},
 'gait_parameter_mismatch':{'plan_step_length_body_heights':gait.step_length_body_heights,'query_step_length_body_heights':bad_gait.step_length_body_heights,'time_s':t2,'exact_root_forward_m':bad_exact.row['root_forward_m'],'nextafter_root_forward_m':bad_adjacent.row['root_forward_m'],'max_local_translation_jump_m':float(np.max(np.abs(np.asarray(bad_exact.pose.translations)-np.asarray(bad_adjacent.pose.translations))))},
 'event_side':{'true_right_liftoff_s':event,'registered_boundary':aligned._is_boundary(event),'registered_boundaries_s':aligned._boundaries,'contacts':{side:[x.row['feet'][foot]['contact'] for foot in ('left','right')] for side,x in side_rows.items()},'derivatives':{side:{'type':type(x).__name__,'status':x.status,'reason':getattr(x,'reason',None)} for side,x in side_derivatives.items()}},
 'contact_source_binding':{'actual_source_sha256':hashlib.sha256(old.raw).hexdigest(),'declared_contact_source_sha256':contact['source']['sha256'],'accepted_material_point_counts':{side:len(points) for side,points in material.material_points.items()}},
 'malformed_plan_errors':malformed,
 'truthy_non_boolean_legacy_overlay_accepted_as':legacy.context.legacy_overlay,
}
path=Path(__file__).with_suffix('.json');path.write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
