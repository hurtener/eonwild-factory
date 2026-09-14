import json
import math
from copy import deepcopy
from pathlib import Path
import pytest
from eonwild_motion.attention import resolve_attention, bound_attention, attention_intent

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('animal', ['allo', 'tarbo'])
def test_envelope_is_symmetric_smooth_and_distinguishes_exceptional(animal):
    p=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    a=resolve_attention(p);e=a['envelope']
    assert bound_attention(e['normalDegrees'],a)['yawDegrees']==e['normalDegrees']
    last=-1.
    for i in range(1801):
        x=i/10.;v=bound_attention(x,a)
        assert last<=v['yawDegrees']<=e['maximumDegrees']
        assert bound_attention(-x,a)['yawDegrees']==-v['yawDegrees']
        assert v['yawDegrees']+v['unfulfilledYawDegrees']==pytest.approx(x)
        last=v['yawDegrees']
    assert e['maximumDegrees']<bound_attention(180.,a,True)['yawDegrees']<=e['hardDegrees']
    x=e['strongDegrees'];h=1e-4
    assert (bound_attention(x+h,a)['yawDegrees']-bound_attention(x-h,a)['yawDegrees'])/(2*h)==pytest.approx(1.,abs=1e-6)
    renamed=deepcopy(p);renamed['id']='unknown-animal'
    for b in renamed['bindings']:b['bone']='renamed_'+b['bone']
    assert resolve_attention(renamed)==a
    for invalid in (float('nan'),float('inf')):
        with pytest.raises(ValueError):bound_attention(invalid,a)


@pytest.mark.parametrize('mutation', ['weights','order','source','limit','nan'])
def test_bad_envelopes_fail_closed(mutation):
    p=json.loads((ROOT/'catalog/embodiment/allo.v1.json').read_text());e=p['attention']['envelope']
    if mutation=='weights':e['neckWeights']=[1.]
    if mutation=='order':e['strongDegrees']=100.
    if mutation=='source':e['source']=''
    if mutation=='limit':p['attention']['yawLimit']=90.
    if mutation=='nan':e['maximumDegrees']=float('nan')
    with pytest.raises(ValueError):resolve_attention(p)


def test_historical_profile_keeps_legacy_behavior():
    p=json.loads((ROOT/'catalog/embodiment/allo.v1.json').read_text())
    p['attention'].pop('envelope')
    assert resolve_attention(p) is None


@pytest.mark.parametrize('animal', ['allo', 'tarbo'])
def test_only_explicit_exceptional_intent_enters_exceptional_range(animal):
    p=json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    a=resolve_attention(p);e=a['envelope']
    for mode in ('none','normal','scan','strong'):
        intent=attention_intent(mode,a)
        assert intent['exceptional'] is False
        assert bound_attention(intent['requestedDegrees'],a)['yawDegrees']<=e['maximumDegrees']
    intent=attention_intent('exceptional',a)
    value=bound_attention(intent['requestedDegrees'],a,intent['exceptional'])
    assert e['maximumDegrees']<value['yawDegrees']<e['hardDegrees']
    with pytest.raises(ValueError):
        attention_intent('unrecognized',a)
