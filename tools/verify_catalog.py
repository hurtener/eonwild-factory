"""Generate a bounded catalog group and retain exact final acceptance evidence.

Independent of the legacy compatibility build. Every nonpassing candidate
keeps the job red; compact summaries make real motion failures diagnosable.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import traceback

from eonwild_motion.factory.compiler import compile_recipe, verify_package
from measure_motion_reference import measure

GROUPS = {
    'locomotion': ['walk.v2', 'reverse-walk.v3', 'run.v3', 'sprint.v3', 'fast-walk.v1'],
    'supported': ['idle.v1', 'alert.v1', 'call.v1', 'bite-miss.v1', 'feeding.v1'],
    'transitions': ['walk-start.v1', 'walk-stop.v1', 'reverse-walk-start.v1', 'reverse-walk-stop.v1',
                    'run-start.v1', 'run-stop.v1', 'sprint-start.v1', 'sprint-stop.v1'],
}


def failures(value, path=''):
    result = []
    if isinstance(value, dict):
        for key, item in value.items():
            here = f'{path}.{key}' if path else key
            if key in ('status', 'verdict') and item in ('FAIL', 'BLOCKED', 'NOT_MEASURED'):
                result.append({'path': path, 'reason': value.get('reason'), 'reasons': value.get('reasons'),
                    'checks': value.get('checks'), 'values': value.get('values'), 'limits': value.get('limits')})
            else:
                result.extend(failures(item, here))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            result.extend(failures(item, f'{path}[{i}]'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', required=True, choices=GROUPS)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in GROUPS[args.group]:
        package = args.output / name
        print('BEGIN_CANDIDATE ' + name, flush=True)
        try:
            compile_recipe(root/f'recipes/heavy-biped/{name}.json', root=root, output=package)
            verification = verify_package(package)
            value = json.loads((package/'validation.json').read_text())
            receipt = json.loads((package/'solver-receipt.json').read_text())
            recipe = json.loads((package/'recipe.json').read_text())
            roles = json.loads((root/recipe['rig']['path']).read_text())['roles']
            measurements = measure(package/'root_motion.glb', clip=recipe['id']+'.root_motion', roles=roles,
                forward_axis=recipe['forward_axis'], up_axis=recipe['up_axis'])
            (package/'native-measurements.json').write_text(json.dumps(measurements, indent=2, allow_nan=False)+'\n')
            row = {'recipe': name, **verification, 'failures': failures(value),
                'refinement': receipt.get('skin_target_refinement'), 'oral': value.get('oral_contact'),
                'rates': value['rotation_rates'], 'continuity': value['cyclic_continuity'],
                'surface_gap_m': value['skinned_contact'].get('maximum_stance_gap_m'),
                'penetration_m': value['skinned_contact'].get('maximum_penetration_m'),
                'native_measurements': measurements}
            if row['refinement']:
                row['refinement'] = {k:v for k,v in row['refinement'].items() if k != 'witnesses'}
        except Exception as exc:
            row = {'recipe': name, 'technical_status': 'ERROR', 'error': str(exc)}
            (args.output/f'{name}.error.log').write_text(traceback.format_exc())
            print(traceback.format_exc(), flush=True)
        results.append(row)
        (args.output/'results.json').write_text(json.dumps({'group': args.group, 'results': results,
            'source_sha': subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
            'visual_review':'PENDING','unity_parity':'NOT_RUN'}, indent=2, allow_nan=False)+'\n')
        print('CANDIDATE_RESULT ' + json.dumps(row, allow_nan=False), flush=True)
    return 0 if all(row['technical_status'] == 'PASS' for row in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
