from dataclasses import replace
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.grounded_gait import GroundedGait,sample_grounded_gait,touchdown_reach
from eonwild_motion.planning.gait_transition import GaitTransition,build_transition_plan


@pytest.mark.parametrize('length',[.6,-.38])
@pytest.mark.parametrize('duty',[.58,.62,.72])
def test_long_stride_has_balanced_stance_without_shortening_it(length,duty):
    gait=GroundedGait(step_length_body_heights=length,duty_factor=duty,centered_stance=True)
    height=2.64
    middle=gait.step_period_s*duty
    row=sample_grounded_gait(gait,middle,height)
    assert row['feet']['left']['contact']
    assert row['feet']['left']['forward_m']-row['root_forward_m']==pytest.approx(0,abs=1e-12)
    start=sample_grounded_gait(gait,0,height)
    end=sample_grounded_gait(gait,2*gait.step_period_s,height)
    assert end['root_forward_m']-start['root_forward_m']==pytest.approx(2*length*height)
    assert end['feet']['left']['forward_m']-start['feet']['left']['forward_m']==pytest.approx(2*length*height)


def test_fixed_reach_mode_keeps_original_recipe_semantics():
    gait=GroundedGait(step_length_body_heights=-.38,touchdown_reach_body_heights=.12)
    assert touchdown_reach(gait,2)==pytest.approx(-.24)
    assert sample_grounded_gait(gait,0,2)['feet']['left']['forward_m']==pytest.approx(-.24)


@pytest.mark.parametrize('invalid',[0,1,'true',None])
def test_centering_requires_explicit_boolean(invalid):
    with pytest.raises(ContractError):GroundedGait(centered_stance=invalid)


def test_transition_uses_identical_steady_placement_authority():
    gait=GroundedGait(step_length_body_heights=.6,centered_stance=True)
    height=2.64
    plan=build_transition_plan(GaitTransition(kind='start',sample_hz=24),gait,height)
    steady=sample_grounded_gait(gait,0,height)
    final=plan['samples'][-1]
    assert final['feet']['left']['forward_m']-final['root_forward_m']==pytest.approx(steady['feet']['left']['forward_m'],abs=1e-7)
