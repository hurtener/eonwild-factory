"""Evaluate actual imported actions in Blender's native dependency graph."""
from pathlib import Path
import hashlib
import json
import math
import sys
sys.path.insert(0, '/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-closed-diagnostics-integration/src')
from eonwild_motion.blender.native_playback import import_gltf_for_native_playback
from mathutils import Vector

import bpy
import numpy as np

OUT = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

request = json.loads((OUT / 'request.json').read_text())
result = {key: value for key, value in request.items() if key != 'modes'}
result.update(blender_version=bpy.app.version_string, request_sha256=sha(OUT / 'request.json'),
              prepare_sha256=sha(OUT / 'prepare.py'), verifier_sha256=sha(Path(__file__)), modes={})
for mode, row in request['modes'].items():
    assert sha(row['glb']) == row['glb_sha256']
    assert sha(row['expected']) == row['expected_sha256']
    expected = np.load(row['expected'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = 24, 1.
    scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1.
    playback = import_gltf_for_native_playback(Path(row['glb']))
    assert playback is not None
    fps = scene.render.fps / scene.render.fps_base
    start = min(float(action.frame_range[0]) for action in bpy.data.actions)
    end = max(float(action.frame_range[1]) for action in bpy.data.actions)
    meshes = [obj for obj in scene.objects if obj.type == 'MESH' and len(obj.data.vertices) == expected.shape[1]]
    assert len(meshes) == 1
    records = []
    for index, time in enumerate(row['times_s']):
        frame = start + time * fps
        integer = math.floor(frame)
        scene.frame_set(integer, subframe=frame - integer)
        playback.apply(time)
        deps = bpy.context.evaluated_depsgraph_get()
        evaluated = meshes[0].evaluated_get(deps)
        mesh = evaluated.to_mesh()
        actual = np.asarray([evaluated.matrix_world @ vertex.co for vertex in mesh.vertices], dtype=float)
        evaluated.to_mesh_clear()
        assert actual.shape == expected[index].shape
        errors = np.linalg.norm(actual - expected[index], axis=1)
        witness = int(np.argmax(errors))
        records.append({'time_s': time, 'blender_frame': frame, 'maximum_same_index_error_m': float(errors[witness]),
                        'rms_same_index_error_m': float(np.sqrt(np.mean(errors ** 2))), 'worst_vertex': witness,
                        'actual_m': actual[witness].tolist(), 'expected_m': expected[index, witness].tolist()})
    # Exercise an actual still render at a serialized interval interior.
    index = 1
    time = row['times_s'][index]
    frame = start + time * fps
    scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
    playback.apply(time)
    camera_data = bpy.data.cameras.new('RootParityCamera')
    camera = bpy.data.objects.new('RootParityCamera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = (10, -10, 6)
    camera.rotation_euler = (Vector((0, 0, 1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 1
    scene.cycles.device = 'CPU'
    scene.render.resolution_x = scene.render.resolution_y = 64
    scene.render.resolution_percentage = 100
    bpy.ops.render.render(write_still=False)
    evaluated = meshes[0].evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    actual = np.asarray([evaluated.matrix_world @ vertex.co for vertex in mesh.vertices], dtype=float)
    evaluated.to_mesh_clear()
    render_error = float(np.max(np.linalg.norm(actual - expected[index], axis=1)))
    maximum = max(item['maximum_same_index_error_m'] for item in records)
    maximum = max(maximum, render_error)
    result['modes'][mode] = {'glb_sha256': row['glb_sha256'], 'expected_sha256': row['expected_sha256'],
                             'post_cycles_render_error_m': render_error, 'native_playback': playback.receipt(), 'vertex_count': expected.shape[1], 'sample_count': len(records), 'imported_fps': fps,
                             'source_action_start': start, 'source_action_end': end,
                             'maximum_same_index_error_m': maximum, 'samples': records,
                             'status': 'PASS' if maximum <= request['maximum_same_index_error_limit_m'] else 'FAIL'}
result['status'] = 'PASS' if all(row['status'] == 'PASS' for row in result['modes'].values()) else 'FAIL'
(OUT / 'native-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, indent=2))
assert result['status'] == 'PASS', 'native Blender sampled skin parity failed'
