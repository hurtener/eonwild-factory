"""Continuous lag is shared choreography, not filtering a rejected export."""
import json
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.solve.airborne_gait import periodic_response, sample_periodic_response, driven_body_response
from eonwild_motion.planning.airborne_gait import load_airborne_gait, build_airborne_plan
from eonwild_motion.planning.gait_transition import GaitTransition, build_transition_plan


def test_reference_states_remain_exact_and_query_order_is_irrelevant():
    t=np.array([0., .1, .3, .6, 1.]); x=np.array([0., 1., -.5, -.2, 0.])
    expected=periodic_response(t,x,.12)
    assert np.array_equal(sample_periodic_response(t,x,.12,t),expected)
    q=np.array([.03,.28,.34,.95,.5])
    assert np.array_equal(sample_periodic_response(t,x,.12,q)[::-1],sample_periodic_response(t,x,.12,q[::-1]))


def test_state_derivative_obeys_the_driven_ode_through_every_knot():
    t=np.array([0.,.1,.3,.6,1.]);x=np.array([0.,1.,-.5,-.2,0.]);tau=.12
    states=periodic_response(t,x,tau);h=1e-7
    for i in range(1,len(t)-1):
        values=sample_periodic_response(t,x,tau,np.array([t[i]-h,t[i],t[i]+h]))
        slopes=np.diff(values)/h
        assert np.max(abs(slopes-(x[i]-states[i])/tau))<1e-4
    # The old angle lerp has unequal incoming/outgoing slopes at this knot.
    assert abs((states[2]-states[1])/(t[2]-t[1])-(states[1]-states[0])/(t[1]-t[0]))>1


@pytest.mark.parametrize('bad', ['nan','unordered','shape','outside','bad-lag'])
def test_bad_queries_do_not_get_clamped_to_a_passing_pose(bad):
    t=[0.,.1,.3,1.];x=[0.,1.,-.5,0.];q=[.05,.4];tau=.2
    if bad=='nan':q[0]=float('nan')
    elif bad=='unordered':t[2]=.1
    elif bad=='shape':x=x[:-1]
    elif bad=='outside':q[0]=-.1
    else:tau=float('inf')
    with pytest.raises(ContractError):sample_periodic_response(t,x,tau,q)


def test_transition_queries_are_exact_on_the_sustained_response_knots():
    root=Path(__file__).resolve().parents[1]
    g=load_airborne_gait(json.loads((root/'catalog/programs/heavy-biped.sprint.v4.json').read_text()))
    roles=json.loads((root/'catalog/rigs/heavy-biped.v9.json').read_text())['roles']
    steady=build_airborne_plan(g,2.64)
    expected=driven_body_response(g,steady,roles)
    # Query the *same generator*, never copy a generated animation into a new one.
    query={**steady,'program':'gait_transition','samples':[{**r,'locomotion_time_s':r['time_s'],'performance_gain':1.} for r in steady['samples']]}
    actual=driven_body_response(g,query,roles)
    for a,b in zip(actual['samples'],expected['samples']):
        assert a['sagittal_node_degrees']==b['sagittal_node_degrees']
