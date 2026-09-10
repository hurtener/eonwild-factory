"""Reopen the actual sequence GLB and check keys and interpolation midpoints."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.solve.skin_rig import SkinRig
package=Path(sys.argv[1]);baseline=json.loads(Path(sys.argv[2]).read_text())
source=Glb(Path(baseline['source']['path']))
emitted=Glb(package/'root_motion.glb')
runtime=json.loads((package/'runtime.json').read_text())
contact=json.loads(Path(baseline['contact_profile']['path']).read_text())
skin=SkinRig(source,runtime['rig_roles'],runtime['forward_axis'],runtime['up_axis'],contact)
tracks,keys=read_animation_tracks(emitted,emitted.document['animations'][0]['name'],require_common_timeline=True)
receipt=json.loads((package/'sequence-contact-samples.json').read_text())
rows=receipt['samples']
times=np.sort(np.concatenate((keys,(keys[:-1]+keys[1:])/2)))
floor=1e9;material=0.;worst={}; measured=0
for time in times:
 trs=[np.array(x,dtype=float) for x in (emitted.rest_translation,emitted.rest_rotation,emitted.rest_scale)]
 for (node,path),track in tracks.items():trs[{'translation':0,'rotation':1,'scale':2}[path]][node]=track.sample(float(time))
 points=skin.skin(skin.world(*trs))
 up_i=int(np.argmax(np.abs(runtime['up_axis'])))
 gap=float(points[:,up_i].min()-skin.ground)
 if gap<floor:floor=gap;worst['floor_time_s']=float(time)
 a=max(0,int(np.searchsorted(keys,time,side='right'))-1);b=min(a+1,len(keys)-1)
 for side in ('left','right'):
  r=rows[a][side]; nxt=rows[b][side]
  if not r['loaded']:continue
  if time>keys[a] and (not nxt['loaded'] or r['vertex_index']!=nxt['vertex_index'] or np.linalg.norm(np.array(r['anchor_m'])-nxt['anchor_m'])>1e-9):continue
  error=float(np.linalg.norm(points[r['vertex_index']]-r['anchor_m']));measured+=1
  if error>material:material=error;worst['material_time_s']=float(time);worst['material_side']=side
result={'status':'MEASURED_DIAGNOSTIC','glb_sha256':hashlib.sha256(emitted.raw).hexdigest(),
 'sample_count':len(times),'loaded_material_measurements':measured,
 'sampling':'all emitted keys and midpoints; material interpolation measured within unchanged support intervals',
 'minimum_full_mesh_gap_m':floor,'maximum_loaded_material_residual_m':material,
 'production_contact_pass':floor>=.0001 and material<=.0002,
 'worst':worst,'visual':'PENDING','serialized_dynamics_parity':'NOT_RUN'}
(package/'serialized-contact-measurement.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
