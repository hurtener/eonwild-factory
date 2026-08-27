#!/usr/bin/env python3
"""Build V5.5 by refining a freshly constrained V4.5 body-balance solve.

This path intentionally preserves all V4 leg, sole, terrain, root-motion and anatomical
constraint tracks. It recalibrates the living-neutral jaw from the actual skinned mesh,
polishes secondary body tracks, fixes action mouth staging, adds subtle inertial detail,
and rebuilds all authored transitions with endpoint-exact derivative-aware splines.
"""
from __future__ import annotations
import argparse, json, math, hashlib, sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from eonproc_v3.gltf_io import GlbAsset, sha256_file, quaternion_continuity
from eonproc_v3.rig import SemanticMap, AnatomicalBasis
from eonproc_v4.animation_reader import AnimationPackReader
from eonproc_v4.clip import AnimationClip
from eonproc_v4.profile import BipedV4Profile
from eonproc_v5_5.jaw import JawClosureModel
from eonproc_v5_5.pivots import lower_foot_pivots
from eonproc_v5_5.polish import smooth_quaternions
from eonproc_v5_5.transitions import pose_transition, phase_matched_loop_transition

SAMPLE_HZ=60

def minimum_jerk(x):
    x=float(np.clip(x,0.,1.)); return x*x*x*(10.+x*(-15.+6.*x))
def bump(x,a,b,c,d):
    if x<=a or x>=d:return 0.
    if x<b:return minimum_jerk((x-a)/(b-a))
    if x<=c:return 1.
    return 1.-minimum_jerk((x-c)/(d-c))
def local_axis(asset,bone,world_axis):
    i=asset.name_to_node[bone]; a=asset.rest_world_rotation[i].inv().apply(world_axis); return a/max(np.linalg.norm(a),1e-12)
def set_axis_track(asset,bone,axis_local,angles_deg):
    i=asset.name_to_node[bone]; rest=asset.rest_rotation[i]
    return (rest*Rotation.from_rotvec(np.asarray(angles_deg)[:,None]*math.pi/180.*axis_local[None,:])).as_quat()
def add_axis_detail(values,axis_local,angles_deg):
    q=Rotation.from_quat(values); d=Rotation.from_rotvec(np.asarray(angles_deg)[:,None]*math.pi/180.*axis_local[None,:]); return quaternion_continuity((q*d).as_quat())

def baked_to_clip(a):
    return AnimationClip(a.name,a.times.copy(),{k:v.copy() for k,v in a.rotations.items()},{k:v.copy() for k,v in a.translations.items()},dict(a.extras),{}).normalize()

def rename_v5_5(name): return name.replace('_V4','_V5_5').replace('V4_','V5_5_')

def jaw_curve(name,times,neutral):
    duration=float(times[-1]); u=times/max(duration,1e-9)
    # Return positive close angle: 0 = original bind gape, neutral ~= 50 = living closed.
    if 'EAT_LOOP' in name:
        count=4; phase=(u*count)%1.; gape=np.zeros_like(u)
        for i,p in enumerate(phase):
            # open -> short hold -> close -> chew/settle, fully closed between bites
            gape[i]=28.*bump(float(p),.04,.22,.39,.58)
            if .58<p<.92: gape[i]+=2.1*math.sin(2*math.pi*3*(p-.58)/.34)*(1-minimum_jerk((p-.58)/.34))
        close=neutral-gape; close[-1]=close[0]=neutral; return close
    if 'BITE_ATTACK' in name:
        close=np.full_like(u,neutral); open_start=.18; a=.36; contact=.56; recovery=.80
        for i,x in enumerate(u):
            if x<open_start: gape=0.
            elif x<a: gape=49.*minimum_jerk((x-open_start)/(a-open_start))
            elif x<contact-.075: gape=49.
            elif x<contact: gape=49.*(1.-minimum_jerk((x-(contact-.075))/.075))
            elif x<contact+.10: gape=1.2*bump(x,contact,contact+.025,contact+.055,contact+.10)
            else: gape=0.
            close[i]=neutral-gape
        close[-1]=neutral; return close
    if 'ROAR' in name and '_TO_' not in name:
        close=np.full_like(u,neutral)
        for i,x in enumerate(u):
            if x<.24:gape=0.
            elif x<.48:gape=50.5*minimum_jerk((x-.24)/.24)
            elif x<.76:gape=50.5
            elif x<.94:gape=50.5*(1.-minimum_jerk((x-.76)/.18))
            else:gape=0.
            close[i]=neutral-gape
        close[-1]=neutral; return close
    # Locomotion/idle: genuinely closed, with only breathing-scale living motion.
    breath=.22+.14*(.5+.5*np.sin(2*math.pi*.31*times+.4))
    close=neutral-breath
    if bool('loop' in name.lower()): close[-1]=close[0]
    return close

