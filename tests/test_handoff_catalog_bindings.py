"""Bindings are necessary but not substitutes for real emitted joins."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.factory.handoff import require_runtime_axes, require_pair
from eonwild_motion.planning.airborne_gait import load_airborne_gait
from eonwild_motion.planning.gait_transition import load_gait_transition, declared_handoff_phase
from eonwild_motion.planning.grounded_gait import load_grounded_gait

ROOT = Path(__file__).resolve().parents[1]
STEADY = {'walk':'walk.v3','reverse-walk':'reverse-walk.v4','run':'run.v4','sprint':'sprint.v4'}


@pytest.mark.parametrize('gait', STEADY)
@pytest.mark.parametrize('kind', ['start','stop'])
def test_phase_zero_handoffs_bind_versioned_gait_snapshots(gait,kind):
    name=f'{gait}-{kind}.v2'
    read=lambda path:json.loads((ROOT/path).read_text())
    transition=read(f'recipes/heavy-biped/{name}.json')
    steady=read(f'recipes/heavy-biped/{STEADY[gait]}.json')
    assert transition['id']==f'heavy-biped.{name}'
    assert transition['version']==2
    assert transition['supersedes']==f'heavy-biped.{gait}-{kind}.v1'
    historical_steady = deepcopy(steady)
    historical_steady['program_profile'] = transition['gait_profile']
    assert transition['gait_profile']['path'].endswith('.phase-zero.json')
    assert require_pair(transition,historical_steady,{'transition_contract':{'kind':kind,'steady_phase_s':0}})==kind
    transition_profile = load_gait_transition(read(transition['program_profile']['path']))
    gait_document = read(transition['gait_profile']['path'])
    load_gait = load_grounded_gait if steady['program'] == 'grounded_gait' else load_airborne_gait
    assert declared_handoff_phase(transition_profile, load_gait(gait_document)) == 0
    for key in ('source','rig','contact_profile','performance_profile','program_profile','gait_profile'):
        ref=transition[key]
        assert hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest()==ref['sha256']


def test_runtime_uses_the_compilers_normalized_axes_not_literal_float_spelling():
    recipe={'forward_axis':[.03893162055641767,0.,.9992418770852486],'up_axis':[0.,1.,0.]}
    runtime={k:(np.asarray(v)/np.linalg.norm(v)).tolist() for k,v in recipe.items()}
    require_runtime_axes(runtime,recipe)
    assert recipe['forward_axis']!=runtime['forward_axis']


@pytest.mark.parametrize('case',['flipped','scaled','small-drift','nonfinite','zero','numeric-string'])
def test_axis_normalization_never_accepts_actual_coordinate_drift(case):
    recipe={'forward_axis':[0.,0.,1.],'up_axis':[0.,1.,0.]};runtime=deepcopy(recipe)
    if case=='flipped':runtime['forward_axis']=[0,0,-1]
    elif case=='scaled':runtime['forward_axis']=[0,0,2]
    elif case=='small-drift':runtime['forward_axis']=[1e-7,0,1]
    elif case=='nonfinite':runtime['forward_axis'][0]=float('nan')
    elif case=='zero':recipe['forward_axis']=[0,0,0]
    elif case=='numeric-string':runtime['forward_axis']=['0','0','1']
    with pytest.raises(ContractError):require_runtime_axes(runtime,recipe)
