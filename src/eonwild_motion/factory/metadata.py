"""Cross-document checks on emitted metadata, not a new motion approval gate.

Hashes establish an inventory; they do not establish that its duration, phase,
coordinate axes or clip identifiers agree. This inspection reads both exports
and keeps technical, visual and Unity acceptance separate.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from .io import digest, frame_axes, read_json


_INPUTS = ('source', 'rig', 'program_profile', 'animal', 'contact_profile', 'performance_profile', 'gait_profile')


def require_metadata(path: Path, manifest: dict) -> None:
    from .compiler import event_track, validate_plan
    recipe, runtime, plan, lock = (read_json(path / name) for name in
        ('recipe.json', 'runtime.json', 'plan.json', 'inputs.lock.json'))
    def require(condition, reason):
        if not condition:
            raise ContractError('package metadata: ' + reason)
    require(manifest.get('id') == recipe.get('id') and manifest.get('version') == recipe.get('version'),
            'recipe and package identity differ')
    require(recipe.get('schema') == 'eonwild.motion.factory-recipe.v1', 'unsupported recipe')
    require(runtime.get('schema') == 'eonwild.motion.runtime-data.v1', 'unsupported runtime data')
    require(lock.get('schema') == 'eonwild.motion.factory-lock.v1', 'unsupported input lock')
    require(lock.get('recipe_sha256') == digest((path / 'recipe.json').read_bytes()), 'recipe lock differs')
    require(lock.get('inputs') == {k: recipe[k] for k in _INPUTS if k in recipe}, 'input bindings differ')
    require(runtime.get('program') == recipe.get('program') == plan.get('program'), 'program differs')
    require(runtime.get('family') == recipe.get('family'), 'family differs')
    if 'animal' in recipe:
        from .animal import biomechanics_report,load_animal_instance,verify_emitted_animal_geometry
        animal_document = read_json(path / 'animal.json')
        require(digest((path/'animal.json').read_bytes()) == recipe['animal']['sha256'],
                'animal snapshot differs from recipe binding')
        animal_instance=load_animal_instance(animal_document,source_sha256=recipe['source']['sha256'])
        animal = read_json(path / 'biomechanics.json')
        runtime_animal = runtime.get('animal')
        require(isinstance(runtime_animal,dict) and runtime_animal.get('id') == animal.get('animal_id')
                and runtime_animal.get('specimen') == animal.get('specimen')
                and runtime_animal.get('uniform_geometry_scale') == animal.get('geometry',{}).get('uniform_scale'),
                'animal runtime and biomechanics evidence differ')
        expected=biomechanics_report(animal_instance,plan,
            actual_semantic_height_m=runtime_animal.get('semantic_pelvis_to_toe_plane_m'))
        require(animal == expected, 'biomechanics report differs from bound animal and plan')
        require(animal.get('force_aware_solver') == 'NOT_IMPLEMENTED'
                and animal.get('contact_force_distribution') == 'NOT_EVALUATED'
                and animal.get('biological_validation') == 'NOT_VALIDATED',
                'animal report overclaims implemented evidence')
    else:
        require(runtime.get('animal') is None, 'unbound animal runtime data')
    require((runtime.get('units'), runtime.get('time_units'), runtime.get('handedness')) == ('m', 's', 'right'),
            'unsupported runtime coordinate convention')
    for key, expected in zip(('forward_axis', 'up_axis'), frame_axes(recipe['forward_axis'], recipe['up_axis'])):
        actual = np.asarray(runtime.get(key))
        require(actual.shape == (3,) and actual.dtype.kind in 'fiu' and np.isfinite(actual).all()
                and np.allclose(actual, expected, rtol=0, atol=1e-12), 'runtime axes differ from the normalized recipe')
    validate_plan(plan, recipe['program'])
    samples = plan['samples']
    require(type(runtime.get('loop')) is bool and runtime['loop'] == plan.get('loop', True), 'loop declaration differs')
    require(type(runtime.get('duration_s')) in (float, int) and runtime['duration_s'] == samples[-1]['time_s'],
            'duration differs from the final plan sample')
    plan_sha = digest((path / 'plan.json').read_bytes())
    require(runtime.get('plan_sha256') == plan_sha, 'runtime plan identity differs')
    require(runtime.get('initial_contacts') == {s: samples[0]['feet'][s]['contact'] for s in ('left', 'right')},
            'initial contact state differs')
    require(runtime.get('events') == sorted(event_track(plan) + plan.get('events', []), key=lambda e: e['time_s']),
            'runtime events differ from choreography')
    require(runtime.get('transition_contract') == plan.get('transition_contract'), 'transition interface differs')
    expected_state = {'program': recipe['program'], 'samples': [
        {'time_s': row['time_s'], 'flight': row['flight'], 'support_count': row['support_count'],
         'contacts': {s: row['feet'][s]['contact'] for s in ('left', 'right')}} for row in samples]}
    times = np.asarray([r['time_s'] for r in samples], dtype=float)
    for mode in ('root_motion', 'in_place'):
        glb = Glb.from_bytes((path / (mode + '.glb')).read_bytes())
        if 'animal' in recipe:
            verify_emitted_animal_geometry(animal_instance, glb, runtime['rig_roles'], runtime['up_axis'],
                actual_semantic_height_m=runtime_animal['semantic_pelvis_to_toe_plane_m'])
        animations = glb.document.get('animations', [])
        require(len(animations) == 1 and animations[0].get('name') == recipe['id'] + '.' + mode,
                'serialized clip identity differs')
        animation = animations[0]
        extras = animation.get('extras', {})
        require(extras.get('program') == recipe['program'] and extras.get('plan_sha256') == plan_sha,
                'serialized plan identity differs')
        require(extras.get('loop') is runtime['loop'] and extras.get('root_motion') is (mode == 'root_motion'),
                'serialized loop/root-motion declaration differs')
        require(glb.document.get('extras', {}).get('eonwildMotionStateTrack') == expected_state,
                'serialized contact state differs')
        require(runtime['rig_roles']['root'] in glb.name_to_node, 'motion root is not in the emitted rig')
        require(bool(animation.get('channels')), 'empty serialized animation')
        for channel in animation['channels']:
            sampler = animation['samplers'][channel['sampler']]
            tt = np.asarray(glb.accessor_values(sampler['input']), dtype=float).reshape(-1)
            require(tt.shape == times.shape and np.isfinite(tt).all() and np.allclose(tt, times, rtol=0, atol=2e-6),
                    'serialized timeline differs from the plan')
