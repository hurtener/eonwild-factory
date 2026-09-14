"""Walking flexion reserve must preserve the articulated endpoint and bone lengths."""
from copy import deepcopy
import numpy as np
import pytest
from test_v9_airborne_gait import fixture
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.grounded_gait import GroundedGait, build_grounded_plan, sample_grounded_gait
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.solve.performance import Performance, decorate_plan
from eonwild_motion.solve.airborne_gait import build_airborne_solve_context, solve_airborne_plan_sample, _interior
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices


def setup(prefix='renamed', scale=1.):
    source, roles = fixture(prefix=prefix, scale=scale, upper_body=True)
    gait = GroundedGait(cycles=1, sample_hz=24)
    plan = decorate_plan(build_grounded_plan(gait, 1.8*scale), Performance(
        pelvis_sway_body_heights=0, pelvis_yaw_degrees=0, pelvis_roll_degrees=0,
        tail_yaw_degrees=0, gaze_elevation_degrees=0, center_tail=False, skin_refinement=False))
    context = build_airborne_solve_context(source, source_clip=None, semantic_roles=roles,
        gait=AirborneGait(), plan=plan, forward_axis=(0,0,1), legacy_overlay=False)
    row = sample_grounded_gait(gait, .1, 1.8*scale)
    for foot in row['feet'].values():
        foot['distal_endpoint_role'] = 'shape_preference'
    return source, context, row


@pytest.mark.parametrize('scale', [.6, 2.])
def test_flexion_reserve_rebalances_joint_rotations_without_shortening_bones(scale):
    source, context, row = setup(scale=scale)
    baseline = solve_airborne_plan_sample(context, row)
    request = deepcopy(row)
    for foot in request['feet'].values():
        foot['walking_knee_preference_degrees'] = 130.
    corrected = solve_airborne_plan_sample(context, request)
    def geometry(pose):
        w = np.asarray(_world_matrices(source, pose.translations, pose.rotations, context.base_s))
        return [w[n][:3,3] for n in context.legs['left']]
    old, new = geometry(baseline), geometry(corrected)
    assert _interior(old[0]-old[1], old[2]-old[1]) > _interior(new[0]-new[1], new[2]-new[1]) + 1
    np.testing.assert_allclose(new[0], old[0], atol=1e-9)
    np.testing.assert_allclose(new[-1], old[-1], atol=1e-9)
    np.testing.assert_allclose(np.linalg.norm(np.diff(new, axis=0), axis=1),
                               np.linalg.norm(np.diff(old, axis=0), axis=1), atol=1e-9)
    assert corrected.maximum_unreachable_extension_m < 1e-9
    assert corrected.maximum_foot_target_residual_m < 1e-9
    replay = solve_airborne_plan_sample(context, row)
    np.testing.assert_array_equal(replay.rotations, baseline.rotations)


@pytest.mark.parametrize('bad', [True, float('nan'), 180., 89.])
def test_invalid_preference_is_rejected(bad):
    _, context, row = setup()
    row['feet']['left']['walking_knee_preference_degrees'] = bad
    with pytest.raises(ContractError, match='walking knee extension preference'):
        solve_airborne_plan_sample(context, row)
