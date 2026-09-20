#!/usr/bin/env python3
"""Build an isolated animation/kinematic-bridge candidate; never overwrite source."""
import argparse,hashlib,json,sys,platform,os
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from eonwild_motion.glb.container import Glb
from eonwild_motion.biomechanics.kinematic_seed import Seed,emit_glb
from eonwild_motion.biomechanics.opensim_bridge import replay,moco_environment_smoke

def main():
    p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,default=ROOT/'catalog/biomechanics/alioramus-altai.kinematic-seed.v1.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--sample-hz',type=int,default=60);p.add_argument('--moco-smoke',action='store_true');a=p.parse_args()
    if a.output.exists():raise RuntimeError('candidate output already exists; refusing overwrite')
    profile=json.loads(a.profile.read_text());source=Glb(ROOT/profile['source']['path']);seed=Seed(source,profile)
    a.output.mkdir(parents=True)
    (a.output/'profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    print('Sampling explicit authored seed',flush=True)
    times,t,q,s,rows=seed.sample(a.sample_hz)
    print('Replaying serialized OpenSim model and coordinate table',flush=True)
    t,q,receipt=replay(seed,a.output,times,t,q,s)
    inplace=t.copy();inplace[:,seed.root,2]-=times*profile['authored_seed']['stride_m']/profile['authored_seed']['cycle_s']
    st,sq,ss,srow=seed.pose(0,standing=True)
    names=['Alioramus_Walk_RootMotion','Alioramus_Walk_InPlace','Alioramus_Standing_Calibrated']
    raw=emit_glb(source,[(names[0],times,t,q),(names[1],times,inplace,q),(names[2],np.array([0.,1.]),np.array([st,st]),np.array([sq,sq]))])
    model_path=a.output/'Alioramus-altai.refresh.glb';model_path.write_bytes(raw)
    # Measure the final re-opened GLB, not the pre-overlay kinematic input.
    from eonwild_motion.glb.animation import read_animation_tracks
    final=Glb(model_path);tracks,final_times=read_animation_tracks(final,names[0],require_common_timeline=True)
    checks=[]
    def final_pose(trs_tracks,time):
        ft=np.array(final.rest_translation,float);fq=np.array(final.rest_rotation,float);fs=np.array(final.rest_scale,float)
        targets={'translation':ft,'rotation':fq,'scale':fs}
        for (node,path),track in trs_tracks.items(): targets[path][node]=track.sample(float(time))
        return ft,fq,fs
    for time in np.linspace(0,times[-1],2*len(times)-1):
        ft,fq,fs=final_pose(tracks,time)
        world=seed.skin.world(ft,fq,fs);skin=seed.skin.skin(world)
        checks.append({'time_s':float(time),'minimum_skin_y_m':float(skin[:,1].min())})
    floor=min(c['minimum_skin_y_m'] for c in checks)
    loop_pos=float(np.max(np.abs(inplace[-1]-inplace[0])))
    dot=np.abs(np.sum(q[-1]*q[0],axis=1));loop_rot=float(np.max(2*np.arccos(np.clip(dot,-1,1))))
    validation={'status':'REVIEW_CANDIDATE_NOT_PRODUCTION','source_sha256':hashlib.sha256(source.raw).hexdigest(),'output_sha256':hashlib.sha256(raw).hexdigest(),'mesh_skin_material_accessors':'BYTE_PRESERVED','source_joint_count':len(source.document['skins'][0]['joints']),'output_joint_count':len(final.document['skins'][0]['joints']),'all_skin_influence_sets':len(seed.skin.weights[0])//4,'vertex_count':len(seed.skin.positions),'sample_hz':a.sample_hz,'samples':len(times),'reopened_keys_and_midpoints':len(checks),'minimum_full_skin_y_m':floor,'inplace_loop_translation_error_m':loop_pos,'loop_rotation_error_rad':loop_rot,'opensim_bridge':receipt['status'],'gait_generation':'AUTHORED_NOT_PREDICTED','force_or_muscle_validation':'NOT_RUN','continuous_contact_and_no_slip':'NOT_CERTIFIED','visual_approval':'PENDING','unity_parity':'NOT_RUN','production_approval':'NOT_GRANTED'}
    (a.output/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');(a.output/'full-skin-samples.json').write_text(json.dumps(checks,indent=2)+'\n')
    (a.output/'contacts.json').write_text(json.dumps({'authority':'planned animation cues, not confirmed world contact','samples':rows},indent=2)+'\n')
    runtime={'schema':'eonwild.biomechanics.transport-candidate.v1','source':profile['source'],'output_sha256':validation['output_sha256'],'animation_type':'Generic','source_frame':profile['coordinate'],'root_node':profile['roles']['root'],'clips':{'root_motion':names[0],'in_place':names[1],'standing':names[2]},'cycle_seconds':profile['authored_seed']['cycle_s'],'nominal_speed_m_s':profile['authored_seed']['stride_m']/profile['authored_seed']['cycle_s'],'unity_position_reflection':[-1,1,1],'unity_axial_vector_reflection':[1,-1,-1],'movement_owner':'choose either root motion OR motor-reconciled in-place; never both','unity_import_parity':'NOT_RUN','fbx_transport':'SEPARATE_UNVERIFIED_CONVERSION'}
    (a.output/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
    np.savez_compressed(a.output/'sampled-motion.npz',times=times,translations=t,rotations=q,scales=s)
    reference_tracks,_=read_animation_tracks(final,names[1],require_common_timeline=True)
    reference=[]
    for time in np.linspace(0,times[-1],9):
        ft,fq,fs=final_pose(reference_tracks,time);world=seed.skin.world(ft,fq,fs)
        reference.append({'time_s':float(time),'positions_gltf_m':{final.nodes[n]['name']:world[n,:3,3].tolist() for n in final.document['skins'][0]['joints']}})
    (a.output/'reference-poses.json').write_text(json.dumps({'output_sha256':validation['output_sha256'],'clip':names[1],'coordinate':profile['coordinate'],'poses':reference},indent=2)+'\n')
    import scipy
    implementation=[Path(__file__),ROOT/'src/eonwild_motion/biomechanics/kinematic_seed.py',ROOT/'src/eonwild_motion/biomechanics/opensim_bridge.py']
    manifest={'git_sha':os.environ.get('GITHUB_SHA','LOCAL_WORKING_FILES_HASHED_BELOW'),'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'implementation_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in implementation},'profile_sha256':hashlib.sha256(a.profile.read_bytes()).hexdigest()}
    (a.output/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if a.moco_smoke: print(moco_environment_smoke(a.output),flush=True)
    print(json.dumps(validation,indent=2),flush=True)
    if floor<-.002 or loop_pos>1e-4 or loop_rot>1e-4:raise RuntimeError('candidate diagnostic gate failed; retained evidence is not approved')
if __name__=='__main__':main()
