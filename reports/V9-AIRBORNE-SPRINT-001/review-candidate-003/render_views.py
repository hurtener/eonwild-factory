"""Native-cadence whole-body side/front/rear review, one loop per view."""
import argparse
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from src.eonwild_motion.blender.render_walk_review import import_character, frame_camera, add_review_ground, _mesh_objects

parser=argparse.ArgumentParser()
parser.add_argument('--candidate',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--ground',type=float,required=True)
parser.add_argument('--view',choices=['side','front','rear'],required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.fps=24
_,objects,timeline=import_character(args.candidate,'V9_AIRBORNE_RUN_IN_PLACE',23,24)
armature=max((o for o in objects if o.type=='ARMATURE'),key=lambda o:len(o.data.bones))
strip=armature.animation_data.nla_tracks['v9-walk-review-loop'].strips[0]
if abs(float(strip.scale)-1)>1e-4:
    raise RuntimeError(f'Native 23-frame Sprint cycle was rescaled: {strip.scale}')
timeline['nla_scene_start']=float(strip.frame_start)
timeline['source_time_formula']='(action_frame_start + (scene_frame - nla_scene_start) / presentation_scale) / fps'
timeline['rendered_samples']=[{'scene_frame':f,'source_time_s':(strip.action_frame_start+(f-strip.frame_start)/strip.scale)/24} for f in range(1,24)]
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.light='STUDIO'
scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='WORLD'
scene.render.resolution_x=1100
scene.render.resolution_y=620
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('sprint-review-world')
scene.world.color=(.065,.075,.075)
scene.frame_start,scene.frame_end=1,23
bounds=[]
for frame in range(1,24):
    scene.frame_set(frame);bpy.context.view_layer.update()
    for obj in _mesh_objects(objects):
        bounds.extend(obj.matrix_world@Vector(c) for c in obj.bound_box)
scene.frame_set(1)
add_review_ground(objects,canonical_ground_y=args.ground)
camera_data=bpy.data.cameras.new('sprint-review-camera');camera_data.type='ORTHO'
camera=bpy.data.objects.new('sprint-review-camera',camera_data)
bpy.context.collection.objects.link(camera);scene.camera=camera
# glTF Y-up forward +Z maps to Blender forward -Y. Small elevation shows feet.
direction={'side':Vector((1,0,.035)),'front':Vector((.04,-1,.08)),'rear':Vector((-.04,1,.08))}[args.view]
facts=frame_camera(camera,direction,objects,1100/620,extra_points=bounds)
camera.data.ortho_scale=max(facts['horizontalSpan'],facts['verticalSpan']*1100/620)*1.18
facts.update(orthoScale=camera.data.ortho_scale,view=args.view,direction=list(direction))
args.output.mkdir(parents=True,exist_ok=False)
(args.output/'render-receipt.json').write_text(json.dumps({'status':'USER_REVIEW_CANDIDATE_NOT_ACCEPTED','timeline':timeline,'camera':facts,'ground':args.ground,'frames':23,'fps':24,'source':str(args.candidate)},indent=2)+'\n')
scene.render.filepath=str(args.output/'frame-')
bpy.ops.render.render(animation=True)
