"""Independent sampled import parity for immutable exploratory cubic bytes."""
from pathlib import Path
import hashlib
import json

import numpy as np

from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.solve.skin_rig import SkinRig

ROOT = Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-closed-diagnostics-integration')
ARC = Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521')
PACKAGE = ARC / 'out/source-cubic-adult-v10-f9ca924'
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = json.loads((PACKAGE / 'manifest.json').read_text())
for name, expected in manifest['files'].items():
    assert sha(PACKAGE / name) == expected, name
recipe = json.loads((PACKAGE / 'recipe.json').read_text())
contact_path = ROOT / recipe['contact_profile']['path']
assert sha(contact_path) == recipe['contact_profile']['sha256']
contact = json.loads(contact_path.read_text())
runtime = json.loads((PACKAGE / 'runtime.json').read_text())
request = {'classification': 'Sampled native Blender import parity, including decoded keys and interval interiors; not full-interval or visual acceptance',
           'reader_head': 'f9ca924bcc79943d2d2b7eeab28bef8763c18ec4',
           'package_manifest_sha256': sha(PACKAGE / 'manifest.json'),
           'contact_sha256': sha(contact_path), 'maximum_same_index_error_limit_m': .0005,
           'basis_conversion': 'glTF(X,Y,Z) to Blender(X,-Z,Y)', 'modes': {}}
for mode in ('root_motion', 'in_place'):
    source = PACKAGE / f'{mode}.glb'
    glb = Glb.from_bytes(source.read_bytes())
    tracks, keys = read_animation_tracks(glb, glb.document['animations'][0]['name'], require_common_timeline=True)
    assert len(keys) == 297
    key_ids = [0, 35, 72, 118, 148, 185, 222, 258, 296]
    interval_ids = [0, 34, 71, 117, 147, 184, 221, 257, 295]
    times = sorted({float(keys[i]) for i in key_ids} | {float((keys[i] + keys[i + 1]) / 2) for i in interval_ids})
    rig = SkinRig(glb, runtime['rig_roles'], runtime['forward_axis'], runtime['up_axis'], contact)
    expected = []
    for time in times:
        values = {'translation': np.asarray(glb.rest_translation, dtype=float).copy(),
                  'rotation': np.asarray(glb.rest_rotation, dtype=float).copy(),
                  'scale': np.asarray(glb.rest_scale, dtype=float).copy()}
        for (node, path), track in tracks.items():
            values[path][node] = track.sample(time)
        xyz = rig.skin(rig.world(values['translation'], values['rotation'], values['scale']))
        expected.append(xyz[:, [0, 2, 1]] * [1., -1., 1.])
    target = OUT / f'{mode}-expected.npy'
    np.save(target, np.asarray(expected))
    request['modes'][mode] = {'glb': str(source), 'glb_sha256': sha(source),
                             'times_s': times, 'expected': str(target), 'expected_sha256': sha(target)}
(OUT / 'request.json').write_text(json.dumps(request, indent=2, sort_keys=True) + '\n')
print(json.dumps({'samples_per_mode': len(times), 'request_sha256': sha(OUT / 'request.json')}))
