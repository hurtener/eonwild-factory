from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import pytest


path = Path(__file__).resolve().parents[1] / 'tools/connected_schedule.py'
spec = importlib.util.spec_from_file_location('connected_schedule_test', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def package(root, name, *, loop, contract=None, phase=.25, distance=2., animal=None):
    folder = root / name
    folder.mkdir()
    runtime = {'duration_s': 1., 'loop': loop, 'forward_axis': [1, 0, 0], 'up_axis': [0, 1, 0],
               'rig_roles': {'root': 'root'}, 'ground_plane': {'up_axis': 'Y', 'level_m': 0},
               'family': 'fixture-biped', 'handedness': 'right', 'units': 'm', 'time_units': 's'}
    if contract:
        runtime['transition_contract'] = {'kind': contract, 'steady_phase_s': phase,
                                          'root_distance_m': distance,
                                          'interface_schema': 'eonwild.motion.gait-interface.v2'}
    shared = {
        'family': 'fixture-biped',
        'source': {'path': 'geometry.glb', 'sha256': 'a' * 64},
        'rig': {'path': 'rig.json', 'sha256': 'b' * 64},
        'contact_profile': {'path': 'contact.json', 'sha256': 'c' * 64},
        'performance_profile': {'path': 'performance.json', 'sha256': 'd' * 64},
        'forward_axis': [1, 0, 0], 'up_axis': [0, 1, 0],
    }
    if animal is not None:
        shared['animal']={'path':'animal.json','sha256':animal*64}
        runtime['animal']={'id':animal,'specimen':'fixture','uniform_geometry_scale':1.0}
    recipe = {**shared, 'program_profile': {'path': 'gait.json', 'sha256': 'e' * 64}}
    if contract:
        recipe['gait_profile'] = recipe.pop('program_profile')
        recipe['program_profile'] = {'path': f'{contract}.json', 'sha256': 'f' * 64}
    (folder / 'recipe.json').write_text(json.dumps(recipe))
    (folder / 'runtime.json').write_text(json.dumps(runtime))
    (folder / 'plan.json').write_text(json.dumps({'samples': [
        {'time_s': 0., 'root_forward_m': 0.}, {'time_s': phase, 'root_forward_m': distance * phase},
        {'time_s': 1., 'root_forward_m': distance}]}))
    (folder / 'inputs.lock.json').write_text(json.dumps({'inputs': {
        'source': shared['source'], 'rig': shared['rig'], **({'animal':shared['animal']} if animal is not None else {}),
    }}))
    (folder / 'root_motion.glb').write_bytes(b'root')
    (folder / 'in_place.glb').write_bytes(b'in-place')
    files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in folder.iterdir()}
    (folder / 'manifest.json').write_text(json.dumps({
        'schema': 'eonwild.motion.factory-package.v1', 'files': files,
    }))
    return folder


def test_schedule_uses_phase_tail_full_cycles_head_without_repeat_or_reset(tmp_path):
    start = package(tmp_path, 'start', loop=False, contract='start')
    steady = package(tmp_path, 'steady', loop=True)
    stop = package(tmp_path, 'stop', loop=False, contract='stop')
    schedule = module.build_connected_schedule(start, steady, stop, cycles=3)
    labels = [row['label'] for row in schedule['segments']]
    assert labels == ['start', 'steady-tail', 'steady-cycle-1', 'steady-cycle-2', 'steady-head', 'stop']
    assert schedule['duration_s'] == pytest.approx(5.)
    assert all('repeat' in row['clock'] for row in schedule['segments'])
    assert all(a['timeline_end_s'] == b['timeline_start_s'] for a, b in zip(schedule['segments'], schedule['segments'][1:]))
    assert all(a['world_root_end_m'] == b['world_root_start_m'] for a, b in zip(schedule['segments'], schedule['segments'][1:]))
    assert module.validate_connected_schedule(json.loads(json.dumps(schedule))) == json.loads(json.dumps(schedule))
    schedule['segments'][1]['source_start_s'] += .01
    with pytest.raises(ValueError, match='canonical immutable sources'):
        module.validate_connected_schedule(schedule)


def test_schedule_rejects_phase_mismatch_or_nonlooping_steady(tmp_path):
    start = package(tmp_path, 'start', loop=False, contract='start', phase=.25)
    steady = package(tmp_path, 'steady', loop=True)
    stop = package(tmp_path, 'stop', loop=False, contract='stop', phase=.5)
    with pytest.raises(ValueError):
        module.build_connected_schedule(start, steady, stop, cycles=1)
    (steady / 'runtime.json').write_text(json.dumps({**json.loads((steady / 'runtime.json').read_text()), 'loop': False}))
    with pytest.raises(ValueError):
        module.build_connected_schedule(start, steady, start, cycles=1)


def test_schedule_rejects_changed_source_identity_and_nonfinite_plan(tmp_path):
    start = package(tmp_path, 'start', loop=False, contract='start')
    steady = package(tmp_path, 'steady', loop=True)
    stop = package(tmp_path, 'stop', loop=False, contract='stop')
    lock_path = stop / 'inputs.lock.json'
    lock = json.loads(lock_path.read_text())
    lock['inputs']['source']['sha256'] = '9' * 64
    lock_path.write_text(json.dumps(lock))
    manifest_path = stop / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['inputs.lock.json'] = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='admitted geometry'):
        module.build_connected_schedule(start, steady, stop, cycles=1)

    plan_path = steady / 'plan.json'
    plan = json.loads(plan_path.read_text())
    plan['samples'][1]['root_forward_m'] = float('nan')
    plan_path.write_text(json.dumps(plan))
    manifest_path = steady / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files']['plan.json'] = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='invalid clock'):
        module.build_connected_schedule(start, steady, start, cycles=1)


def test_schedule_rejects_mixed_or_different_animal_instances(tmp_path):
    start=package(tmp_path,'start',loop=False,contract='start',animal='a')
    steady=package(tmp_path,'steady',loop=True,animal='a')
    stop=package(tmp_path,'stop',loop=False,contract='stop',animal='b')
    with pytest.raises(ValueError,match='animal identity'):
        module.build_connected_schedule(start,steady,stop,cycles=1)
