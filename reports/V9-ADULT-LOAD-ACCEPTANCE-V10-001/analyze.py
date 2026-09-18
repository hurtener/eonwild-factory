"""Reopened V9/V10 emitted body, leg, and skin comparison."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import math
import sys

import numpy as np

REPO = Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-adult-load-acceptance')
TASK = Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521')
sys.path.insert(0, str(REPO / 'src'))

from eonwild_motion.factory.animal import scaled_contact_profile
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose
from eonwild_motion.solve.skin_rig import SkinRig

PACKAGES = {
    'v9': TASK / 'out/continuation-adult-v9-axial-jaw-001',
    'v10': TASK / 'out/tarbosaurus-adult-walk-load-acceptance-v10-94c81e7',
}
MODES = {'root_motion': 'root_motion.glb', 'in_place': 'in_place.glb'}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed_rotation_degrees(left: np.ndarray, right: np.ndarray, axis: np.ndarray) -> float:
    relative = right[:3, :3] @ np.linalg.inv(left[:3, :3])
    cosine = float(np.clip((np.trace(relative) - 1.) / 2., -1., 1.))
    angle = math.acos(cosine)
    if angle <= 1e-12:
        return 0.
    vector = np.array([
        relative[2, 1] - relative[1, 2],
        relative[0, 2] - relative[2, 0],
        relative[1, 0] - relative[0, 1],
    ]) / (2. * math.sin(angle))
    return math.degrees(angle) * float(vector @ axis)


def without_offsets(plan: dict) -> dict:
    result = json.loads(json.dumps(plan))
    result.pop('performance', None)
    for row in result['samples']:
        for foot in row['feet'].values():
            foot.pop('target_offset_m', None)
    return result


loaded = {}
result = {
    'schema': 'eonwild.motion.adult-load-acceptance-emitted-audit.v1',
    'classification': (
        'Reopened emitted TRS, full multi-influence foot skin, and compiler receipts. '
        'The load-acceptance response is authored kinematic art direction, not COM, '
        'force, work, mass response, biological validation, visual approval or Unity parity.'
    ),
    'source_head': '94c81e7e3bb00e2e6057fd1babb183adb70ff9e3',
    'packages': {},
}
for label, package in PACKAGES.items():
    plan = json.loads((package / 'plan.json').read_text())
    runtime = json.loads((package / 'runtime.json').read_text())
    recipe = json.loads((package / 'recipe.json').read_text())
    bio = json.loads((package / 'biomechanics.json').read_text())
    validation = json.loads((package / 'validation.json').read_text())
    contact = scaled_contact_profile(
        json.loads((REPO / recipe['contact_profile']['path']).read_text()),
        bio['geometry']['uniform_scale'],
    )
    up = np.asarray(runtime['up_axis'], dtype=float)
    forward = np.asarray(runtime['forward_axis'], dtype=float)
    lateral = np.cross(up, forward)
    role_names = runtime['rig_roles']
    step = plan['parameters']['step_period_s']
    duty = plan['parameters']['duty_factor']
    targets = {
        'DS_left_leads': (duty - .5) * step,
        'SS_left': duty * step,
        'DS_right_leads': (duty + .5) * step,
        'SS_right': (duty + 1.) * step,
    }
    package_data = {
        'manifest_sha256': sha(package / 'manifest.json'),
        'plan_sha256': sha(package / 'plan.json'),
        'recipe_sha256': sha(package / 'recipe.json'),
        'technical_status': validation['technical_status'],
        'solver_feasibility': validation['solver_feasibility'],
        'rotation_rates': validation['rotation_rates'],
        'articulation_envelopes': validation['articulation_envelopes'],
        'cyclic_continuity': validation['cyclic_continuity'],
        'skinned_contact': {
            'root_motion': validation['skinned_contact'],
            'in_place': validation['in_place_skinned_contact'],
        },
        'modes': {},
    }
    loaded[label] = {'plan': plan, 'modes': {}, 'up': up, 'forward': forward, 'lateral': lateral}
    for mode, filename in MODES.items():
        glb = Glb.from_bytes((package / filename).read_bytes())
        skin = SkinRig(glb, role_names, forward, up, contact)
        tracks, times = _clip_state(glb, glb.document['animations'][0]['name'])
        times = np.asarray(times, dtype=float)
        assert len(times) == len(plan['samples']) == 297
        nodes = {
            name: glb.name_to_node[role_names[name]]
            for name in ('root', 'pelvis', 'chest', 'head')
        }
        nodes['tail_tip'] = glb.name_to_node[role_names['tail'][-1]]
        worlds_by_key = []
        skin_gap = {side: [] for side in ('left', 'right')}
        for index in range(len(times)):
            worlds = skin.world(*_pose(glb, tracks, index))
            worlds_by_key.append(worlds)
            for side in ('left', 'right'):
                points = skin.skin(worlds, skin.foot_masks[side])
                gap = float(np.min(points @ up) - skin.ground)
                skin_gap[side].append(gap)
        landmarks = {}
        for name, target in targets.items():
            index = int(np.argmin(abs(times - target)))
            root_position = worlds_by_key[index][nodes['root'], :3, 3]
            landmarks[name] = {
                'index': index,
                'time_s': float(times[index]),
                'target_time_s': target,
                'time_error_s': float(times[index] - target),
                'contacts': [side for side in ('left', 'right')
                             if plan['samples'][index]['feet'][side]['contact']],
                'root_relative_role_positions_m': {
                    role: (worlds_by_key[index][node, :3, 3] - root_position).tolist()
                    for role, node in nodes.items() if role != 'root'
                },
                'foot_patch_minimum_gap_m': {
                    side: skin_gap[side][index] for side in ('left', 'right')
                },
            }
        swing_min = {}
        interior_swing_min = {}
        for side in ('left', 'right'):
            indices = [i for i, row in enumerate(plan['samples'])
                       if not row['feet'][side]['contact']]
            witness = min(indices, key=lambda i: skin_gap[side][i])
            swing_min[side] = {
                'minimum_gap_m': skin_gap[side][witness],
                'index': witness,
                'time_s': float(times[witness]),
            }
            interior = [
                i for i in indices
                if .25 <= plan['samples'][i]['feet'][side]['swing_phase'] <= .75
            ]
            interior_witness = min(interior, key=lambda i: skin_gap[side][i])
            interior_swing_min[side] = {
                'minimum_gap_m': skin_gap[side][interior_witness],
                'index': interior_witness,
                'time_s': float(times[interior_witness]),
                'swing_phase': plan['samples'][interior_witness]['feet'][side]['swing_phase'],
            }
        mode_data = {
            'glb_sha256': sha(package / filename),
            'sample_count': len(times),
            'landmarks': landmarks,
            'swing_full_patch_minimum_gap_m': swing_min,
            'interior_swing_25_to_75_full_patch_minimum_gap_m': interior_swing_min,
        }
        package_data['modes'][mode] = mode_data
        loaded[label]['modes'][mode] = {
            'times': times, 'worlds': worlds_by_key, 'nodes': nodes,
        }
    result['packages'][label] = package_data

assert without_offsets(loaded['v9']['plan']) == without_offsets(loaded['v10']['plan'])
result['preserved_plan_contract'] = {
    'parameters_and_rows_without_performance_or_internal_target_offsets_equal': True,
    'sample_count': len(loaded['v10']['plan']['samples']),
    'duration_s': loaded['v10']['plan']['duration_s'],
    'root_forward_terminal_m': loaded['v10']['plan']['samples'][-1]['root_forward_m'],
    'candidate_peak_compression_m': .01 * loaded['v10']['plan']['body_height_m'],
    'candidate_peak_added_vertical_acceleration_mps2': (
        24. * .01 * loaded['v10']['plan']['body_height_m']
        / loaded['v10']['plan']['parameters']['step_period_s'] ** 2
    ),
}
result['v10_minus_v9'] = {'modes': {}}
for mode in MODES:
    old = loaded['v9']['modes'][mode]
    new = loaded['v10']['modes'][mode]
    assert np.array_equal(old['times'], new['times'])
    mode_delta = {'landmarks': {}, 'maximum_role_position_delta_m': {}}
    for name, target in {
        'DS_left_leads': (.62 - .5) * 1.23,
        'SS_left': .62 * 1.23,
        'DS_right_leads': (.62 + .5) * 1.23,
        'SS_right': (.62 + 1.) * 1.23,
    }.items():
        index = int(np.argmin(abs(new['times'] - target)))
        row = {}
        for role in ('pelvis', 'chest', 'head', 'tail_tip'):
            old_root = old['worlds'][index][old['nodes']['root'], :3, 3]
            new_root = new['worlds'][index][new['nodes']['root'], :3, 3]
            old_position = old['worlds'][index][old['nodes'][role], :3, 3] - old_root
            new_position = new['worlds'][index][new['nodes'][role], :3, 3] - new_root
            delta = new_position - old_position
            row[role] = {
                'world_delta_m': delta.tolist(),
                'up_delta_m': float(delta @ loaded['v10']['up']),
                'forward_delta_m': float(delta @ loaded['v10']['forward']),
                'lateral_delta_m': float(delta @ loaded['v10']['lateral']),
                'signed_lateral_axis_rotation_delta_degrees': signed_rotation_degrees(
                    old['worlds'][index][old['nodes'][role]],
                    new['worlds'][index][new['nodes'][role]],
                    loaded['v10']['lateral'],
                ),
            }
        mode_delta['landmarks'][name] = {
            'index': index, 'time_s': float(new['times'][index]), 'roles': row,
        }
    for role in ('pelvis', 'chest', 'head', 'tail_tip'):
        values = []
        for index in range(len(new['times'])):
            old_root = old['worlds'][index][old['nodes']['root'], :3, 3]
            new_root = new['worlds'][index][new['nodes']['root'], :3, 3]
            old_position = old['worlds'][index][old['nodes'][role], :3, 3] - old_root
            new_position = new['worlds'][index][new['nodes'][role], :3, 3] - new_root
            values.append(float(np.linalg.norm(new_position - old_position)))
        witness = int(np.argmax(values))
        mode_delta['maximum_role_position_delta_m'][role] = {
            'value_m': values[witness], 'index': witness,
            'time_s': float(new['times'][witness]),
        }
    result['v10_minus_v9']['modes'][mode] = mode_delta

out = Path(__file__).with_name('result.json')
out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps({
    'result': str(out),
    'sha256': sha(out),
    'v10_manifest': result['packages']['v10']['manifest_sha256'],
    'v10_technical_status': result['packages']['v10']['technical_status'],
    'plan_preserved': result['preserved_plan_contract'],
    'root_motion_landmarks': result['v10_minus_v9']['modes']['root_motion']['landmarks'],
    'v10_swing_gaps': result['packages']['v10']['modes']['root_motion']['swing_full_patch_minimum_gap_m'],
}, indent=2, allow_nan=False))
