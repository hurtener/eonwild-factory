"""A rehashed but contradictory runtime/clip must not masquerade as verified."""
import json
from pathlib import Path
import shutil

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.compiler import compile_recipe, verify_package
from eonwild_motion.factory.io import digest, write_json
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.whole_body_gait_transition import _encode
from test_factory import make_recipe


@pytest.fixture(scope='module')
def candidate(tmp_path_factory):
    root = tmp_path_factory.mktemp('metadata-candidate')
    recipe = make_recipe(root)
    out = root / 'candidate'
    compile_recipe(recipe, root=root, output=out)
    return out


def rehash(package, name):
    m = json.loads((package / 'manifest.json').read_text())
    m['files'][name] = digest((package / name).read_bytes())
    write_json(package / 'manifest.json', m)


@pytest.mark.parametrize('case', ['id', 'version', 'duration', 'axes', 'units', 'loop', 'initial-contact',
    'events', 'phase', 'plan-lock', 'recipe-lock', 'input-lock', 'clip-name', 'clip-root', 'clip-loop', 'clip-plan', 'clip-state'])
def test_contradictory_metadata_rejects_even_with_fresh_inventory_hashes(candidate, tmp_path, case):
    out = tmp_path / 'candidate'
    shutil.copytree(candidate, out)
    filename = 'runtime.json'
    d = json.loads((out / filename).read_text())
    if case in ('id', 'version'):
        filename = 'manifest.json';d = json.loads((out / filename).read_text());d[case] = 'wrong'
    elif case == 'duration': d['duration_s'] += .001
    elif case == 'axes': d['forward_axis'][0] += 1e-6
    elif case == 'units': d['units'] = 'cm'
    elif case == 'loop': d['loop'] = False
    elif case == 'initial-contact': d['initial_contacts']['left'] = not d['initial_contacts']['left']
    elif case == 'events': d['events'].append({'time_s':0, 'name':'invented'})
    elif case == 'phase': d['transition_contract'] = {'kind':'start', 'steady_phase_s':.3}
    elif case == 'plan-lock': d['plan_sha256'] = '0' * 64
    elif case in ('recipe-lock', 'input-lock'):
        filename = 'inputs.lock.json';d = json.loads((out / filename).read_text())
        if case == 'recipe-lock': d['recipe_sha256'] = '0' * 64
        else: d['inputs']['program_profile']['sha256'] = '0' * 64
    elif case.startswith('clip-'):
        filename = 'root_motion.glb'
        g = Glb.from_bytes((out / filename).read_bytes());a = g.document['animations'][0]
        if case == 'clip-name': a['name'] = 'wrong'
        elif case == 'clip-root': a['extras']['root_motion'] = False
        elif case == 'clip-loop': a['extras']['loop'] = False
        elif case == 'clip-plan': a['extras']['plan_sha256'] = '0' * 64
        else: g.document['extras']['eonwildMotionStateTrack']['samples'][0]['contacts']['left'] = False
        (out / filename).write_bytes(_encode(g.document, g.binary));d = None
    if d is not None: write_json(out / filename, d)
    if filename != 'manifest.json': rehash(out, filename)
    with pytest.raises(ContractError, match='package metadata'):
        verify_package(out)


def test_complete_old_package_remains_inspectable_without_recompiling(candidate):
    result = verify_package(candidate)
    assert result['integrity'] == 'PASS'
    assert result['technical_status'] == 'BLOCKED'  # no actual skin fixture; not an approval
    assert result['production_approved'] is False
