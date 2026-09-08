"""Regression witnesses for articulation, recipe reuse, and real cyclic contact."""
from copy import deepcopy
from dataclasses import replace
import math
from pathlib import Path
import json

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.airborne_gait import AirborneGait, build_airborne_plan
from eonwild_motion.planning.gait_transition import GaitTransition, build_transition_plan
from eonwild_motion.planning.grounded_gait import GroundedGait, sample_grounded_gait, build_grounded_plan
from eonwild_motion.factory.io import digest, json_bytes
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import (
    _clip_state, _pose, _rotation_from_matrix, _world_matrices,
    _world_position,
)
from eonwild_motion.solve.airborne_gait import solve_airborne_gait
from eonwild_motion.solve.performance import (
    Performance, _support_timed_axial_clock,
    _support_timed_pelvis_forward_carrier,
    _support_timed_sagittal_pulse, apply_performance,
    decorate_plan, load_performance, phase_and_gain,
)
from test_v9_airborne_gait import fixture
from eonwild_motion.solve.skin_rig import rotation_matrix
from eonwild_motion.solve.skin_targets import cyclic_authority, _cyclic_fill
from eonwild_motion.dynamics.contact_authority import PatchFrame, AuthorityThresholds


@pytest.mark.parametrize('length', [.6, -.38])
def test_articulated_grounded_stroke_is_not_the_old_shuffle(length):
    gait = GroundedGait(step_length_body_heights=length, toe_flex_degrees=24,
        foot_recovery_pitch_degrees=28, push_off_pitch_degrees=20, rounded_swing_peak_fraction=.42)
    plan = build_grounded_plan(gait, 2.5)
    rows = plan['samples']
    assert rows[-1]['root_forward_m'] == pytest.approx(2 * gait.cycles * length * 2.5)
    assert not any(row['flight'] for row in rows)
    assert {row['support_count'] for row in rows} == {1, 2}
    foot = [row['feet']['left'] for row in rows]
    assert max(f['toe_flex_degrees'] for f in foot) > 23
    assert min(f['foot_pitch_degrees'] for f in foot) < -25
    assert max(f['foot_pitch_degrees'] for f in foot) > 18
    assert max(f['height_m'] for f in foot) > .1


@pytest.mark.parametrize('boundary', ['release', 'touchdown'])
def test_authored_ankle_and_toes_have_continuous_release(boundary):
    gait = GroundedGait(toe_flex_degrees=24,foot_recovery_pitch_degrees=28,push_off_pitch_degrees=20)
    period = 2 * gait.step_period_s
    t = period * gait.duty_factor if boundary == 'release' else period
    eps = 1e-6
    frames = [sample_grounded_gait(gait, t + d, 2.)['feet']['left'] for d in [-eps, 0, eps]]
    for key in ['height_m','forward_m','foot_pitch_degrees','toe_flex_degrees']:
        assert abs(frames[0][key] - frames[2][key]) < 1e-5


@pytest.mark.parametrize('parameters', [{'lane_width_body_heights':0}, {'tail_yaw_degrees':100}, {'center_tail':1}, {'gaze_elevation_degrees':float('nan')}, {'pelvis_sway_body_heights':.1}])
def test_performance_rejects_invalid_or_unbounded_controls(parameters):
    with pytest.raises(ContractError): Performance(**parameters)


def test_performance_has_no_shared_mutable_plan_state():
    plan = build_grounded_plan(GroundedGait(),2.)
    before = json.dumps(plan,sort_keys=True)
    a = decorate_plan(plan,Performance())
    b = decorate_plan(plan,Performance(gaze_elevation_degrees=5))
    a['samples'][0]['feet']['left']['forward_m']=99
    assert json.dumps(plan,sort_keys=True)==before
    assert b['samples'][0]['feet']['left']['forward_m']!=99
    with pytest.raises(ContractError): load_performance({'schema':'eonwild.motion.performance.v1','parameters':{'mystery':3}})


def test_opt_in_body_carriers_preserve_legacy_plan_bytes():
    plan = build_grounded_plan(GroundedGait(), 2.)
    assert digest(json_bytes(plan)) == "d072715a03d517df64c43553d69311fec94b020b002bce46ce1a0215ca9e066c"
    assert "pelvis_height_carrier" not in plan["parameters"]
    decorated = decorate_plan(plan, Performance())
    assert digest(json_bytes(decorated)) == "cb07b756443ee231d12bec2a5e948a23f8a31ea8048a937966c0ed2e90e4dce3"
    assert "support_directed_pelvis_carrier" not in decorated["performance"]
    assert "support_timed_axial_carrier" not in decorated["performance"]


@pytest.mark.parametrize("value", [True, False, 0, "bounce", float("nan")])
def test_grounded_rejects_malformed_pelvis_height_carrier(value):
    with pytest.raises(ContractError):
        GroundedGait(pelvis_height_carrier=value)


@pytest.mark.parametrize("value", [0, 1, "yes", float("nan")])
def test_performance_rejects_malformed_support_carrier(value):
    with pytest.raises(ContractError):
        Performance(support_directed_pelvis_carrier=value)


def test_support_carrier_is_grounded_only_even_when_explicitly_false():
    airborne = build_airborne_plan(AirborneGait(cycles=1, sample_hz=24), 2.)
    for value in (False, True):
        with pytest.raises(ContractError, match="requires grounded locomotion"):
            decorate_plan(
                airborne,
                Performance(support_directed_pelvis_carrier=value),
            )


@pytest.mark.parametrize("value", [0, 1, "yes", float("nan")])
def test_performance_rejects_malformed_support_timed_axial_carrier(value):
    with pytest.raises(ContractError):
        Performance(support_timed_axial_carrier=value)


def test_support_timed_axial_carrier_requires_centered_tail_and_grounded_plan():
    with pytest.raises(ContractError, match="requires centered tail semantics"):
        Performance(support_timed_axial_carrier=True, center_tail=False)
    airborne = build_airborne_plan(AirborneGait(cycles=1, sample_hz=24), 2.)
    for value in (False, True):
        with pytest.raises(ContractError, match="requires grounded locomotion"):
            decorate_plan(
                airborne,
                Performance(support_timed_axial_carrier=value),
            )


def _axial_performance_plan(gait, **changes):
    values = {
        "pelvis_sway_body_heights": 0,
        "pelvis_roll_degrees": 0,
        "pelvis_yaw_degrees": 2,
        "tail_yaw_degrees": 16,
        "gaze_elevation_degrees": 0,
        "center_tail": True,
        "support_timed_axial_carrier": True,
        "skin_refinement": False,
    }
    values.update(changes)
    return decorate_plan(build_grounded_plan(gait, 2.), Performance(**values))


def _forward_position(worlds, node, forward):
    return float(np.asarray(_world_position(worlds[node])) @ forward)


