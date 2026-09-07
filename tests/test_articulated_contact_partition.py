"""The metatarsal may articulate without treating the pad as the ankle."""
from copy import deepcopy
from dataclasses import replace
import numpy as np
import pytest

from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.airborne_gait import build_airborne_plan
from eonwild_motion.planning.grounded_gait import GroundedGait, build_grounded_plan
from eonwild_motion.solve.airborne_gait import solve_airborne_gait, _recovery_pitch_target
from eonwild_motion.solve.performance import Performance, decorate_plan
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices
from eonwild_motion.glb.container import Glb
from test_v9_airborne_gait import fixture


@pytest.mark.parametrize('travel',[.18,-.18])
def test_stance_pad_and_digits_are_fixed_while_metatarsal_articulates(travel, monkeypatch):
    import importlib
    solver_module = importlib.import_module('eonwild_motion.solve.airborne_gait')
    original_recovery = solver_module._recovery_pitch_target
    recovery_modes = []

    def observe_recovery(gait, foot_plan, *, airborne):
        recovery_modes.append(airborne)
        return original_recovery(gait, foot_plan, airborne=airborne)

    monkeypatch.setattr(solver_module, '_recovery_pitch_target', observe_recovery)
    source,roles=fixture()
    height=1.0
    plan=build_grounded_plan(GroundedGait(step_length_body_heights=travel,
        touchdown_reach_body_heights=.08,cycles=1,sample_hz=24,
        push_off_pitch_degrees=18,foot_recovery_pitch_degrees=24,toe_flex_degrees=15),height)
    plan=decorate_plan(plan,Performance(lane_width_body_heights=.3,center_tail=False,
        pelvis_sway_body_heights=0,pelvis_yaw_degrees=0,pelvis_roll_degrees=0,tail_yaw_degrees=0,
        gaze_elevation_degrees=0,skin_refinement=False))
    # The synthetic limb fixture has no axial body. A zeroed performance layer
    # still needs explicit axial roles; reuse valid existing nodes by role in
    # this isolated limb test without claiming real-family transfer.
    roles=dict(roles)
    roles.setdefault('chest',roles['pelvis'])
    roles.setdefault('head',roles['pelvis'])
    roles.setdefault('tail',[])
    raw,_,_,receipt=solve_airborne_gait(source,source_clip=None,semantic_roles=roles,
        gait=AirborneGait(cycles=1,sample_hz=24),up_axis=(0,1,0),forward_axis=(0,0,1),
        plan_override=plan,legacy_overlay=False)
    glb=Glb.from_bytes(raw)
    tracks,times=_clip_state(glb,glb.document['animations'][0]['name'])
    matrices=[_world_matrices(glb,*_pose(glb,tracks,i)) for i in range(len(times))]
    for side in ('left','right'):
        chain=roles['legs'][side]['contactChain']
        nodes=[glb.name_to_node[n] for digit in roles['legs'][side]['toeChains'] for n in digit]
        pairs=0
        for i in range(1,len(times)):
            if plan['samples'][i-1]['feet'][side]['contact'] and plan['samples'][i]['feet'][side]['contact']:
                a=np.array([matrices[i-1][n] for n in nodes])
                b=np.array([matrices[i][n] for n in nodes])
                assert np.max(np.abs(a-b))<2e-5
                pairs+=1
        assert pairs>2
        pitch=[row['feet'][side]['solved_foot_pitch_degrees'] for row in receipt['emitted_proxy_samples']]
        assert np.ptp(pitch)>1
    assert recovery_modes and not any(recovery_modes)


def test_no_nearly_straight_toe_projection_in_new_material_partition():
    # Source-level safeguard supplements the actual FK witness above; the
    # legacy branch must remain available for immutable reproduction.
    import inspect
    body=inspect.getsource(solve_airborne_gait)
    assert 'rot[foot] = _world_rotation' in body
    assert 'for _ in range(18 if not material_partition' in body


def test_same_authored_phase_is_independent_of_prior_sampling_history():
    source, roles = fixture()
    gait = AirborneGait(cycles=1, sample_hz=24)
    base = build_airborne_plan(gait, 1.0)
    target = deepcopy(base['samples'][6])
    solved = []
    for prior_pitch in (-45.0, 85.0):
        prior = deepcopy(base['samples'][0])
        prior['time_s'] = target['time_s'] - 0.001
        for side in ('left', 'right'):
            prior['feet'][side]['foot_pitch_degrees'] = prior_pitch
        plan = {**deepcopy(base), 'samples': [prior, deepcopy(target)]}
        _, _, _, receipt = solve_airborne_gait(
            source, source_clip=None, semantic_roles=roles, gait=gait,
            up_axis=(0, 1, 0), forward_axis=(0, 0, 1),
            plan_override=plan, legacy_overlay=False,
        )
        solved.append({
            side: receipt['emitted_proxy_samples'][1]['feet'][side]['solved_foot_pitch_degrees']
            for side in ('left', 'right')
        })
    assert solved[0] == solved[1]


def test_airborne_recovery_carrier_does_not_reinterpret_grounded_profiles():
    gait = AirborneGait(swing_recovery_peak_fraction=0.42, swing_hip_lift_degrees=40)
    foot = {"contact": False, "swing_phase": 0.7, "foot_pitch_degrees": 24.0}
    assert _recovery_pitch_target(gait, foot, airborne=False) == 24.0
    assert _recovery_pitch_target(gait, foot, airborne=True) < 24.0
    epsilon = 1e-6
    foot['swing_phase'] = gait.swing_recovery_peak_fraction
    at_peak = _recovery_pitch_target(gait, foot, airborne=True)
    foot['swing_phase'] += epsilon
    after_peak = _recovery_pitch_target(gait, foot, airborne=True)
    assert abs((after_peak - at_peak) / epsilon) < 0.01
    foot['swing_phase'] = 1.0
    at_touchdown = _recovery_pitch_target(gait, foot, airborne=True)
    foot['swing_phase'] -= epsilon
    before_touchdown = _recovery_pitch_target(gait, foot, airborne=True)
    assert at_touchdown == 24.0
    assert abs((at_touchdown - before_touchdown) / epsilon) < 0.01
