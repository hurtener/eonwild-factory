"""Render the real refreshed GLB and export an editable/FBX transport candidate.

Run with Blender --background --python this-file -- --package PACKAGE --output DIR.
No generated illustration, mesh replacement, timing changes or hidden rig reduction.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--views',nargs='+',default=['side','three-quarter','front'])
    parser.add_argument('--stills-only',action='store_true')
    parser.add_argument('--width',type=int,default=1280)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    runtime=json.loads((args.package/'runtime.json').read_text())
    source=args.package/'Alioramus-altai.refresh.glb'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=runtime['output_sha256']:
        raise RuntimeError('render input does not match candidate identity')
    args.output.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.fps=60;scene.render.fps_base=1.
    bpy.ops.import_scene.gltf(filepath=str(source))
    arms=[o for o in scene.objects if o.type=='ARMATURE']
    if len(arms)!=1:raise RuntimeError('expected one complete imported armature')
    arm=arms[0]
    for tr in arm.animation_data.nla_tracks:tr.mute=True
    meshes=[o for o in scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    if len(meshes)!=1:raise RuntimeError('expected one real skinned mesh')
    model=meshes[0]
    def choose(name):
        action=bpy.data.actions.get(name)
        if action is None:raise RuntimeError('requested clip absent')
        arm.animation_data.action=action
        arm.animation_data.action_slot=action.slots[0]
        bpy.context.view_layer.update()
    choose(runtime['clips']['in_place'])
    scene.frame_start=0;scene.frame_end=round(runtime['cycle_seconds']*60)
    scene.frame_set(0)
    scene.render.engine='BLENDER_WORKBENCH'
    scene.render.resolution_x=args.width;scene.render.resolution_y=round(args.width/1.6);scene.render.resolution_percentage=100
    scene.display.render_aa='8'
    shade=scene.display.shading;shade.light='STUDIO';shade.color_type='TEXTURE'
    shade.show_shadows=False;shade.show_cavity=True;shade.cavity_type='BOTH'
    shade.curvature_ridge_factor=1.25;shade.curvature_valley_factor=1.0
    shade.background_type='VIEWPORT';shade.background_color=(1,1,1);scene.world=bpy.data.worlds.new('Review white');scene.world.color=(1,1,1)
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0))
    floor=bpy.context.object;floor.name='Review floor (hidden; physical y=0 unchanged)';floor.hide_render=True;floor.hide_viewport=True
    camera_data=bpy.data.cameras.new('Review camera');camera=bpy.data.objects.new('Review camera',camera_data)
    scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO'
    cameras={'side':((-8,0,1.0),(0,0,.87),5.10),'three-quarter':((-7,-5,2.8),(0,0,.86),4.8),'front':((0,-8,1.05),(0,0,.83),2.95)}
    # Record actual imported joint heads: glTF->Blender is (x,-z,y).
    landmarks=[]
    reference=json.loads((args.package/'reference-poses.json').read_text())
    if reference['output_sha256']!=runtime['output_sha256'] or reference['clip']!=runtime['clips']['in_place']:
        raise RuntimeError('reference poses do not belong to this clip')
    parity=[]
    for expected in reference['poses']:
        time=expected['time_s']
        frame=time*60;scene.frame_set(math.floor(frame),subframe=frame%1)
        positions={b.name:list(arm.matrix_world@b.head) for b in arm.pose.bones}
        landmarks.append({'time_s':time,'positions_blender_m':positions})
        errors=[]
        for name,p in expected['positions_gltf_m'].items():
            target=Vector((p[0],-p[2],p[1]));errors.append((Vector(positions[name])-target).length)
        parity.append({'time_s':time,'maximum_joint_error_m':max(errors)})
    (args.output/'blender-joint-samples.json').write_text(json.dumps(landmarks,indent=2)+'\n')
    maximum=max(p['maximum_joint_error_m'] for p in parity)
    (args.output/'blender-import-parity.json').write_text(json.dumps({'scope':'nine imported Blender poses; not continuous or Unity validation','max_joint_error_m':maximum,'samples':parity},indent=2)+'\n')
    if maximum>1e-4:raise RuntimeError('Blender imported joint landmark gate failed')
    # Export full rig and three independent baked actions, preserving the source blend.
    choose(runtime['clips']['in_place']);scene.frame_set(0)
    for obj in scene.objects:obj.select_set(False)
    arm.select_set(True);model.select_set(True);bpy.context.view_layer.objects.active=arm
    fbx=args.output/'Alioramus-altai.refresh.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},
        add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,
        bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_step=1.,
        bake_anim_simplify_factor=0.,bake_anim_force_startend_keying=True,
        axis_forward='-Z',axis_up='Y',global_scale=1.,apply_unit_scale=True,
        path_mode='COPY',embed_textures=True)
    receipt={'source_sha256':runtime['output_sha256'],'blender':bpy.app.version_string,
        'skin_bones':len(arm.data.bones),'vertices':len(model.data.vertices),
        'source_cycle_s':runtime['cycle_seconds'],'video_fps':30,'mode':'native imported in-place action',
        'renderer':'Blender Workbench textured geometry review, not final PBR lighting',
        'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'fbx_unity_parity':'NOT_RUN','views':[]}
    for view in args.views:
        if view not in cameras:raise RuntimeError('unknown view')
        position,target,scale=cameras[view];camera.location=position
        camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=scale
        choose(runtime['clips']['standing']);scene.frame_set(0)
        scene.render.filepath=str(args.output/f'standing-{view}.png');bpy.ops.render.render(write_still=True)
        choose(runtime['clips']['in_place'])
        frames=[0,7,14,21,28,35] if args.stills_only else range(round(runtime['cycle_seconds']*30))
        folder=args.output/view;folder.mkdir(exist_ok=True)
        for index in frames:
            scene.frame_set(index*2)
            scene.render.filepath=str(folder/f'{index:04d}.png');bpy.ops.render.render(write_still=True)
        receipt['views'].append({'view':view,'camera_position':position,'target':target,'ortho_width':scale,'frames':len(frames)})
    position,target,scale=cameras['three-quarter'];camera.location=position
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=scale
    choose(runtime['clips']['in_place']);scene.frame_set(0)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'Alioramus-altai.refresh.blend'))
    (args.output/'render-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    # Reopen transport independently; this is not Unity acceptance.
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60
    bpy.ops.import_scene.fbx(filepath=str(fbx))
    reopened_arms=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    reopened_meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    actions=[{'name':a.name,'duration_s':float(a.frame_range[1]-a.frame_range[0])/60} for a in bpy.data.actions]
    fbx_check={'status':'FBX_REOPENED_NOT_UNITY_VALIDATED','sha256':receipt['fbx_sha256'],'bone_count':sum(len(a.data.bones) for a in reopened_arms),'actions':actions,'maximum_influences_per_vertex':max(len(v.groups) for m in reopened_meshes for v in m.data.vertices),'unity_parity':'NOT_RUN'}
    (args.output/'fbx-reopen.json').write_text(json.dumps(fbx_check,indent=2)+'\n')
    if len(reopened_arms)!=1 or fbx_check['bone_count']!=receipt['skin_bones'] or len(actions)!=3:
        raise RuntimeError('FBX reopen lost bones or actions')
    actual=sorted(round(a['duration_s'],6) for a in actions)
    if actual!=sorted([1.,round(runtime['cycle_seconds'],6),round(runtime['cycle_seconds'],6)]):
        raise RuntimeError('FBX changed native clip timing')
    print('REVIEW_EXPORT_COMPLETE',json.dumps(receipt),flush=True)

if __name__=='__main__':main()
