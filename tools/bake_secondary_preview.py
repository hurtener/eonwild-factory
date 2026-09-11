"""Bake the portable consumer layer into a NEW Blender-readable preview GLB.

Never used as input to locomotion generation; does not overwrite admitted motion.
"""
import argparse,json,hashlib,struct
from pathlib import Path
import numpy as np
from eonwild_motion.embodiment import validate,SecondaryState,joints
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.math.quaternion import multiply,from_rotation_vector
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--motion',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hz',type=int,default=60);a=p.parse_args()
if a.output.resolve()==a.motion.resolve():raise ValueError('Preview must not overwrite source')
d=json.loads(a.profile.read_text());g=Glb(a.motion);validate(d,[n.get('name','') for n in g.nodes])
if hashlib.sha256(g.raw).hexdigest()!=d['source']['motionSha256']:raise ValueError('Motion hash mismatch')
tracks,_=read_animation_tracks(g,g.document['animations'][0]['name'],require_common_timeline=False)
roles={b['role']:g.name_to_node[b['bone']] for b in d['bindings']};specs=joints(d);indices=[roles[j['role']] for j in specs]
def pose(time):
 trs=[list(g.rest_translation),list(g.rest_rotation),list(g.rest_scale)]
 for (idx,kind),track in tracks.items():trs[['translation','rotation','scale'].index(kind)][idx]=track.sample(time)
 return trs,_world_matrices(g,*trs)
q=d['sequence'];forward=np.array([0.,0.,1.]);span=.1
for time in np.linspace(q['walkStart'],q['walkEnd'],17):
 _,w=pose(time);span=max(span,abs(np.dot(np.array(w[roles['leftFoot']])[:3,3]-np.array(w[roles['rightFoot']])[:3,3],forward)))
state=SecondaryState(d);times=np.linspace(0,q['duration'],int(np.ceil(q['duration']*a.hz))+1);rotations=[[] for _ in specs];previous=None
for k,time in enumerate(times):
 trs,w=pose(time);root=np.array(w[roles['root']])[:3,3];dt=0 if k==0 else time-times[k-1];travel=np.zeros(3) if previous is None else root-previous;travel[1]=0;previous=root
 signal=np.dot(np.array(w[roles['leftFoot']])[:3,3]-np.array(w[roles['rightFoot']])[:3,3],forward)/span
 angles=state.step(float(dt),0 if dt==0 else float(np.linalg.norm(travel)/dt),float(signal))
 for i,(node,j,angle) in enumerate(zip(indices,specs,angles)):
  rotations[i].append(multiply(trs[1][node],from_rotation_vector(np.array(j['axis'])*np.deg2rad(angle))).tolist())
doc=g.document;binary=bytearray(g.binary)
def accessor(values,width):
 while len(binary)%4:binary.append(0)
 data=np.asarray(values,dtype='<f4');offset=len(binary);binary.extend(data.tobytes());vi=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':data.nbytes});ai=len(doc['accessors']);entry={'bufferView':vi,'componentType':5126,'count':len(values),'type':'SCALAR' if width==1 else 'VEC4'}
 if width==1:entry.update(min=[float(data.min())],max=[float(data.max())])
 doc['accessors'].append(entry);return ai
animation=doc['animations'][0];animation['channels']=[c for c in animation['channels'] if not(c['target']['node'] in indices and c['target']['path']=='rotation')];ti=accessor(times,1)
for node,values in zip(indices,rotations):
 si=len(animation['samplers']);animation['samplers'].append({'input':ti,'output':accessor(values,4),'interpolation':'LINEAR'});animation['channels'].append({'sampler':si,'target':{'node':node,'path':'rotation'}})
doc.setdefault('extras',{})['secondaryPreview']={'profileSha256':hashlib.sha256(a.profile.read_bytes()).hexdigest(),'sourceMotionSha256':d['source']['motionSha256'],'status':'consumer preview only; attention excluded; not contact-certified'};doc['buffers'][0]['byteLength']=len(binary)
raw=json.dumps(doc,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);binary+=b'\0'*((-len(binary))%4);result=struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result);Glb(a.output);print(a.output)
