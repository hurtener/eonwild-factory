"""Locked candidate identity and non-shortcut regressions; not visual approval."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.planning.grounded_gait import load_grounded_gait

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_text())


@pytest.mark.parametrize('name,version', [('sprint',4),('fast-walk',2)])
def test_candidate_owns_versioned_metadata_and_exact_input_hashes(name,version):
    recipe = read(f'recipes/heavy-biped/{name}.v{version}.json')
    assert recipe['id'] == f'heavy-biped.{name}.v{version}'
    assert recipe['version'] == version
    assert recipe['supersedes'] == f'heavy-biped.{name}.v{version-1}'
    for key in ('source','rig','contact_profile','performance_profile','program_profile'):
        reference = recipe[key]
        assert hashlib.sha256((ROOT/reference['path']).read_bytes()).hexdigest() == reference['sha256']
    assert recipe['program_profile']['path'] == f'catalog/programs/heavy-biped.{name}.v{version}.json'


def test_full_stride_sprint_does_not_change_speed_flight_or_any_limb_gate():
    before = asdict(load_airborne_gait(read('catalog/programs/heavy-biped.sprint.v3.json')))
    after = asdict(load_airborne_gait(read('catalog/programs/heavy-biped.sprint.v4.json')))
    for key in ('step_length_body_heights','step_period_s','flight_fraction','flight_height_body_heights',
                'hip_extension_limit_degrees','hip_flexion_limit_degrees','knee_min_interior_degrees',
                'knee_max_interior_degrees','ankle_min_interior_degrees','ankle_max_interior_degrees',
                'max_joint_angular_velocity_degrees_per_s','max_ankle_pitch_velocity_degrees_per_s',
                'push_off_pitch_degrees','toe_flex_degrees','cycles','sample_hz','boundary_sample_hz'):
        assert after[key] == before[key], key
    assert after['step_length_body_heights'] == 1.55
    assert after['step_period_s'] == 23/48
    assert after['swing_transport_ramp_fraction'] > 0
    assert after['swing_lower_fraction'] > before['swing_lower_fraction']


def test_fast_walk_remains_a_grounded_program_not_a_retimed_run():
    recipe = read('recipes/heavy-biped/fast-walk.v2.json')
    assert recipe['program'] == 'grounded_gait'
    gait = load_grounded_gait(read(recipe['program_profile']['path']))
    assert gait.duty_factor > .5
    assert gait.step_length_body_heights == .6
    assert gait.step_period_s == .8