@pytest.mark.parametrize("mirrored_roles", [False, True])
def test_axial_clock_advances_leading_semantic_hip_in_renamed_scaled_frame(
        mirrored_roles):
    source, roles = fixture("renamed_axial_", 1.6, upper_body=True)
    if mirrored_roles:
        roles["legs"]["left"], roles["legs"]["right"] = (
            roles["legs"]["right"], roles["legs"]["left"])
    up = np.array([0., 1., 0.])
    forward = np.array([1., 0., 1.]) / math.sqrt(2)
    lateral = np.cross(up, forward)
    gait = GroundedGait(
        step_period_s=1.23,
        duty_factor=.62,
        step_length_body_heights=.6,
        cycles=1,
        sample_hz=120,
    )
    plan = _axial_performance_plan(gait)
    hips = {
        side: source.name_to_node[roles["legs"][side]["contactChain"][0]]
        for side in ("left", "right")
    }
    base = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)
    hip_midpoint = sum(
        (np.asarray(_world_position(base[node])) for node in hips.values()),
        np.zeros(3),
    ) / 2
    left_offset = float(
        (np.asarray(_world_position(base[hips["left"]])) - hip_midpoint) @ lateral)

    for side, time in (
            ("left", (gait.duty_factor - .5) * gait.step_period_s),
            ("right", (gait.duty_factor + .5) * gait.step_period_s)):
        row = sample_grounded_gait(gait, time, 2.)
        _, posed = _performance_pose(source, roles, plan, row, up, forward)
        other = "right" if side == "left" else "left"
        leading_advance = (
            _forward_position(posed, hips[side], forward)
            - _forward_position(base, hips[side], forward))
        trailing_advance = (
            _forward_position(posed, hips[other], forward)
            - _forward_position(base, hips[other], forward))
        assert leading_advance > trailing_advance
        _, _, pulse = _support_timed_axial_clock(
            source, base, roles, plan, time, 1., lateral)
        expected_sign = -math.copysign(1., left_offset) if side == "left" else math.copysign(1., left_offset)
        assert math.copysign(1., pulse) == expected_sign


def test_axial_clock_is_periodic_zero_at_single_support_and_scales_with_gain():
    source, roles = fixture("axial_clock_", 1.3, upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([.6, 0., .8])
    lateral = np.cross(up, forward)
    gait = GroundedGait(
        step_period_s=1.23, duty_factor=.62,
        step_length_body_heights=.6, cycles=1, sample_hz=120)
    plan = _axial_performance_plan(gait)
    base = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)
    cycle = 2 * gait.step_period_s
    for step_index in (0, 1):
        stance = (step_index + gait.duty_factor) * gait.step_period_s
        _, _, pulse = _support_timed_axial_clock(
            source, base, roles, plan, stance, 1., lateral)
        assert pulse == pytest.approx(0, abs=1e-14)
    for time in (.1476, .611, 1.3776):
        full = _support_timed_axial_clock(
            source, base, roles, plan, time, 1., lateral)[2]
        half = _support_timed_axial_clock(
            source, base, roles, plan, time, .5, lateral)[2]
        repeated = _support_timed_axial_clock(
            source, base, roles, plan, time + cycle, 1., lateral)[2]
        assert half == pytest.approx(.5 * full, abs=1e-14)
        assert repeated == pytest.approx(full, abs=1e-14)
    h = 1e-5
    values = [
        _support_timed_axial_clock(
            source, base, roles, plan, offset, 1., lateral)[2]
        for offset in (-h, 0., h, cycle - h, cycle, cycle + h)
    ]
    assert values[:3] == pytest.approx(values[3:], abs=1e-12)


def test_axial_clock_rejects_conflicting_or_malformed_choreography():
    source, roles = fixture("axial_bad_", 1., upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([0., 0., 1.])
    lateral = np.cross(up, forward)
    gait = GroundedGait(
        step_length_body_heights=.6, cycles=1, sample_hz=120)
    plan = _axial_performance_plan(gait)
    base = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)

    bad = deepcopy(plan)
    bad["parameters"]["step_length_body_heights"] = -.6
    with pytest.raises(ContractError, match="conflicts with foot choreography"):
        _support_timed_axial_clock(
            source, base, roles, bad, .1, 1., lateral)

    malformed = deepcopy(plan)
    malformed["parameters"]["duty_factor"] = "wide"
    with pytest.raises(ContractError, match="finite two-step grounded clock"):
        _support_timed_axial_clock(
            source, base, roles, malformed, .1, 1., lateral)

    reverse = _axial_performance_plan(replace(gait, step_length_body_heights=-.6))
    with pytest.raises(ContractError, match="conflicts with foot choreography"):
        _support_timed_axial_clock(
            source, base, roles, reverse, .1, 1., lateral)


@pytest.mark.parametrize("kind", ["start", "stop"])
def test_axial_clock_admission_is_independent_of_sparse_transition_grid(kind):
    source, roles = fixture("axial_sparse_", 1., upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([0., 0., 1.])
    lateral = np.cross(up, forward)
    gait = GroundedGait(
        step_period_s=1.23, duty_factor=.62,
        step_length_body_heights=.6, cycles=1, sample_hz=120)
    performance = Performance(
        center_tail=True, support_timed_axial_carrier=True)
    full = decorate_plan(
        build_transition_plan(GaitTransition(kind), gait, 2.), performance)
    sparse = deepcopy(full)
    sparse["samples"] = [full["samples"][-1 if kind == "start" else 0]]
    row = sparse["samples"][0]
    base = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)
    phase, gain = phase_and_gain(row)
    assert _support_timed_axial_clock(
        source, base, roles, sparse, phase, gain, lateral) == pytest.approx(
            _support_timed_axial_clock(
                source, base, roles, full, phase, gain, lateral), abs=1e-15)


