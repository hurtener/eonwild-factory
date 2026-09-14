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
from eonwild_motion.solve.airborne_gait import solve_airborne_plan_sample, _outward_knee_bend_normal, _interior, _qrotvec, _qrotate, _qmul, _qinv, _world_rotation, _local_delta
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices, _rotation_from_matrix
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _encode
from eonwild_motion.planning.directional_steps import DirectionalSteps
from eonwild_motion.solve.turn_attention import turn_look_yaw
from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities, plan_directional
from eonwild_motion.solve.turn_support import accommodate_support_planes, TurnLoadResponse, loaded_hip_roll
from eonwild_motion.solve.turn_contact import tangent, material_patch_correction, material_patch_drift
from eonwild_motion.planning.grounded_gait import smooth, grounded_swing_articulation
from eonwild_motion.planning.foot_articulation import declare_pad_recovery_sample
from eonwild_motion.planning.reverse_walking import reverse_articulation, reverse_attention
from eonwild_motion.planning.lateral_recovery import lateral_articulation, lateral_attention
from eonwild_motion.attention import resolve_attention, bound_attention, attention_intent

class Captured(Exception): pass

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--motion-set',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--fps',type=int,default=24);ap.add_argument('--limit',type=float)
    ap.add_argument('--profile',type=Path,help='Animal embodiment with locomotion capabilities; omit to reproduce the preserved choreography')
    ap.add_argument('--recipe',type=Path,default=Path('catalog/behaviors/directional-review.v1.json'))
    ap.add_argument('--reverse-look-mode', choices=('none','normal','scan','strong','exceptional'),
                    help='Diagnostic intent override; animal angles still come from the profile')
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
    recipe=json.loads((repo/a.recipe).read_text())
    recipe_input=deepcopy(recipe)
    walk_recovery=recipe.get('walking',{}).get('articulation_source')=='admitted_grounded_walk'
    reverse_recovery=recipe.get('walking',{}).get('articulation_source')=='backward_grounded'
    lateral_recovery=recipe.get('walking',{}).get('articulation_source')=='lateral_grounded'
    if lateral_recovery and not a.profile:raise ValueError('Lateral recovery requires an animal profile')
    if a.reverse_look_mode:
        if not reverse_recovery:raise ValueError('Reverse look override requires backward choreography')
        recipe['reverse']['look_mode']=a.reverse_look_mode
    if walk_recovery:
        recipe['walking']['heel_roll_degrees']=q._locomotion_gait.push_off_pitch_degrees
        recipe['walking']['clearance_body_heights']=q._locomotion_gait.swing_clearance_body_heights
        if recipe['walking'].get('recovery_timing')=='overlapping_walk_release':
            recipe['walking']['rounded_swing_peak_fraction']=q._locomotion_gait.rounded_swing_peak_fraction
    if any('step_scale_of_normal' in b for b in recipe['blocks']) and not a.profile:
        raise ValueError('Profile-relative walking steps require an animal capability profile')
    half=float(c.plan['performance']['lane_width_body_heights'])*c.body_height/2
    if reverse_recovery:
        half=.5*recipe['reverse']['stance_width_body_heights']*c.body_height
    if lateral_recovery:
        half=.5*recipe['lateral']['stance_width_body_heights']*c.body_height
    if not lateral_recovery and all(abs(b.get('step_scale_of_normal',b.get('step_length_body_heights',0.)))<1e-12 for b in recipe['blocks']):
        half=.5*recipe['turn_stance']['width_body_heights']*c.body_height
    lanes={s:c.hip_lane_center+math.copysign(half,c.hip_offsets[s]) for s in c.legs}
    heights={s:float(c.base_w[ch[-1]][:3,3]@c.up) for s,ch in c.legs.items()}
    sequence=None
    if not a.profile:
        sequence=DirectionalSteps(c.origin,c.forward,c.lateral,c.up,c.body_height,lanes,heights,recipe['blocks'],recipe['step_seconds'],turn_stance=recipe['turn_stance'])
    capabilities=None; capability_plan=None; profile=None
    if a.profile:
        profile=json.loads(a.profile.read_text()); capabilities=resolve_capabilities(profile)
        motion_set=json.loads(a.motion_set.read_text())
        baseline=json.loads((repo/motion_set['baseline']['path']).read_text())
        if profile['authoring']['animalInstance']['geometry_calibration']['source_geometry_sha256'] != baseline['source']['sha256']:
            raise ValueError('Profile geometry identity mismatch')
        if not math.isclose(profile['authoring']['bodyHeightM'],c.body_height,rel_tol=1e-6):
            raise ValueError('Profile body calibration does not match admitted rig')
        sequence,capability_plan=plan_directional(capabilities,c.origin,c.forward,c.lateral,c.up,c.body_height,lanes,heights,recipe)
        recipe=deepcopy(recipe);recipe['turn_attention']['lead_seconds']=capabilities['attentionLeadSeconds']
        if recipe.get('walking'):recipe['walking']=dict(sequence.walking)
    animal_attention=resolve_attention(profile) if profile else None
    if lateral_recovery and not animal_attention:raise ValueError('Lateral recovery requires profile attention')
    neck_weights=None; exceptional_attention=False
    if animal_attention:
        bindings={b['role']:b['bone'] for b in profile['bindings']}
        weight_by_bone=dict(zip((bindings[r] for r in profile['neckRoles']),animal_attention['envelope']['neckWeights']))
        neck_weights=[weight_by_bone[n] for n in c.roles['neck']]
        recipe['turn_attention']['neck_share']=animal_attention['neckShare']
        if reverse_recovery and 'look_mode' in recipe['reverse']:
            intent=attention_intent(recipe['reverse']['look_mode'],animal_attention)
            recipe['reverse']['look_degrees']=intent['requestedDegrees']
            exceptional_attention=intent['exceptional']
    elif reverse_recovery and 'look_mode' in recipe['reverse']:
        raise ValueError('Reverse attention mode requires an animal attention envelope')
    response_seconds=capabilities['responseSeconds'] if capabilities else .24
    load_response=TurnLoadResponse(sequence,capabilities,recipe['turn_load_response']) if capabilities and 'turn_load_response' in recipe else None
    load_binding=hashlib.sha256(json.dumps({'recipe':recipe,'capabilities':capabilities,'source':hashlib.sha256(source.raw).hexdigest()},sort_keys=True).encode()).hexdigest()
    turn_shapes={}
    for side,chain in c.legs.items():
        hp,kp,ap,fp=[np.asarray(c.base_w[n])[:3,3] for n in chain]
        turn_shapes[side]={'knee_interior_degrees':min(recipe['turn_leg_shape']['maximum_preferred_knee_interior_degrees'],_interior(hp-kp,ap-kp)-recipe['turn_leg_shape']['knee_softening_degrees_from_neutral']), 'ankle_interior_degrees':_interior(kp-ap,fp-ap)}
    # Each planted interval owns its world bend plane. During recovery the
    # plane can reorient toward the next placement, then stays fixed again.
    support_planes={}
    for side,chain in c.legs.items():
        entries=[]
        for at in [0.]+[e['end'] for e in sequence.events if e['side']==side]:
            ref=sequence.sample(at);f=ref['feet'][side]
            qbody=_qrotvec(c.up*ref['heading']);qfoot=_qrotvec(c.up*f['heading'])
            hp=c.origin+np.asarray(_qrotate(qbody,c.base_w[chain[0]][:3,3]-c.origin))+ref['center']
            hp-=c.up*(recipe['turn_leg_shape']['pelvis_settle_body_heights']+.008*ref['weight']**2)*c.body_height
            ap=f['position']-np.asarray(_qrotate(qfoot,c.base_w[chain[-1]][:3,3]-c.base_w[chain[-2]][:3,3]))
            n=_outward_knee_bend_normal(ap-hp,np.asarray(_qrotate(qfoot,c.anatomical_normals[side])),np.asarray(_qrotate(qfoot,c.lateral))*math.copysign(1,c.hip_offsets[side]),c.knee_bend_plane_outward_degrees)
            entries.append((at,n))
        support_planes[side]=entries
    duration=min(sequence.duration,a.limit) if a.limit else sequence.duration
    times=np.linspace(0,duration,round(duration*a.fps)+1)
    upi=int(np.argmax(abs(c.up)));poses=[];checks=[];samples=[]
    # Keep admitted neutral posture; directional timing replaces periodic straight-walk body response.
    context=replace(c,legacy_overlay=False)
    print('Captured admitted source',len(times),'samples; height',c.body_height,flush=True)
    tail_rate = 0.
    contact_references={s:None for s in c.legs};release_offsets={s:np.zeros(3) for s in c.legs}
    for i,t in enumerate(times):
        step=sequence.sample(t);yaw=_qrotvec(c.up*step['heading']); inv=_qinv(yaw)
        normals={};gains={};hips={};ankles={}
        loads=load_response.loads(t) if load_response else None
        roll_angle=load_response.roll(t) if load_response else 0.
        settle=recipe['turn_leg_shape']['pelvis_settle_body_heights']+(0. if load_response else .008*step['weight']**2)
        support_delta=np.zeros(3)
        for side,chain in c.legs.items():
            f=step['feet'][side];entries=support_planes[side]
            n=entries[0][1]
            for idx,e in enumerate(e for e in sequence.events if e['side']==side):
                if t>=e['end']:n=entries[idx+1][1]
                elif t>=e['start']:
                    u=f['swing_phase'] if not f['contact'] else (1. if t>e['start']+.5*e['duration'] else 0.)
                    n=(1-smooth(u))*entries[idx][1]+smooth(u)*entries[idx+1][1]
                    break
            normals[side]=n/np.linalg.norm(n)
            u=f['swing_phase'];gains[side]=loads[side] if loads is not None else (1. if f['contact'] else 1-smooth(min(u,1-u)/.18))
            hips[side]=c.origin+np.asarray(_qrotate(yaw,c.base_w[chain[0]][:3,3]-c.origin))+step['center']
            hips[side]-=c.up*settle*c.body_height
            ankles[side]=f['position']-np.asarray(_qrotate(_qrotvec(c.up*f['heading']),c.base_w[chain[-1]][:3,3]-c.base_w[chain[-2]][:3,3]))
        if load_response:
            pelvis=c.origin+np.asarray(_qrotate(yaw,c.base_w[c.pelvis][:3,3]-c.origin))+step['center']-c.up*settle*c.body_height
            hips,support_delta=loaded_hip_roll(hips,pelvis,loads,np.asarray(_qrotate(yaw,c.forward)),c.up,roll_angle)
        accommodation=accommodate_support_planes(hips,ankles,normals,gains,c.up,c.forward,c.lateral,c.body_height)
        step['center']=step['center']+accommodation
        angular_rate=(sequence.body(t+.01)[1]-sequence.body(t-.01)[1])/.02
        tail_rate += (angular_rate-tail_rate)*(1-math.exp(-1/(a.fps*response_seconds)))
        base_r=list(c.base_r)
        for role,lag in [('spine',.20),('tail',-.55)]:
            names=list(c.roles.get(role,[]))
            for name in names:
                node=source.name_to_node[name]
                local_axis=np.asarray(_qrotate(_qinv(_rotation_from_matrix(c.base_w[node])),c.up))
                base_r[node]=_qmul(base_r[node],_qrotvec(local_axis*(tail_rate if role=='tail' else angular_rate)*lag/max(1,len(names))))
        attention=recipe["turn_attention"]
        look_yaw=turn_look_yaw(sequence,t,attention["lead_seconds"],attention["maximum_degrees"],attention.get("anticipation_gain",1.))
        if reverse_recovery:
            look_yaw=reverse_attention(sequence,t,recipe['reverse'])
        if lateral_recovery:
            look_yaw=lateral_attention(sequence,t,recipe['lateral'],animal_attention)
        attention_result=bound_attention(math.degrees(look_yaw),animal_attention,exceptional=exceptional_attention) if animal_attention else None
        if attention_result:look_yaw=math.radians(attention_result['yawDegrees'])
        context=replace(c,base_r=tuple(base_r),legacy_overlay=False)
        row={'time_s':float(t),'root_forward_m':0.,'pelvis_height_offset_m':-settle*c.body_height,'flight':False,'support_count':sum(f['contact'] for f in step['feet'].values()),'performance_gain':0.,'feet':{}}
        for s,f in step['feet'].items():
            target=c.origin+np.asarray(_qrotate(inv,f['position']-c.origin-step['center']))
            u=f['swing_phase'];roll=f.get('roll_degrees',0.)
            in_place=step['turn_in_place']
            row['feet'][s]={'contact':f['contact'],'forward_m':0.,'height_m':0.,'swing_phase':u,'toe_flex_degrees':(10 if in_place else 14)*math.sin(math.pi*u)**2,'foot_pitch_degrees':(-12 if in_place else -10)*math.sin(math.pi*u)**2,'articulation_scale':0. if in_place else 1.,'world_foot_target_m':target.tolist(),'foot_yaw_radians':f['heading']-step['heading'],'stance_roll_pitch_degrees':roll,'stance_roll_swing_pitch_degrees':roll,'stance_roll_release_scale':f.get('roll_scale',0.),'distal_endpoint_role':'shape_preference'}
            if walk_recovery and not in_place:
                scale=f['walk_articulation_scale']
                foot=row['feet'][s]
                if 'knee_extension_preference_degrees' in recipe['walking']:
                    foot['walking_knee_preference_degrees']=recipe['walking']['knee_extension_preference_degrees']
                foot['articulation_scale']=scale
                # The curve owns support/heading/heel timing; the admitted walk
                # supplies coordinated metatarsal, pad and toe recovery.
                if not f['contact']:
                    foot.update(grounded_swing_articulation(q._locomotion_gait,u))
                    foot['toe_flex_degrees']*=scale
                    if 'metatarsal_recovery_gain' in foot:
                        foot['metatarsal_recovery_gain']*=scale
                foot['foot_pitch_degrees']=roll
            if reverse_recovery:
                row['feet'][s].update(reverse_articulation(u,f['contact'],roll,recipe['reverse']))
            if lateral_recovery:
                row['feet'][s].update(lateral_articulation(u,f['contact'],roll,recipe['lateral']))
            if in_place or recipe.get('walking',{}).get('preserve_support_planes',False):
                row['feet'][s]['turn_support_normal']=list(_qrotate(inv,normals[s]))
            if in_place:
                row['feet'][s]['turn_choreographed_pitch_degrees']=row['feet'][s]['foot_pitch_degrees']
                fold=math.sin(math.pi*u)**2
                row['feet'][s]['turn_leg_shape']={
                    'knee_interior_degrees':turn_shapes[s]['knee_interior_degrees']+5-22*fold,
                    'ankle_interior_degrees':turn_shapes[s]['ankle_interior_degrees']-12*fold}
        if walk_recovery and not step['turn_in_place']:
            declare_pad_recovery_sample(dict(c.plan['parameters']),row)
        body_sample={'sagittal_node_degrees':{},'turn_attention':{'yaw_radians':look_yaw,'neck_share':attention['neck_share']}}
        if neck_weights is not None:body_sample['turn_attention']['neck_weights']=neck_weights
        if load_response:
            body_sample['body_support_control']={'policy_id':'turn_load_response.v1','binding_sha256':load_binding,'translation_forward_up_lateral_m':[0.,float(support_delta@c.up),0.],'rotation_pitch_roll_yaw_radians':[0.,roll_angle,0.]}
        nominal_targets={s:np.asarray(f['world_foot_target_m']).copy() for s,f in row['feet'].items()}
        for s,f in row['feet'].items():
            if not f['contact']:
                contact_references[s]=None
                release=release_offsets[s]*(1-smooth(f['swing_phase']/.25))
                f['world_foot_target_m']=(nominal_targets[s]+np.asarray(_qrotate(inv,release))).tolist()
        # Correct material tangential drift and the floor after all body changes.
        for iteration in range(4):
            pose=solve_airborne_plan_sample(context,row,body_response_sample=body_sample)
            worlds=np.asarray(_world_matrices(source,pose.translations,pose.rotations,c.base_s))
            patches={s:skin.skin(worlds,v) for s,v in ids.items()}
            errors={s:skin.ground-float((p@c.up).min()) for s,p in patches.items()}
            world_patches={s:np.asarray([c.origin+_qrotate(yaw,v-c.origin)+step['center'] for v in p]) for s,p in patches.items()}
            for s,f in row['feet'].items():
                if f['contact'] and contact_references[s] is None:contact_references[s]=world_patches[s].copy()
            if iteration==3:break
            for s,e in errors.items():
                delta=c.up*e if row['feet'][s]['contact'] or e>0 else np.zeros(3)
                if row['feet'][s]['contact']:
                    delta+=np.asarray(_qrotate(inv,material_patch_correction(world_patches[s],contact_references[s],c.up)))
                row['feet'][s]['world_foot_target_m']=(np.asarray(row['feet'][s]['world_foot_target_m'])+delta).tolist()
        for s,f in row['feet'].items():
            if f['contact']:release_offsets[s]=tangent(np.asarray(_qrotate(yaw,np.asarray(f['world_foot_target_m'])-nominal_targets[s])),c.up)
        tr=list(pose.translations);rot=list(pose.rotations)
        rootworld=worlds[c.root];newpos=c.origin+np.asarray(_qrotate(yaw,rootworld[:3,3]-c.origin))+step['center']
        tr[c.root]=tuple(np.asarray(tr[c.root])+_local_delta(source,worlds,c.root,newpos-rootworld[:3,3]))
        rot[c.root]=_world_rotation(source,worlds,c.root,_qmul(yaw,_rotation_from_matrix(rootworld)))
        poses.append((tr,rot));samples.append({'load_shares':loads,'pelvis_roll_degrees':math.degrees(roll_angle),'support_pelvis_drop_m':float(support_delta@c.up),'look_yaw_degrees':math.degrees(look_yaw),'time_s':float(t),'label':step['label'],'heading':step['heading'],'center':step['center'].tolist(),'feet':{s:{'contact':f['contact'],'heading':f['heading'],'position':f['position'].tolist()} for s,f in step['feet'].items()}})
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
    receipt={'recipe':recipe,'motion_set':str(a.motion_set),'status':'DIRECTIONAL_DIAGNOSTIC','visual':'PENDING','production':False,'duration_s':duration,'source_sha256':hashlib.sha256(source.raw).hexdigest(),'emitted_sha256':hashlib.sha256(glb).hexdigest(),'mass':'pelvis accommodation to planted leg planes; authored kinematics, not final mass correction','contact':'four-pass frozen material-patch centroid tangential correction and floor solve; full-patch drift measured separately','samples':samples,'checks':checks}
    receipt['recipe_input']=recipe_input
    if animal_attention:
        receipt['attention_envelope']=animal_attention
        receipt['attention_exceptional']=exceptional_attention
    if a.reverse_look_mode:receipt['diagnostic_overrides']={'reverse.look_mode':a.reverse_look_mode}
    if walk_recovery:receipt['walking_articulation_parameters']=dict(c.plan['parameters'])
    if capabilities:
        receipt['capabilities']=capabilities;receipt['capability_plan']=capability_plan
        receipt['profile_sha256']=hashlib.sha256(a.profile.read_bytes()).hexdigest()
        receipt['mass']='mass/force-scaled preparation; load-weighted hip-plane accommodation and compliant pelvis roll; final whole-body force balance remains pending'
        receipt['load_response_seconds']=load_response.response_seconds if load_response else None
        (out/'source-animal.profile.json').write_bytes(a.profile.read_bytes())
        (out/'resolved-capabilities.json').write_text(json.dumps({'profileSha256':receipt['profile_sha256'],'motionSha256':receipt['emitted_sha256'],'resolved':capabilities,'walking':capability_plan['walk']},indent=2)+'\n')
    from eonwild_motion.glb.container import Glb
    from eonwild_motion.glb.animation import read_animation_tracks
    emitted=Glb(out/'root_motion.glb');tracks,_=read_animation_tracks(emitted,'directional-review',require_common_timeline=True)
    reopened_skin=SkinRig(emitted,c.roles,c.forward,c.up,capture['kwargs']['contact_profile'])
    final_checks=[];reopened_contacts=[];references={s:None for s in c.legs}
    for t in times:
        tr=list(c.base_t);ro=list(c.base_r)
        for (node,path),track in tracks.items():
            if path=='translation':tr[node]=tuple(track.sample(float(t)))
            elif path=='rotation':ro[node]=tuple(track.sample(float(t)))
        w=np.asarray(_world_matrices(emitted,tr,ro,c.base_s))
        pp={s:reopened_skin.skin(w,v) for s,v in ids.items()}
        final_checks.append({'time_s':float(t),'floor_gap_m':{side:float((patch@c.up).min()-skin.ground) for side,patch in pp.items()}})
        observed={}
        for side,f in sequence.sample(t)['feet'].items():
            if f['contact']:
                if references[side] is None:references[side]=pp[side].copy()
                observed[side]=material_patch_drift(pp[side],references[side],c.up)
            else:references[side]=None
        reopened_contacts.append({'time_s':float(t),'planted':observed})
    receipt['reopened_emitted_skin_samples']=final_checks
    receipt['reopened_material_contact_samples']=reopened_contacts
    (out/'directional.json').write_text(json.dumps(receipt,indent=2));print('EMITTED',out,flush=True)
if __name__=='__main__':main()
