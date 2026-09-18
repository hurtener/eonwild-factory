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

# Blender does not reliably add a --python script's directory to sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from eonwild_motion.blender.native_playback import (
    import_gltf_for_native_playback,
    requires_exact_cubic_playback,
)
from preview_clock import SOURCE_FPS, source_frame, transport_clock
from review_timing import native_sample_times, native_still_times


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_frame(scene, value, *, playback=None, source_time_s=None):
    frame = math.floor(value)
    scene.frame_set(frame, subframe=value - frame)
    if playback is not None:
        if source_time_s is None:
            raise ValueError('exact native playback requires source seconds')
        playback.apply(source_time_s)


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


def export_transport(scene, actions, clock, target):
    """Export and reopen one unit-scale, zero-based FBX transport strip."""
    matching = [action for action in actions if abs(float(action.frame_range[0]) - clock.source_start_frame) <= 64 * math.ulp(max(1., abs(clock.source_start_frame)))
        and abs(float(action.frame_range[1]) - clock.source_end_frame) <= 64 * math.ulp(max(1., abs(clock.source_end_frame)))]
    if len(matching) != 1:
        raise ValueError('FBX transport requires one action spanning the declared source clock')
    armatures = [obj for obj in scene.objects if obj.type == 'ARMATURE']
    if len(armatures) != 1:
        raise ValueError('FBX transport requires one imported armature')
    armature = armatures[0]
    armature.animation_data_create()
    armature.animation_data.action = None
    track = armature.animation_data.nla_tracks.new()
    # Blender's creation API requires an integer placement even though the
    # resulting strip endpoints are floating point.
    strip = track.strips.new('FactoryTransport', int(clock.transport_start_frame), matching[0])
    strip.action_frame_start = clock.source_start_frame
    strip.action_frame_end = clock.source_end_frame
    strip.frame_start = clock.transport_start_frame
    strip.frame_end = clock.transport_end_frame
    strip.blend_type = 'REPLACE'
    strip.extrapolation = 'NOTHING'
    strip.use_animated_time = False
    if abs(strip.scale - 1.0) > 64 * math.ulp(1.0):
        raise ValueError(f'FBX transport would retime source action: NLA scale {strip.scale}')
    nla_scale = float(strip.scale)
    bpy.ops.export_scene.fbx(filepath=str(target), object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=True, bake_anim_step=clock.bake_step_frames,
        bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0,
        axis_forward='-Z', axis_up='Y', global_scale=1.0, apply_unit_scale=True,
        path_mode='COPY', embed_textures=True)
    # This is transport evidence only; it does not establish Unity parity.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    reopened = bpy.context.scene
    reopened.render.fps, reopened.render.fps_base = clock.source_fps, 1
    bpy.ops.import_scene.fbx(filepath=str(target))
    imported = list(bpy.data.actions)
    if not imported:
        raise ValueError('FBX transport reopened without animation')
    start = min(float(action.frame_range[0]) for action in imported)
    end = max(float(action.frame_range[1]) for action in imported)
    tolerance = 64 * math.ulp(max(1., abs(clock.transport_end_frame)))
    # Blender's importer presents an FBX zero timestamp at frame 1.  Preserve
    # that documented import origin, and measure the actual reopened interval
    # rather than falsely demanding a Blender-frame zero.
    if abs((end - start) - clock.duration_frames) > tolerance:
        raise ValueError(f'FBX transport duration changed on reopen: {end - start} != {clock.duration_frames}')
    return {'sha256': sha(target), 'nla_scale': nla_scale, 'reopened_status': 'PASS',
        'reopened_frame_start': start, 'reopened_frame_end': end,
        'reopened_duration_s': (end - start) / clock.source_fps}


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


