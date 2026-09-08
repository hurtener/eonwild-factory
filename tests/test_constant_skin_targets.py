from copy import deepcopy
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from test_canonical_support_anchors import _bound_walk, _canonical_plan, _provider

def _law():
 s,r,c,g,solver,steady,f=_bound_walk(); plan=_canonical_plan(g,float(steady['body_height_m'])); p=_provider(s,r,c,g,solver,plan,f)
 q=SourceMotionQuery(s,semantic_roles=r,solver_gait=solver,locomotion_gait=g,plan=plan,up_axis=(0,1,0),forward_axis=f,contact_profile=c)
 return CanonicalConstantSkinTargetLaw.build(q,p,source=s,semantic_roles=r,solver_gait=solver,locomotion_gait=g,transition=None,plan=plan,contact_profile=c,up_axis=(0,1,0),forward_axis=f),q

def test_constant_law_is_bound_immutable_and_history_independent():
 law,q=_law(); first=law.value(.2); later=law.value(.6); repeat=law.value(.2)
 for side in ('left','right'):
  assert first.corrections_m[side].flags.writeable is False
  assert (first.corrections_m[side] == repeat.corrections_m[side]).all()
  assert first.observations[side]['residual_m'] <= .0002
  assert later.observations[side]['minimum_gap_m'] >= 0
 assert 'UNAVAILABLE' in first.branch_witness['status']

def test_constant_law_rejects_refined_or_mismatched_request():
 law,q=_law(); s,r,c,g,solver,steady,f=_bound_walk(); plan=_canonical_plan(g,float(steady['body_height_m'])); plan['samples'][0]['feet']['left']['target_offset_m']=[0,0,0]
 refined=SourceMotionQuery(s,semantic_roles=r,solver_gait=solver,locomotion_gait=g,plan=plan,up_axis=(0,1,0),forward_axis=f,contact_profile=c)
 with pytest.raises(ContractError,match='unrefined'):
  CanonicalConstantSkinTargetLaw.build(refined,law._provider,source=s,semantic_roles=r,solver_gait=solver,locomotion_gait=g,transition=None,plan=plan,contact_profile=c,up_axis=(0,1,0),forward_axis=f)
 with pytest.raises(ContractError): law.value(float('nan'))
