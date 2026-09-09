"""Immutable start -> steady cycles -> stop review scheduling.

This schedule carries phase and declared root travel explicitly.  It never
uses NLA repeat, a fitted seam, or copied boundary poses.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
import sys


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_VERIFY_SCRIPT = """\
import json
import sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
source = (root / 'src').resolve()
sys.path.insert(0, str(source))
from eonwild_motion.factory import compiler
if not Path(compiler.__file__).resolve().is_relative_to(source):
    raise RuntimeError('factory verifier did not load from the requested checkout')
print(json.dumps(compiler.verify_package(Path(sys.argv[2]).resolve()), allow_nan=False))
"""


def _verification_python() -> Path:
    # Preserve a virtual-environment symlink: resolving it would discard the
    # environment's site-packages and run the base interpreter directly.
    executable = Path(sys.executable)
    if 'bpy' not in sys.modules and executable.name.startswith('python'):
        return executable
    candidate = _REPOSITORY_ROOT / '.venv/bin/python'
    if not candidate.is_file():
        raise ValueError('connected review requires the repository Python environment for package verification')
    return candidate


def _verify_factory_package(package: Path) -> None:
    try:
        environment = {key: value for key, value in os.environ.items()
                       if key not in ('PYTHONHOME', 'PYTHONPATH')}
        process = subprocess.run(
            [str(_verification_python()), '-c', _VERIFY_SCRIPT, str(_REPOSITORY_ROOT), str(package)],
            cwd=_REPOSITORY_ROOT, capture_output=True, text=True, timeout=300, env=environment)
        result = json.loads(process.stdout) if process.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise ValueError(f'connected review package verification could not run: {package}: {exc}') from exc
    if process.returncode != 0 or not isinstance(result, dict) or result.get('integrity') != 'PASS':
        detail = process.stderr.strip()[-2000:] or process.stdout.strip()[-2000:]
        raise ValueError(f'connected review package does not pass factory verification: {package}: {detail}')


def _engine_files(lock: dict, package: Path) -> dict[str, str]:
    if not isinstance(lock, dict):
        raise ValueError(f'connected review package lacks compiler fingerprints: {package}')
    engine_files = lock.get('engine_files')
    if not isinstance(engine_files, dict) or not engine_files:
        raise ValueError(f'connected review package lacks compiler fingerprints: {package}')
    for name, sha256 in engine_files.items():
        normalized = PurePosixPath(name) if isinstance(name, str) else None
        if (normalized is None or not name or normalized.is_absolute() or normalized.as_posix() != name
                or any(part in ('.', '..') for part in normalized.parts)
                or not isinstance(sha256, str) or re.fullmatch(r'[0-9a-f]{64}', sha256) is None):
            raise ValueError(f'connected review package has invalid compiler fingerprints: {package}')
    return engine_files


def _load(package: Path) -> dict:
    package = Path(package).resolve()
    _verify_factory_package(package)
    manifest = package / 'manifest.json'
    runtime = package / 'runtime.json'
    plan = package / 'plan.json'
    inputs = package / 'inputs.lock.json'
    recipe = package / 'recipe.json'
    if not all(path.is_file() for path in (manifest, runtime, plan, inputs, recipe)):
        raise ValueError('connected review requires complete immutable packages')
    manifest_value = json.loads(manifest.read_text())
    files = manifest_value.get('files')
    if manifest_value.get('schema') != 'eonwild.motion.factory-package.v1' or not isinstance(files, dict):
        raise ValueError('connected review requires a factory package manifest')
    required = {'root_motion.glb', 'in_place.glb', 'runtime.json', 'plan.json', 'inputs.lock.json', 'recipe.json'}
    if not required.issubset(files):
        raise ValueError('connected review package is missing required declared files')
    for name, expected in files.items():
        path = package / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'connected review package file hash mismatch: {name}')
    lock = json.loads(inputs.read_text())
    named = lock.get('inputs', {})
    identity = {key: named.get(key) for key in ('source', 'rig')}
    if any(not isinstance(value, dict) or set(value) != {'path', 'sha256'} for value in identity.values()):
        raise ValueError('connected review package lacks source/rig identity')
    resolution = lock.get('motion_set_resolution')
    baseline_identity = None
    if resolution is not None:
        if (not isinstance(resolution, dict)
                or not isinstance(resolution.get('identities'), dict)):
            raise ValueError('connected review package lacks motion baseline identity')
        baseline_identity = {
            'binding': resolution.get('baseline'),
            'identity': resolution['identities'].get('baseline'),
            'snapshot_sha256': files.get('motion-baseline.json'),
        }
    value = {'path': str(package), 'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
             'runtime': json.loads(runtime.read_text()), 'plan': json.loads(plan.read_text()),
             'recipe': json.loads(recipe.read_text()), 'source_identity': identity,
             'animal_identity': named.get('animal'), 'baseline_identity': baseline_identity,
             'engine_files': _engine_files(lock, package)}
    rows = value['plan'].get('samples')
    if not isinstance(rows, list) or len(rows) < 2:
        raise ValueError('connected review requires a native plan timeline')
    if any(isinstance(row.get('time_s'), bool) or not isinstance(row.get('time_s'), (int, float))
           or not math.isfinite(row['time_s']) or isinstance(row.get('root_forward_m'), bool)
           or not isinstance(row.get('root_forward_m'), (int, float)) or not math.isfinite(row['root_forward_m'])
           for row in rows):
        raise ValueError('connected review plan has invalid clock or declared travel')
    times = [float(row['time_s']) for row in rows]
    duration = value['runtime'].get('duration_s')
    if (isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration)
            or duration <= 0 or abs(times[0]) > 2e-6 or abs(times[-1] - duration) > 2e-6
            or any(after <= before for before, after in zip(times, times[1:]))):
        raise ValueError('connected review plan does not have one ordered native duration')
    return value


def _phase(contract: dict, kind: str) -> float:
    interface = contract.get('interface_schema')
    if contract.get('kind') != kind or interface not in (
        'eonwild.motion.gait-interface.v1', 'eonwild.motion.gait-interface.v2'):
        raise ValueError(f'connected review requires a declared {kind} interface')
    phase = contract.get('steady_phase_s')
    if isinstance(phase, bool) or not isinstance(phase, (int, float)) or not math.isfinite(phase) or phase < 0:
        raise ValueError('connected review has invalid declared steady phase')
    if interface == 'eonwild.motion.gait-interface.v1' and phase != 0:
        raise ValueError('connected review v1 interface requires zero steady phase')
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
    if start['source_identity'] != steady['source_identity'] or start['source_identity'] != stop['source_identity']:
        raise ValueError('connected review packages do not share admitted geometry and rig identity')
    if start['animal_identity'] != steady['animal_identity'] or start['animal_identity'] != stop['animal_identity']:
        raise ValueError('connected review packages do not share animal identity')
    if start['baseline_identity'] != steady['baseline_identity'] or start['baseline_identity'] != stop['baseline_identity']:
        raise ValueError('connected review packages do not share motion baseline identity')
    if start['engine_files'] != steady['engine_files'] or start['engine_files'] != stop['engine_files']:
        raise ValueError('connected review packages do not share compiler fingerprints')
    for transition in (start, stop):
        if transition['recipe'].get('gait_profile') != steady['recipe'].get('program_profile'):
            raise ValueError('connected review transition is not recipe-bound to the steady gait')
        for key in ('family', 'source', 'rig', 'animal', 'contact_profile', 'performance_profile', 'forward_axis', 'up_axis'):
            if transition['recipe'].get(key) != steady['recipe'].get(key):
                raise ValueError(f'connected review recipe {key} differs')
    sr, rr, tr = (value['runtime'] for value in (start, steady, stop))
    if rr.get('loop') is not True or sr.get('loop') is not False or tr.get('loop') is not False:
        raise ValueError('connected review requires non-looping start/stop and a looping steady package')
    for key in ('family', 'animal', 'forward_axis', 'up_axis', 'rig_roles', 'ground_plane', 'handedness', 'units', 'time_units'):
        if sr.get(key) != rr.get(key) or sr.get(key) != tr.get(key):
            raise ValueError(f'connected review package {key} differs')
    start_phase = _phase(sr.get('transition_contract', {}), 'start')
    stop_phase = _phase(tr.get('transition_contract', {}), 'stop')
    for value, runtime in ((start, sr), (stop, tr)):
        travel = float(value['plan']['samples'][-1]['root_forward_m']) - float(value['plan']['samples'][0]['root_forward_m'])
        declared = runtime['transition_contract'].get('root_distance_m')
        if (isinstance(declared, bool) or not isinstance(declared, (int, float)) or not math.isfinite(declared)
                or abs(float(declared) - travel) > 2e-6):
            raise ValueError('connected review transition root distance differs from its plan')
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
        entries.append((f'steady-cycle-{cycles}', steady, 0., duration))
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
            'source_identity': start['source_identity'],
            'animal_identity': start['animal_identity'],
            **({'motion_baseline_identity': start['baseline_identity']}
               if start['baseline_identity'] is not None else {}),
            'engine_files': start['engine_files'],
            'steady_phase_s': phase, 'segments': segments, 'duration_s': cursor_time,
            'declared_root_travel_m': cursor_travel, 'modes': ('root_motion', 'in_place'),
            'visual_review': 'PENDING', 'unity_validation': 'NOT_RUN',
            'classification': 'immutable source-segment diagnostic; no blend, retime, endpoint fitting, or Unity claim'}


def validate_connected_schedule(schedule: dict) -> dict:
    """Recompute the schedule from its immutable sources and reject any edit."""
    if not isinstance(schedule, dict) or schedule.get('schema') != 'eonwild.motion.connected-review-schedule.v1':
        raise ValueError('unsupported connected review schedule')
    segments = schedule.get('segments')
    if not isinstance(segments, list) or len(segments) < 3:
        raise ValueError('connected review schedule has too few source intervals')
    if segments[0].get('label') != 'start' or segments[-1].get('label') != 'stop':
        raise ValueError('connected review schedule lacks canonical start/stop intervals')
    steady_packages = {row.get('package') for row in segments
                       if str(row.get('label', '')).startswith('steady-')}
    if len(steady_packages) != 1:
        raise ValueError('connected review schedule lacks one canonical steady source')
    canonical = build_connected_schedule(Path(segments[0]['package']), Path(next(iter(steady_packages))),
                                         Path(segments[-1]['package']), cycles=schedule.get('cycles'))
    canonical = json.loads(json.dumps(canonical, allow_nan=False))
    if schedule != canonical:
        raise ValueError('connected review schedule differs from its canonical immutable sources')
    return schedule
