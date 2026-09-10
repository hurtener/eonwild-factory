from copy import deepcopy
import math

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.airborne_gait import (
    _prepare_body_pose,
    _rotation_from_matrix,
    _world_matrices,
)
from eonwild_motion.solve.body_support_control import BodySupportControl
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
from eonwild_motion.solve.whole_body_gait_transition import _encode
from test_source_motion_query import _grounded_query, _scaled_adult_v7_query


def _control(query, coefficients):
    return BodySupportControl.build(
        coefficients,
        same_foot_cycle_s=query._plan["same_foot_cycle_s"],
        body_height_m=query.context.body_height,
        up_axis=query.context.up,
        forward_axis=query.context.forward,
    )


def _rebuild(query, source, roles, gait, plan, solver, control):
    return SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=gait,
        plan=plan,
        forward_axis=(0., 0., 1.),
        body_support_control=control,
    )


def test_default_and_zero_control_preserve_exact_existing_pose():
    query, source, roles, gait, plan, solver = _grounded_query()
    zero = _rebuild(query, source, roles, gait, plan, solver, _control(query, [0.] * 12))
    for time_s in (0., plan["same_foot_cycle_s"] * .37, plan["duration_s"]):
        baseline = query.evaluate(time_s)
        controlled = zero.evaluate(time_s)
        assert controlled.pose == baseline.pose
        assert np.array_equal(controlled.worlds, baseline.worlds)
    receipt = zero.body_support_control_receipt()
    assert receipt["coefficients"] == (0.,) * 12
    assert receipt["up_axis"] == pytest.approx(query.context.up)
    assert receipt["forward_axis"] == pytest.approx(query.context.forward)
    assert query.body_support_control_receipt() is None


def test_control_applies_world_pelvis_transform_before_leg_ik_with_rotated_parent():
    initial, source, roles, _, _, _ = _grounded_query()
    document = deepcopy(source.document)
    root = source.name_to_node[roles["root"]]
    angle = math.radians(37.)
    document["nodes"][root]["rotation"] = [0., math.sin(angle / 2), 0., math.cos(angle / 2)]
    rotated = Glb.from_bytes(_encode(document, source.binary))
    query, source, roles, gait, plan, solver = _grounded_query(source=rotated, roles=roles)
    coefficients = np.zeros(12)
    coefficients[[1, 3, 5]] = [0.012, 0.006, -0.004]
    coefficients[[7, 9, 11]] = [0.02, -0.01, 0.015]
    controlled = _rebuild(query, source, roles, gait, plan, solver, _control(query, coefficients))
    row = plan["samples"][0]
    _, base_t, base_r = _prepare_body_pose(query.context, row, query._body_sample(0, row))
    _, next_t, next_r = _prepare_body_pose(controlled.context, row, controlled._body_sample(0, row))
    base_world = np.asarray(_world_matrices(source, base_t, base_r, query.context.base_s))
    next_world = np.asarray(_world_matrices(source, next_t, next_r, query.context.base_s))
    pelvis, root = query.context.pelvis, query.context.root
    expected_delta = (query.context.forward * .012 + query.context.up * .006
                      + query.context.lateral * -.004)
    assert next_world[pelvis, :3, 3] - base_world[pelvis, :3, 3] == pytest.approx(expected_delta, abs=1e-12)
    assert np.array_equal(next_world[root], base_world[root])
    # The world rotation differs on all three declared axes despite a rotated parent.
    assert not np.allclose(
        _rotation_from_matrix(next_world[pelvis]),
        _rotation_from_matrix(base_world[pelvis]),
        rtol=0., atol=1e-10,
    )
    solved_base, solved_next = query.evaluate(0.), controlled.evaluate(0.)
    assert solved_next.row == solved_base.row
    assert np.array_equal(solved_next.worlds[root], solved_base.worlds[root])


def test_control_preserves_performance_foot_targets_and_root_travel():
    query, source, roles, plan = _scaled_adult_v7_query()
    coefficients = np.zeros(12)
    coefficients[[1, 3, 5, 7, 9, 11]] = [.01, .005, -.003, .01, -.005, .008]
    control = _control(query, coefficients)
    controlled = SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=query._solver_gait,
        locomotion_gait=query._locomotion_gait,
        plan=plan,
        up_axis=query._up_axis,
        forward_axis=query._forward_axis,
        legacy_overlay=query._legacy_overlay,
        body_support_control=control,
    )
    for time_s in (0., .31):
        baseline, shifted = query.evaluate(time_s), controlled.evaluate(time_s)
        assert np.array_equal(shifted.worlds[query.context.root], baseline.worlds[query.context.root])
        for side in ("left", "right"):
            assert shifted.pose.feet[side]["target_foot_world_m"] == pytest.approx(
                baseline.pose.feet[side]["target_foot_world_m"], abs=1e-12)


def test_periodic_control_is_query_order_independent_at_source_cycle_seam():
    query, source, roles, gait, plan, solver = _grounded_query()
    coefficients = np.linspace(-0.01, 0.01, 12)
    controlled = _rebuild(query, source, roles, gait, plan, solver, _control(query, coefficients))
    cycle = plan["same_foot_cycle_s"]
    start_row = controlled._sample_row(0.)
    end_row = controlled._sample_row(cycle)
    start = controlled._body_sample(None, start_row)["body_support_control"]
    end = controlled._body_sample(None, end_row)["body_support_control"]
    assert start["translation_forward_up_lateral_m"] == pytest.approx(
        end["translation_forward_up_lateral_m"], abs=1e-14)
    assert start["rotation_pitch_roll_yaw_radians"] == pytest.approx(
        end["rotation_pitch_roll_yaw_radians"], abs=1e-14)
    times = (.17, .83, .41)
    forward = {time: controlled.evaluate(time).pose for time in times}
    reverse = {time: controlled.evaluate(time).pose for time in reversed(times)}
    assert forward == reverse


@pytest.mark.parametrize(
    "coefficients,cycle,height,up,forward,message",
    [
        ([0.] * 11, 2., 1.6, (0., 1., 0.), (0., 0., 1.), "12 finite"),
        ([0.] * 11 + [float("nan")], 2., 1.6, (0., 1., 0.), (0., 0., 1.), "12 finite"),
        ([0.2] + [0.] * 11, 2., 1.6, (0., 1., 0.), (0., 0., 1.), "policy bound"),
        ([0.] * 12, 0., 1.6, (0., 1., 0.), (0., 0., 1.), "source cycle"),
        ([0.] * 12, 2., 0., (0., 1., 0.), (0., 0., 1.), "body height"),
        ([0.] * 12, 2., 1.6, (0., 2., 0.), (0., 0., 1.), "unit vector"),
        ([0.] * 12, 2., 1.6, (0., 1., 0.), (0., 1., 0.), "orthogonal"),
    ],
)
def test_control_rejects_invalid_coefficients_bounds_clock_and_frames(
    coefficients, cycle, height, up, forward, message
):
    with pytest.raises(ContractError, match=message):
        BodySupportControl.build(
            coefficients,
            same_foot_cycle_s=cycle,
            body_height_m=height,
            up_axis=up,
            forward_axis=forward,
        )


def test_control_binding_detects_internal_corruption():
    query, source, roles, gait, plan, solver = _grounded_query()
    control = _control(query, [0.] * 12)
    controlled = _rebuild(query, source, roles, gait, plan, solver, control)
    object.__setattr__(control, "coefficients", (0.01,) + control.coefficients[1:])
    with pytest.raises(ContractError, match="binding differs"):
        controlled.evaluate(.2)
