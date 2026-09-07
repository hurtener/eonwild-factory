import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import (
    G_M_S2, apply_uniform_geometry_scale, biomechanics_report, load_animal_instance,
    verify_source_calibration,
)
from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.factory.source import admit_geometry,geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.grounded_gait import load_grounded_gait, sample_grounded_gait
from eonwild_motion.solve.performance import load_performance
from test_v9_airborne_gait import fixture

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v1.json'
SOURCE_SHA='044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6'


def loaded():
    return load_animal_instance(json.loads(PROFILE.read_text()),source_sha256=SOURCE_SHA)


def test_adult_benchmark_keeps_specimen_specific_evidence_separate():
    animal=loaded()
    assert animal['document']['specimen']=='PIN 552-1'
    assert animal['mass_kg']==2816.3
    assert animal['hindlimb_length_m']==2.415
    source=(2.809591402742045+2.809591766137104)/2
    assert animal['uniform_scale']==pytest.approx(2.415/source,rel=0,abs=1e-15)
    assert animal['document']['measurements']['body_mass']['source']['locator'].startswith('Table 2')
    assert '0.8' in animal['document']['measurements']['hip_height_proxy']['evidence_kind']
    assert animal['document']['morphology_comparison']['status']=='UNVERIFIED'
    assert 'without specimen identifier' in animal['document']['morphology_comparison']['source']['locator']


@pytest.mark.parametrize('case',['source','mass-unit','missing-provenance','nan','policy','specimen'])
def test_animal_contract_fails_closed(case):
    data=json.loads(PROFILE.read_text());sha=SOURCE_SHA
    if case=='source':sha='0'*64
    elif case=='mass-unit':data['measurements']['body_mass']['unit']='lb'
    elif case=='missing-provenance':del data['measurements']['hindlimb_length']['source']
    elif case=='nan':data['measurements']['hip_height_proxy']['value']=float('nan')
    elif case=='policy':data['geometry_calibration']['scale_policy']='mass_only'
    else:data['specimen']=''
    with pytest.raises(ContractError):load_animal_instance(data,source_sha256=sha)


def test_uniform_scale_changes_measured_geometry_not_only_metadata():
    source,roles=fixture(upper_body=True)
    source=Glb.from_bytes(admit_geometry(source,roles,reference_clip='source')[0])
    before=geometry_height(source,roles,[0,1,0]);scale=loaded()['uniform_scale']
    apply_uniform_geometry_scale(source,scale)
    after=geometry_height(source,roles,[0,1,0])
    assert after==pytest.approx(before*scale)
    roots=[i for i,parent in enumerate(source.parents) if parent is None]
    assert roots and all(source.rest_scale[i][0]==pytest.approx(scale) for i in roots)


def test_committed_source_calibration_is_recomputed_from_bound_rig_and_skin():
    recipe=json.loads((ROOT/'recipes/heavy-biped/walk.v3.json').read_text())
    source=Glb.from_bytes((ROOT/recipe['source']['path']).read_bytes())
    roles=json.loads((ROOT/recipe['rig']['path']).read_text())['roles']
    contact=json.loads((ROOT/recipe['contact_profile']['path']).read_text())
    animal=loaded()
    actual=verify_source_calibration(animal,source,roles,contact,recipe['forward_axis'],recipe['up_axis'])
    assert actual['skin_length']==pytest.approx(11.961980831084903,abs=2e-6)
    broken=deepcopy(animal);broken['source_measurements_m']['skin_length']+=.01
    with pytest.raises(ContractError,match='skin_length'):
        verify_source_calibration(broken,source,roles,contact,recipe['forward_axis'],recipe['up_axis'])


def test_benchmark_recipe_binds_animal_without_superseding_engineering_walk():
    path=ROOT/'recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v1.json'
    recipe,paths=load_recipe(path,ROOT)
    engineering=json.loads((ROOT/'recipes/heavy-biped/walk.v3.json').read_text())
    assert recipe['animal']['path']==str(PROFILE.relative_to(ROOT))
    assert 'animal' in paths and 'supersedes' not in recipe
    assert recipe['program_profile'] != engineering['program_profile']
    assert recipe['performance_profile'] != engineering['performance_profile']


