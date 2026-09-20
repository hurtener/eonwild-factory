"""Read-only archive inventory for the September 2026 feasibility investigation.

Usage: python tools/research/inspect_opensim_resources.py RESEARCH_CACHE OUTPUT
Does not execute downloaded code, install software, or modify source models.
"""
import argparse
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def inspect_model(data):
    # Older OpenSim emits C++ class names containing ::. Its own loader accepts
    # these; ElementTree does not. Normalize tag spelling in memory only.
    root = ET.fromstring(data.replace(b'::', b'__'))
    bodies = root.findall('.//BodySet/objects/Body')
    forces = root.findall('.//ForceSet/objects/*')
    return {
        'inspection_tag_normalization_only': b'::' in data,
        'moving_bodies': sum(b.attrib.get('name') != 'ground' for b in bodies),
        'coordinates': len(root.findall('.//Coordinate')),
        'muscles': sum('Muscle' in f.tag for f in forces),
        'mass_kg': sum(float(b.findtext('mass', '0')) for b in bodies),
        'force_classes': sorted({f.tag for f in forces}),
        'contact_geometry_count': len(root.findall('.//ContactGeometrySet/objects/*')),
    }


def inspect_archive(data, prefix=''):
    result = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for entry in archive.infolist():
            name = entry.filename
            if entry.is_dir() or '__MACOSX' in name:
                continue
            if not name.lower().endswith(('.osim', '.msl', '.jnt', '.zip')):
                continue
            raw = archive.read(name)
            if name.lower().endswith('.zip'):
                result.extend(inspect_archive(raw, prefix+name+'!'))
                continue
            row = {'path': prefix+name, 'bytes': len(raw),
                   'sha256': hashlib.sha256(raw).hexdigest()}
            if name.lower().endswith('.osim'):
                row['model'] = inspect_model(raw)
            elif name.lower().endswith('.msl'):
                text = raw.decode(errors='replace')
                row['parameter_values'] = {key: sorted(set(re.findall(
                    '^'+key+r'\s+(\S+)', text, re.M))) for key in
                    ('max_force', 'optimal_fiber_length', 'tendon_slack_length')}
                row['muscle_definition_count_including_defaults'] = len(
                    re.findall('^beginmuscle', text, re.M))
            result.append(row)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('cache', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    result = {'date': '2026-09-20', 'scope': 'Archive inspection; not gait validation',
              'archives': []}
    for metadata_name in ('figshare-4982492.json', 'figshare-4982981.json', 'gracilisuchus.source'):
        metadata = json.loads((args.cache/metadata_name).read_text())
        for file in metadata['files']:
            raw = (args.cache/file['name']).read_bytes()
            assert hashlib.md5(raw).hexdigest() == file['computed_md5']
            result['archives'].append({
                'name': file['name'], 'doi': metadata['doi'],
                'source': file['download_url'], 'license': metadata['license'],
                'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'publisher_md5_verified': True, 'inventory': inspect_archive(raw)})
    name = 'coelophysis-data-s1-s2.zip'
    raw = (args.cache/name).read_bytes()
    result['archives'].append({
        'name': name,
        'source': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8457660/supplementaryFiles',
        'doi': '10.1126/sciadv.abi7348', 'bytes': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'license_status': 'Article CC BY-NC 4.0; no separate permissive code/model license verified.',
        'inventory': inspect_archive(raw)})
    result['repositories'] = {name: {
        'tree_sha': json.loads((args.cache/file).read_text())['sha']}
        for name, file in [('PredSim', 'predsim-tree.source'),
                           ('MuSkeMo', 'muskemo-tree.source'),
                           ('OpenSim_4.6', 'opensim-tree.json')]}
    result['native_model_load'] = json.loads((args.cache/'model-load.json').read_text())
    raw_log = (args.cache/'moco-smoke.log').read_bytes()
    saved_log = ('\n'.join(line.rstrip() for line in raw_log.decode().splitlines())+'\n').encode()
    evidence = args.output.parent/'opensim-evidence'
    evidence.mkdir(exist_ok=True)
    (evidence/'moco-smoke.log').write_bytes(saved_log)
    result['moco_optimization_smoke'] = {
        'status': 'BLOCKED_RUNTIME_DEPENDENCY',
        'example': 'OpenSim 4.6 exampleSlidingMass.py',
        'reason': 'IPOPT cannot load missing libgfortran.5.dylib',
        'example_sha256': hashlib.sha256((args.cache/'exampleSlidingMass.py').read_bytes()).hexdigest(),
        'raw_log_sha256': hashlib.sha256(raw_log).hexdigest(),
        'log_sha256': hashlib.sha256(saved_log).hexdigest(),
        'saved_log_normalization': 'Trailing whitespace removed; diagnostic content unchanged.',
        'dinosaur_optimization': 'NOT_RUN', 'unity_transfer': 'NOT_RUN'}
    args.output.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