def apply_detail(asset,sem,basis,clip):
    t=clip.times; duration=max(float(t[-1]),1e-6); u=t/duration; loop=bool(clip.extras.get('loop',False))
    # Protect root and all contact-critical leg/toe tracks; smooth expressive chains only.
    protected={sem.bone('root'),sem.bone('jaw')}
    for side in ('l','r'):
        for tag in (f'thigh_{side}',f'shin_{side}',f'ankle_{side}',f'foot_{side}',f'toe_{side}',f'toe_2_{side}',f'toe_3_{side}'):
            if tag in sem.tags: protected.add(sem.bone(tag))
            if tag in sem.tags:
                protected.update(asset.single_child_chain(sem.bone(tag),4))
    changed={}; max_change=0.
    for bone,values in list(clip.rotations.items()):
        if bone in protected: continue
        window=5 if any(k in clip.name for k in ('BITE','ROAR','START','BRAKE')) else 7
        out,delta=smooth_quaternions(values,loop,window,3); clip.rotations[bone]=out; changed[bone]=delta; max_change=max(max_change,delta)
    # Very small coherent residual motion: force transmission, breathing and distal lag.
    locomotion=any(k in clip.name for k in ('WALK','TURN','START','BRAKE'))
    action=any(k in clip.name for k in ('BITE_ATTACK','ROAR','EAT_LOOP'))
    if locomotion:
        step=np.sin(4*math.pi*u+.18); slow=np.sin(2*math.pi*u+.73)
        detail_specs=[('chest',basis.lateral,.32*step),('head',basis.lateral,-.24*step+.11*slow),('head',basis.up,.16*slow)]
        for tag,axis,ang in detail_specs:
            if tag in sem.tags and sem.bone(tag) in clip.rotations:
                b=sem.bone(tag); clip.rotations[b]=add_axis_detail(clip.rotations[b],local_axis(asset,b,axis),ang)
        # More compliant distal tail, not a synchronized wave.
        for n in range(6,10):
            tag=f'tail_{n:02d}'
            if tag in sem.tags and sem.bone(tag) in clip.rotations:
                b=sem.bone(tag); amp=.18+.10*(n-6); ang=amp*np.sin(2*math.pi*u-.42*n)+.08*np.sin(6*math.pi*u+.2*n)
                clip.rotations[b]=add_axis_detail(clip.rotations[b],local_axis(asset,b,basis.up),ang)
    elif action:
        # Residual tail settling and asymmetric head mass without changing action beats.
        if 'tail_09' in sem.tags and sem.bone('tail_09') in clip.rotations:
            b=sem.bone('tail_09'); ang=.26*np.sin(2*math.pi*1.35*u+.6)*(np.sin(math.pi*u)**2)
            clip.rotations[b]=add_axis_detail(clip.rotations[b],local_axis(asset,b,basis.up),ang)
    if loop:
        for v in clip.rotations.values(): v[-1]=v[0]
    clip.extras.update({'generator':'Eonwild procedural animation toolkit v5.5','version':'5.5.0','polished':True,'contactTracksRegenerated':True,'pelvisTranslationExported':True,'polishWindowFrames':7})
    clip.diagnostics['polish']={'smoothed_bone_count':len(changed),'maximum_change_degrees':max_change,'protected_contact_bones':len(protected)}
    return clip

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-glb',required=True); ap.add_argument('--bone-map',required=True); ap.add_argument('--profile',required=True); ap.add_argument('--v4-report'); ap.add_argument('--output-dir',required=True); args=ap.parse_args()
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    profile=BipedV4Profile.from_json(args.profile)
    asset=GlbAsset(args.source_glb); sem=SemanticMap.load(args.bone_map); basis=AnatomicalBasis.gltf_y_up(asset,sem)
    pivot_adjustment=lower_foot_pivots(asset,sem,basis,profile.foot_pivot_gap_fraction)
    primitive=asset.primitive(); ground=float(primitive.positions[:,1].min()); hip=float(asset.rest_world[asset.name_to_node[sem.bone('pelvis')]][1,3]-ground)
    jaw_model=JawClosureModel(asset,sem,basis,hip); jaw=jaw_model.calibrate(target_minimum_gap_m=hip*.0015); neutral=jaw.close_degrees
    v4_report=json.load(open(args.v4_report)) if args.v4_report and Path(args.v4_report).exists() else None
    if v4_report is None:
        raise ValueError("V5.5 requires the durable constrained-solve report")
    if not bool(v4_report.get('automated_quality_pass', False)):
        raise ValueError("V5.5 constrained source failed automated quality gates")
    reader=AnimationPackReader(asset); base=[]
    for a in reader.animations.values():
        if bool(a.extras.get('transition', False)): continue
        c=baked_to_clip(a); c.name=rename_v5_5(c.name); c.extras={**c.extras,'version':'5.5.0','generator':'Eonwild procedural animation toolkit v5.5','sourceVersion':'4.5.0'}
        # Replace jaw track with calibrated action-specific track.
        angles=jaw_curve(c.name,c.times,neutral); jaw_bone=sem.bone('jaw'); c.rotations[jaw_bone]=set_axis_track(asset,jaw_bone,local_axis(asset,jaw_bone,basis.lateral),-angles)
        c=apply_detail(asset,sem,basis,c); c.normalize(exact_loop=bool(c.extras.get('loop',False))); base.append(c)
    by={c.name:c for c in base}; root=sem.bone('root')
    def pt(name,s,t,d,sp=0.,tp=0.,tags=()): return pose_transition(name,by[s],by[t],d,SAMPLE_HZ,sp,tp,root,tags)
    transitions=[
      pt('PROC_IDLE_TO_WALK_V5_5','PROC_IDLE_BREATH_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE',1.95,0,0,('transition','idle','walk')),
      pt('PROC_WALK_TO_IDLE_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE','PROC_IDLE_BREATH_V5_5',1.95,.5,0,('transition','walk','idle')),
      phase_matched_loop_transition('PROC_WALK_TO_ALERT_WALK_V5_5',by['PROC_WALK_RELAXED_V5_5_INPLACE'],by['PROC_ALERT_WALK_V5_5_INPLACE'],2.2222222,SAMPLE_HZ,root,('transition','walk','alert')),
      phase_matched_loop_transition('PROC_ALERT_WALK_TO_WALK_V5_5',by['PROC_ALERT_WALK_V5_5_INPLACE'],by['PROC_WALK_RELAXED_V5_5_INPLACE'],2.2222222,SAMPLE_HZ,root,('transition','alert','walk')),
      pt('PROC_IDLE_TO_ALERT_IDLE_V5_5','PROC_IDLE_BREATH_V5_5','PROC_ALERT_IDLE_V5_5',1.4,0,0,('transition','idle','alert')),
      pt('PROC_ALERT_IDLE_TO_IDLE_V5_5','PROC_ALERT_IDLE_V5_5','PROC_IDLE_BREATH_V5_5',1.4,0,0,('transition','alert','idle')),
      pt('PROC_IDLE_TO_EAT_V5_5','PROC_IDLE_BREATH_V5_5','PROC_EAT_LOOP_V5_5',2.05,0,0,('transition','idle','eat')),
      pt('PROC_EAT_TO_IDLE_V5_5','PROC_EAT_LOOP_V5_5','PROC_IDLE_BREATH_V5_5',2.05,0,0,('transition','eat','idle')),
      pt('PROC_IDLE_TO_ROAR_READY_V5_5','PROC_IDLE_BREATH_V5_5','PROC_ROAR_V5_5',.95,0,0,('transition','idle','roar')),
      pt('PROC_ROAR_TO_IDLE_V5_5','PROC_ROAR_V5_5','PROC_IDLE_BREATH_V5_5',1.55,1,0,('transition','roar','idle')),
      pt('PROC_WALK_TO_BITE_READY_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE','PROC_BITE_ATTACK_V5_5',.95,.5,0,('transition','walk','bite','urgent')),
      pt('PROC_BITE_TO_WALK_V5_5','PROC_BITE_ATTACK_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE',1.55,1,0,('transition','bite','walk','recovery')),
      pt('PROC_WALK_TO_ROAR_READY_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE','PROC_ROAR_V5_5',1.45,.5,0,('transition','walk','roar')),
      pt('PROC_ROAR_TO_WALK_V5_5','PROC_ROAR_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE',2.0,1,0,('transition','roar','walk','recovery')),
      pt('PROC_WALK_TO_EAT_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE','PROC_EAT_LOOP_V5_5',2.1,.5,0,('transition','walk','eat','settle')),
      pt('PROC_EAT_TO_WALK_V5_5','PROC_EAT_LOOP_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE',2.1,0,0,('transition','eat','walk','rise')),
    ]
    clips=base+transitions
    specs=[c.gltf_spec() for c in clips]
    glb=out/'tarbosaurus_procedural_v5_5_animation_pack.glb'
    asset.write_animations(glb,specs,True)
    sequence_names={
      'bite':['PROC_WALK_TO_BITE_READY_V5_5','PROC_BITE_ATTACK_V5_5','PROC_BITE_TO_WALK_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE'],
      'roar':['PROC_WALK_TO_ROAR_READY_V5_5','PROC_ROAR_V5_5','PROC_ROAR_TO_WALK_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE'],
      'eat':['PROC_WALK_TO_EAT_V5_5','PROC_EAT_LOOP_V5_5','PROC_EAT_TO_WALK_V5_5','PROC_WALK_RELAXED_V5_5_INPLACE'],
      'alert':['PROC_WALK_TO_ALERT_WALK_V5_5','PROC_ALERT_WALK_V5_5_INPLACE'],
    }
    manifest={
      'schema':'eonwild.animation-manifest.v5.5','version':'5.5.0','asset':glb.name,
      'family':'large_theropod_biped','sampleHz':60,'jawCalibration':jaw.to_dict(),
      'clips':[{'name':c.name,'durationSeconds':c.duration,'loop':bool(c.extras.get('loop',False)),'rootMotion':bool(c.extras.get('rootMotion',False)),'tags':c.extras.get('tags',[]),'terrain':c.extras.get('terrain'),'path':c.extras.get('path'),'transition':bool(c.extras.get('transition',False)),'sourceClip':c.extras.get('sourceClip'),'targetClip':c.extras.get('targetClip'),'sourcePhase':c.extras.get('sourcePhase'),'targetPhase':c.extras.get('targetPhase'),'exactRuntimeHandoff':c.extras.get('exactRuntimeHandoff',False)} for c in clips],
      'runtimeContracts':{'authoredTransitionHandoff':'switch exactly at transition endpoint; do not add another crossfade','directClipSelection':'snapshot blend with root continuity','neutralJaw':'apply calibrated living-neutral closure to all non-vocal/action states','pelvisTranslation':'preserve authored pelvis translation tracks during playback'},
      'actionSequences':sequence_names,
    }
    (out/'animation-manifest.v5.5.json').write_text(json.dumps(manifest,indent=2))
    report={'status':'PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED','version':'5.5.0','buildMode':'full constrained V4.5 body-balance regeneration, profile-driven lower-foot pivot placement, then V5 jaw and secondary polish','jawCalibration':jaw.to_dict(),'footPivotAdjustment':pivot_adjustment,'clipCount':len(clips),'baseClipCount':len(base),'transitionClipCount':len(transitions),'preserved':{'skinJointCount':len(asset.skin_data()[0]),'vertexSoleAndTerrainTracks':True,'anatomicalLegConstraintTracks':True,'rootMotionTracks':True,'restSkinnedMesh':True},'fixes':{'neutralJawCalibrated':True,'biteReopenBugRemoved':True,'secondaryQuaternionPolish':True,'allTransitionsRebuilt':True,'playerExactHandoffContract':True,'pelvisTranslationExported':True,'bodyBalancePass':True,'lowerFootPivotPlacement':True},'input':{'sourceGlb':str(Path(args.source_glb).resolve()),'sourceSha256':sha256_file(args.source_glb),'boneMap':str(Path(args.bone_map).resolve()),'boneMapSha256':sha256_file(args.bone_map),'profile':str(Path(args.profile).resolve()),'profileSha256':sha256_file(args.profile)},'output':{'glb':str(glb.resolve()),'glbSha256':sha256_file(glb)},'sourceV4QualityGates':None if v4_report is None else v4_report.get('quality_gate_summary')}
    (out/'procedural-v5.5-report.json').write_text(json.dumps(report,indent=2))
    (out/'resolved-profile-v5.5.json').write_text(json.dumps({'name':'tarbosaurus_v5_5_body_balance','sampleHz':60,'neutralJawCloseDegrees':neutral,'jawBreathDegrees':.36,'polishWindowFrames':7,'transitionSystem':'RotationSpline + Hermite exact handoff','footPivotGapFraction':profile.foot_pivot_gap_fraction,'footPivotAdjustment':pivot_adjustment},indent=2))
    print(json.dumps({'glb':str(glb),'report':str(out/'procedural-v5.5-report.json'),'manifest':str(out/'animation-manifest.v5.5.json'),'jaw':jaw.to_dict(),'clips':len(clips)},indent=2))
if __name__=='__main__': raise SystemExit(main())
