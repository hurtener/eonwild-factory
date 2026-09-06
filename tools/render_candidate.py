"""Render actual serialized channels with Blender Cycles CPU; optionally FBX.

blender -b --python tools/render_candidate.py -- --package out/run --output out/review
The root-motion view follows the semantic root with its camera only. Ground,
mesh, animation, scale and contact floor stay unchanged. A reference package
may select a historical clip for comparison, never for motion generation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy
from mathutils import Vector

SOURCE_FPS = 120


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_frame(scene, value):
    frame = math.floor(value)
    scene.frame_set(frame, subframe=value - frame)


def area_light(scene, name, position, target, power, size):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy, data.size = power, size
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (target - position).to_track_quat('-Z', 'Y').to_euler()


def semantic_root(scene, runtime):
    name = runtime.get('rig_roles', {}).get('root')
    matches = [(obj, obj.pose.bones[name]) for obj in scene.objects
        if obj.type == 'ARMATURE' and name in obj.pose.bones]
    if len(matches) == 1:
        obj, bone = matches[0]
        return lambda: (obj.matrix_world @ bone.matrix).translation.copy()
    objects = [obj for obj in scene.objects if obj.name == name and obj.type != 'MESH']
    if len(objects) == 1:
        return lambda: objects[0].matrix_world.translation.copy()
    raise ValueError(f'cannot uniquely resolve the declared root for camera tracking: {name!r}')


def camera_spec(path, *, view, focus, center, position, root, scale):
    expected = {'schema', 'view', 'focus', 'center_relative_root', 'position_relative_root', 'orthographic_scale'}
    if path is not None and path.exists():
        value = json.loads(path.read_text())
        if set(value) != expected or value['schema'] != 'eonwild.motion.review-camera.v1' or value['view'] != view or value['focus'] != focus:
            raise ValueError('camera lock does not match this comparison view')
        for key in ('center_relative_root', 'position_relative_root'):
            if len(value[key]) != 3 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in value[key]):
                raise ValueError('invalid locked camera coordinates')
        scale = value['orthographic_scale']
        if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not math.isfinite(scale) or not 0 < scale < 1000:
            raise ValueError('invalid locked camera scale')
        return value
    value = {'schema': 'eonwild.motion.review-camera.v1', 'view': view, 'focus': focus,
        'center_relative_root': list(center - root), 'position_relative_root': list(position - root),
        'orthographic_scale': scale}
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Never replace an existing comparison camera.
        with path.open('x') as handle:
            json.dump(value, handle, indent=2)
            handle.write('\n')
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--view', choices=('side', 'three-quarter', 'front', 'rear'), default='three-quarter')
    parser.add_argument('--focus', choices=('body', 'feet'), default='body')
    parser.add_argument('--mode', choices=('root_motion', 'in_place'), default='in_place')
    parser.add_argument('--camera-lock', type=Path)
    parser.add_argument('--fps', type=int, default=24)
    parser.add_argument('--width', type=int, default=640)
    parser.add_argument('--samples', type=int, default=16)
    parser.add_argument('--fbx', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not 12 <= args.fps <= 120 or not 320 <= args.width <= 3840 or not 1 <= args.samples <= 256:
        raise ValueError('invalid review resolution, samples or frame rate')
    package, output = args.package.resolve(), args.output.resolve()
    source_name = args.mode + '.glb'
    source = package / source_name
    manifest = json.loads((package / 'manifest.json').read_text())
    if sha(source) != manifest['files'][source_name]:
        raise ValueError('candidate hash does not match its manifest')
    runtime = json.loads((package / 'runtime.json').read_text())
    if sha(package / 'runtime.json') != manifest['files']['runtime.json']:
        raise ValueError('runtime metadata hash mismatch')
    duration = float(runtime['duration_s'])
    if not math.isfinite(duration) or not 0 < duration <= 60:
        raise ValueError('review duration outside supported envelope')
    output.mkdir(parents=True, exist_ok=False)
    frames = output / 'frames'
    frames.mkdir()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = SOURCE_FPS, 1
    scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    if not meshes or not any(obj.type == 'ARMATURE' for obj in scene.objects):
        raise ValueError('candidate import has no rigged mesh')
    actions = list(bpy.data.actions)
    if not actions:
        raise ValueError('candidate import has no animation actions')
    start = min(float(action.frame_range[0]) for action in actions)
    end = max(float(action.frame_range[1]) for action in actions)
    if abs((end - start) / SOURCE_FPS - duration) > 2e-5:
        raise ValueError(f'imported duration changed: {(end-start)/SOURCE_FPS} != {duration}')
    count = max(2, int(math.ceil(duration * args.fps)))
    scene.frame_start, scene.frame_end = math.floor(start), round(end)
    set_frame(scene, start)
    root_position = semantic_root(scene, runtime)
    initial_root = root_position()
    exports = {}
    if args.fbx:
        if abs(start - round(start)) > .001 or abs(end - round(end)) > .001:
            raise ValueError('FBX transport requires endpoints on the declared 120 Hz grid')
        target = output / 'motion.fbx'
        bpy.ops.export_scene.fbx(filepath=str(target), object_types={'ARMATURE', 'MESH'},
            add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
            bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
            axis_forward='-Z', axis_up='Y', global_scale=1.0, apply_unit_scale=True,
            path_mode='COPY', embed_textures=True)
        exports['motion.fbx'] = sha(target)
    points = []
    for k in range(9):
        set_frame(scene, start + (end - start) * k / 8)
        shift = root_position() - initial_root if args.mode == 'root_motion' else Vector((0, 0, 0))
        deps = bpy.context.evaluated_depsgraph_get()
        for obj in meshes:
            evaluated = obj.evaluated_get(deps)
            points.extend(evaluated.matrix_world @ Vector(corner) - shift for corner in evaluated.bound_box)
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center, span = (low + high) / 2, max(high - low)
    if span <= 0:
        raise ValueError('degenerate candidate bounds')
    plane = runtime.get('ground_plane')
    if plane is None or plane['up_axis'] != 'Y':
        raise ValueError('this review scene requires an explicitly declared Y-up contact floor')
    ground_level = float(plane['level_m'])
    if not math.isfinite(ground_level):
        raise ValueError('invalid review floor')
    f = runtime['forward_axis']
    # glTF Y-up -> Blender Z-up, with no presentation scaling.
    forward = Vector((f[0], -f[2], f[1])).normalized()
    lateral = Vector((0, 0, 1)).cross(forward).normalized()
    offset = lateral + (forward * .65 if args.view == 'three-quarter' else Vector((0, 0, 0)))
    if args.view in ('front', 'rear'):
        offset = forward * (1 if args.view == 'front' else -1)
    if args.focus == 'feet':
        # Framing only. The declared floor is never fitted to the bounds.
        height = float(runtime.get('body_height_m', max(.1, (high.z - ground_level) * .55)))
        center = Vector((initial_root.x, initial_root.y, ground_level + .45 * height))
        span = 2.4 * height
    position = center + offset.normalized() * span * 1.65 + Vector((0, 0, span * .25))
    spec = camera_spec(args.camera_lock, view=args.view, focus=args.focus, center=center,
        position=position, root=initial_root, scale=span * 1.28)
    camera_base = initial_root + Vector(spec['position_relative_root'])
    camera_center = initial_root + Vector(spec['center_relative_root'])
    (output / 'camera.json').write_text(json.dumps(spec, indent=2) + '\n')
    camera_data = bpy.data.cameras.new('ReviewCamera')
    camera = bpy.data.objects.new('ReviewCamera', camera_data)
    scene.collection.objects.link(camera)
    camera.location = camera_base
    camera.rotation_euler = (camera_center - camera_base).to_track_quat('-Z', 'Y').to_euler()
    camera_data.type, camera_data.ortho_scale = 'ORTHO', spec['orthographic_scale']
    camera_data.clip_end = max(1000., span * 10)
    scene.camera = camera
    bpy.ops.mesh.primitive_plane_add(size=max(span * 12, 100), location=(initial_root.x, initial_root.y, ground_level))
    ground = bpy.context.object
    ground.name = 'ReviewGround'
    material = bpy.data.materials.new('ReviewGroundMaterial')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .85
    geometry = nodes.new('ShaderNodeNewGeometry')
    checker = nodes.new('ShaderNodeTexChecker')
    checker.inputs['Scale'].default_value = 2.
    checker.inputs['Color1'].default_value = (.18, .20, .22, 1)
    checker.inputs['Color2'].default_value = (.23, .25, .27, 1)
    links.new(geometry.outputs['Position'], checker.inputs['Vector'])
    links.new(checker.outputs['Color'], bsdf.inputs['Base Color'])
    ground.data.materials.append(material)
    if scene.world is None:
        scene.world = bpy.data.worlds.new('ReviewWorld')
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value = (.32, .36, .42, 1)
    background.inputs['Strength'].default_value = .45
    area_light(scene, 'Key', center + lateral * span * .7 + Vector((0, 0, span)), center, span * span * 90, span * .8)
    area_light(scene, 'Fill', center - lateral * span * .8 + forward * span * .4 + Vector((0, 0, span * .5)), center, span * span * 35, span)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples, scene.cycles.seed = args.samples, 0
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces, scene.cycles.diffuse_bounces, scene.cycles.glossy_bounces = 3, 2, 2
    scene.render.use_persistent_data = True
    scene.render.threads_mode, scene.render.threads = 'FIXED', 2
    scene.render.resolution_x = args.width
    scene.render.resolution_y = int(args.width * 9 / 16) // 2 * 2
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    timeline = []
    for index in range(count):
        time = index / args.fps
        set_frame(scene, start + time * SOURCE_FPS)
        shift = root_position() - initial_root if args.mode == 'root_motion' else Vector((0, 0, 0))
        camera.location = camera_base + shift
        scene.render.filepath = str(frames / f'{index:05d}.png')
        bpy.ops.render.render(write_still=True)
        timeline.append({'index': index, 'source_time_s': time, 'blender_frame': start + time * SOURCE_FPS,
            'camera_translation_m': list(shift)})
    (output / 'timeline.json').write_text(json.dumps(timeline, indent=2) + '\n')
    video = output / 'preview.mp4'
    subprocess.run(['ffmpeg', '-y', '-framerate', str(args.fps), '-i', str(frames / '%05d.png'),
        '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate', '-of', 'json', str(video)], text=True))['streams'][0]
    if int(probe['nb_read_frames']) != count:
        raise ValueError('encoded preview has missing or extra frames')
    numerator, denominator = map(int, probe['r_frame_rate'].split('/'))
    if numerator != args.fps * denominator:
        raise ValueError('encoded preview changed the native review frame rate')
    cover = output / 'cover.png'
    cover.write_bytes((frames / f'{count // 3:05d}.png').read_bytes())
    receipt = {'schema': 'eonwild.motion.review-render.v2', 'source_sha256': sha(source),
        'manifest_sha256': sha(package / 'manifest.json'), 'renderer_sha256': sha(Path(__file__)),
        'source_kind': manifest.get('kind', 'unapproved_candidate'), 'technical_status': manifest.get('technical_status', 'NOT_EVALUATED'),
        'blender': bpy.app.version_string, 'engine': 'CYCLES_CPU', 'samples': args.samples, 'denoising': False,
        'fps': args.fps, 'frames': count, 'verified_encoded_frames': int(probe['nb_read_frames']),
        'source_duration_s': duration, 'encoded_duration_s': count / args.fps,
        'source_frame_start': start, 'source_frame_end': end, 'source_fps': SOURCE_FPS,
        'timing': 'native-time sampling; no speed adjustment; video omits duplicate loop endpoint',
        'mode': args.mode, 'view': args.view, 'focus': args.focus, 'camera': spec,
        'media': {name: sha(output / name) for name in ('preview.mp4', 'cover.png', 'camera.json', 'timeline.json')},
        'exports': exports, 'visual_approval': 'PENDING', 'unity_import_validation': 'NOT_RUN',
        'ground_level_m': ground_level,
        'presentation': 'fixed declared floor and 0.5 m world checker; camera-only root tracking; no bbox floor fitting or animal rescaling'}
    (output / 'render-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
