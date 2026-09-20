"""Actual-rig bridge fixtures. Passing tests do not approve anatomy or gait."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.biomechanics.kinematic_seed import Seed,align,emit_glb,load_rig
from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks
from eonwild_motion.solve.whole_body_gait_transition import _encode

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def source():
    return Glb(ROOT/'assets/animals/Models/Alioramus-altai.glb')

@pytest.fixture
def profile():
    return json.loads((ROOT/'catalog/biomechanics/alioramus-altai.kinematic-seed.v1.json').read_text())

@pytest.fixture(scope='module')
def sample(source):
    profile=json.loads((ROOT/'catalog/biomechanics/alioramus-altai.kinematic-seed.v1.json').read_text())
    seed=Seed(source,profile);times=np.array([0,.175,.35,.7,1.05,1.4])
    poses=[seed.pose(float(t)) for t in times]
    return seed,times,np.array([p[0] for p in poses]),np.array([p[1] for p in poses]),np.array([p[2] for p in poses]),poses


def test_actual_asset_identity_and_complete_influences(source,profile):
    seed=Seed(source,profile)
    assert hashlib.sha256(source.raw).hexdigest()==profile['source']['sha256']
    assert len(source.document['skins'][0]['joints'])==76
    assert seed.skin.weights.shape==(15952,12)
    assert not source.document.get('animations')

@pytest.mark.parametrize('field,value', [('sha256','0'*64)])
def test_wrong_source_rejected(source,profile,field,value):
    profile['source'][field]=value
    with pytest.raises(ContractError,match='source hash'):Seed(source,profile)


def test_unknown_frame_rejected(source,profile):
    profile['coordinate']['up']=[0,0,1]
    with pytest.raises(ContractError,match='normalize'):Seed(source,profile)


def test_missing_semantic_role_rejected(source,profile):
    profile['roles']['head']='missing'
    with pytest.raises(ContractError,match='missing semantic'):Seed(source,profile)


def test_swapped_chain_topology_rejected(source,profile):
    c=profile['roles']['legs']['left']['contactChain'];c[1],c[2]=c[2],c[1]
    with pytest.raises(ContractError,match='topology'):Seed(source,profile)


def test_shared_bilateral_leg_rejected(source,profile):
    profile['roles']['legs']['right']['contactChain']=profile['roles']['legs']['left']['contactChain'][:]
    with pytest.raises(ContractError,match='share joints'):Seed(source,profile)

@pytest.mark.parametrize('value',[float('nan'),float('inf'),True,'fast'])
def test_invalid_settings_rejected(source,profile,value):
    profile['authored_seed']['stride_m']=value
    with pytest.raises(ContractError):Seed(source,profile)

@pytest.mark.parametrize('hz',[0,9,241,True,30.5])
def test_bad_sample_rate_rejected(source,profile,hz):
    with pytest.raises(ContractError,match='sample rate'):Seed(source,profile).sample(hz)


def test_seed_is_finite_looping_and_skin_clear(sample):
    seed,times,t,q,s,poses=sample
    assert np.isfinite(t).all() and np.isfinite(q).all()
    assert min(p[3]['minimum_skin_y_m'] for p in poses)>-1e-5
    assert max(max(p[3]['foot_fk_error_m'].values()) for p in poses)<5e-5
    inplace=t.copy();inplace[:,seed.root,2]-=times*.7
    np.testing.assert_allclose(inplace[0],inplace[-1],atol=1e-10)
    qa=q[0]/np.linalg.norm(q[0],axis=1,keepdims=True);qb=q[-1]/np.linalg.norm(q[-1],axis=1,keepdims=True)
    np.testing.assert_allclose(np.abs(np.sum(qa*qb,axis=1)),1,atol=1e-10,rtol=0)
    for row in poses:
        assert any(row[3]['contacts'].values())


def test_standing_is_separate_and_does_not_rebind(source,profile):
    seed=Seed(source,profile);original=source.raw
    t,q,s,row=seed.pose(0,standing=True)
    assert row['minimum_skin_y_m']>-.00001
    assert all(row['contacts'].values())
    assert source.raw==original
    assert not np.array_equal(t,np.array(source.rest_translation))


def test_fixed_segment_lengths(sample):
    seed,times,t,q,s,poses=sample
    for ti,qi,si in zip(t,q,s):
        world=seed.skin.world(ti,qi,si)
        for chain in seed.legs.values():
            for p,c in zip(chain,chain[1:]):
                assert abs(np.linalg.norm(world[p,:3,3]-world[c,:3,3])-np.linalg.norm(seed.rest[p,:3,3]-seed.rest[c,:3,3]))<5e-5


def test_deterministic_pose_has_no_carried_state(sample):
    seed,times,t,q,s,poses=sample
    seed.pose(.52)
    other=seed.pose(float(times[1]))
    np.testing.assert_array_equal(other[0],t[1]);np.testing.assert_array_equal(other[1],q[1])


def test_original_binary_data_survives_emission(sample):
    seed,times,t,q,s,poses=sample
    raw=emit_glb(seed.source,[('test',times,t,q)])
    out=Glb(raw=raw)
    for key in ('nodes','meshes','skins','materials','images','textures'):
        assert out.document.get(key)==seed.source.document.get(key)
    for i in range(len(seed.source.document['accessors'])):
        assert out.accessor_bytes(i)==seed.source.accessor_bytes(i)
    assert bytes(out.binary[:len(seed.source.binary)])==bytes(seed.source.binary)
    tracks,actual=read_animation_tracks(out,'test',require_common_timeline=True)
    np.testing.assert_allclose(actual,times,atol=1e-7)
    assert all(np.isfinite(tr.sample(.2625)).all() for tr in tracks.values())

@pytest.mark.parametrize('fault',['unordered','zero-quaternion','nan-translation'])
def test_invalid_motion_is_not_emitted(sample,fault):
    seed,times,t,q,s,poses=sample;times=times.copy();t=t.copy();q=q.copy()
    if fault=='unordered':times[1]=times[0]
    if fault=='zero-quaternion':q[0,0]=0
    if fault=='nan-translation':t[0,0,0]=np.nan
    with pytest.raises(ContractError):emit_glb(seed.source,[('bad',times,t,q)])


def test_renamed_actual_rig_uses_profile_not_bone_literals(source,profile,sample):
    doc=deepcopy(source.document);mapping={n['name']:'renamed_'+str(i) for i,n in enumerate(doc['nodes'])}
    for node in doc['nodes']:node['name']=mapping[node['name']]
    renamed=Glb(raw=_encode(doc,bytearray(source.binary)))
    def rename(v):
        if isinstance(v,str):return mapping[v]
        if isinstance(v,dict):return {k:rename(x) for k,x in v.items()}
        return [rename(x) for x in v]
    profile['roles']=rename(profile['roles']);profile['source']['sha256']=hashlib.sha256(renamed.raw).hexdigest()
    seed=Seed(renamed,profile);pose=seed.pose(.175)
    np.testing.assert_allclose(pose[0],sample[2][1],atol=1e-12)
    np.testing.assert_allclose(pose[1],sample[3][1],atol=1e-12)


def test_real_opensim_serialized_replay(sample,tmp_path):
    pytest.importorskip('opensim')
    from eonwild_motion.biomechanics.opensim_bridge import replay
    seed,times,t,q,s,poses=sample
    rt,rq,receipt=replay(seed,tmp_path,times,t,q,s)
    assert receipt['status']=='PASS_KINEMATIC_BRIDGE_ONLY'
    assert receipt['moving_bodies']==76 and receipt['coordinates']==231
    assert receipt['all_coordinates_accounted_for']
    assert receipt['max_target_frame_position_error_m']<5e-5
    assert receipt['dinosaur_prediction']=='NOT_RUN'
    assert receipt['unity_parity']=='NOT_RUN'
    for i in range(len(times)):
        np.testing.assert_allclose(seed.skin.world(rt[i],rq[i],s[i]),seed.skin.world(t[i],q[i],s[i]),atol=1e-5)


def test_antipodal_alignment_fails_instead_of_inventing_twist():
    with pytest.raises(ContractError,match='antipodal'):align([0,1,0],[0,-1,0])
