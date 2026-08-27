#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys,math,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation,Slerp
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'scripts'))
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap,AnatomicalBasis
from eonproc_v4.animation_reader import AnimationPackReader

def sample(values,phase):
    f=float(np.clip(phase,0,1))*(len(values)-1);i=int(math.floor(f));j=min(i+1,len(values)-1);u=f-i
    return Slerp([0,1],Rotation.from_quat(np.stack([values[i],values[j]])))([u]).as_quat()[0]
def qerr(a,b): return float(np.degrees(np.linalg.norm((Rotation.from_quat(a).inv()*Rotation.from_quat(b)).as_rotvec())))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--generated',required=True);ap.add_argument('--bone-map',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--player-js');ap.add_argument('--output',required=True);a=ap.parse_args()
 src=GlbAsset(a.source);gen=GlbAsset(a.generated);sem=SemanticMap.load(a.bone_map);basis=AnatomicalBasis.gltf_y_up(gen,sem);reader=AnimationPackReader(gen);manifest=json.load(open(a.manifest))
 names=list(reader.animations);assert len(names)==37,(len(names),names);assert len(set(names))==37;assert all('_V5' in n for n in names);assert not any('_V4' in n for n in names)
 sj,sib=src.skin_data();gj,gib=gen.skin_data();assert sj==gj;assert np.array_equal(sib,gib);assert len(gj)==75
 jaw=sem.bone('jaw');idx=gen.name_to_node[jaw];axis=gen.rest_world_rotation[idx].inv().apply(basis.lateral);axis/=np.linalg.norm(axis);rest=gen.rest_rotation[idx]
 def close_deg(anim,index):
  q=Rotation.from_quat(anim.rotations[jaw][index]);rv=(rest.inv()*q).as_rotvec();return -float(np.degrees(np.dot(rv,axis)))
 neutral_names=[n for n in names if any(k in n for k in ('WALK','TURN','START','BRAKE','IDLE')) and not reader.animations[n].extras.get('transition')]
 neutral_min=min(min(close_deg(reader.animation(n),i) for i in range(len(reader.animation(n).times))) for n in neutral_names)
 assert neutral_min>49.5,neutral_min
 bite=reader.animation('PROC_BITE_ATTACK_V5');contact=int(round(.56*(len(bite.times)-1)));bite_contact=close_deg(bite,contact);bite_end=close_deg(bite,-1);assert bite_contact>49.5 and bite_end>49.5,(bite_contact,bite_end)
 roar=reader.animation('PROC_ROAR_V5');roar_min=min(close_deg(roar,i) for i in range(len(roar.times)));roar_end=close_deg(roar,-1);assert roar_min<1.0 and roar_end>49.5,(roar_min,roar_end)
 eat=reader.animation('PROC_EAT_LOOP_V5');assert close_deg(eat,0)>49.5 and close_deg(eat,-1)>49.5
 max_endpoint_rot=0.;max_endpoint_pos=0.;transition_count=0
 for n,anim in reader.animations.items():
  assert np.all(np.diff(anim.times)>0),n
  if not anim.extras.get('transition'):continue
  transition_count+=1;s=reader.animation(anim.extras['sourceClip']);t=reader.animation(anim.extras['targetClip']);sp=float(anim.extras.get('sourcePhase',0));tp=float(anim.extras.get('targetPhase',0))
  for bone,vals in anim.rotations.items():
   sv=s.rotations.get(bone,t.rotations[bone]);tv=t.rotations.get(bone,s.rotations[bone]);max_endpoint_rot=max(max_endpoint_rot,qerr(vals[0],sample(sv,sp)),qerr(vals[-1],sample(tv,tp)))
  for node,vals in anim.translations.items():
   sv=s.translations.get(node,t.translations[node]);tv=t.translations.get(node,s.translations[node]);si=int(round(sp*(len(sv)-1)));ti=int(round(tp*(len(tv)-1)));max_endpoint_pos=max(max_endpoint_pos,float(np.max(np.abs(vals[0]-sv[si]))),float(np.max(np.abs(vals[-1]-tv[ti]))))
 assert transition_count==16;assert max_endpoint_rot<1e-4,max_endpoint_rot;assert max_endpoint_pos<1e-6,max_endpoint_pos
 mnames={x['name'] for x in manifest['clips']};assert mnames==set(names);assert manifest['jawCalibration']['close_degrees']==50.0
 player={}
 if a.player_js:
  js=Path(a.player_js).read_text();player={'activeButtons':'aria-pressed' in js and 'is-active' in js,'exactHandoff':'exactHandoff' in js or 'commitQueuedClip' in js,'noLegacyDoubleFade':'this.nextTime' not in js,'rootContinuity':'rootOffset' in js,'playState':'syncPlaybackUI' in js}
  assert all(player.values()),player
 result={'status':'PASS','clipCount':len(names),'transitionCount':transition_count,'skinJointCount':len(gj),'skinOrderPreserved':True,'inverseBindMatricesExact':True,'neutralJawMinimumCloseDegrees':neutral_min,'biteContactCloseDegrees':bite_contact,'biteEndCloseDegrees':bite_end,'roarMaximumGapeCloseDegrees':roar_min,'roarEndCloseDegrees':roar_end,'maxTransitionEndpointRotationErrorDegrees':max_endpoint_rot,'maxTransitionEndpointPositionError':max_endpoint_pos,'playerContract':player,'generatedSha256':hashlib.sha256(Path(a.generated).read_bytes()).hexdigest()}
 Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