def projected_camera_frame(points, *, viewing_direction, fallback_center, fallback_span, aspect):
    """Return a full-body orthographic frame for one declared view direction.

    Bounds are projected onto the camera plane once, over the complete native
    clip.  They only choose a camera target and scale; scene transforms, floor
    and root tracking remain untouched.
    """
    direction = viewing_direction.normalized()
    right = direction.cross(Vector((0, 0, 1)))
    if right.length < 1e-8:
        raise ValueError('review camera direction is parallel to world up')
    right.normalize()
    up = right.cross(direction).normalized()
    horizontal = [point.dot(right) for point in points]
    vertical = [point.dot(up) for point in points]
    depth = [point.dot(direction) for point in points]
    left, right_edge = min(horizontal), max(horizontal)
    bottom, top = min(vertical), max(vertical)
    depth_center = (min(depth) + max(depth)) / 2
    target = right * ((left + right_edge) / 2) + up * ((bottom + top) / 2) + direction * depth_center
    projected_height = max(1e-6, top - bottom)
    projected_width = max(1e-6, right_edge - left)
    # 8% room keeps tail/feet readable without fitting individual frames.
    # Blender's landscape orthographic_scale is the visible width.  Constrain
    # both projected width and height, rather than treating it as height.
    scale = max(projected_width, projected_height * aspect) * 1.08
    if not math.isfinite(scale) or scale <= 0:
        return fallback_center, fallback_span * 1.28
    return target, scale


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
    parser.add_argument('--still-times', type=float, nargs='+',
                        help='render only these exact native source seconds; no film or FBX')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not 12 <= args.fps <= 120 or not 320 <= args.width <= 3840 or not 1 <= args.samples <= 256:
        raise ValueError('invalid review resolution, samples or frame rate')
    package, output = args.package.resolve(), args.output.resolve()
    source_name = args.mode + '.glb'
    source = package / source_name
    manifest_path = package / 'manifest.json'
    manifest_sha = sha(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    source_sha = sha(source)
    if source_sha != manifest['files'][source_name]:
        raise ValueError('candidate hash does not match its manifest')
    runtime = json.loads((package / 'runtime.json').read_text())
    if sha(package / 'runtime.json') != manifest['files']['runtime.json']:
        raise ValueError('runtime metadata hash mismatch')
    duration = runtime['duration_s']
    still_mode = args.still_times is not None
    if still_mode and args.fbx:
        raise ValueError('native still diagnosis cannot export FBX')
    if args.fbx and requires_exact_cubic_playback(source):
        raise ValueError(
            'FBX transport is unsupported for task-owned CUBICSPLINE sampling; '
            'native source-time rendering does not create authoritative Blender curves'
        )
    sample_times = (native_still_times(duration, args.still_times) if still_mode
                    else native_sample_times(duration, args.fps))
    if not math.isfinite(duration) or not 0 < duration <= 60:
        raise ValueError('review duration outside supported envelope')
    output.mkdir(parents=True, exist_ok=False)
    frames = output / 'frames'
    frames.mkdir()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = SOURCE_FPS, 1
    scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1
    playback = import_gltf_for_native_playback(source)
    # Blender's glTF importer owns its action-frame representation and may
    # reset scene FPS (currently 24).  Seconds remain the package authority;
    # never mistake the factory's 120 Hz plan samples for imported frame IDs.
    action_fps = scene.render.fps / scene.render.fps_base
    if not math.isfinite(action_fps) or action_fps <= 0:
        raise ValueError('imported action has invalid frame clock')
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    if not meshes or not any(obj.type == 'ARMATURE' for obj in scene.objects):
        raise ValueError('candidate import has no rigged mesh')
    actions = list(bpy.data.actions)
    if not actions:
        raise ValueError('candidate import has no animation actions')
    start = min(float(action.frame_range[0]) for action in actions)
    end = max(float(action.frame_range[1]) for action in actions)
    clock = transport_clock(start, end, duration, action_fps)
    source_duration = clock.duration_s
    count = len(sample_times)
    scene.frame_start, scene.frame_end = math.floor(start), round(end)
    set_frame(scene, start, playback=playback, source_time_s=0.0)
    root_position = semantic_root(scene, runtime)
    initial_root = root_position()
    exports = {}
    points = []
    # Camera coverage is a whole-clip claim: inspect every native review
    # sample and the exact source endpoint, never nine representative probes.
    for time in [*sample_times, source_duration]:
        set_frame(scene, start + time * action_fps, playback=playback, source_time_s=time)
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
    # The side/end-on views need their own projected fit.  A tail's world
    # length is horizontal in a side view, not a reason to make its height
    # occupy only a small fraction of the film.  Feet focus remains an
    # explicit close diagnostic crop.
    aspect = 16 / 9
    if args.focus == 'body':
        viewing_direction = (offset.normalized() * 1.65 + Vector((0, 0, .25))).normalized()
        center, scale = projected_camera_frame(points, viewing_direction=viewing_direction,
            fallback_center=center, fallback_span=span, aspect=aspect)
    else:
        scale = span * 1.28
        viewing_direction = (offset.normalized() * 1.65 + Vector((0, 0, .25))).normalized()
    position = center + viewing_direction * max(span, scale) * 1.65
    spec = camera_spec(args.camera_lock, view=args.view, focus=args.focus, center=center,
        position=position, root=initial_root, scale=scale)
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
    for index, time in enumerate(sample_times):
        set_frame(scene, start + time * action_fps, playback=playback, source_time_s=time)
        shift = root_position() - initial_root if args.mode == 'root_motion' else Vector((0, 0, 0))
        camera.location = camera_base + shift
        scene.render.filepath = str(frames / f'{index:05d}.png')
        bpy.ops.render.render(write_still=True)
        timeline.append({'index': index, 'source_time_s': time, 'blender_frame': source_frame(start, time, action_fps),
            'camera_translation_m': list(shift)})
    (output / 'timeline.json').write_text(json.dumps(timeline, indent=2) + '\n')
    if still_mode:
        source_after = sha(source)
        manifest_after = sha(manifest_path)
        if source_after != source_sha or manifest_after != manifest_sha:
            raise ValueError('candidate package changed during still diagnosis')
        stills = [{**row, 'file': f"frames/{row['index']:05d}.png",
            'sha256': sha(frames / f"{row['index']:05d}.png")} for row in timeline]
        receipt = {'schema': 'eonwild.motion.review-stills.v1',
            'source_sha256': source_after, 'manifest_sha256': manifest_after,
            'renderer_sha256': sha(Path(__file__)),
            'timing_sampler_sha256': sha(Path(__file__).with_name('review_timing.py')),
            'source_kind': manifest.get('kind', 'unapproved_candidate'),
            'technical_status': manifest.get('technical_status', 'NOT_EVALUATED'),
            'blender': bpy.app.version_string, 'engine': 'CYCLES_CPU',
            'samples': args.samples, 'denoising': False,
            'declared_duration_s': duration, 'source_duration_s': source_duration,
            'source_frame_start': start, 'source_frame_end': end, 'source_fps': action_fps,
            'requested_native_times_s': sample_times, 'stills': stills,
            'mode': args.mode, 'view': args.view, 'focus': args.focus, 'camera': spec,
            'media': {'camera.json': sha(output / 'camera.json'),
                      'timeline.json': sha(output / 'timeline.json')},
            'diagnostic_scope': 'requested native-time stills only; no encoded film or full-cycle review claim',
            'visual_approval': 'PENDING', 'unity_import_validation': 'NOT_RUN',
            'ground_level_m': ground_level,
            'presentation': 'fixed declared floor and 0.5 m world checker; camera-only root tracking; no bbox floor fitting or animal rescaling'}
        if playback is not None:
            receipt['native_playback'] = playback.receipt()
        (output / 'render-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))
        return
    terminal = None
    if runtime.get('loop') is False:
        set_frame(scene, start + source_duration * action_fps,
                  playback=playback, source_time_s=source_duration)
        shift = root_position() - initial_root if args.mode == 'root_motion' else Vector((0, 0, 0))
        camera.location = camera_base + shift
        scene.render.filepath = str(output / 'terminal.png')
        bpy.ops.render.render(write_still=True)
        terminal = {'source_time_s': source_duration, 'sha256': sha(output / 'terminal.png')}
    video = output / 'preview.mp4'
    subprocess.run(['ffmpeg', '-y', '-framerate', str(args.fps), '-i', str(frames / '%05d.png'),
        '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(video)], check=True)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=nb_read_frames,width,height,r_frame_rate', '-of', 'json', str(video)], text=True))['streams'][0]
    if int(probe['nb_read_frames']) != count:
        raise ValueError('encoded preview has missing or extra frames')
    numerator, denominator = map(int, probe['r_frame_rate'].split('/'))
    if numerator != args.fps * denominator:
        raise ValueError('encoded preview changed the fixed review frame rate')
    cover = output / 'cover.png'
    cover.write_bytes((frames / f'{count // 3:05d}.png').read_bytes())
    if args.fbx:
        exports['motion.fbx'] = export_transport(scene, actions, clock, output / 'motion.fbx')
    receipt = {'schema': 'eonwild.motion.review-render.v2', 'source_sha256': sha(source),
        'manifest_sha256': sha(package / 'manifest.json'), 'renderer_sha256': sha(Path(__file__)),
        'timing_sampler_sha256': sha(Path(__file__).with_name('review_timing.py')),
        'source_kind': manifest.get('kind', 'unapproved_candidate'), 'technical_status': manifest.get('technical_status', 'NOT_EVALUATED'),
        'blender': bpy.app.version_string, 'engine': 'CYCLES_CPU', 'samples': args.samples, 'denoising': False,
        'fps': args.fps, 'frames': count, 'verified_encoded_frames': int(probe['nb_read_frames']),
        'declared_duration_s': duration, 'source_duration_s': source_duration, 'encoded_duration_s': count / args.fps,
        'source_frame_start': start, 'source_frame_end': end, 'source_fps': action_fps,
        'factory_sample_hz': SOURCE_FPS,
        'transport_clock': clock.receipt() if args.fbx else None,
        'timing': 'fixed-rate preview evaluates immutable source seconds on [0,duration); no speed adjustment or duplicate endpoint',
        'terminal_pose': terminal,
        'mode': args.mode, 'view': args.view, 'focus': args.focus, 'camera': spec,
        'media': {name: sha(output / name) for name in ('preview.mp4', 'cover.png', 'camera.json', 'timeline.json')},
        'exports': exports, 'visual_approval': 'PENDING', 'unity_import_validation': 'NOT_RUN',
        'ground_level_m': ground_level,
        'presentation': 'fixed declared floor and 0.5 m world checker; camera-only root tracking; no bbox floor fitting or animal rescaling'}
    if playback is not None:
        receipt['native_playback'] = playback.receipt()
    (output / 'render-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
