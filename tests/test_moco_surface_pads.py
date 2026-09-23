import copy
import numpy as np
from eonwild_motion.solve.moco_tasks import foot_geometry


def test_surface_contacts_cover_asymmetric_feet_without_increasing_total_stiffness():
    x, z = np.meshgrid(np.linspace(-.2, .8, 30), np.linspace(-.6, .2, 25))
    vertices = np.c_[x.ravel(), np.full(x.size, -.18), z.ravel()]
    admission = {'points': {f'{side}Leg.{i}': [0, -i, 0] for side in ('left', 'right') for i in range(4)},
                 'foot_surface': {side: {'vertices_m': (vertices * [1, 1, sign]).tolist(),
                                         'toe_midpoint_m': [.3, 0, 0]}
                                  for side, sign in [('left', 1), ('right', -1)]}}
    recipe = {'spatial': True, 'calibrated_task': {'pad_radius_leg_lengths': .04, 'pad_envelope_margin_m': .005}}
    old = foot_geometry(admission, recipe)
    enabled = copy.deepcopy(recipe)
    enabled['calibrated_task']['surface_edge_pads'] = True
    new = foot_geometry(admission, enabled)
    assert old['sites'] == new['sites']
    assert not old['sites_by_side']
    for side, sign in [('l', -1), ('r', 1)]:
        sites = new['sites_by_side'][side]
        assert len(sites) > len(old['sites'])
        assert np.isclose(sum(s.get('stiffness_share', 1) for s in sites), 5)
        assert max(sign * s['center_local_m'][2] for s in sites) > .5
        assert all(np.isclose(s['center_local_m'][1] - s['radius_m'], -.185) for s in sites)
