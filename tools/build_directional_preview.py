#!/usr/bin/env python3
"""Source-driven directional diagnostic. Never consumes a prior animated take."""
import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.skin_rig import SkinRig
from eonwild_motion.solve.airborne_gait import solve_airborne_plan_sample, _interior, _qrotvec, _qrotate, _qmul, _qinv, _world_rotation, _local_delta
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices, _rotation_from_matrix
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _encode
from eonwild_motion.planning.directional_steps import DirectionalSteps
from eonwild_motion.solve.turn_attention import turn_look_yaw

class Captured(Exception): pass

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--motion-set',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--fps',type=int,default=24);ap.add_argument('--limit',type=float)
    a=ap.parse_args(); repo=Path.cwd(); out=a.output.resolve()
    if out.exists(): raise RuntimeError('refusing to overwrite diagnostic')
    capture={}; original=CanonicalConstantSkinTargetLaw.__dict__['build']
    def intercept(cls,query,provider,**kwargs):
        capture.update(query=query,provider=provider,kwargs=kwargs);raise Captured()
    CanonicalConstantSkinTargetLaw.build=classmethod(intercept)
    try:
        try:compile_motion_set(a.motion_set.resolve(),'walk',root=repo,output=out.parent/(out.name+'.never-published'))
        except Captured:pass
    finally:CanonicalConstantSkinTargetLaw.build=original
    q=capture['query'];c=q.context; source=capture['kwargs']['source']; provider=capture['provider']
    skin=SkinRig(source,c.roles,c.forward,c.up,capture['kwargs']['contact_profile'])
    ids={s:np.asarray(provider.anchor_for(s).material_vertex_indices) for s in c.legs}
    recipe=json.loads((repo/'catalog/behaviors/directional-review.v1.json').read_text())
    half=float(c.plan['performance']['lane_width_body_heights'])*c.body_height/2
    if all(abs(b['step_length_body_heights'])<1e-12 for b in recipe['blocks']):
        half=.5*recipe['turn_stance']['width_body_heights']*c.body_height
    lanes={s:c.hip_lane_center+math.copysign(half,c.hip_offsets[s]) for s in c.legs}
    heights={s:float(c.base_w[ch[-1]][:3,3]@c.up) for s,ch in c.legs.items()}
    sequence=DirectionalSteps(c.origin,c.forward,c.lateral,c.up,c.body_height,lanes,heights,recipe['blocks'],recipe['step_seconds'],turn_stance=recipe['turn_stance'])
    turn_shapes={}
    for side,chain in c.legs.items():
        hp,kp,ap,fp=[np.asarray(c.base_w[n])[:3,3] for n in chain]
        turn_shapes[side]={'knee_interior_degrees':min(recipe['turn_leg_shape']['maximum_preferred_knee_interior_degrees'],_interior(hp-kp,ap-kp)-recipe['turn_leg_shape']['knee_softening_degrees_from_neutral']), 'ankle_interior_degrees':_interior(kp-ap,fp-ap)}
    duration=min(sequence.duration,a.limit) if a.limit else sequence.duration
    times=np.linspace(0,duration,round(duration*a.fps)+1)
    upi=int(np.argmax(abs(c.up)));poses=[];checks=[];samples=[]
    # Keep admitted neutral posture; directional timing replaces periodic straight-walk body response.
    context=replace(c,legacy_overlay=False)
    print('Captured admitted source',len(times),'samples; height',c.body_height,flush=True)
    tail_rate = 0.
    for i,t in enumerate(times):
        step=sequence.sample(t);yaw=_qrotvec(c.up*step['heading']); inv=_qinv(yaw)
        angular_rate=(sequence.body(t+.01)[1]-sequence.body(t-.01)[1])/.02
        tail_rate += (angular_rate-tail_rate)*(1-math.exp(-1/(a.fps*.24)))
        base_r=list(c.base_r)
        for role,lag in [('spine',.20),('tail',-.55)]:
            names=list(c.roles.get(role,[]))
            for name in names:
                node=source.name_to_node[name]
                local_axis=np.asarray(_qrotate(_qinv(_rotation_from_matrix(c.base_w[node])),c.up))
                base_r[node]=_qmul(base_r[node],_qrotvec(local_axis*(tail_rate if role=='tail' else angular_rate)*lag/max(1,len(names))))
        attention=recipe["turn_attention"]
        look_yaw=turn_look_yaw(sequence,t,attention["lead_seconds"],attention["maximum_degrees"])
        context=replace(c,base_r=tuple(base_r),legacy_overlay=False)
        row={'time_s':float(t),'root_forward_m':0.,'pelvis_height_offset_m':-(recipe['turn_leg_shape']['pelvis_settle_body_heights']+.008*step['weight']**2)*c.body_height,'flight':False,'support_count':sum(f['contact'] for f in step['feet'].values()),'performance_gain':0.,'feet':{}}
        for s,f in step['feet'].items():
            target=c.origin+np.asarray(_qrotate(inv,f['position']-c.origin-step['center']))
            u=f['swing_phase'];roll=f.get('roll_degrees',0.)
            in_place=step['turn_in_place']
            row['feet'][s]={'contact':f['contact'],'forward_m':0.,'height_m':0.,'swing_phase':u,'toe_flex_degrees':(10 if in_place else 14)*math.sin(math.pi*u)**2,'foot_pitch_degrees':(-7 if in_place else -10)*math.sin(math.pi*u)**2,'articulation_scale':0. if in_place else 1.,'world_foot_target_m':target.tolist(),'foot_yaw_radians':f['heading']-step['heading'],'stance_roll_pitch_degrees':roll,'stance_roll_swing_pitch_degrees':roll,'stance_roll_release_scale':f.get('roll_scale',0.),'distal_endpoint_role':'shape_preference'}
            if in_place:
                fold=math.sin(math.pi*u)**2
                row['feet'][s]['turn_leg_shape']={
                    'knee_interior_degrees':turn_shapes[s]['knee_interior_degrees']+5-22*fold,
                    'ankle_interior_degrees':turn_shapes[s]['ankle_interior_degrees']-12*fold}
        # Fast floor correction only. Tangential material locking is measured separately at review.
        for iteration in range(3):
            pose=solve_airborne_plan_sample(context,row,body_response_sample={'sagittal_node_degrees':{},'turn_attention':{'yaw_radians':look_yaw,'neck_share':attention['neck_share']}})
            worlds=np.asarray(_world_matrices(source,pose.translations,pose.rotations,c.base_s))
            patches={s:skin.skin(worlds,v) for s,v in ids.items()}
            errors={s:skin.ground-float((p@c.up).min()) for s,p in patches.items()}
            if iteration==2:break
            for s,e in errors.items():
                if row['feet'][s]['contact'] or e>0:
                    row['feet'][s]['world_foot_target_m']=(np.asarray(row['feet'][s]['world_foot_target_m'])+c.up*e).tolist()
        tr=list(pose.translations);rot=list(pose.rotations)
        rootworld=worlds[c.root];newpos=c.origin+np.asarray(_qrotate(yaw,rootworld[:3,3]-c.origin))+step['center']
        tr[c.root]=tuple(np.asarray(tr[c.root])+_local_delta(source,worlds,c.root,newpos-rootworld[:3,3]))
        rot[c.root]=_world_rotation(source,worlds,c.root,_qmul(yaw,_rotation_from_matrix(rootworld)))
        poses.append((tr,rot));samples.append({'look_yaw_degrees':math.degrees(look_yaw),'time_s':float(t),'label':step['label'],'heading':step['heading'],'center':step['center'].tolist(),'feet':{s:{'contact':f['contact'],'heading':f['heading'],'position':f['position'].tolist()} for s,f in step['feet'].items()}})
        checks.append({'time_s':float(t),'floor_gap_m':{s:-e for s,e in errors.items()},'unreachable_extension_m':pose.maximum_unreachable_extension_m,'foot_target_residual_m':pose.maximum_foot_target_residual_m,'turn_leg_angles':{s:f.get('turn_leg_angles_degrees') for s,f in pose.feet.items()}})
        if i%24==0:print('Solved',i,'/',len(times),flush=True)
    translations=np.asarray([p[0] for p in poses]);rotations=np.asarray([p[1] for p in poses]);rotations/=np.linalg.norm(rotations,axis=2)[:,:,None]
    for i in range(1,len(rotations)):
        flip=np.sum(rotations[i-1]*rotations[i],axis=1)<0;rotations[i,flip]*=-1
    document=deepcopy(source.document);binary=bytearray(source.binary);ta=_append_accessor(document,binary,times[:,None],'SCALAR');samplers=[];channels=[]
    for node in range(len(source.nodes)):
        for path,values in [('translation',translations[:,node]),('rotation',rotations[:,node])]:
            access=_append_accessor(document,binary,values,'VEC3' if path=='translation' else 'VEC4');samplers.append({'input':ta,'output':access,'interpolation':'LINEAR'});channels.append({'sampler':len(samplers)-1,'target':{'node':node,'path':path}})
    document['animations']=[{'name':'directional-review','samplers':samplers,'channels':channels}];document['buffers'][0]['byteLength']=len(binary)
    out.mkdir(parents=True);glb=_encode(document,binary);(out/'root_motion.glb').write_bytes(glb)
    receipt={'recipe':recipe,'motion_set':str(a.motion_set),'status':'DIRECTIONAL_DIAGNOSTIC','visual':'PENDING','production':False,'duration_s':duration,'source_sha256':hashlib.sha256(source.raw).hexdigest(),'emitted_sha256':hashlib.sha256(glb).hexdigest(),'mass':'authored lateral support shift only; not final mass correction','contact':'three-pass floor correction; material tangential locking not certified','samples':samples,'checks':checks}
    from eonwild_motion.glb.container import Glb
    from eonwild_motion.glb.animation import read_animation_tracks
    emitted=Glb(out/'root_motion.glb');tracks,_=read_animation_tracks(emitted,'directional-review',require_common_timeline=True)
    reopened_skin=SkinRig(emitted,c.roles,c.forward,c.up,capture['kwargs']['contact_profile'])
    final_checks=[]
    for t in np.linspace(0,duration,37):
        tr=list(c.base_t);ro=list(c.base_r)
        for (node,path),track in tracks.items():
            if path=='translation':tr[node]=tuple(track.sample(float(t)))
            elif path=='rotation':ro[node]=tuple(track.sample(float(t)))
        w=np.asarray(_world_matrices(emitted,tr,ro,c.base_s))
        final_checks.append({'time_s':float(t),'floor_gap_m':{side:float((reopened_skin.skin(w,v)@c.up).min()-skin.ground) for side,v in ids.items()}})
    receipt['reopened_emitted_skin_samples']=final_checks
    (out/'directional.json').write_text(json.dumps(receipt,indent=2));print('EMITTED',out,flush=True)
if __name__=='__main__':main()
