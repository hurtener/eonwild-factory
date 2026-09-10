"""Split proximal toe segments in admitted neutral geometry; never alter input assets."""
import argparse, json, hashlib
from copy import deepcopy
from pathlib import Path
import numpy as np
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _encode

def refine(source_path, rig_path, output):
 if output.exists(): raise ValueError('output already exists; preserve previous admission')
 g=Glb(source_path); rig=json.loads(rig_path.read_text())
 d=deepcopy(g.document); data=bytearray(g.binary)
 if d.get('animations'): d.pop('animations')
 worlds=np.array(_world_matrices(g,g.rest_translation,g.rest_rotation,g.rest_scale))
 additions=[]
 for side,leg in rig['roles']['legs'].items():
  for ordinal,chain in enumerate(leg['toeChains']):
   if len(chain)!=3: raise ValueError('refinement expects three-node source digit')
   parent,child=[g.name_to_node[n] for n in chain[:2]]
   name=f'PedalIntermediate.{side}.{ordinal}'
   if name in g.name_to_node: raise ValueError('already refined')
   node=len(d['nodes']); local=np.array(g.rest_translation[child])*.55
   d['nodes'].append({'name':name,'translation':local.tolist(),'children':[child]})
   children=d['nodes'][parent]['children']
   children[children.index(child)]=node
   d['nodes'][child]['translation']=(np.array(g.rest_translation[child])*.45).tolist()
   matrix=np.eye(4); matrix[:3,3]=local
   new_world=worlds[parent]@matrix
   additions.append((parent,child,node,name,new_world))
   chain.insert(1,name)
 for skin_i,skin in enumerate(d['skins']):
  original_joints=list(skin['joints'])
  ibms=np.array(g.accessor_values(skin['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
  indices={}
  expanded=list(ibms)
  for parent,child,node,name,nw in additions:
   if parent not in original_joints: continue
   pi=original_joints.index(parent);ni=len(skin['joints'])
   skin['joints'].append(node);indices[parent]=ni
   expanded.append(np.linalg.inv(nw)@worlds[parent]@ibms[pi])
  skin['inverseBindMatrices']=_append_accessor(d,data,np.array(expanded).transpose(0,2,1).reshape(-1,16),'MAT4')
  for meshnode in g.nodes:
   if meshnode.get('skin')!=skin_i or 'mesh' not in meshnode:continue
   meshidx=meshnode['mesh'];meshworld=worlds[g.nodes.index(meshnode)]
   for prim_i,primitive in enumerate(g.document['meshes'][meshidx]['primitives']):
    attrs=primitive['attributes']; positions=np.array(g.accessor_values(attrs['POSITION']))
    suffixes=sorted(int(k.split('_')[1]) for k in attrs if k.startswith('JOINTS_'))
    ji=np.concatenate([np.array(g.accessor_values(attrs[f'JOINTS_{s}']),dtype=int) for s in suffixes],axis=1)
    ws=np.concatenate([np.array(g.accessor_values(attrs[f'WEIGHTS_{s}']),dtype=float) for s in suffixes],axis=1)
    deform=worlds[original_joints]@ibms
    positions=np.einsum('vkij,vj,vk->vi',deform[ji],np.c_[positions,np.ones(len(positions))],ws)[:,:3]
    capacity=ji.shape[1]+4
    newj=np.zeros((len(ji),capacity),dtype=int);neww=np.zeros((len(ji),capacity))
    for v,(jrow,wrow) in enumerate(zip(ji,ws)):
     owners={}
     for j,weight in zip(jrow,wrow):
      if weight:owners[int(j)]=owners.get(int(j),0)+float(weight)
     for parent,child,node,name,nw in additions:
      if parent not in indices:continue
      pi=original_joints.index(parent);weight=owners.get(pi,0)
      if not weight:continue
      a=worlds[parent,:3,3];delta=worlds[child,:3,3]-a
      u=float((positions[v]-a)@delta/(delta@delta))
      gain=np.clip((u-.2)/.75,0,1);gain=gain*gain*(3-2*gain)
      owners[pi]=weight*(1-gain);owners[indices[parent]]=weight*gain
     selected=sorted(((j,v) for j,v in owners.items() if v>0),key=lambda kv:-kv[1])
     if len(selected)>capacity:raise ValueError('influence capacity exceeded')
     for k,(j,weight) in enumerate(selected):
      newj[v,k]=j;neww[v,k]=weight
    # glTF JOINTS require integer accessors.
    dest=d['meshes'][meshidx]['primitives'][prim_i]['attributes']
    for s in range(capacity//4):
     chunk=newj[:,4*s:4*s+4]
     while len(data)%4:data.append(0)
     offset=len(data);data.extend(chunk.astype('<u2').tobytes())
     view=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':chunk.size*2})
     accessor=len(d['accessors']);d['accessors'].append({'bufferView':view,'componentType':5123,'count':len(chunk),'type':'VEC4'})
     dest[f'JOINTS_{s}']=accessor;dest[f'WEIGHTS_{s}']=_append_accessor(d,data,neww[:,4*s:4*s+4],'VEC4')
 d['buffers'][0]['byteLength']=len(data)
 raw=_encode(d,data); output.mkdir(parents=True,exist_ok=False)
 (output/'source.glb').write_bytes(raw)
 rig['version']=rig['version']+1;rig['id']=rig['id'].rsplit('-v',1)[0]+f"-v{rig['version']}"
 rig['provenance']={'status':'engineering_candidate','purpose':'Additional intermediate deformation hinge; not fossil reconstruction','input_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest()}
 (output/'rig.json').write_text(json.dumps(rig,indent=2)+'\n')
 receipt={'source_sha256':hashlib.sha256(raw).hexdigest(),'new_joints':[x[3] for x in additions],'split_fraction':.55,'skin_transfer':'smooth projection onto split segment; all original influences conserved'}
 (output/'rig-refinement.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps(receipt))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path);p.add_argument('--rig',type=Path);p.add_argument('--output',type=Path);a=p.parse_args();refine(a.source,a.rig,a.output)
