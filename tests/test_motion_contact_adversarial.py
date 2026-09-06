"""Adversarial coordinate/continuity contracts, separate from visual approval."""
from copy import deepcopy
import math
import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.quality import emitted_cyclic_continuity
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.performance import phase_and_gain
from eonwild_motion.solve.skin_targets import evaluate_skin, _cyclic_fill
from eonwild_motion.solve.whole_body_gait_transition import _build_glb
from test_v9_airborne_gait import fixture


@pytest.mark.parametrize('row', [
    {'time_s': 0, 'performance_gain': True},
    {'time_s': 0, 'performance_gain': -0.1},
    {'time_s': 0, 'performance_gain': 1.1},
    {'time_s': 0, 'performance_gain': math.nan},
    {'time_s': 0, 'locomotion_time_s': math.inf},
    {'time_s': 0, 'locomotion_time_s': -1},
])
def test_phase_and_gain_fail_closed(row):
    with pytest.raises(ContractError):
        phase_and_gain(row)


def test_transition_uses_locomotion_clock_not_action_clock():
    assert phase_and_gain({'time_s': 4.2, 'locomotion_time_s': .3, 'performance_gain': .4}) == (.3, .4)
    assert phase_and_gain({'time_s': 4.2}) == (4.2, 1.)


def test_one_shot_skin_corrections_never_wrap_between_unrelated_endpoints():
    times = np.arange(7, dtype=float)
    values = np.zeros((7, 3))
    values[2] = [1., 2., 3.]
    values[4] = [7., 8., 9.]
    loaded = np.array([False, False, True, False, True, False, False])
    actual = _cyclic_fill(times, values, loaded, loop=False)
    assert np.array_equal(actual[0], values[2])
    assert np.array_equal(actual[1], values[2])
    assert np.array_equal(actual[5], values[4])
    assert np.array_equal(actual[6], values[4])
    assert np.array_equal(actual[loaded], values[loaded])
    assert np.all(actual[3] > values[2]) and np.all(actual[3] < values[4])
    assert not np.array_equal(_cyclic_fill(times, values, loaded), actual)


def frames_in_place():
    frames = []
    for time in np.linspace(0., 1., 11):
        feet = {}
        for side, lane in (('left', -.15), ('right', .15)):
            points = [{'point_m': [float(-time + dx), 0., lane + dz]} for dx, dz in ((0, 0), (.04, 0), (0, .05))]
            feet[side] = {'sole_points': deepcopy(points), 'toe_points': deepcopy(points)}
        frames.append({'time_s': float(time), 'root_m': [0., 0., 0.], 'feet': feet})
    return frames


def support_plan():
    return {'loop': False, 'samples': [{'time_s': float(t), 'root_forward_m': float(t),
        'feet': {side: {'contact': True} for side in ('left', 'right')}} for t in np.linspace(0, 1, 11)]}


def test_in_place_skin_requires_the_correct_motor_travel(monkeypatch):
    frames = frames_in_place()
    before = deepcopy(frames)
    monkeypatch.setattr('eonwild_motion.solve.skin_targets.skin_frames', lambda *args: (frames, {}))
    profile = {'geometry': {'ground': {'up_axis': 'Y', 'level_m': 0.}}}
    plan = support_plan()
    offsets = np.array([[r['root_forward_m'], 0, 0] for r in plan['samples']])
    assert evaluate_skin(None, profile, plan)['verdict'] == 'FAIL'
    assert evaluate_skin(None, profile, plan, world_offsets=offsets)['verdict'] == 'PASS'
    assert evaluate_skin(None, profile, plan, world_offsets=offsets * 2)['verdict'] == 'FAIL'
    # The audit must not mutate the skin frames, floor, or input plan.
    assert frames == before
    assert profile['geometry']['ground']['level_m'] == 0


@pytest.mark.parametrize('offsets', [[], [[0., 0., 0.]], [[math.nan, 0., 0.]] * 11, [[0., 0.]] * 11])
def test_in_place_reconstruction_cannot_accept_missing_or_nonfinite_samples(monkeypatch, offsets):
    monkeypatch.setattr('eonwild_motion.solve.skin_targets.skin_frames', lambda *args: (frames_in_place(), {}))
    with pytest.raises(ContractError):
        evaluate_skin(None, {'geometry': {'ground': {'up_axis': 'Y', 'level_m': 0.}}}, support_plan(), world_offsets=offsets)


def serialized_clip(times, angles, *, flip_signs=False, travel=None):
    source, roles = fixture()
    node = source.name_to_node[roles['root']]
    radians = np.radians(angles)
    rotations = np.column_stack((np.zeros(len(times)), np.sin(radians / 2), np.zeros(len(times)), np.cos(radians / 2)))
    if flip_signs:
        rotations[1::2] *= -1
    translations = np.zeros((len(times), 3))
    translations[:, 2] = np.asarray(times) if travel is None else travel
    raw = _build_glb(source, 'continuity-witness', np.asarray(times),
        {(node, 'rotation'): rotations, (node, 'translation'): translations}, 'adversarial-test', {})
    return Glb.from_bytes(raw)


def test_cyclic_velocity_is_native_time_and_quaternion_sign_invariant():
    times = np.linspace(0., 2., 241)
    angles = 8 * np.sin(math.pi * times)
    for flip in (False, True):
        report = emitted_cyclic_continuity(serialized_clip(times, angles, flip_signs=flip), loop=True)
        assert report['status'] == 'PASS'
        assert report['maximum_angular_velocity_seam_degrees_per_s'] < .01


def test_endpoint_pose_closure_cannot_hide_angular_velocity_jump():
    times = np.linspace(0., 1., 121)
    angles = 45 * times * (1 - times)
    assert angles[0] == angles[-1] == 0
    report = emitted_cyclic_continuity(serialized_clip(times, angles), loop=True)
    assert report['status'] == 'FAIL'
    assert report['maximum_angular_velocity_seam_degrees_per_s'] == pytest.approx(90, abs=.01)


def test_endpoint_root_displacement_cannot_hide_speed_jump():
    times = np.linspace(0., 1., 121)
    report = emitted_cyclic_continuity(serialized_clip(times, np.zeros_like(times), travel=times**2), loop=True)
    assert report['status'] == 'FAIL'
    assert report['maximum_linear_velocity_seam_m_per_s'] == pytest.approx(2, abs=.001)


def test_cyclic_gate_does_not_claim_a_one_shot_is_a_loop():
    times = np.linspace(0., 1., 121)
    assert emitted_cyclic_continuity(serialized_clip(times, 30 * times), loop=False)['status'] == 'NOT_APPLICABLE'
