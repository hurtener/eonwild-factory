"""Read-only, cross-toolchain diagnosis of a locked legacy reproduction.

The actual output is never replaced by expected bytes, and a nonmatching
hash always exits nonzero. This tool is not a production generator.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from eonwild_motion.glb.container import Glb
from eonwild_motion.pipeline.build import build_layered_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='working')
    parser.add_argument('--resolved', type=Path)
    parser.add_argument('--write-request', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
    if args.resolved:
        resolved = json.loads(args.resolved.read_text())
    else:
        # The Blender child consumes the already validated request just as
        # production build does; it need not import host-only schema packages.
        from eonwild_motion.contracts.resolve import resolve_profile
        resolved = resolve_profile(args.profile).runtime_document()
    if args.write_request:
        with args.write_request.open('x') as handle:
            json.dump(resolved, handle, indent=2)
        return 0
    if args.output is None:
        parser.error('--output is required unless writing a request')
    args.output.mkdir(parents=True, exist_ok=False)
    source_raw = Path(resolved['inputPath']).read_bytes()
    expected_raw = Path(resolved['approvedOutputPath']).read_bytes()
    if hashlib.sha256(source_raw).hexdigest() != resolved['inputSha256']:
        raise ValueError('diagnostic source hash mismatch')
    if hashlib.sha256(expected_raw).hexdigest() != resolved['approvedOutputSha256']:
        raise ValueError('diagnostic reference hash mismatch')
    raw, metrics = build_layered_bytes(Glb.from_bytes(source_raw), resolved['documents']['rig'],
        resolved['documents']['motion'], resolved['layers'])
    actual, expected = Glb.from_bytes(raw), Glb.from_bytes(expected_raw)
    actual_sha = hashlib.sha256(raw).hexdigest()
    changes = []
    for animation in expected.document['animations']:
        for channel in animation['channels']:
            sampler = animation['samplers'][channel['sampler']]
            accessor = sampler['output']
            a = np.asarray(actual.accessor_values(accessor), dtype=float)
            b = np.asarray(expected.accessor_values(accessor), dtype=float)
            if a.shape != b.shape:
                changes.append({'accessor': accessor, 'shape_mismatch': [list(a.shape), list(b.shape)]})
                continue
            unequal = a != b
            if unequal.any():
                index = np.unravel_index(int(np.abs(a-b).argmax()), a.shape)
                changes.append({'clip': animation['name'], 'node': channel['target']['node'],
                    'name': expected.nodes[channel['target']['node']].get('name'),
                    'path': channel['target']['path'], 'accessor': accessor,
                    'different_scalars': int(unequal.sum()), 'maximum_absolute_difference': float(np.abs(a-b).max()),
                    'witness_index': list(map(int, index)), 'actual': float(a[index]), 'expected': float(b[index])})
    report = {'schema': 'eonwild.motion.reproduction-diagnostic.v1',
        'python': platform.python_version(), 'numpy': np.__version__, 'numpy_path': np.__file__,
        'platform': platform.platform(), 'expected_sha256': resolved['approvedOutputSha256'],
        'actual_sha256': actual_sha, 'exact_match': actual_sha == resolved['approvedOutputSha256'],
        'same_json_document': actual.document == expected.document, 'same_byte_length': len(raw) == len(expected_raw),
        'changed_channels': changes,
        'classification': 'diagnosis only; locked output hash is still mandatory'}
    try:
        import bpy
        report['blender'] = bpy.app.version_string
    except ImportError:
        report['blender'] = None
    (args.output/'diagnostic.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    (args.output/'layer-metrics.json').write_text(json.dumps(metrics, indent=2, allow_nan=False)+'\n')
    (args.output/'actual.glb').write_bytes(raw)
    print('REPRODUCTION_DIAGNOSTIC ' + json.dumps(report, allow_nan=False), flush=True)
    return 0 if report['exact_match'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
