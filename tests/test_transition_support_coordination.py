"""Prospective placements preserve the bound gait rather than shorten it.

Planner tests are not final skinned handoff acceptance; CI checks both exports.
"""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.airborne_gait import load_airborne_gait, build_airborne_plan
from eonwild_motion.planning.grounded_gait import GroundedGait, load_grounded_gait, build_grounded_plan
from eonwild_motion.planning.gait_transition import (
    GaitTransition, _Choreography, build_transition_plan, declared_handoff_phase,
)
from eonwild_motion.planning.parameters import gait_parameters

ROOT = Path(__file__).resolve().parents[1]
STEADY = ('walk.v3', 'reverse-walk.v4', 'run.v4', 'sprint.v4')


def gait(name):
    data = json.loads((ROOT / 'catalog/programs' / ('heavy-biped.' + name + '.json')).read_text())
    return load_grounded_gait(data) if 'grounded' in data['schema'] else load_airborne_gait(data)


def choreography(name, kind):
    bound = gait(name)
    return _Choreography(GaitTransition(kind, support_placement='integrated_support',
        handoff_phase_fraction=.125, handoff_sample_hz=bound.handoff_sample_hz), bound, 2.6416714066117652)


@pytest.mark.parametrize('name', STEADY)
@pytest.mark.parametrize('kind', ['start', 'stop'])
def test_committed_support_is_immutable_and_bound_gait_is_unchanged(name, kind):
    c = choreography(name, kind)
    before = asdict(c.gait)
    plan = build_transition_plan(c.transition, c.gait, c.height)
    assert plan['parameters'] == gait_parameters(c.gait)
    assert before == asdict(c.gait)
    assert plan['same_foot_cycle_s'] == 2 * c.gait.step_period_s
    assert all(not cue['authoritative_world_fact'] for cue in plan['events'])
    if c.grounded:
        for side in ('left', 'right'):
            assert {row['feet'][side]['contact'] for row in plan['samples']} == {False, True}
    sign = np.sign(c.speed)
    assert min(sign * np.diff([r['root_forward_m'] for r in plan['samples']])) >= -1e-12
    for a, b in zip(plan['samples'], plan['samples'][1:]):
        for side in ('left', 'right'):
            fa, fb = a['feet'][side], b['feet'][side]
            if fa['contact'] and fb['contact'] and fa['touchdown_time_s'] == fb['touchdown_time_s']:
                assert fa['forward_m'] == fb['forward_m']


def test_accelerating_sprint_releases_low_speed_support_before_body_runs_away():
    c = choreography('sprint.v4', 'start')
    old = _Choreography(replace(c.transition, support_placement='instantaneous_speed'), c.gait, c.height)
    touchdown = c.period
    assert c.liftoff(touchdown) < old.liftoff(touchdown)
    travel = c.root(c.liftoff(touchdown))[0] - c.root(touchdown)[0]
    expected = c.root(touchdown)[0] + c.reach * travel / (c.speed * c.stance)
    assert abs(c.touchdown(touchdown) - expected) < 1e-12
    assert c.touchdown(touchdown) > old.touchdown(touchdown)
    # Reproduce the old infeasible support interval, not a changed envelope.
    time = 1.4114583333333333
    assert old.foot('left', time)['contact']
    assert not c.foot('left', time)['contact']
    assert c.gait.step_length_body_heights == 1.55
    assert c.gait.step_period_s == 23 / 48
    assert c.gait.flight_fraction == .22
    assert c.gait.max_joint_angular_velocity_degrees_per_s == 1200


@pytest.mark.parametrize('name', STEADY)
def test_loaded_interface_is_on_the_bound_clock_and_has_persistent_contact_context(name):
    c = choreography(name, 'start')
    builder = build_grounded_plan if c.grounded else build_airborne_plan
    steady = builder(c.gait, c.height)
    phase = declared_handoff_phase(c.transition, c.gait)
    matches = [r for r in steady['samples'] if abs(r['time_s'] - phase) < 1e-9]
    assert len(matches) == 1
    index = steady['samples'].index(matches[0])
    native = [row['time_s'] for row in steady['samples'][index - 2:index + 3]]
    assert np.diff(native) == pytest.approx(np.full(4, 1 / c.gait.handoff_sample_hz))
    expected = matches[0]
    plan = build_transition_plan(c.transition, c.gait, c.height)
    contract = plan['transition_contract']
    assert contract['steady_phase_s'] == phase > 0
    assert contract['exit_pose'] == 'locomotion_declared_phase'
    assert contract['interface_schema'] == 'eonwild.motion.gait-interface.v2'
    a = plan['samples'][-1]
    assert a['root_velocity_mps'] == c.speed
    assert a['support_count'] == expected['support_count'] > 0
    for side in ('left', 'right'):
        f, g = a['feet'][side], expected['feet'][side]
        assert f['contact'] == g['contact']
        assert abs(f['forward_m'] - a['root_forward_m'] - (g['forward_m'] - expected['root_forward_m'])) < 1e-9
        for key in ('height_m', 'foot_pitch_degrees', 'toe_flex_degrees', 'swing_phase'):
            assert abs(f[key] - g[key]) < 1e-8
        if f['contact']:
            assert all(r['feet'][side]['contact'] for r in plan['samples'][-3:])