def test_axial_clock_phases_proximal_tail_after_centering():
    source, roles = fixture("axial_tail_", 1., upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([0., 0., 1.])
    gait = GroundedGait(
        step_period_s=1.23, duty_factor=.62,
        step_length_body_heights=.6, cycles=1, sample_hz=120)
    plan = _axial_performance_plan(gait)
    first, child = [source.name_to_node[name] for name in roles["tail"][:2]]

    def tail_yaw(time):
        row = sample_grounded_gait(gait, time, 2.)
        _, posed = _performance_pose(source, roles, plan, row, up, forward)
        direction = np.asarray(_world_position(posed[child])) - np.asarray(
            _world_position(posed[first]))
        direction -= up * float(direction @ up)
        direction /= np.linalg.norm(direction)
        target = -forward
        return math.degrees(math.atan2(
            float(up @ np.cross(target, direction)), float(target @ direction)))

    double = (gait.duty_factor - .5) * gait.step_period_s
    stance = gait.duty_factor * gait.step_period_s
    weights = np.linspace(.6, 1.4, len(roles["tail"]))
    weights /= weights.sum()
    assert tail_yaw(double) == pytest.approx(-16 * weights[0], abs=1e-8)
    assert tail_yaw(stance) == pytest.approx(0, abs=1e-8)


@pytest.mark.parametrize("kind", ["start", "stop"])
def test_support_timed_axial_carrier_matches_grounded_transition_interface(kind):
    source, roles = fixture("axial_transition_", 1., upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([0., 0., 1.])
    gait = GroundedGait(
        step_period_s=1.23, duty_factor=.62,
        step_length_body_heights=.6, cycles=1, sample_hz=120)
    performance = Performance(
        pelvis_sway_body_heights=0,
        pelvis_roll_degrees=0,
        pelvis_yaw_degrees=2,
        tail_yaw_degrees=16,
        gaze_elevation_degrees=0,
        center_tail=True,
        support_timed_axial_carrier=True,
    )
    steady = decorate_plan(build_grounded_plan(gait, 2.), performance)
    transition = decorate_plan(
        build_transition_plan(GaitTransition(kind), gait, 2.), performance)
    transition_row = transition["samples"][-1 if kind == "start" else 0]
    steady_row = steady["samples"][0]
    assert transition_row["locomotion_time_s"] == pytest.approx(0)
    assert transition_row["performance_gain"] == pytest.approx(1)
    _, transition_pose = _performance_pose(
        source, roles, transition, transition_row, up, forward)
    _, steady_pose = _performance_pose(
        source, roles, steady, steady_row, up, forward)
    body_names = list(dict.fromkeys([
        roles["pelvis"], *roles.get("spine", []), roles["chest"],
        *roles.get("neck", []), roles["head"], *roles.get("tail", []),
    ]))
    for name in body_names:
        node = source.name_to_node[name]
        assert np.asarray(transition_pose[node]) == pytest.approx(
            np.asarray(steady_pose[node]), abs=1e-12)


def test_stance_vault_proxy_uses_declared_support_clock_and_analytic_velocity():
    height = 2.3
    gait = GroundedGait(
        step_period_s=1.23,
        duty_factor=.62,
        pelvis_crouch_body_heights=.01,
        pelvis_excursion_body_heights=.016,
        pelvis_height_carrier="stance_vault_proxy",
    )
    amplitude = gait.pelvis_excursion_body_heights * height
    standing = -gait.pelvis_crouch_body_heights * height
    for cycle in (0, 1):
        stance_mid = (cycle + gait.duty_factor) * gait.step_period_s
        row = sample_grounded_gait(gait, stance_mid, height)
        assert row["stage"] == "SINGLE_SUPPORT"
        assert row["pelvis_height_offset_m"] == pytest.approx(standing, abs=1e-14)
        assert row["pelvis_vertical_velocity_mps"] == pytest.approx(0, abs=1e-14)
        double_mid = (cycle + gait.duty_factor - .5) * gait.step_period_s
        row = sample_grounded_gait(gait, double_mid, height)
        assert row["stage"] == "DOUBLE_SUPPORT"
        assert row["pelvis_height_offset_m"] == pytest.approx(standing - amplitude, abs=1e-14)
        assert row["pelvis_vertical_velocity_mps"] == pytest.approx(0, abs=1e-14)
    cycle = 2 * gait.step_period_s
    for t in (.317, .941):
        a = sample_grounded_gait(gait, t, height)
        b = sample_grounded_gait(gait, t + cycle, height)
        assert b["pelvis_height_offset_m"] == pytest.approx(a["pelvis_height_offset_m"], abs=1e-14)
        assert b["pelvis_vertical_velocity_mps"] == pytest.approx(a["pelvis_vertical_velocity_mps"], abs=1e-14)
    t = .49
    h = 1e-6
    before = sample_grounded_gait(gait, t - h, height)["pelvis_height_offset_m"]
    after = sample_grounded_gait(gait, t + h, height)["pelvis_height_offset_m"]
    expected = sample_grounded_gait(gait, t, height)["pelvis_vertical_velocity_mps"]
    assert (after - before) / (2 * h) == pytest.approx(expected, abs=1e-10)


def _performance_pose(source, roles, plan, row, up, forward):
    base_worlds = _world_matrices(
        source,
        source.rest_translation,
        source.rest_rotation,
        source.rest_scale,
    )
    translations = source.rest_translation[:]
    rotations = source.rest_rotation[:]
    scales = source.rest_scale[:]
    apply_performance(
        source,
        translations,
        rotations,
        scales,
        base_worlds,
        roles,
        plan,
        row,
        up,
        forward,
    )
    return base_worlds, _world_matrices(source, translations, rotations, scales)


@pytest.mark.parametrize("mirrored_roles", [False, True])
def test_support_carrier_follows_semantic_hips_in_a_non_axis_aligned_frame(mirrored_roles):
    source, roles = fixture("support", upper_body=True)
    if mirrored_roles:
        roles["legs"]["left"], roles["legs"]["right"] = (
            roles["legs"]["right"], roles["legs"]["left"])
    up = np.array([0., 1., 0.])
    forward = np.array([1., 0., 1.]) / math.sqrt(2)
    lateral = np.cross(up, forward)
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62)
    performance = Performance(
        pelvis_sway_body_heights=.006,
        pelvis_roll_degrees=.6,
        support_directed_pelvis_carrier=True,
    )
    plan = decorate_plan(build_grounded_plan(gait, 2.), performance)
    pelvis = source.name_to_node[roles["pelvis"]]
    for cycle, side in ((0, "left"), (1, "right")):
        t = (cycle + gait.duty_factor) * gait.step_period_s
        row = sample_grounded_gait(gait, t, 2.)
        assert row["support_count"] == 1 and row["feet"][side]["contact"]
        base, posed = _performance_pose(source, roles, plan, row, up, forward)
        support_hip = source.name_to_node[roles["legs"][side]["contactChain"][0]]
        support_direction = np.asarray(_world_position(base[support_hip])) - np.asarray(
            _world_position(base[pelvis]))
        shift = np.asarray(_world_position(posed[pelvis])) - np.asarray(
            _world_position(base[pelvis]))
        assert shift @ support_direction > 0
        assert abs(shift @ lateral) == pytest.approx(
            performance.pelvis_sway_body_heights * plan["body_height_m"],
            abs=1e-10,
        )
        local_up = np.linalg.solve(np.asarray(base[pelvis])[:3, :3], up)
        posed_up = np.asarray(posed[pelvis])[:3, :3] @ local_up
        assert (posed_up - up) @ support_direction > 0
    double_mid = (gait.duty_factor - .5) * gait.step_period_s
    row = sample_grounded_gait(gait, double_mid, 2.)
    assert row["support_count"] == 2
    base, posed = _performance_pose(source, roles, plan, row, up, forward)
    shift = np.asarray(_world_position(posed[pelvis])) - np.asarray(
        _world_position(base[pelvis]))
    assert np.linalg.norm(shift) < 1e-12
    local_up = np.linalg.solve(np.asarray(base[pelvis])[:3, :3], up)
    posed_up = np.asarray(posed[pelvis])[:3, :3] @ local_up
    assert abs((posed_up - up) @ lateral) < 1e-12


@pytest.mark.parametrize("kind", ["start", "stop"])
def test_opt_in_body_carriers_match_grounded_transition_interface(kind):
    source, roles = fixture("transition", upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([0., 0., 1.])
    gait = GroundedGait(
        cycles=1,
        sample_hz=120,
        pelvis_height_carrier="stance_vault_proxy",
    )
    performance = Performance(support_directed_pelvis_carrier=True)
    steady = decorate_plan(build_grounded_plan(gait, 2.), performance)
    transition = decorate_plan(
        build_transition_plan(GaitTransition(kind), gait, 2.),
        performance,
    )
    transition_row = transition["samples"][-1 if kind == "start" else 0]
    steady_row = steady["samples"][0]
    assert transition_row["locomotion_time_s"] == pytest.approx(0)
    assert transition_row["performance_gain"] == pytest.approx(1)
    assert transition_row["pelvis_height_offset_m"] == pytest.approx(
        steady_row["pelvis_height_offset_m"], abs=1e-12)
    _, transition_pose = _performance_pose(
        source, roles, transition, transition_row, up, forward)
    _, steady_pose = _performance_pose(
        source, roles, steady, steady_row, up, forward)
    pelvis = source.name_to_node[roles["pelvis"]]
    assert np.asarray(transition_pose[pelvis]) == pytest.approx(
        np.asarray(steady_pose[pelvis]), abs=1e-12)


def test_support_carrier_rejects_hips_without_declared_lateral_separation():
    source, roles = fixture("support", upper_body=True)
    up = np.array([0., 1., 0.])
    forward = np.array([1., 0., 0.])
    gait = GroundedGait()
    plan = decorate_plan(
        build_grounded_plan(gait, 2.),
        Performance(support_directed_pelvis_carrier=True),
    )
    row = sample_grounded_gait(gait, gait.duty_factor * gait.step_period_s, 2.)
    with pytest.raises(ContractError, match="separated along the declared lateral axis"):
        _performance_pose(source, roles, plan, row, up, forward)


@pytest.mark.parametrize("value", [-.1, 3.1, True, float("nan")])
def test_upper_trunk_counterroll_rejects_invalid_values(value):
    with pytest.raises(ContractError):
        Performance(
            support_directed_pelvis_carrier=True,
            upper_trunk_counterroll_degrees=value,
        )


def test_upper_trunk_counterroll_requires_support_carrier():
    for carrier in (None, False):
        with pytest.raises(ContractError, match="requires the support-directed"):
            Performance(
                support_directed_pelvis_carrier=carrier,
                upper_trunk_counterroll_degrees=.9,
            )


def test_support_counterroll_is_distributed_over_unique_actual_trunk_chain():
    root = Path(__file__).resolve().parents[1]
    source = Glb.from_bytes((root / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb").read_bytes())
    roles = json.loads((root / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]
    up = np.array([0., 1., 0.])
    forward = np.array([.03893162055641767, 0., .9992418770852486])
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62)
    performance = Performance(
        pelvis_sway_body_heights=.018,
        pelvis_yaw_degrees=0,
        pelvis_roll_degrees=1.5,
        tail_yaw_degrees=0,
        gaze_elevation_degrees=0,
        center_tail=False,
        support_directed_pelvis_carrier=True,
        upper_trunk_counterroll_degrees=.9,
    )
    plan = decorate_plan(build_grounded_plan(gait, 2.), performance)
    row = sample_grounded_gait(
        gait, gait.duty_factor * gait.step_period_s, 2.)
    base, posed = _performance_pose(source, roles, plan, row, up, forward)
    names = [roles["pelvis"], *roles["spine"], roles["chest"]]
    nodes = [source.name_to_node[name] for name in names]
    angles = []
    for node in nodes:
        base_rotation = rotation_matrix(_rotation_from_matrix(base[node]))
        posed_rotation = rotation_matrix(_rotation_from_matrix(posed[node]))
        local_up = base_rotation.T @ up
        posed_up = posed_rotation @ local_up
        angles.append(math.degrees(math.atan2(
            forward @ np.cross(up, posed_up),
            up @ posed_up,
        )))
    weights = np.linspace(.6, 1.4, len(nodes) - 1)
    weights /= weights.sum()
    expected = [1.5]
    for weight in weights:
        expected.append(expected[-1] - .9 * weight)
    assert angles == pytest.approx(expected, abs=5e-6)
    assert angles[-1] == pytest.approx(.6, abs=5e-6)
    assert all(a > b for a, b in zip(angles, angles[1:]))


def test_upper_trunk_counterroll_is_present_in_serialized_actual_rig_motion():
    root = Path(__file__).resolve().parents[1]
    source = Glb.from_bytes((root / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb").read_bytes())
    roles = json.loads((root / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]
    up = (0., 1., 0.)
    forward = (.03893162055641767, 0., .9992418770852486)
    height = geometry_height(source, roles, up)
    gait = GroundedGait(
        step_period_s=1.23,
        duty_factor=.62,
        cycles=1,
        sample_hz=24,
        step_length_body_heights=.1,
        touchdown_reach_body_heights=.05,
        swing_clearance_body_heights=.08,
    )
    performance = Performance(
        pelvis_sway_body_heights=.018,
        pelvis_yaw_degrees=0,
        pelvis_roll_degrees=1.5,
        tail_yaw_degrees=0,
        gaze_elevation_degrees=0,
        center_tail=False,
        support_directed_pelvis_carrier=True,
        upper_trunk_counterroll_degrees=.9,
        skin_refinement=False,
    )
    plan = decorate_plan(build_grounded_plan(gait, height), performance)
    raw, _, _, _ = solve_airborne_gait(
        source,
        source_clip=None,
        semantic_roles=roles,
        gait=AirborneGait(
            step_period_s=gait.step_period_s,
            cycles=1,
            sample_hz=gait.sample_hz,
        ),
        up_axis=up,
        forward_axis=forward,
        plan_override=plan,
        legacy_overlay=False,
    )
    emitted = Glb.from_bytes(raw)
    tracks, times = _clip_state(
        emitted, emitted.document["animations"][0]["name"])
    index = int(np.argmin(np.abs(
        np.asarray(times) - gait.duty_factor * gait.step_period_s)))
    translations, rotations, scales = _pose(emitted, tracks, index)
    posed = _world_matrices(emitted, translations, rotations, scales)
    base = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)
    names = [roles["pelvis"], *roles["spine"], roles["chest"]]
    nodes = [source.name_to_node[name] for name in names]
    forward_array = np.asarray(forward)
    up_array = np.asarray(up)
    angles = []
    for node in nodes:
        base_rotation = rotation_matrix(_rotation_from_matrix(base[node]))
        posed_rotation = rotation_matrix(_rotation_from_matrix(posed[node]))
        posed_up = posed_rotation @ (base_rotation.T @ up_array)
        angles.append(math.degrees(math.atan2(
            forward_array @ np.cross(up_array, posed_up),
            up_array @ posed_up,
        )))
    sample_time = float(times[index])
    carrier = -math.cos(math.pi * (sample_time / gait.step_period_s - gait.duty_factor))
    expected = [-1.5 * carrier]
    weights = np.linspace(.6, 1.4, len(nodes) - 1)
    weights /= weights.sum()
    for weight in weights:
        expected.append(expected[-1] + .9 * carrier * weight)
    assert angles == pytest.approx(expected, abs=2e-4)
    assert all(a > b for a, b in zip(angles, angles[1:]))
    assert angles[-1] == pytest.approx(-.6 * carrier, abs=2e-4)


@pytest.mark.parametrize("spine", [None, [], 17])
def test_upper_trunk_counterroll_rejects_malformed_or_empty_spine(spine):
    source, roles = fixture("counter", upper_body=True)
    roles["spine"] = spine
    up = np.array([0., 1., 0.])
    forward = np.array([0., 0., 1.])
    gait = GroundedGait()
    plan = decorate_plan(
        build_grounded_plan(gait, 2.),
        Performance(
            support_directed_pelvis_carrier=True,
            upper_trunk_counterroll_degrees=.9,
        ),
    )
    row = sample_grounded_gait(
        gait, gait.duty_factor * gait.step_period_s, 2.)
    with pytest.raises(ContractError, match="semantic spine sequence"):
        _performance_pose(source, roles, plan, row, up, forward)


def test_upper_trunk_counterroll_rejects_leg_chain_masquerading_as_trunk():
    source, roles = fixture("counter", upper_body=True)
    leg = roles["legs"]["left"]["contactChain"]
    roles["spine"] = leg[:-1]
    roles["chest"] = leg[-1]
    gait = GroundedGait()
    plan = decorate_plan(
        build_grounded_plan(gait, 2.),
        Performance(
            support_directed_pelvis_carrier=True,
            upper_trunk_counterroll_degrees=.9,
        ),
    )
    row = sample_grounded_gait(
        gait, gait.duty_factor * gait.step_period_s, 2.)
    with pytest.raises(ContractError, match="disjoint from other semantic roles"):
        _performance_pose(
            source, roles, plan, row,
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


def test_upper_trunk_counterroll_rejects_disconnected_spine_order():
    root = Path(__file__).resolve().parents[1]
    source = Glb.from_bytes((root / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb").read_bytes())
    roles = json.loads((root / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]
    roles["spine"][0], roles["spine"][1] = roles["spine"][1], roles["spine"][0]
    gait = GroundedGait()
    plan = decorate_plan(
        build_grounded_plan(gait, 2.),
        Performance(
            support_directed_pelvis_carrier=True,
            upper_trunk_counterroll_degrees=.9,
        ),
    )
    row = sample_grounded_gait(
        gait, gait.duty_factor * gait.step_period_s, 2.)
    with pytest.raises(ContractError, match="must follow actual topology"):
        _performance_pose(
            source, roles, plan, row,
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


def test_direct_airborne_override_cannot_forge_support_carrier_identity():
    source, roles = fixture("airborne", upper_body=True)
    plan = build_airborne_plan(AirborneGait(cycles=1, sample_hz=24), 2.)
    plan["performance"] = {
        key: value for key, value in Performance(
            support_directed_pelvis_carrier=True,
        ).__dict__.items() if value is not None
    }
    with pytest.raises(ContractError, match="requires grounded locomotion"):
        _performance_pose(
            source, roles, plan, plan["samples"][0],
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


def _sagittal_performance(**changes):
    values = {
        "pelvis_sway_body_heights": 0,
        "pelvis_yaw_degrees": 0,
        "pelvis_roll_degrees": 0,
        "tail_yaw_degrees": 0,
        "gaze_elevation_degrees": 0,
        "center_tail": False,
        "support_timed_sagittal_carrier": True,
        "pelvis_support_pitch_degrees": 1.2,
        "upper_trunk_counterpitch_degrees": .75,
        "neck_counterpitch_degrees": .45,
        "tail_counterpitch_degrees": 1.5,
    }
    values.update(changes)
    return Performance(**values)


@pytest.mark.parametrize("value", [0, 1, "yes", float("nan")])
def test_sagittal_carrier_rejects_malformed_flag(value):
    with pytest.raises(ContractError):
        _sagittal_performance(support_timed_sagittal_carrier=value)


@pytest.mark.parametrize("field", [
    "pelvis_support_pitch_degrees",
    "upper_trunk_counterpitch_degrees",
    "neck_counterpitch_degrees",
    "tail_counterpitch_degrees",
])
def test_sagittal_carrier_requires_every_amplitude(field):
    with pytest.raises(ContractError, match="requires all pitch amplitudes"):
        _sagittal_performance(**{field: None})


@pytest.mark.parametrize(("field", "value"), [
    ("pelvis_support_pitch_degrees", 3.1),
    ("upper_trunk_counterpitch_degrees", -.1),
    ("neck_counterpitch_degrees", 2.1),
    ("tail_counterpitch_degrees", 4.1),
    ("tail_counterpitch_degrees", True),
    ("tail_counterpitch_degrees", float("nan")),
])
def test_sagittal_carrier_rejects_invalid_amplitudes(field, value):
    with pytest.raises(ContractError):
        _sagittal_performance(**{field: value})


def test_sagittal_amplitudes_require_opt_in_carrier():
    for carrier in (None, False):
        with pytest.raises(ContractError, match="require the support-timed"):
            _sagittal_performance(support_timed_sagittal_carrier=carrier)


def test_sagittal_carrier_is_grounded_only():
    airborne = build_airborne_plan(AirborneGait(cycles=1, sample_hz=24), 2.)
    with pytest.raises(ContractError, match="requires grounded locomotion"):
        decorate_plan(airborne, _sagittal_performance())


def test_sagittal_pulse_uses_declared_support_clock_and_closes_c2():
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62)
    plan = build_grounded_plan(gait, 2.)
    step = gait.step_period_s
    for cycle in (0, 1):
        stance = (cycle + gait.duty_factor) * step
        double = (cycle + gait.duty_factor - .5) * step
        assert _support_timed_sagittal_pulse(plan, stance, 1.) == pytest.approx(-1)
        assert _support_timed_sagittal_pulse(plan, double, 1.) == pytest.approx(1)
        assert _support_timed_sagittal_pulse(
            plan, stance - .25 * step, 1.) == pytest.approx(0, abs=1e-14)
        assert _support_timed_sagittal_pulse(plan, stance + .25 * step, 1.) == pytest.approx(0, abs=1e-14)
    cycle = 2 * step
    h = 1e-4
    for t in (.317, .941):
        values = []
        for offset in (-h, 0, h):
            values.append(_support_timed_sagittal_pulse(plan, t + offset, .7))
        repeated = [
            _support_timed_sagittal_pulse(plan, t + cycle + offset, .7)
            for offset in (-h, 0, h)
        ]
        assert repeated == pytest.approx(values, abs=1e-12)
        first = (values[2] - values[0]) / (2 * h)
        repeated_first = (repeated[2] - repeated[0]) / (2 * h)
        second = (values[2] - 2 * values[1] + values[0]) / h**2
        repeated_second = (
            repeated[2] - 2 * repeated[1] + repeated[0]) / h**2
        assert repeated_first == pytest.approx(first, abs=1e-9)
        assert repeated_second == pytest.approx(second, abs=5e-7)


@pytest.mark.parametrize("value", [-.1, 1., True, "yes", float("nan")])
def test_pelvis_forward_velocity_carrier_rejects_unphysical_coefficients(value):
    with pytest.raises(ContractError):
        Performance(pelvis_forward_velocity_modulation_fraction=value)


def test_pelvis_forward_velocity_carrier_requires_grounded_stance_vault():
    carrier = Performance(pelvis_forward_velocity_modulation_fraction=.145)
    airborne = build_airborne_plan(AirborneGait(cycles=1, sample_hz=24), 2.)
    with pytest.raises(ContractError, match="requires grounded locomotion"):
        decorate_plan(airborne, carrier)
    grounded = build_grounded_plan(GroundedGait(), 2.)
    decorated = decorate_plan(grounded, carrier)
    with pytest.raises(ContractError, match="requires stance_vault_proxy"):
        _support_timed_pelvis_forward_carrier(decorated, .2, .145)


@pytest.mark.parametrize("stride", [.6, -.6])
def test_pelvis_forward_carrier_has_analytic_periodic_speed_and_net_travel(stride):
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62,
        step_length_body_heights=stride,
        pelvis_height_carrier="stance_vault_proxy")
    plan = build_grounded_plan(gait, 2.270663281560174)
    coefficient = .14519967609352594
    step = gait.step_period_s
    mean = stride * plan["body_height_m"] / step
    for t in (.173, .941):
        displacement, velocity = _support_timed_pelvis_forward_carrier(
            plan, t, coefficient)
        repeated = _support_timed_pelvis_forward_carrier(
            plan, t + step, coefficient)
        assert repeated == pytest.approx((displacement, velocity), abs=1e-14)
        h = 1e-6
        before = _support_timed_pelvis_forward_carrier(
            plan, t - h, coefficient)[0]
        after = _support_timed_pelvis_forward_carrier(
            plan, t + h, coefficient)[0]
        assert (after - before) / (2 * h) == pytest.approx(velocity, abs=1e-10)
    high = (gait.duty_factor) * step
    low = (gait.duty_factor - .5) * step
    assert _support_timed_pelvis_forward_carrier(
        plan, high, coefficient)[1] == pytest.approx(-coefficient * mean)
    assert _support_timed_pelvis_forward_carrier(
        plan, low, coefficient)[1] == pytest.approx(coefficient * mean)
    assert plan["samples"][-1]["root_forward_m"] == pytest.approx(
        2 * gait.cycles * stride * plan["body_height_m"])


def test_pelvis_forward_carrier_uses_rotated_frame_and_actual_root_hierarchy():
    source, roles = _actual_source_and_roles()
    up = np.array([0., 1., 0.])
    forward = np.array([.03893162055641767, 0., .9992418770852486])
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62,
        step_length_body_heights=.6,
        pelvis_height_carrier="stance_vault_proxy")
    coefficient = .14519967609352594
    plan = decorate_plan(build_grounded_plan(gait, 2.270663281560174),
        Performance(pelvis_sway_body_heights=0, pelvis_yaw_degrees=0,
            pelvis_roll_degrees=0, tail_yaw_degrees=0,
            gaze_elevation_degrees=0, center_tail=False,
            pelvis_forward_velocity_modulation_fraction=coefficient))
    t = (gait.duty_factor + .25) * gait.step_period_s
    row = sample_grounded_gait(gait, t, plan["body_height_m"])
    base, posed = _performance_pose(source, roles, plan, row, up, forward)
    pelvis = source.name_to_node[roles["pelvis"]]
    delta = np.asarray(_world_position(posed[pelvis])) - _world_position(base[pelvis])
    expected = _support_timed_pelvis_forward_carrier(plan, t, coefficient)[0]
    assert delta @ forward == pytest.approx(expected, abs=1e-10)
    assert delta @ up == pytest.approx(0, abs=1e-10)
    assert delta @ np.cross(up, forward) == pytest.approx(0, abs=1e-10)
    forged = dict(roles)
    forged["root"] = roles["spine"][0]
    with pytest.raises(ContractError, match="root-to-pelvis hierarchy"):
        _performance_pose(source, forged, plan, row, up, forward)


def test_zero_pelvis_forward_carrier_is_exact_motion_identity_on_actual_rig():
    source, roles = _actual_source_and_roles()
    up = (0., 1., 0.)
    forward = (.03893162055641767, 0., .9992418770852486)
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62,
        cycles=1, sample_hz=24, step_length_body_heights=.1,
        touchdown_reach_body_heights=.05,
        swing_clearance_body_heights=.08,
        pelvis_height_carrier="stance_vault_proxy")
    common = dict(pelvis_sway_body_heights=0, pelvis_yaw_degrees=0,
        pelvis_roll_degrees=0, tail_yaw_degrees=0,
        gaze_elevation_degrees=0, center_tail=False,
        skin_refinement=False)
    outputs = []
    for coefficient in (None, 0.):
        performance = Performance(**common,
            pelvis_forward_velocity_modulation_fraction=coefficient)
        plan = decorate_plan(build_grounded_plan(gait, 2.), performance)
        if coefficient == 0:
            assert "pelvis_forward_velocity_modulation_fraction" not in plan["performance"]
        root_motion, in_place, _, _ = solve_airborne_gait(
            source, source_clip=None, semantic_roles=roles,
            gait=AirborneGait(step_period_s=gait.step_period_s,
                cycles=1, sample_hz=gait.sample_hz),
            up_axis=up, forward_axis=forward, plan_override=plan,
            legacy_overlay=False)
        outputs.append((root_motion, in_place))
    assert outputs[0] == outputs[1]


def _actual_source_and_roles():
    root = Path(__file__).resolve().parents[1]
    source = Glb.from_bytes((root / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb").read_bytes())
    roles = json.loads((root / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]
    return source, roles


def _signed_world_rotation_delta(base, posed, node, axis):
    base_rotation = rotation_matrix(_rotation_from_matrix(base[node]))
    posed_rotation = rotation_matrix(_rotation_from_matrix(posed[node]))
    delta = posed_rotation @ base_rotation.T
    angle = math.acos(float(np.clip((np.trace(delta) - 1) / 2, -1, 1)))
    if angle < 1e-12:
        return 0.
    rotation_axis = np.array([
        delta[2, 1] - delta[1, 2],
        delta[0, 2] - delta[2, 0],
        delta[1, 0] - delta[0, 1],
    ]) / (2 * math.sin(angle))
    return math.degrees(angle) * float(rotation_axis @ axis)


@pytest.mark.parametrize(("offset_cycles", "pulse"), [(-.5, 1.), (0, -1.)])
def test_sagittal_carrier_has_signed_distributed_actual_rig_response(
        offset_cycles, pulse):
    source, roles = _actual_source_and_roles()
    up = np.array([0., 1., 0.])
    forward = np.array([.03893162055641767, 0., .9992418770852486])
    lateral = np.cross(up, forward)
    gait = GroundedGait(step_period_s=1.23, duty_factor=.62)
    plan = decorate_plan(build_grounded_plan(gait, 2.), _sagittal_performance())
    time_s = (gait.duty_factor + offset_cycles) * gait.step_period_s
    row = sample_grounded_gait(gait, time_s, 2.)
    base, posed = _performance_pose(source, roles, plan, row, up, forward)
    pelvis = source.name_to_node[roles["pelvis"]]
    pelvis_rotation = rotation_matrix(_rotation_from_matrix(posed[pelvis]))
    base_rotation = rotation_matrix(_rotation_from_matrix(base[pelvis]))
    delta = pelvis_rotation @ base_rotation.T
    assert (delta @ up - up) @ forward * pulse > 0
    assert (delta @ forward - forward) @ up * pulse < 0

    trunk = [roles["pelvis"], *roles["spine"], roles["chest"]]
    trunk_expected = [1.2 * pulse]
    trunk_weights = np.linspace(.6, 1.4, len(trunk) - 1)
    trunk_weights /= trunk_weights.sum()
    for weight in trunk_weights:
        trunk_expected.append(trunk_expected[-1] - .75 * pulse * weight)
    trunk_actual = [
        _signed_world_rotation_delta(
            base, posed, source.name_to_node[name], lateral)
        for name in trunk
    ]
    assert trunk_actual == pytest.approx(trunk_expected, abs=2e-5)

    neck_weights = np.linspace(.6, 1.4, len(roles["neck"]))
    neck_weights /= neck_weights.sum()
    neck_expected = []
    value = trunk_expected[-1]
    for weight in neck_weights:
        value -= .45 * pulse * weight
        neck_expected.append(value)
    neck_actual = [
        _signed_world_rotation_delta(
            base, posed, source.name_to_node[name], lateral)
        for name in roles["neck"]
    ]
    assert neck_actual == pytest.approx(neck_expected, abs=2e-5)

    tail_weights = np.linspace(.6, 1.4, len(roles["tail"]))
    tail_weights /= tail_weights.sum()
    tail_expected = []
    value = 1.2 * pulse
    for weight in tail_weights:
        value -= 1.5 * pulse * weight
        tail_expected.append(value)
    tail_actual = [
        _signed_world_rotation_delta(
            base, posed, source.name_to_node[name], lateral)
        for name in roles["tail"]
    ]
    assert tail_actual == pytest.approx(tail_expected, abs=2e-5)
    head = source.name_to_node[roles["head"]]
    assert _signed_world_rotation_delta(base, posed, head, lateral) == pytest.approx(0, abs=2e-5)


def test_sagittal_carrier_is_present_in_serialized_actual_rig_motion():
    source, roles = _actual_source_and_roles()
    up = np.array([0., 1., 0.])
    forward = np.array([.03893162055641767, 0., .9992418770852486])
    lateral = np.cross(up, forward)
    height = geometry_height(source, roles, up)
    gait = GroundedGait(
        step_period_s=1.23,
        duty_factor=.62,
        cycles=1,
        sample_hz=24,
        step_length_body_heights=.1,
        touchdown_reach_body_heights=.05,
        swing_clearance_body_heights=.08,
    )
    plan = decorate_plan(
        build_grounded_plan(gait, height),
        _sagittal_performance(skin_refinement=False),
    )
    raw, _, _, _ = solve_airborne_gait(
        source,
        source_clip=None,
        semantic_roles=roles,
        gait=AirborneGait(
            step_period_s=gait.step_period_s,
            cycles=1,
            sample_hz=gait.sample_hz,
        ),
        up_axis=tuple(up),
        forward_axis=tuple(forward),
        plan_override=plan,
        legacy_overlay=False,
    )
    emitted = Glb.from_bytes(raw)
    tracks, times = _clip_state(
        emitted, emitted.document["animations"][0]["name"])
    index = int(np.argmin(np.abs(
        np.asarray(times) - gait.duty_factor * gait.step_period_s)))
    translations, rotations, scales = _pose(emitted, tracks, index)
    posed = _world_matrices(emitted, translations, rotations, scales)
    base = _world_matrices(
        source, source.rest_translation, source.rest_rotation, source.rest_scale)
    pulse = _support_timed_sagittal_pulse(
        plan, float(times[index]), 1.)

    nodes = {
        "pelvis": source.name_to_node[roles["pelvis"]],
        "chest": source.name_to_node[roles["chest"]],
        "neck": source.name_to_node[roles["neck"][-1]],
        "head": source.name_to_node[roles["head"]],
        "tail": source.name_to_node[roles["tail"][-1]],
    }
    angles = {
        label: _signed_world_rotation_delta(base, posed, node, lateral)
        for label, node in nodes.items()
    }
    assert angles["pelvis"] == pytest.approx(1.2 * pulse, abs=2e-4)
    assert angles["chest"] == pytest.approx(.45 * pulse, abs=2e-4)
    assert angles["neck"] == pytest.approx(0, abs=2e-4)
    assert angles["head"] == pytest.approx(0, abs=2e-4)
    assert angles["tail"] == pytest.approx(-.3 * pulse, abs=2e-4)


@pytest.mark.parametrize("role, value", [
    ("neck", None),
    ("neck", []),
    ("tail", None),
    ("tail", []),
])
def test_sagittal_carrier_rejects_malformed_or_empty_body_chains(role, value):
    source, roles = _actual_source_and_roles()
    roles[role] = value
    gait = GroundedGait()
    plan = decorate_plan(build_grounded_plan(gait, 2.), _sagittal_performance())
    row = sample_grounded_gait(gait, gait.duty_factor * gait.step_period_s, 2.)
    with pytest.raises(ContractError):
        _performance_pose(
            source, roles, plan, row,
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


def test_sagittal_carrier_rejects_leg_as_neck_and_disconnected_tail():
    source, roles = _actual_source_and_roles()
    gait = GroundedGait()
    plan = decorate_plan(build_grounded_plan(gait, 2.), _sagittal_performance())
    row = sample_grounded_gait(gait, gait.duty_factor * gait.step_period_s, 2.)
    roles["neck"] = list(roles["legs"]["left"]["contactChain"])
    with pytest.raises(ContractError, match="disjoint from other semantic roles"):
        _performance_pose(
            source, roles, plan, row,
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))
    source, roles = _actual_source_and_roles()
    roles["tail"][0], roles["tail"][1] = roles["tail"][1], roles["tail"][0]
    with pytest.raises(ContractError, match="must follow actual topology"):
        _performance_pose(
            source, roles, plan, row,
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


def test_sagittal_carrier_rejects_unrelated_existing_root_on_actual_rig():
    source, roles = _actual_source_and_roles()
    roles["root"] = "Bone_060"
    assert roles["root"] in source.name_to_node
    gait = GroundedGait()
    plan = decorate_plan(build_grounded_plan(gait, 2.), _sagittal_performance())
    row = sample_grounded_gait(gait, gait.duty_factor * gait.step_period_s, 2.)
    with pytest.raises(ContractError, match="must follow actual topology"):
        _performance_pose(
            source, roles, plan, row,
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


def test_direct_airborne_override_cannot_forge_sagittal_carrier_identity():
    source, roles = _actual_source_and_roles()
    plan = build_airborne_plan(AirborneGait(cycles=1, sample_hz=24), 2.)
    plan["performance"] = {
        key: value for key, value in _sagittal_performance().__dict__.items()
        if value is not None
    }
    with pytest.raises(ContractError, match="requires grounded locomotion"):
        _performance_pose(
            source, roles, plan, plan["samples"][0],
            np.array([0., 1., 0.]), np.array([0., 0., 1.]))


@pytest.mark.parametrize("kind", ["start", "stop"])
def test_sagittal_carrier_matches_grounded_transition_interface(kind):
    source, roles = _actual_source_and_roles()
    up = np.array([0., 1., 0.])
    forward = np.array([.03893162055641767, 0., .9992418770852486])
    gait = GroundedGait(cycles=1, sample_hz=120)
    performance = _sagittal_performance()
    steady = decorate_plan(build_grounded_plan(gait, 2.), performance)
    transition = decorate_plan(
        build_transition_plan(GaitTransition(kind), gait, 2.), performance)
    transition_row = transition["samples"][-1 if kind == "start" else 0]
    steady_row = steady["samples"][0]
    assert transition_row["locomotion_time_s"] == pytest.approx(0)
    assert transition_row["performance_gain"] == pytest.approx(1)
    _, transition_pose = _performance_pose(
        source, roles, transition, transition_row, up, forward)
    _, steady_pose = _performance_pose(
        source, roles, steady, steady_row, up, forward)
    body_names = [
        roles["pelvis"], *roles["spine"], roles["chest"],
        *roles["neck"], roles["head"], *roles["tail"],
    ]
    for name in body_names:
        node = source.name_to_node[name]
        assert np.asarray(transition_pose[node]) == pytest.approx(
            np.asarray(steady_pose[node]), abs=1e-12)


def patch(time,x,y=0):
    points=((x,y,0),(x+.05,y,0),(x,y,.08))
    return PatchFrame(time,points,points)


def test_loop_terminal_contact_gets_real_next_cycle_context():
    # Late support begins exactly at the duplicate end. It must be evaluated
    # with next cycle's contacts, not rejected as one isolated frame.
    frames=[patch(0,0),patch(.1,0),patch(.2,0,.1),patch(.3,1,.1),patch(.4,1)]
    loaded=[True,True,False,False,True]
    verdict=cyclic_authority(frames,loaded,[1,0,0],AuthorityThresholds())
    assert verdict['verdict']=='PASS'
    assert verdict['maximum_skin_seam_error_m']==pytest.approx(0)


@pytest.mark.parametrize('case',['hover','skate','seam','state'])
def test_cyclic_authority_does_not_hide_bad_endpoints_or_contacts(case):
    frames=[patch(0,0),patch(.1,0),patch(.2,0,.1),patch(.3,1,.1),patch(.4,1)]
    loaded=[True,True,False,False,True]
    if case=='hover': frames=[replace(f,sole_m=tuple((x,y+.01,z) for x,y,z in f.sole_m),toe_m=tuple((x,y+.01,z) for x,y,z in f.toe_m)) for f in frames]
    if case=='skate': frames[1]=patch(.1,.1)
    if case=='seam': frames[-1]=patch(.4,1.01)
    if case=='state': loaded[-1]=False
    assert cyclic_authority(frames,loaded,[1,0,0],AuthorityThresholds())['verdict']=='FAIL'


def test_unloaded_correction_is_bounded_between_contact_endpoints():
    times=np.linspace(0,1,11)
    loaded=np.array([True,True,True,False,False,False,False,False,True,True,True])
    values=np.zeros((11,3));values[8:,1]=.02
    filled=_cyclic_fill(times,values,loaded)
    assert np.array_equal(filled[loaded],values[loaded])
    assert np.all(filled[:,1]>=0) and np.all(filled[:,1]<=.02)


def test_new_locomotion_recipes_retain_v9_run_stride_and_explicit_narrow_gauge():
    root=Path(__file__).parents[1]
    for gait in ['run','sprint']:
        old=json.loads((root/f'catalog/programs/heavy-biped.{gait}.v2.json').read_text())['parameters']
        new=json.loads((root/f'catalog/programs/heavy-biped.{gait}.v3.json').read_text())['parameters']
        for key in ['step_length_body_heights','step_period_s','flight_fraction','compression_peak_fraction','push_off_start_fraction']:
            assert new[key]==old[key]
    for name in ['walk.v2','fast-walk.v1','reverse-walk.v3','run.v3','sprint.v3']:
        recipe=json.loads((root/f'recipes/heavy-biped/{name}.json').read_text())
        assert 'performance_profile' in recipe
        params=json.loads((root/recipe['performance_profile']['path']).read_text())['parameters']
        assert params['lane_width_body_heights']<=.3
        assert params['tail_yaw_degrees']>0
