"""Regression witnesses for articulation, recipe reuse, and real cyclic contact."""
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
    Performance, apply_performance, decorate_plan, load_performance,
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


def test_upper_trunk_counterroll_rejects_duplicate_or_disconnected_roles():
    source, roles = fixture("counter", upper_body=True)
    roles["spine"] = [roles["chest"]]
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
    with pytest.raises(ContractError, match="unique semantic spine/chest chain"):
        _performance_pose(source, roles, plan, row, up, forward)


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