def test_bound_gait_rejects_a_transition_with_a_different_interface():
    bound = gait('sprint.v4')
    with pytest.raises(ContractError, match='differs from the bound gait'):
        declared_handoff_phase(
            GaitTransition('start', handoff_phase_fraction=.1), bound,
        )


def test_bound_gait_rejects_a_transition_with_a_different_interface_rate():
    bound = gait('sprint.v4')
    with pytest.raises(ContractError, match='sample rate differs'):
        declared_handoff_phase(GaitTransition('start', handoff_phase_fraction=.125,
            handoff_sample_hz=960), bound)


def test_phase_zero_interface_keeps_requested_dense_transition_context():
    bound = GroundedGait(cycles=1, sample_hz=120,
        handoff_phase_fraction=0, handoff_sample_hz=960)
    transition = GaitTransition('stop', handoff_phase_fraction=0,
        boundary_sample_hz=480, handoff_sample_hz=960)
    plan = build_transition_plan(transition, bound, 2.0)
    times = np.asarray([row['time_s'] for row in plan['samples'][:3]])
    assert np.diff(times) == pytest.approx([1 / 960, 1 / 960])


def test_absent_interface_fields_preserve_legacy_plan_parameters():
    bound = GroundedGait(cycles=1, sample_hz=120)
    steady = build_grounded_plan(bound, 2.0)
    transition = build_transition_plan(GaitTransition('start'), bound, 2.0)
    for parameters in (steady['parameters'], transition['parameters']):
        assert 'handoff_phase_fraction' not in parameters
        assert 'handoff_sample_hz' not in parameters
        assert 'boundary_sample_hz' not in parameters
    assert 'handoff_sample_hz' not in transition['transition_parameters']


@pytest.mark.parametrize('name', STEADY)
def test_stop_preserves_the_in_progress_swing_target_at_the_declared_phase(name):
    c = choreography(name, 'stop')
    actual = c.sample(0)
    expected = c.sampler(c.gait, c.join_phase, c.height)
    for side in ('left', 'right'):
        a, b = actual['feet'][side], expected['feet'][side]
        assert a['contact'] == b['contact']
        assert abs(a['forward_m'] - (b['forward_m'] - expected['root_forward_m'])) < 1e-9
        for key in ('height_m', 'foot_pitch_degrees', 'toe_flex_degrees', 'swing_phase'):
            assert abs(a[key] - b[key]) < 1e-8
    end = c.sample(c.duration)
    assert end['root_velocity_mps'] == 0
    assert end['support_count'] == 2
    assert all(f['height_m'] == 0 for f in end['feet'].values())


@pytest.mark.parametrize('field,value', [
    ('handoff_phase_fraction', True), ('handoff_phase_fraction', float('nan')),
    ('handoff_phase_fraction', -.01), ('handoff_phase_fraction', .26),
    ('support_placement', 'slide'), ('support_placement', None),
])
def test_invalid_interface_or_contact_policy_fails_closed(field, value):
    with pytest.raises(ContractError):
        GaitTransition('start', **{field: value})


@pytest.mark.parametrize('name', STEADY)
@pytest.mark.parametrize('kind', ['start', 'stop'])
def test_new_recipes_lock_current_steady_inputs_without_retiming(name, kind):
    base = name.rsplit('.v', 1)[0]
    recipe = json.loads((ROOT / f'recipes/heavy-biped/{base}-{kind}.v3.json').read_text())
    steady = json.loads((ROOT / f'recipes/heavy-biped/{name}.json').read_text())
    assert recipe['id'] == f'heavy-biped.{base}-{kind}.v3' and recipe['version'] == 3
    for key in ('source', 'rig', 'contact_profile', 'performance_profile', 'forward_axis', 'up_axis'):
        assert recipe[key] == steady[key]
    assert recipe['gait_profile'] == steady['program_profile']
    for key in ('source', 'rig', 'contact_profile', 'performance_profile', 'program_profile', 'gait_profile'):
        binding = recipe[key]
        assert hashlib.sha256((ROOT / binding['path']).read_bytes()).hexdigest() == binding['sha256']
