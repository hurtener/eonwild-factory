#!/usr/bin/env python3
"""Reopen a directional candidate and measure semantic joints at keys and midpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.airborne_gait import _interior


def measure(package):
    glb = Glb(package / 'root_motion.glb')
    receipt = json.loads((package / 'directional.json').read_text())
    profile_bytes = (package / 'source-animal.profile.json').read_bytes()
    if (hashlib.sha256(glb.raw).hexdigest() != receipt['emitted_sha256']
            or hashlib.sha256(profile_bytes).hexdigest() != receipt['profile_sha256']):
        raise ValueError('Candidate motion or semantic profile identity mismatch')
    bindings = {b['role']: b['bone'] for b in json.loads(profile_bytes)['bindings']}
    chains = {s: [glb.name_to_node[bindings[f'legs.{s}.contactChain.{i}']]
                  for i in range(4)] for s in ('left', 'right')}
    tracks, _ = read_animation_tracks(glb, 'directional-review', require_common_timeline=True)
    keys = np.asarray([r['time_s'] for r in receipt['samples']])
    times = np.sort(np.concatenate((keys, (keys[1:] + keys[:-1]) / 2)))
    rows = []
    for time in times:
        tr, ro = list(glb.rest_translation), list(glb.rest_rotation)
        for (node, path), track in tracks.items():
            if path == 'translation': tr[node] = track.sample(float(time))
            elif path == 'rotation': ro[node] = track.sample(float(time))
        worlds = np.asarray(_world_matrices(glb, tr, ro, glb.rest_scale))
        for side, chain in chains.items():
            hip, knee, ankle, foot = [worlds[n][:3, 3] for n in chain]
            rows.append({'time_s': float(time), 'side': side,
                         'knee_interior_degrees': _interior(hip-knee, ankle-knee),
                         'ankle_interior_degrees': _interior(knee-ankle, foot-ankle)})
    return {'method': 'Reopened final GLB world joint centers at source keys and midpoints; 180 degrees is straight. Diagnostic, not biological ROM or continuous-time certification.',
            'motion_sha256': receipt['emitted_sha256'], 'profile_sha256': receipt['profile_sha256'],
            'sample_times': len(times),
            'maximum_knee': max(rows, key=lambda r: r['knee_interior_degrees']),
            'maximum_ankle': max(rows, key=lambda r: r['ankle_interior_degrees']),
            'samples': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = measure(args.package)
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({k: v for k, v in data.items() if k != 'samples'}, indent=2))
