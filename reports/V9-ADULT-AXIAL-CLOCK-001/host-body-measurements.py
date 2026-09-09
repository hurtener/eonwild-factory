"""Independent reopened body geometry comparison, without motion edits."""
from pathlib import Path
import hashlib
import json
import numpy as np

from eonwild_motion.factory.animal import scaled_contact_profile
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose
from eonwild_motion.solve.skin_rig import SkinRig

TASK = Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521')
REPO = Path('/Volumes/m2-extended-disk/Repos/eonwild-factory')
PACKAGES = {
    'v8': TASK / 'out/continuation-adult-v8-bind-pose-001',
    'axial_483e006': TASK / 'worktrees/eonwild-adult-axial-clock/out/continuation-adult-v8-axial-clock-001/package',
}
result = {
    'classification': 'Reopened complete emitted geometry only. Trunk vertex means and closed-surface uniform-volume centroids are geometric descriptors, not animal COM, load distribution, forces, stability or visual approval.',
    'position_frame': 'All reported positions are relative to the emitted root-node origin, projected on the declared world lateral axis. Volume is in world metres cubed.',
    'packages': {},
}
for label, package in PACKAGES.items():
    plan = json.loads((package / 'plan.json').read_text())
    runtime = json.loads((package / 'runtime.json').read_text())
    recipe = json.loads((package / 'recipe.json').read_text())
    bio = json.loads((package / 'biomechanics.json').read_text())
    roles = runtime['rig_roles']
    blob = (package / 'root_motion.glb').read_bytes()
    glb = Glb.from_bytes(blob)
    profile = scaled_contact_profile(
        json.loads((REPO / recipe['contact_profile']['path']).read_text()),
        bio['geometry']['uniform_scale'],
    )
    skin = SkinRig(glb, roles, runtime['forward_axis'], runtime['up_axis'], profile)
    tracks, times = _clip_state(glb, glb.document['animations'][0]['name'])
    times = np.asarray(times)
    assert len(times) == len(plan['samples'])
    nodes = {name: glb.name_to_node[roles[name]] for name in ('root', 'pelvis', 'chest', 'head')}
    nodes['tail_tip'] = glb.name_to_node[roles['tail'][-1]]
    trunk_nodes = [glb.name_to_node[n] for n in [*roles['spine'], roles['chest']]]
    trunk_strength = np.sum(skin.weights * np.isin(skin.node_ids, trunk_nodes), axis=1)
    trunk_mask = np.flatnonzero(trunk_strength >= .5)
    assert len(trunk_mask)
    primitive = glb.document['meshes'][0]['primitives'][0]
    assert primitive.get('mode', 4) == 4
    triangles = np.asarray(glb.accessor_values(primitive['indices']), dtype=int).reshape(-1, 3)
    step = plan['parameters']['step_period_s']
    duty = plan['parameters']['duty_factor']
    targets = {'DS_left': (duty-.5)*step, 'SS_left': duty*step,
               'DS_right': (duty+.5)*step, 'SS_right': (duty+1)*step}
    landmarks = {int(np.argmin(abs(times-t))): name for name, t in targets.items()}
    series = {name: [] for name in nodes if name != 'root'}
    phase_rows = {}
    for i, time in enumerate(times):
        worlds = skin.world(*_pose(glb, tracks, i))
        root = worlds[nodes['root'], :3, 3]
        for name in series:
            series[name].append(float((worlds[nodes[name], :3, 3]-root) @ skin.lateral))
        if i not in landmarks:
            continue
        xyz = skin.skin(worlds)
        a, b, c = (xyz[triangles[:, j]] for j in range(3))
        volume_terms = np.einsum('ij,ij->i', a, np.cross(b, c)) / 6
        volume = float(np.sum(volume_terms))
        center = np.einsum('i,ij->j', volume_terms, a+b+c) / (4*volume)
        phase_rows[landmarks[i]] = {
            'index': i, 'time_s': float(time), 'target_time_s': targets[landmarks[i]],
            'contacts': [s for s in ('left', 'right') if plan['samples'][i]['feet'][s]['contact']],
            'lateral_role_origins_m': {n: series[n][-1] for n in series},
            'trunk_vertex_mean_lateral_m': float((xyz[trunk_mask].mean(axis=0)-root) @ skin.lateral),
            'uniform_volume_centroid_lateral_m': float((center-root) @ skin.lateral),
            'oriented_volume_m3': volume,
        }
    result['packages'][label] = {
        'root_motion_sha256': hashlib.sha256(blob).hexdigest(),
        'sample_count': len(times), 'trunk_vertex_count': len(trunk_mask),
        'lateral_peak_to_peak_m': {n: float(np.ptp(v)) for n, v in series.items()},
        'landmarks': phase_rows,
    }
out = Path(__file__).with_suffix('.json')
out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
print(json.dumps(result, indent=2, allow_nan=False))
print('receipt_sha256', hashlib.sha256(out.read_bytes()).hexdigest())
