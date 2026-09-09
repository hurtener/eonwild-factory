"""Read-only native-time motion measurements for comparison, not generation.

The selected GLB is never rewritten. These geometric measurements are not a
paleobiological verdict or a substitute for viewing its skinned performance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices


def angular_range(rotations):
    q = np.asarray(rotations, dtype=float)
    norm = np.linalg.norm(q, axis=1)
    if np.any(norm < 1e-8) or not np.isfinite(q).all():
        raise ContractError('invalid serialized orientation')
    q /= norm[:, None]
    # Exact pairwise rotational diameter, including all serialized samples.
    smallest = 1.
    for begin in range(0, len(q), 256):
        smallest = min(smallest, float(np.min(np.abs(q[begin:begin + 256] @ q.T))))
    return math.degrees(2 * math.acos(float(np.clip(smallest, 0, 1))))


def interior(a, b, c):
    u, v = a - b, c - b
    norms = np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1)
    if np.any(norms < 1e-10):
        raise ContractError('degenerate joint geometry')
    return np.degrees(np.arccos(np.clip(np.sum(u * v, axis=1) / norms, -1, 1)))


def interval(values):
    values = np.asarray(values)
    return {'minimum': float(np.min(values)), 'maximum': float(np.max(values)),
        'median': float(np.median(values)), 'range': float(np.ptp(values))}


def measure(path: Path, *, clip: str, roles: dict, forward_axis, up_axis=(0., 1., 0.)):
    raw = path.read_bytes()
    glb = Glb.from_bytes(raw)
    tracks, times = _clip_state(glb, clip)
    times = np.asarray(times, dtype=float)
    if len(times) < 3 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ContractError('reference has no ordered native timeline')
    up, forward = np.asarray(up_axis, dtype=float), np.asarray(forward_axis, dtype=float)
    if up.shape != (3,) or forward.shape != (3,) or not np.isfinite([up, forward]).all():
        raise ContractError('invalid comparison axes')
    up /= np.linalg.norm(up)
    forward -= up * float(forward @ up)
    forward /= np.linalg.norm(forward)
    if not np.isfinite(forward).all():
        raise ContractError('comparison axes are degenerate')
    lateral = np.cross(up, forward)
    poses = [_pose(glb, tracks, i) for i in range(len(times))]
    world = np.array([_world_matrices(glb, *pose) for pose in poses])
    rotations = np.array([pose[1] for pose in poses])
    names = glb.name_to_node
    position = lambda name: world[:, names[name], :3, 3]
    root, pelvis = position(roles['root']), position(roles['pelvis'])
    feet = {s: position(roles['legs'][s]['contactChain'][-1]) for s in ('left', 'right')}
    result = {'schema': 'eonwild.motion.native-comparison.v1', 'artifact': str(path),
        'sha256': hashlib.sha256(raw).hexdigest(), 'clip': clip, 'native_samples': len(times),
        'duration_s': float(times[-1] - times[0]), 'sample_interval_s': interval(np.diff(times)),
        'forward_axis': forward.tolist(), 'up_axis': up.tolist(),
        'root_displacement_m': (root[-1] - root[0]).tolist(),
        'signed_root_distance_m': float((root[-1] - root[0]) @ forward),
        'mean_root_speed_mps': float((root[-1] - root[0]) @ forward / (times[-1] - times[0])),
        'signed_foot_gauge_m': interval((feet['right'] - feet['left']) @ lateral),
        'pelvis_height_m': interval(pelvis @ up), 'legs': {},
        'classification': 'read-only geometry at native serialized times; no retiming, motion transfer, or approval'}
    for side in ('left', 'right'):
        chain = roles['legs'][side]['contactChain']
        hip, knee, ankle, foot = [position(name) for name in chain]
        result['legs'][side] = {
            'root_relative_foot_stroke_m': interval((foot - root) @ forward),
            'hip_sagittal_degrees': interval(np.degrees(np.arctan2((knee - hip) @ forward, -(knee - hip) @ up))),
            'knee_interior_degrees': interval(interior(hip, knee, ankle)),
            'ankle_interior_degrees': interval(interior(knee, ankle, foot)),
            'local_joint_rotation_range_degrees': {name: angular_range(rotations[:, names[name]]) for name in chain},
            'digit_local_rotation_range_degrees': {
                name: angular_range(rotations[:, names[name]]) for digit in roles['legs'][side]['toeChains'] for name in digit}}
    tip = position(roles['tail'][-1]) - pelvis
    result['tail_tip_lateral_m'] = interval(tip @ lateral)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glb', type=Path, required=True)
    parser.add_argument('--clip', required=True)
    parser.add_argument('--rig', type=Path, required=True)
    parser.add_argument('--forward', type=float, nargs=3, required=True)
    parser.add_argument('--up', type=float, nargs=3, default=(0., 1., 0.))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve() in (args.glb.resolve(), args.rig.resolve()):
        raise ContractError('measurement output must be new and cannot overwrite a source')
    result = measure(args.glb, clip=args.clip, roles=json.loads(args.rig.read_text())['roles'],
        forward_axis=args.forward, up_axis=args.up)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
