"""Adversarial boundary tests; actual skinned joins are checked separately."""
from copy import deepcopy
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.factory.handoff import compare_boundaries,require_pair


def boundary(times,position_shift=0.,velocity=1.,omega=.2):
    t=np.array(times,dtype=float)
    p=np.zeros((3,2,3));p[:,:,0]=t[:,None]*velocity+position_shift;p[:,1,1]=1
    q=np.zeros((3,2,4));q[:,:,1]=np.sin(t[:,None]*omega/2);q[:,:,3]=np.cos(t[:,None]*omega/2)
    skin=p.copy();skin[:,1,1]=0
    return {'times':t,'positions':p,'rotations':q,'skin':skin,'contacts':{'left':True,'right':False}}


def pair():return boundary([-.03,-.01,0],position_shift=8),boundary([0,.007,.021])


def test_native_uneven_boundary_alignment_without_mutation():
    a,b=pair();old=deepcopy((a,b))
    assert compare_boundaries(a,b,[8,0,0])['status']=='PASS'
    for value,prior in zip((a,b),old):
        for key in ('times','positions','rotations','skin'):assert np.array_equal(value[key],prior[key])


def test_antipodal_quaternion_is_not_a_false_snap():
    a,b=pair();b['rotations'][::2]*=-1
    assert compare_boundaries(a,b,[8,0,0])['status']=='PASS'


@pytest.mark.parametrize('case',['position','skin','linear','angular','contacts','double-root'])
def test_endpoint_equality_does_not_hide_other_failures(case):
    a,b=pair()
    if case=='position':b['positions'][:,:,1]+=.02
    elif case=='skin':b['skin'][:,:,1]+=.001
    elif case=='linear':b['positions'][:,:,0]+=b['times'][:,None]*.02
    elif case=='angular':b=boundary([0,.007,.021],omega=1.)
    elif case=='contacts':b['contacts']['left']=False
    elif case=='double-root':b['positions'][:,:,0]+=b['times'][:,None]
    assert compare_boundaries(a,b,[8,0,0])['status']=='FAIL'


@pytest.mark.parametrize('key',['positions','skin','rotations','times'])
@pytest.mark.parametrize('which',[0,1])
def test_invalid_original_endpoint_is_rejected(key,which):
    values=list(pair());values[which][key][-1 if which==0 else 0]=np.nan
    with pytest.raises(ContractError):compare_boundaries(*values,[8,0,0])


@pytest.mark.parametrize('case',['zero-quaternion','boolean-contact','short','unordered','mismatched-skin','mismatched-nodes','numeric-string'])
def test_malformed_evidence_fails_closed(case):
    a,b=pair()
    if case=='zero-quaternion':b['rotations'][0]=0
    elif case=='boolean-contact':b['contacts']['left']=1
    elif case=='short':b['times']=b['times'][:2]
    elif case=='unordered':b['times'][1]=0
    elif case=='mismatched-skin':b['skin']=b['skin'][:,:1]
    elif case=='mismatched-nodes':b['positions']=b['positions'][:,:1];b['rotations']=b['rotations'][:,:1]
    elif case=='numeric-string':b['times']=b['times'].astype(str)
    with pytest.raises(ContractError):compare_boundaries(a,b,[8,0,0])


def bound_recipes():
    common={'source':{'path':'neutral.glb','sha256':'1'},'rig':{'path':'rig.json','sha256':'2'},
            'contact_profile':{'path':'contact.json','sha256':'3'},'performance_profile':{'path':'performance.json','sha256':'4'},
            'family':'generic','forward_axis':[1,0,0],'up_axis':[0,1,0]}
    steady={**common,'program':'airborne_gait','program_profile':{'path':'gait.json','sha256':'5'}}
    trans={**common,'program':'gait_transition','gait_profile':deepcopy(steady['program_profile'])}
    return trans,steady,{'transition_contract':{'kind':'start','steady_phase':0}}


@pytest.mark.parametrize('key',['source','rig','contact_profile','performance_profile','family','forward_axis','up_axis','gait_profile'])
def test_wrong_provenance_is_not_a_valid_handoff(key):
    a,b,r=bound_recipes();a[key]='different'
    with pytest.raises(ContractError):require_pair(a,b,r)


@pytest.mark.parametrize('phase',[None,True,.1,'0'])
def test_phase_is_explicit_without_best_fit_search(phase):
    a,b,r=bound_recipes();assert require_pair(a,b,r)=='start'
    r['transition_contract']['steady_phase']=phase
    with pytest.raises(ContractError):require_pair(a,b,r)
