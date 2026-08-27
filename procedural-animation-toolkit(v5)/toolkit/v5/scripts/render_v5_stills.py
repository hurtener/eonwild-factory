from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];V5=ROOT/'toolkit/v5';sys.path.insert(0,str(V5/'scripts'))
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader
from eonproc_v4.locomotion import TerrainAwareLocomotionGenerator
from eonproc_v4.profile import BipedV4Profile
from eonproc_v4.terrain import FlatTerrain
from render_v5_validation import V5Renderer
source=GlbAsset(ROOT/'inputs/tarbosaurus_source.glb');animated=GlbAsset(ROOT/'validated_result/v5/tarbosaurus_procedural_v5_animation_pack.glb');v4=GlbAsset(ROOT/'validated_result/v4/tarbosaurus_procedural_v4_animation_pack.glb');sem=SemanticMap.load(ROOT/'inputs/tarbosaurus_bone_map.edited.yml');gen=TerrainAwareLocomotionGenerator(source,sem,BipedV4Profile());terrain=FlatTerrain(gen.mesh_ground);renderer=V5Renderer(source,gen,520,292,ROOT/'validated_result/v5/showcase');pack=AnimationPackReader(animated);pack4=AnimationPackReader(v4);root_rest=source.rest_translation[source.name_to_node[gen.root]]
out=ROOT/'validated_result/v5/showcase';out.mkdir(exist_ok=True)

def frame(reader,name,phase,view='threeq'):
 a=reader.animation(name);t=a.duration*phase;world=reader.world_matrices_at(a,t);r,lat,fwd=renderer.set_pose(world,False);return renderer.render(r,lat,fwd,view)
def montage(name,title,items,cols=4):
 ims=[]
 for label,reader,clip,phase,view in items:
  im=frame(reader,clip,phase,view);d=ImageDraw.Draw(im);d.rectangle((0,0,230,29),fill=(245,245,241));d.text((8,8),label,fill=(20,25,23));ims.append(im)
 rows=(len(ims)+cols-1)//cols;canvas=Image.new('RGB',(520*cols,292*rows),(240,241,238));d=ImageDraw.Draw(canvas);d.rectangle((0,0,canvas.width,32),fill=(16,26,24));d.text((12,10),title,fill=(242,230,190));
 # leave header overlay by pasting from y32? easiest increase canvas
 canvas2=Image.new('RGB',(canvas.width,canvas.height+36),(240,241,238));canvas2.paste(canvas,(0,36));d=ImageDraw.Draw(canvas2);d.rectangle((0,0,canvas2.width,36),fill=(16,26,24));d.text((12,12),title,fill=(242,230,190))
 for i,im in enumerate(ims):canvas2.paste(im,((i%cols)*520,36+(i//cols)*292))
 path=out/name;canvas2.save(path,quality=88);print(path)
montage('v5_idle_keyframes.jpg','V5 living-neutral idle — mouth remains closed',[(f'{p:.0%}',pack,'PROC_IDLE_BREATH_V5',p,'threeq') for p in (0,.25,.5,.75)],4)
montage('v5_eat_keyframes.jpg','V5 eating — open, contact, chew, complete closure between bites',[(f'phase {p:.2f}',pack,'PROC_EAT_LOOP_V5',p,'threeq') for p in (.02,.07,.12,.16,.20,.24,.27,.32)],4)
montage('v5_bite_keyframes.jpg','V5 bite — anticipation, open delivery, full contact closure, recovery',[(f'phase {p:.2f}',pack,'PROC_BITE_ATTACK_V5',p,'threeq') for p in (0,.18,.30,.44,.54,.56,.68,1)],4)
montage('v5_roar_keyframes.jpg','V5 roar — intentional gape only during display, then full neutral closure',[(f'phase {p:.2f}',pack,'PROC_ROAR_V5',p,'threeq') for p in (0,.24,.42,.58,.78,.94,1)],4)
montage('v4_v5_jaw_comparison.jpg','Living-neutral jaw comparison — V4 generic 33° vs V5 calibrated 50°',[
 ('V4 idle · visible gape',pack4,'PROC_IDLE_BREATH_V4',.25,'side'),('V5 idle · closed',pack,'PROC_IDLE_BREATH_V5',.25,'side'),('V4 walk · visible gape',pack4,'PROC_WALK_RELAXED_V4_INPLACE',.25,'side'),('V5 walk · closed',pack,'PROC_WALK_RELAXED_V5_INPLACE',.25,'side')],4)
montage('v5_transition_endpoint_check.jpg','V5 exact handoff endpoints — authored transition end equals following clip start',[
 ('walk→bite end',pack,'PROC_WALK_TO_BITE_READY_V5',1,'threeq'),('bite start',pack,'PROC_BITE_ATTACK_V5',0,'threeq'),('bite end',pack,'PROC_BITE_ATTACK_V5',1,'threeq'),('bite→walk start',pack,'PROC_BITE_TO_WALK_V5',0,'threeq'),
 ('walk→roar end',pack,'PROC_WALK_TO_ROAR_READY_V5',1,'threeq'),('roar start',pack,'PROC_ROAR_V5',0,'threeq'),('roar end',pack,'PROC_ROAR_V5',1,'threeq'),('roar→walk start',pack,'PROC_ROAR_TO_WALK_V5',0,'threeq')],4)
