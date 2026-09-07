"""Immutable start -> steady cycles -> stop review scheduling.

This schedule carries phase and declared root travel explicitly.  It never
uses NLA repeat, a fitted seam, or copied boundary poses.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


def _load(package: Path) -> dict:
    package = Path(package).resolve()
    manifest = package / 'manifest.json'
    runtime = package / 'runtime.json'
    plan = package / 'plan.json'
    if not all(path.is_file() for path in (manifest, runtime, plan)):
        raise ValueError('connected review requires complete immutable packages')
    value = {'path': str(package), 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
             'runtime': json.loads(runtime.read_text()), 'plan': json.loads(plan.read_text())}
    rows = value['plan'].get('samples')
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError('connected review requires a native plan timeline')
    if any(not isinstance(row.get('time_s'), (int, float)) or not isinstance(row.get('root_forward_m'), (int, float))
           for row in rows):
        raise ValueError('connected review plan has invalid clock or declared travel')
    return value


def _phase(contract: dict, kind: str) -> float:
    if contract.get('kind') != kind or contract.get('interface_schema') not in (
        'eonwild.motion.gait-interface.v1', 'eonwild.motion.gait-interface.v2'):
        raise ValueError(f'connected review requires a declared {kind} interface')
    phase = contract.get('steady_phase_s')
    if isinstance(phase, bool) or not isinstance(phase, (int, float)) or not math.isfinite(phase) or phase < 0:
        raise ValueError('connected review has invalid declared steady phase')
    return float(phase)


def _distance(plan: dict, time_s: float) -> float:
    matches = [row['root_forward_m'] for row in plan['samples'] if abs(row['time_s'] - time_s) <= 2e-6]
    if len(matches) != 1:
        raise ValueError('connected review phase is not an actual native sample')
    return float(matches[0])


def build_connected_schedule(start_package: Path, steady_package: Path, stop_package: Path, *, cycles: int) -> dict:
    if type(cycles) is not int or not 1 <= cycles <= 32:
        raise ValueError('connected review cycles must be an integer from 1 to 32')
    start, steady, stop = (_load(path) for path in (start_package, steady_package, stop_package))
    sr, rr, tr = (value['runtime'] for value in (start, steady, stop))
    if rr.get('loop') is not True or sr.get('loop') is not False or tr.get('loop') is not False:
        raise ValueError('connected review requires non-looping start/stop and a looping steady package')
    for key in ('forward_axis', 'up_axis', 'rig_roles', 'ground_plane'):
        if sr.get(key) != rr.get(key) or sr.get(key) != tr.get(key):
            raise ValueError(f'connected review package {key} differs')
    start_phase = _phase(sr.get('transition_contract', {}), 'start')
    stop_phase = _phase(tr.get('transition_contract', {}), 'stop')
    if abs(start_phase - stop_phase) > 2e-6:
        raise ValueError('connected review start/stop declared phases differ')
    duration = float(rr['duration_s'])
    phase = start_phase
    if phase > duration:
        raise ValueError('connected review phase exceeds steady duration')
    entries: list[tuple[str, dict, float, float]] = [('start', start, 0., float(sr['duration_s']))]
    if phase:
        entries.append(('steady-tail', steady, phase, duration))
    for index in range(cycles - 1):
        entries.append((f'steady-cycle-{index + 1}', steady, 0., duration))
    if phase:
        entries.append(('steady-head', steady, 0., phase))
    elif cycles:
        entries.append(('steady-cycle-1', steady, 0., duration))
    entries.append(('stop', stop, 0., float(tr['duration_s'])))
    cursor_time = 0.
    cursor_travel = 0.
    segments = []
    for label, package, source_start, source_end in entries:
        if source_end <= source_start:
            continue
        source_distance_start = _distance(package['plan'], source_start)
        source_distance_end = _distance(package['plan'], source_end)
        row = {'label': label, 'package': package['path'], 'manifest_sha256': package['manifest_sha256'],
               'source_start_s': source_start, 'source_end_s': source_end,
               'timeline_start_s': cursor_time, 'timeline_end_s': cursor_time + source_end - source_start,
               'declared_root_start_m': source_distance_start, 'declared_root_end_m': source_distance_end,
               # Add this constant only for root_motion.  In-place samples use
               # the same offset plus their exact plan root curve at each source time.
               'root_motion_parent_offset_m': cursor_travel - source_distance_start,
               'world_root_start_m': cursor_travel,
               'world_root_end_m': cursor_travel + source_distance_end - source_distance_start,
               'clock': 'immutable source interval; no repeat, retime, blend, or copied boundary pose'}
        segments.append(row)
        cursor_time = row['timeline_end_s']
        cursor_travel = row['world_root_end_m']
    return {'schema': 'eonwild.motion.connected-review-schedule.v1', 'cycles': cycles,
            'steady_phase_s': phase, 'segments': segments, 'duration_s': cursor_time,
            'declared_root_travel_m': cursor_travel, 'modes': ('root_motion', 'in_place'),
            'visual_review': 'PENDING', 'unity_validation': 'NOT_RUN',
            'classification': 'immutable source-segment diagnostic; no blend, retime, endpoint fitting, or Unity claim'}