def test_adult_walk_profile_has_observable_distal_release_and_tail_coordination():
    adult=json.loads((ROOT/'recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v1.json').read_text())
    engineering=json.loads((ROOT/'recipes/heavy-biped/walk.v3.json').read_text())
    adult_gait=load_grounded_gait(json.loads((ROOT/adult['program_profile']['path']).read_text()))
    engineering_gait=load_grounded_gait(json.loads((ROOT/engineering['program_profile']['path']).read_text()))
    times=[2*adult_gait.step_period_s*i/240 for i in range(241)]
    adult_feet=[sample_grounded_gait(adult_gait,t,2.)['feet']['left'] for t in times]
    engineering_feet=[sample_grounded_gait(engineering_gait,t,2.)['feet']['left'] for t in times]
    assert max(row['foot_pitch_degrees'] for row in adult_feet) > max(row['foot_pitch_degrees'] for row in engineering_feet)+7
    assert min(row['foot_pitch_degrees'] for row in adult_feet) < min(row['foot_pitch_degrees'] for row in engineering_feet)-7
    assert max(row['toe_flex_degrees'] for row in adult_feet) > max(row['toe_flex_degrees'] for row in engineering_feet)+5
    adult_performance_document=json.loads((ROOT/adult['performance_profile']['path']).read_text())
    adult_performance=load_performance(adult_performance_document)
    engineering_performance=load_performance(json.loads((ROOT/engineering['performance_profile']['path']).read_text()))
    assert adult_performance.tail_yaw_degrees > engineering_performance.tail_yaw_degrees
    assert adult_performance.tail_lag_fraction > engineering_performance.tail_lag_fraction
    assert adult_performance_document['classification']=='art-directed coordination; no force or biological claim'
    assert adult_performance_document['reference']['classification']=='visual direction only; no biological or force claim'
    assert adult_performance_document['reference']['source_frame_rate_hz']==24
    for asset in adult_performance_document['reference']['assets']:
        assert hashlib.sha256((ROOT/asset['path']).read_bytes()).hexdigest()==asset['sha256']


def test_report_exposes_scale_kinematics_and_nonclaims():
    plan={'samples':[
        {'time_s':0.,'root_forward_m':0.,'pelvis_height_offset_m':0.},
        {'time_s':.5,'root_forward_m':1.,'pelvis_height_offset_m':.1},
        {'time_s':1.,'root_forward_m':2.,'pelvis_height_offset_m':0.},
    ]}
    report=biomechanics_report(loaded(),plan,actual_semantic_height_m=2.)
    assert report['mass_proxies']['weight_newtons']==pytest.approx(2816.3*G_M_S2)
    assert report['kinematics']['peak_root_speed_mps']==pytest.approx(2.)
    assert report['kinematics']['froude_using_study_hip_proxy'] != report['kinematics']['froude_using_actual_semantic_height']
    assert report['kinematics']['peak_pelvis_vertical_acceleration_in_g']>0
    assert report['geometry']['planned_pelvis_height_to_published_hindlimb_ratio_range']==pytest.approx([2/2.415,2.1/2.415])
    assert report['force_aware_solver']=='NOT_IMPLEMENTED'
    assert report['anatomical_fit']['status']=='UNVERIFIED'
    assert report['anatomical_fit']['source_semantic_segment_fractions'] != pytest.approx(report['anatomical_fit']['published_taxon_level_segment_fractions'],abs=.01)
    assert report['mass_proxies']['peak_pelvis_mass_times_acceleration_over_body_weight']>0
    assert report['contact_force_distribution']==report['segment_inertia']==report['stress_and_tissue_limits']=='NOT_EVALUATED'
    assert 'not whole-body center of mass' in report['pelvis_acceleration_force_interpretation']
