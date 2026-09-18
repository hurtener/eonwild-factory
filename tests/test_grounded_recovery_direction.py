"""Production-rig regression for the versioned hanging-foot recovery policy."""
import json
from pathlib import Path

import numpy as np

from eonwild_motion.factory.animal import apply_uniform_geometry_scale, load_animal_instance
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import build_grounded_plan, load_grounded_gait
from eonwild_motion.solve.airborne_gait import solve_airborne_gait
from eonwild_motion.solve.performance import decorate_plan, load_performance


ROOT=Path(__file__).resolve().parents[1]
RECIPE=ROOT/'recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v2.json'


def test_emitted_adult_recovery_trails_then_opens_without_limb_translation():
    recipe=json.loads(RECIPE.read_text())
    source=Glb.from_bytes((ROOT/recipe['source']['path']).read_bytes())
    roles=json.loads((ROOT/recipe['rig']['path']).read_text())['roles']
    animal=load_animal_instance(json.loads((ROOT/recipe['animal']['path']).read_text()),
                                source_sha256=recipe['source']['sha256'])
    apply_uniform_geometry_scale(source,animal['uniform_scale'])
    gait=load_grounded_gait(json.loads((ROOT/recipe['program_profile']['path']).read_text()))
    plan=decorate_plan(build_grounded_plan(gait,geometry_height(source,roles,recipe['up_axis'])),
                       load_performance(json.loads((ROOT/recipe['performance_profile']['path']).read_text())))

    targets=[]
    for side in ('left','right'):
        for phase in (.324,.547,.822):
            targets.append((side,phase,min(range(len(plan['samples'])),key=lambda i:
                abs(plan['samples'][i]['feet'][side]['swing_phase']-phase)
                if not plan['samples'][i]['feet'][side]['contact'] else 2.)))
    indices=sorted({0,len(plan['samples'])-1,*(index for _,_,index in targets)})
    sparse=dict(plan,samples=[plan['samples'][index] for index in indices])
    solver_gait=AirborneGait(step_period_s=gait.step_period_s,cycles=gait.cycles,
                            sample_hz=gait.sample_hz,swing_hip_lift_degrees=gait.swing_hip_lift_degrees)
    raw,_,_,_=solve_airborne_gait(source,source_clip=None,semantic_roles=roles,gait=solver_gait,
                                  up_axis=tuple(recipe['up_axis']),forward_axis=tuple(recipe['forward_axis']),
                                  plan_override=sparse,legacy_overlay=False)
    emitted=Glb.from_bytes(raw)
    tracks,_=_clip_state(emitted,emitted.document['animations'][0]['name'])
    index_in_sparse={original:current for current,original in enumerate(indices)}
    forward=np.asarray(recipe['forward_axis'],dtype=float); forward/=np.linalg.norm(forward)
    up=np.asarray(recipe['up_axis'],dtype=float); up/=np.linalg.norm(up)

    for side,phase,original_index in targets:
        current=index_in_sparse[original_index]
        world=_world_matrices(emitted,*_pose(emitted,tracks,current))
        foot=emitted.name_to_node[roles['legs'][side]['contactChain'][-1]]
        tips=[emitted.name_to_node[chain[-1]] for chain in roles['legs'][side]['toeChains']]
        direction=np.mean([np.asarray(_world_position(world[node])) for node in tips],axis=0)
        direction-=np.asarray(_world_position(world[foot])); direction/=np.linalg.norm(direction)
        if phase < .6:
            assert float(direction@forward)<-.05
            assert float(direction@-up)>.98
        else:
            assert float(direction@forward)>.85
            assert float(direction@-up)>.4

    limb_names={name for side in ('left','right') for name in
                (*roles['legs'][side]['contactChain'],
                 *(name for chain in roles['legs'][side]['toeChains'] for name in chain))}
    for name in limb_names:
        values=tracks[(name,'translation')]
        assert np.allclose(values,values[0],rtol=0,atol=0)
