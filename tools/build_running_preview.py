#!/usr/bin/env python3
"""Emit current admitted rigs with shared running choreography, then reopen skin.

Diagnostic source-admission seam matches directional previews; no prior take is
used for timing or axes. Final skin corrections are measured, not auto-approved.
"""
import argparse
from copy import deepcopy
from dataclasses import replace, asdict
import hashlib,json,math
from pathlib import Path
import numpy as np
from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.skin_rig import SkinRig
from eonwild_motion.solve.airborne_gait import solve_airborne_plan_sample, driven_body_response
from eonwild_motion.planning.airborne_gait import build_airborne_plan
from eonwild_motion.planning.running import resolve_running, build_running_review_plan
from eonwild_motion.solve.performance import Performance
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor,_encode
from eonwild_motion.solve.turn_contact import tangent,material_patch_correction,material_patch_drift
from eonwild_motion.planning.grounded_gait import smooth
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks

class Captured(Exception):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--motion-set',type=Path,required=True);ap.add_argument('--profile',type=Path,required=True);ap.add_argument('--recipe',type=Path,default=Path('catalog/behaviors/running-review.v1.json'));ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output
 if out.exists():raise ValueError('Refusing to overwrite candidate')
 captured={};original=CanonicalConstantSkinTargetLaw.__dict__['build']
 def intercept(cls,query,provider,**kw):captured.update(query=query,provider=provider,kwargs=kw);raise Captured()
 CanonicalConstantSkinTargetLaw.build=classmethod(intercept)
 try:
  try:compile_motion_set(a.motion_set.resolve(),'walk',root=Path.cwd(),output=out.parent/(out.name+'.never-published'))
  except Captured:pass
 finally:CanonicalConstantSkinTargetLaw.build=original
 q=captured['query'];c=q.context;source=captured['kwargs']['source'];provider=captured['provider'];profile=json.loads(a.profile.read_text());recipe=json.loads(a.recipe.read_text())
 if not math.isclose(profile['authoring']['bodyHeightM'],c.body_height,rel_tol=1e-6):raise ValueError('Profile height mismatch')
 if hashlib.sha256(source.raw).hexdigest()!=profile['authoring']['animalInstance']['geometry_calibration']['source_geometry_sha256']:raise ValueError('Profile geometry mismatch')
 gait=resolve_running(profile,recipe)
 cycle=None
 if recipe.get('coordination'):
  from eonwild_motion.planning.running_support import RunningSupportCycle,support_body_response
  cycle=RunningSupportCycle(gait,c.body_height,recipe['coordination']);plan=cycle.plan()
 else:plan=build_running_review_plan(gait,c.body_height,profile['locomotion']['walk']['preferredSpeed']['value'])
 times=[r['time_s'] for r in plan['samples']]
 # Preserve neutral jaw and centered-tail admissions; gait-specific body phase
 # uses a restrained continuous carrier instead of walking support timing.
 perf=asdict(Performance(lane_width_body_heights=c.plan['performance']['lane_width_body_heights'],pelvis_sway_body_heights=.006,pelvis_roll_degrees=.7,pelvis_yaw_degrees=1.2,tail_yaw_degrees=6,gaze_elevation_degrees=0,center_lanes_on_bilateral_hip_midpoint=True))
 from build_walk_sequence_preview import plain
 perf['neutral_jaw_calibration']=plain(dict(c.plan['performance']).get('neutral_jaw_calibration'))
 if cycle:perf.update(pelvis_sway_body_heights=0.,pelvis_roll_degrees=0.,pelvis_yaw_degrees=0.,tail_yaw_degrees=2.)
 if cycle and cycle.policy.get('regional_body_response'):perf['tail_yaw_degrees']=0.
 plan['performance']=perf
 context=replace(c,gait=gait,plan=plan,legacy_overlay=False)
 response=support_body_response(cycle,plan,c.roles,profile,c.hip_offsets) if cycle else driven_body_response(gait,plan,c.roles)['samples']
 skin=SkinRig(source,c.roles,c.forward,c.up,captured['kwargs']['contact_profile']);ids={s:np.asarray(provider.anchor_for(s).material_vertex_indices) for s in c.legs}
 refs={s:None for s in c.legs};release={s:np.zeros(3) for s in c.legs};poses=[];checks=[]
 print('RUN_SOURCE',len(times),'samples',gait.step_period_s,'seconds per step',flush=True)
 for i,(row,body) in enumerate(zip(plan['samples'],response)):
  if i==0 or row['review_segment']!=plan['samples'][i-1]['review_segment']:
   refs={s:None for s in c.legs};release={s:np.zeros(3) for s in c.legs}
  half=.5*perf['lane_width_body_heights']*c.body_height;nominal={}
  for s,f in row['feet'].items():
   lane=c.hip_lane_center+math.copysign(half,c.hip_offsets[s]);base=c.base_w[c.legs[s][-1]][:3,3]
   target=c.origin+c.forward*f['forward_m']+c.lateral*lane;target+=c.up*(float(base@c.up)+f['height_m']-float(target@c.up));nominal[s]=target.copy()
   if not f['contact']:refs[s]=None;target+=release[s]*(1-smooth(f['swing_phase']/.3))
   f['world_foot_target_m']=target.tolist()
  for iteration in range(4):
   pose=solve_airborne_plan_sample(context,row,body_response_sample=body);w=np.asarray(_world_matrices(source,pose.translations,pose.rotations,c.base_s));patches={s:skin.skin(w,v) for s,v in ids.items()};errors={s:skin.ground-float((p@c.up).min()) for s,p in patches.items()}
   for s,f in row['feet'].items():
    if f['contact'] and refs[s] is None:refs[s]=patches[s].copy()
   if iteration==3:break
   for s,f in row['feet'].items():
    delta=c.up*errors[s] if f['contact'] or errors[s]>0 else np.zeros(3)
    if f['contact']:delta+=material_patch_correction(patches[s],refs[s],c.up)
    f['world_foot_target_m']=(np.asarray(f['world_foot_target_m'])+delta).tolist()
  for s,f in row['feet'].items():
   if f['contact']:release[s]=tangent(np.asarray(f['world_foot_target_m'])-nominal[s],c.up)
  poses.append((pose.translations,pose.rotations));checks.append({'time_s':row['time_s'],'unreachable_m':pose.maximum_unreachable_extension_m,'foot_target_residual_m':pose.maximum_foot_target_residual_m,'articulation_violation_degrees':pose.maximum_articulation_envelope_violation_degrees,'floor_gap_m':{s:-v for s,v in errors.items()}})
  if i%48==0:print('Solved',i,'/',len(times),flush=True)
 document=deepcopy(source.document);binary=bytearray(source.binary);ta=_append_accessor(document,binary,np.asarray(times),'SCALAR');samplers=[];channels=[]
 tr=np.asarray([p[0] for p in poses]);ro=np.asarray([p[1] for p in poses]);ro/=np.linalg.norm(ro,axis=2)[:,:,None]
 for i in range(1,len(ro)):
  flip=np.sum(ro[i-1]*ro[i],axis=1)<0;ro[i,flip]*=-1
 for node in range(len(source.nodes)):
  for path,values in [('translation',tr[:,node]),('rotation',ro[:,node])]:
   acc=_append_accessor(document,binary,values,'VEC3' if path=='translation' else 'VEC4');samplers.append({'input':ta,'output':acc,'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':node,'path':path}})
 document['animations']=[{'name':'running-review','samplers':samplers,'channels':channels}];document['buffers'][0]['byteLength']=len(binary);out.mkdir(parents=True);payload=_encode(document,binary);(out/'root_motion.glb').write_bytes(payload)
 emitted=Glb(out/'root_motion.glb');tracks,_=read_animation_tracks(emitted,'running-review',require_common_timeline=True);reopened=SkinRig(emitted,c.roles,c.forward,c.up,captured['kwargs']['contact_profile']);measured=[];refs={s:None for s in c.legs}
 for i,t in enumerate(times):
  if i==0 or plan['samples'][i]['review_segment']!=plan['samples'][i-1]['review_segment']:
   refs={s:None for s in c.legs}
  ts=list(c.base_t);rs=list(c.base_r)
  for (node,path),track in tracks.items():
   if path=='translation':ts[node]=tuple(track.sample(t))
   elif path=='rotation':rs[node]=tuple(track.sample(t))
  w=np.asarray(_world_matrices(emitted,ts,rs,c.base_s));p={s:reopened.skin(w,v) for s,v in ids.items()};drift={}
  for s,f in plan['samples'][i]['feet'].items():
   if f['contact']:
    if refs[s] is None:refs[s]=p[s].copy()
    drift[s]=material_patch_drift(p[s],refs[s],c.up)
   else:refs[s]=None
  measured.append({'time_s':t,'floor_gap_m':{s:float((v@c.up).min()-skin.ground) for s,v in p.items()},'contact_drift':drift})
 receipt={'checkpoint':recipe.get('checkpoint',30 if cycle else 29),'status':'RUNNING_DIAGNOSTIC','visual':'PENDING','production':False,'source_sha256':hashlib.sha256(source.raw).hexdigest(),'emitted_sha256':hashlib.sha256(payload).hexdigest(),'profile_sha256':hashlib.sha256(a.profile.read_bytes()).hexdigest(),'recipe':recipe,'motion_set':str(a.motion_set),'plan':plan,'checks':checks,'reopened':measured,'limits':'Authored body response and sampled patch-centroid/floor correction; no force balance or arbitrary terrain certification.'}
 (out/'running.json').write_text(json.dumps(receipt,indent=2));(out/'source-animal.profile.json').write_bytes(a.profile.read_bytes());print('EMITTED',out,flush=True)
if __name__=='__main__':main()
