from pathlib import Path
import importlib.util
import json
import sys

import pytest


path = Path(__file__).resolve().parents[1] / 'tools/connected_schedule.py'
spec = importlib.util.spec_from_file_location('connected_schedule_test', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def package(root, name, *, loop, contract=None, phase=.25, distance=2.):
    folder = root / name
    folder.mkdir()
    runtime = {'duration_s': 1., 'loop': loop, 'forward_axis': [1, 0, 0], 'up_axis': [0, 1, 0],
               'rig_roles': {'root': 'root'}, 'ground_plane': {'up_axis': 'Y', 'level_m': 0}}
    if contract:
        runtime['transition_contract'] = {'kind': contract, 'steady_phase_s': phase,
                                          'interface_schema': 'eonwild.motion.gait-interface.v2'}
    (folder / 'runtime.json').write_text(json.dumps(runtime))
    (folder / 'plan.json').write_text(json.dumps({'samples': [
        {'time_s': 0., 'root_forward_m': 0.}, {'time_s': phase, 'root_forward_m': distance * phase},
        {'time_s': 1., 'root_forward_m': distance}]}))
    (folder / 'manifest.json').write_text('{}')
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


def test_schedule_rejects_phase_mismatch_or_nonlooping_steady(tmp_path):
    start = package(tmp_path, 'start', loop=False, contract='start', phase=.25)
    steady = package(tmp_path, 'steady', loop=True)
    stop = package(tmp_path, 'stop', loop=False, contract='stop', phase=.5)
    with pytest.raises(ValueError):
        module.build_connected_schedule(start, steady, stop, cycles=1)
    (steady / 'runtime.json').write_text(json.dumps({**json.loads((steady / 'runtime.json').read_text()), 'loop': False}))
    with pytest.raises(ValueError):
        module.build_connected_schedule(start, steady, start, cycles=1)
