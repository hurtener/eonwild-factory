from copy import deepcopy
import json
from pathlib import Path
import pytest
from eonwild_motion.embodiment import validate, SecondaryState
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture(params=['allo','tarbo'])
def profile(request):return json.loads((ROOT/'catalog/embodiment'/f'{request.param}.v1.json').read_text())
def test_optional_anatomy_and_renaming(profile):
 p=deepcopy(profile);p['secondary']['arms']=[];p['secondary']['hasJaw']=False
 for b in p['bindings']:b['bone']='renamed_'+b['bone']
 names=list({b['bone'] for b in p['bindings']});validate(p,names)
 assert SecondaryState(p).step(.1,1,.5)==[]
def test_missing_or_ambiguous_binding_rejected(profile):
 names=list({b['bone'] for b in profile['bindings']});validate(profile,names)
 with pytest.raises(ValueError):validate(profile,names+[names[0]])
 with pytest.raises(ValueError):validate(profile,names[1:])
def test_corruption_rejected(profile):
 for mutate in [lambda p:p['secondary']['arms'][0].update(axis=[0,0,0]),lambda p:p['secondary'].update(breathPeriod=float('nan')),lambda p:p['bindings'].append(p['bindings'][0]),lambda p:p['sequence'].update(walkEnd=0)]:
  p=deepcopy(profile);mutate(p)
  with pytest.raises(ValueError):validate(p)
def test_pause_determinism_and_settling(profile):
 a=SecondaryState(profile);b=SecondaryState(profile)
 for i in range(500):assert a.step(1/60,1,.5)==b.step(1/60,1,.5)
 before=a.step(0,0,-1);assert a.step(0,3,1)==before
 for i in range(600):a.step(1/60,0,1)
 assert a.walking<1e-12
 with pytest.raises(ValueError):a.step(-1,0,0)
