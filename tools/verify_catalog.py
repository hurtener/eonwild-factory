"""Compile selected locked recipes and require actual final technical gates.

Per-recipe jobs prevent one slow or infeasible action from hiding all other
results. Diagnostic measurements live outside immutable candidate packages.
No whitelist grants approval: every requested recipe must independently pass.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import traceback

from eonwild_motion.factory.compiler import compile_recipe, verify_package
from measure_motion_reference import measure

GROUPS = {
    'animal-benchmarks': ['tarbosaurus-pin-552-1-adult-walk.v3'],
    'locomotion': ['walk.v3', 'reverse-walk.v4', 'run.v4', 'sprint.v4', 'fast-walk.v2'],
    'supported': ['idle.v1', 'alert.v1', 'call.v1', 'bite-miss.v2', 'feeding.v2'],
    'transitions': ['walk-start.v3', 'walk-stop.v3', 'reverse-walk-start.v3', 'reverse-walk-stop.v3',
                    'run-start.v3', 'run-stop.v3', 'sprint-start.v3', 'sprint-stop.v3'],
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--group', choices=GROUPS)
    selection.add_argument('--recipes', nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    names = GROUPS[args.group] if args.group else args.recipes
    if len(set(names)) != len(names) or any(re.fullmatch(r'[a-z][a-z0-9-]*\.v[1-9][0-9]*', name) is None for name in names):
        parser.error('recipe names must be unique versioned catalog names')
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    source_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    for name in names:
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
            (args.output/f'{name}.native-measurements.json').write_text(json.dumps(measurements, indent=2, allow_nan=False)+'\n')
            row = {'recipe': name, **verification, 'failures': failures(value),
                'rates': value['rotation_rates'], 'continuity': value['cyclic_continuity'],
                'feasibility': value['solver_feasibility'], 'oral': value.get('oral_contact'),
                'surface_gap_m': value['skinned_contact'].get('maximum_stance_gap_m'),
                'penetration_m': value['skinned_contact'].get('maximum_penetration_m')}
            refinement = receipt.get('skin_target_refinement')
            if refinement:
                row['refinement'] = {k:v for k,v in refinement.items() if k != 'witnesses'}
        except Exception as exc:
            row = {'recipe': name, 'technical_status': 'ERROR', 'error': str(exc)}
            (args.output/f'{name}.error.log').write_text(traceback.format_exc())
            print(traceback.format_exc(), flush=True)
        results.append(row)
        (args.output/'results.json').write_text(json.dumps({'results': results, 'source_sha': source_sha,
            'visual_review':'PENDING','unity_parity':'NOT_RUN','production_approved':False}, indent=2, allow_nan=False)+'\n')
        print('CANDIDATE_RESULT ' + json.dumps(row, allow_nan=False), flush=True)
    return 0 if results and all(row['technical_status'] == 'PASS' for row in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
