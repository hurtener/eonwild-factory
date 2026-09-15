from copy import deepcopy
from pathlib import Path
import json
import numpy as np
import pytest
from eonwild_motion.planning.running import resolve_running,running_sample
from eonwild_motion.planning.running import running_adjustment_sample,build_running_review_plan
ROOT=Path(__file__).resolve().parents[1]
RECIPE=json.loads((ROOT/'catalog/behaviors/running-review.v1.json').read_text())

def profile(animal='allo'):
 return json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())

@pytest.mark.parametrize('animal',['allo','tarbo'])
def test_declared_stride_and_speed_survive_resolution(animal):
 p=profile(animal);g=resolve_running(p,RECIPE);h=p['authoring']['bodyHeightM'];values=p['locomotion']['run']
 assert g.step_length_body_heights*h==pytest.approx(values['stepLength']['value'])
 assert g.step_length_body_heights*h/g.step_period_s==pytest.approx(values['preferredSpeed']['value'])
 assert 2*g.step_length_body_heights*h==pytest.approx(values['sameFootStride']['value'])
 assert g.touchdown_reach_body_heights*h==pytest.approx(RECIPE['touchdown_reach_step_fraction']*values['stepLength']['value'])
 p['id']='renamed';p['authoring']['animalInstance']['taxon']='unknown'
 assert resolve_running(p,RECIPE)==g

def test_running_contacts_and_recovery_are_periodic_and_continuous():
 p=profile();g=resolve_running(p,RECIPE);h=p['authoring']['bodyHeightM'];cycle=2*g.step_period_s;eps=1e-7
 for t in np.linspace(.001,cycle-.001,150):
  a=running_sample(g,t,h);b=running_sample(g,t+cycle,h)
  assert a['support_count'] in (0,1)
  for s in a['feet']:
   x,y=a['feet'][s],b['feet'][s]
   assert x['contact']==y['contact']
   assert y['forward_m']-x['forward_m']==pytest.approx(2*g.step_length_body_heights*h)
   assert y['height_m']==pytest.approx(x['height_m'])
 for boundary in [0,g.step_period_s*(1-g.flight_fraction),g.step_period_s,cycle]:
  a=running_sample(g,boundary-eps,h);b=running_sample(g,boundary+eps,h)
  assert abs(a['pelvis_height_offset_m']-b['pelvis_height_offset_m'])<1e-5
  for s in a['feet']:
   for key in ['forward_m','height_m','foot_pitch_degrees']:
    assert abs(a['feet'][s][key]-b['feet'][s][key])<1e-4

def test_running_values_reject_incoherent_units_and_stride():
 p=profile();p['locomotion']['run']['stepLength']['unit']='cm'
 with pytest.raises(ValueError):resolve_running(p,RECIPE)
 p=profile();p['locomotion']['run']['sameFootStride']['value']*=1.2
 with pytest.raises(ValueError):resolve_running(p,RECIPE)
 r=deepcopy(RECIPE);r['touchdown_reach_step_fraction']=0
 with pytest.raises(ValueError):resolve_running(profile(),r)

@pytest.mark.parametrize('animal',['allo','tarbo'])
def test_run_braking_retains_useful_support_and_stops_without_a_reverse_step(animal):
 p=profile(animal);g=resolve_running(p,RECIPE);h=p['authoring']['bodyHeightM'];walk=p['locomotion']['walk']['preferredSpeed']['value']
 rows=[running_adjustment_sample(g,t,h,kind='brake',walking_speed=walk) for t in np.linspace(0,1.8*g.step_period_s,181)]
 assert all(r['feet']['left']['contact'] for r in rows)
 assert all(r['feet']['left']['foot_pitch_degrees']==0 for r in rows)
 assert all(r['feet']['left']['forward_m']==rows[0]['feet']['left']['forward_m'] for r in rows)
 assert np.min(np.diff([r['root_forward_m'] for r in rows]))>=-1e-9
 assert np.min(np.diff([r['feet']['right']['forward_m'] for r in rows]))>=-1e-9
 assert rows[-1]['support_count']==2
 assert rows[-1]['root_forward_m']==pytest.approx(rows[-2]['root_forward_m'])
 for f in rows[-1]['feet'].values():assert f['foot_pitch_degrees']==0
 plan=build_running_review_plan(g,h,walk)
 assert np.min(np.diff(np.asarray([r['time_s'] for r in plan['samples']],dtype=np.float32)))>0
 assert {s['name'] for s in plan['segments']}=={'run','runEntryLeft','runEntryRight','runBrakeLeft','runBrakeRight'}

def test_running_approach_does_not_add_a_second_recovery_fold():
 from eonwild_motion.solve.airborne_gait import _recovery_pitch_target
 p=profile();g=resolve_running(p,RECIPE);h=p['authoring']['bodyHeightM']
 for u in np.linspace(.45,.99,30):
  t=g.step_period_s*(1-g.flight_fraction)+u*g.step_period_s*(1+g.flight_fraction)
  f=running_sample(g,t,h)['feet']['left']
  assert _recovery_pitch_target(g,f,airborne=True)==f['foot_pitch_degrees']
  if u>.8: assert abs(f['pad_pitch_degrees'])<1e-8
