"""Select one immutable historical clip for visual comparison ONLY.

No animation is fitted, transferred, retimed, generated, or imported into a
behavior program. Geometry, binary accessors, coordinate frame and samples are
unchanged. The review-only schema cannot be promoted as a factory package.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile

from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state
from eonwild_motion.solve.whole_body_gait_transition import _encode


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(source: Path, expected_sha256: str, clip: str, rig: Path, contact: Path,
            forward, output: Path, *, loop: bool):
    raw = source.read_bytes()
    if digest(raw) != expected_sha256:
        raise ContractError('reference source changed; refusing review')
    if output.exists():
        raise ContractError('reference output already exists')
    if len(forward) != 3 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in forward):
        raise ContractError('reference forward axis must be explicit and finite')
    if abs(sum(v*v for v in forward)-1) > 1e-5 or abs(forward[1]) > 1e-5:
        raise ContractError('review supports a declared unit horizontal forward axis')
    original = Glb.from_bytes(raw)
    matches = [a for a in original.document['animations'] if a.get('name') == clip]
    if len(matches) != 1:
        raise ContractError('reference clip must resolve uniquely')
    _, times = _clip_state(original, clip)
    if len(times) < 2 or abs(times[0]) > 1e-8 or not 0 < times[-1] <= 60:
        raise ContractError('reference must retain a zero-origin native timeline')
    document = deepcopy(original.document)
    document['animations'] = [deepcopy(matches[0])]
    selected = _encode(document, original.binary)
    profile, binding = json.loads(contact.read_text()), json.loads(rig.read_text())
    runtime = {'schema': 'eonwild.motion.reference-runtime.v1', 'rig_roles': binding['roles'],
        'duration_s': float(times[-1]), 'loop': loop, 'forward_axis': list(forward), 'up_axis': [0.,1.,0.],
        'ground_plane': profile['geometry']['ground'], 'unity_import_status': 'NOT_VERIFIED'}
    runtime_raw = (json.dumps(runtime, indent=2)+'\n').encode()
    receipt = {'schema': 'eonwild.motion.immutable-reference.v1', 'original': str(source),
        'original_sha256': digest(raw), 'selected_clip': clip, 'selected_sha256': digest(selected),
        'rig_sha256': digest(rig.read_bytes()), 'contact_profile_sha256': digest(contact.read_bytes()),
        'native_samples': len(times), 'duration_s': float(times[-1]),
        'operation': 'select exactly one existing animation; binary data, geometry and sample times unchanged',
        'generation_input': False, 'production_approval_transferred': False}
    payloads = {'root_motion.glb': selected, 'runtime.json': runtime_raw,
        'reference.json': (json.dumps(receipt, indent=2)+'\n').encode()}
    manifest = {'schema': 'eonwild.motion.reference-review-package.v1', 'kind': 'immutable_historical_comparison',
        'technical_status': 'NOT_REEVALUATED', 'production_approved': False,
        'files': {name: digest(data) for name,data in payloads.items()}}
    output.parent.mkdir(parents=True,exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.reference-',dir=output.parent))
    try:
        for name,data in payloads.items():
            (stage/name).write_bytes(data)
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        if digest(source.read_bytes()) != expected_sha256:
            raise ContractError('reference changed during preparation')
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True)
        raise
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--clip',required=True)
    parser.add_argument('--rig',type=Path,required=True)
    parser.add_argument('--contact',type=Path,required=True)
    parser.add_argument('--forward',type=float,nargs=3,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--loop',action='store_true')
    args=parser.parse_args()
    print(json.dumps(prepare(args.source,args.sha256,args.clip,args.rig,args.contact,args.forward,args.output,loop=args.loop),indent=2))


if __name__=='__main__':
    main()
