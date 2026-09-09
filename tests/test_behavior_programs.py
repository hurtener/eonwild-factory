"""Behavior-program contracts; geometric fixtures are not species approval."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.airborne_gait import load_airborne_gait, sample_airborne_gait
from eonwild_motion.planning.grounded_gait import load_grounded_gait, sample_grounded_gait
from eonwild_motion.planning.gait_transition import GaitTransition, _Choreography, build_transition_plan, load_gait_transition
from eonwild_motion.planning.supported_action import curve, load_supported_action, resample_chain

ROOT = Path(__file__).resolve().parents[1]


def profile(name):
    return json.loads((ROOT / 'catalog/programs' / f'heavy-biped.{name}.json').read_text())


def gait(name):
    payload = profile(name)
    return load_grounded_gait(payload) if payload['schema'].endswith('grounded-gait.v1') else load_airborne_gait(payload)


@pytest.mark.parametrize('count', [1, 2, 3, 7, 11, 32])
@pytest.mark.parametrize('values', [[1., 8., -3., 5.], [-4., -1., -9.], [2., -2., 7., -7.], [1.]])
def test_chain_mapping_conserves_signed_integral(values, count):
    result = resample_chain(values, count)
    assert result.shape == (count,)
    assert abs(sum(result) - sum(values)) < 1e-12


@pytest.mark.parametrize('values,count', [([True], 2), ([float('nan')], 3), ([1], True), ([1], 0), ([], 2), ([1], 129)])
def test_chain_mapping_rejects_invalid_inputs(values, count):
    with pytest.raises(ContractError):
        resample_chain(values, count)


@pytest.mark.parametrize('time,keys', [(True, [[0, 0], [1, 1]]), (float('inf'), [[0, 0], [1, 1]]),
    (0, [[0, True], [1, 1]]), (0, [[0, 0], [0, 1]]), (0, [[0, 0], [1, float('nan')]])])
def test_behavior_curves_fail_closed(time, keys):
    with pytest.raises(ContractError):
        curve(time, keys)


def test_curve_preserves_shape_and_rest_endpoint_velocity():
    keys = [[0, 0], [.3, .8], [1, 1], [2, 0]]
    sampled = [curve(float(t), keys) for t in np.linspace(0, 2, 501)]
    assert min(sampled) >= 0 and max(sampled) <= 1
    h = 1e-5
    assert abs((curve(h, keys) - curve(0, keys)) / h) < .001
    assert abs((curve(2, keys) - curve(2 - h, keys)) / h) < .001


@pytest.mark.parametrize('name', ['idle.v1', 'alert.v1', 'call.v1', 'bite-miss.v1', 'feeding.v1'])
def test_restored_behavior_profiles_are_typed(name):
    action = load_supported_action(profile(name))
    assert len(action.support_reach_body_heights) == 2
    assert len(action.translation_scale_body_heights) == 3
    assert action.duration_seconds > 0


@pytest.mark.parametrize('field,value', [('sample_hz', True), ('loop', 1), ('translation_scale_body_heights', [1, 1]),
    ('translation_scale_body_heights', [1, float('inf'), 1]), ('support_reach_body_heights', [0, 2]),
    ('support_reach_body_heights', [True, 0]), ('max_joint_rate_degrees_per_second', 1201)])
def test_supported_profile_rejects_unsafe_parameters(field, value):
    payload = profile('feeding.v1')
    payload[field] = value
    with pytest.raises(ContractError):
        load_supported_action(payload)


def test_event_timing_and_limits_are_not_silently_repaired():
    payload = profile('bite-miss.v1')
    payload['events'] = list(reversed(payload['events']))
    with pytest.raises(ContractError):
        load_supported_action(payload)
    payload = profile('feeding.v1')
    payload['support_limits']['knee_interior_degrees'] = [155, 80]
    with pytest.raises(ContractError):
        load_supported_action(payload)


@pytest.mark.parametrize('name', ['walk.v2', 'reverse-walk.v3', 'run.v3', 'sprint.v3'])
@pytest.mark.parametrize('kind', ['start', 'stop'])
def test_transition_keeps_stance_anchors_and_signed_root_authority(name, kind):
    locomotion = gait(name)
    transition = GaitTransition(kind)
    plan = build_transition_plan(transition, locomotion, 2.5)
    rows = plan['samples']
    assert not plan['loop']
    assert rows[0]['time_s'] == 0 and rows[-1]['time_s'] == plan['duration_s']
    assert np.all(np.diff([r['time_s'] for r in rows]) > 0)
    sign = np.sign(locomotion.step_length_body_heights)
    assert all(sign * r['root_velocity_mps'] >= 0 for r in rows)
    assert np.min(sign * np.diff([r['root_forward_m'] for r in rows])) >= -1e-12
    for a, b in zip(rows, rows[1:]):
        for side in ('left', 'right'):
            fa, fb = a['feet'][side], b['feet'][side]
            if fa['contact'] and fb['contact'] and fa['touchdown_time_s'] == fb['touchdown_time_s']:
                assert abs(fa['forward_m'] - fb['forward_m']) < 1e-12
        assert b['support_count'] == sum(int(f['contact']) for f in b['feet'].values())
        assert b['flight'] == (b['support_count'] == 0)
    if name.startswith(('walk', 'reverse')):
        assert not any(r['flight'] for r in rows)
    ready = rows[0] if kind == 'start' else rows[-1]
    assert ready['root_velocity_mps'] == 0 and ready['root_acceleration_mps2'] == 0
    assert ready['support_count'] == 2
    for foot in ready['feet'].values():
        assert foot['height_m'] == 0 and foot['foot_pitch_degrees'] == 0 and foot['toe_flex_degrees'] == 0
    assert all(not cue['authoritative_world_fact'] for cue in plan['events'])


@pytest.mark.parametrize('name', ['walk.v2', 'reverse-walk.v3', 'run.v3', 'sprint.v3'])
def test_start_joins_the_actual_locomotion_plan_not_just_its_root(name):
    locomotion = gait(name)
    c = _Choreography(GaitTransition('start'), locomotion, 2.5)
    sampler = sample_grounded_gait if name.startswith(('walk', 'reverse')) else sample_airborne_gait
    for phase in (.55, .69, .8, .97, 1.):
        active = c.ramp + phase * c.period
        row = c.sample(c.delay + active)
        expected = sampler(locomotion, active, c.height)
        assert row['support_count'] == expected['support_count']
        assert abs(row['pelvis_height_offset_m'] - expected['pelvis_height_offset_m']) < 1e-10
        for side in ('left', 'right'):
            actual, wanted = row['feet'][side], expected['feet'][side]
            assert actual['contact'] == wanted['contact']
            for key in ('height_m', 'foot_pitch_degrees', 'toe_flex_degrees', 'swing_phase'):
                assert abs(actual[key] - wanted[key]) < 1e-8, (name, phase, side, key, actual[key], wanted[key])
            assert abs((actual['forward_m'] - row['root_forward_m']) - (wanted['forward_m'] - expected['root_forward_m'])) < 1e-9


@pytest.mark.parametrize('name', ['walk.v2', 'reverse-walk.v3', 'run.v3', 'sprint.v3'])
def test_stop_enters_exactly_at_steady_phase_zero(name):
    locomotion = gait(name)
    c = _Choreography(GaitTransition('stop'), locomotion, 2.5)
    actual = c.sample(0.)
    expected = c.sampler(locomotion, 0., c.height)
    for side in ('left', 'right'):
        for key in ('forward_m', 'height_m', 'foot_pitch_degrees', 'toe_flex_degrees', 'swing_phase'):
            assert abs(actual['feet'][side][key] - expected['feet'][side][key]) < 1e-8


@pytest.mark.parametrize('kind', ['start', 'stop'])
def test_root_integration_matches_velocity_and_acceleration(kind):
    c = _Choreography(GaitTransition(kind), gait('run.v3'), 2.5)
    h = 1e-5
    for u in (.05, .2, .5, .8, .95):
        t = c.ramp * u
        x, v, a = c.root(t)
        before, after = c.root(t - h), c.root(t + h)
        assert abs((after[0] - before[0]) / (2 * h) - v) < 1e-7
        assert abs((after[1] - before[1]) / (2 * h) - a) < 1e-7


@pytest.mark.parametrize('parameters', [{'kind': 'rewind'}, {'kind': 'start', 'ramp_cycles': True},
    {'kind': 'stop', 'sample_hz': 0}, {'kind': 'start', 'anticipation_seconds': float('nan')},
    {'kind': 'stop', 'boundary_sample_hz': 100}, {'kind': 'start', 'minimum_swing_scale': 0}])
def test_transition_rejects_malformed_profiles(parameters):
    with pytest.raises(ContractError):
        load_gait_transition({'schema': 'eonwild.motion.gait-transition.v1', 'parameters': parameters})
