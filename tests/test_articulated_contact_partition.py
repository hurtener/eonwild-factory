"""The metatarsal may articulate without treating the pad as the ankle."""
from dataclasses import replace
import numpy as np
import pytest

from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import GroundedGait, build_grounded_plan
from eonwild_motion.solve.airborne_gait import solve_airborne_gait
from eonwild_motion.solve.performance import Performance, decorate_plan
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices
from eonwild_motion.glb.container import Glb
from test_v9_airborne_gait import fixture


@pytest.mark.parametrize('travel',[.18,-.18])
def test_stance_pad_and_digits_are_fixed_while_metatarsal_articulates(travel):
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


def test_no_nearly_straight_toe_projection_in_new_material_partition():
    # Source-level safeguard supplements the actual FK witness above; the
    # legacy branch must remain available for immutable reproduction.
    import inspect
    body=inspect.getsource(solve_airborne_gait)
    assert 'rot[foot] = _world_rotation' in body
    assert '14 if material_partition else 7' in body
